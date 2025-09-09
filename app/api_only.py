#!/usr/bin/env python3

import json
import os
import time
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    Response,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    jsonify
)
from werkzeug.exceptions import NotFound

from wyzebridge.build_config import VERSION
# Import WyzeApiBridge dynamically to avoid circular imports
from wyzebridge import config
from wyzebridge.auth import WbAuth


def create_app():
    """Create Flask app for API-only mode."""
    app = Flask(__name__)
    
    # Import WyzeApiBridge here to avoid circular imports
    from wyze_api_bridge import WyzeApiBridge
    wb = WyzeApiBridge()
    
    try:
        wb.start()
    except RuntimeError as ex:
        print(f"❌ Failed to start API-only bridge: {ex}")
        print("Please ensure your credentials are correct and host is up to date.")
        exit(1)

    def auth_required(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if not wb.api.auth:
                return jsonify({"error": "Authentication required"}), 401
            return view(*args, **kwargs)
        return wrapped_view

    @app.route("/login", methods=["GET", "POST"])
    def wyze_login():
        """Login endpoint for Wyze credentials."""
        if wb.api.auth:
            return jsonify({"status": "already authenticated"})
            
        if request.method == "GET":
            return jsonify({
                "status": "login required",
                "fields": ["email", "password", "keyId", "apiKey"]
            })

        # Handle token-based auth
        tokens = request.form.get("tokens") or request.json.get("tokens") if request.is_json else None
        refresh = request.form.get("refresh") or request.json.get("refresh") if request.is_json else None

        if tokens or refresh:
            wb.api.token_auth(tokens=tokens, refresh=refresh)
            return jsonify({"status": "success", "method": "token"})

        # Handle credential-based auth
        data = request.get_json() if request.is_json else request.form
        credentials = {
            "email": data.get("email"),
            "password": data.get("password"),
            "key_id": data.get("keyId"),
            "api_key": data.get("apiKey"),
        }

        if all(credentials.values()):
            wb.api.creds.update(**credentials)
            return jsonify({"status": "success", "method": "credentials"})

        return jsonify({"status": "error", "message": "missing credentials"}), 400

    @app.route("/")
    def index():
        """API-only mode information endpoint."""
        return jsonify({
            "service": "Docker Wyze Bridge API-Only",
            "version": VERSION,
            "mode": "api_only",
            "description": "Camera control and MQTT integration without video streaming",
            "endpoints": {
                "health": "/health",
                "login": "/login",
                "cameras": "/api",
                "camera_info": "/api/<camera_name>",
                "camera_control": "/api/<camera_name>/<command>",
                "thumbnail": "/thumb/<camera_name>.jpg",
                "restart": "/restart/<command>"
            }
        })

    @app.route("/health")
    def health():
        """Health check endpoint."""
        health_data = wb.health()
        status_code = 200 if health_data.get("wyze_authed", False) else 503
        return jsonify(health_data), status_code

    @app.route("/api")
    @auth_required
    def api_all_cams():
        """Get information about all cameras."""
        cameras = {}
        for uri, cam in wb._cameras.items():
            cameras[uri] = {
                "name": cam.nickname,
                "uri": uri,
                "mac": cam.mac,
                "model": cam.product_model,
                "firmware": cam.firmware_ver,
                "ip": cam.ip,
                "online": True,  # API-only mode doesn't track streaming status
                "pan_cam": cam.is_pan_cam,
                "rtsp_fw": False,  # No RTSP in API-only mode
                "thumbnail_url": f"/thumb/{uri}.jpg",
                "control_url": f"/api/{uri}",
            }
        
        return jsonify({
            "cameras": cameras,
            "total": len(cameras),
            "mode": "api_only"
        })

    @app.route("/api/<string:cam_name>")
    @auth_required  
    def api_cam(cam_name: str):
        """Get information about a specific camera."""
        if cam_name not in wb._cameras:
            return jsonify({"error": f"Camera '{cam_name}' not found"}), 404
            
        cam = wb._cameras[cam_name]
        return jsonify({
            "name": cam.nickname,
            "uri": cam_name,
            "mac": cam.mac,
            "model": cam.product_model,
            "firmware": cam.firmware_ver,
            "ip": cam.ip,
            "online": True,
            "pan_cam": cam.is_pan_cam,
            "thumbnail_url": f"/thumb/{cam_name}.jpg",
            "control_commands": [
                "power", "notifications", "motion_detection", "irled", 
                "night_vision", "status_light", "alarm", "update_snapshot"
            ] + (["rotary_action", "rotary_degree", "pan_cruise", "motion_tracking"] if cam.is_pan_cam else [])
        })

    @app.route("/api/<cam_name>/<cam_cmd>", methods=["GET", "PUT", "POST"])
    @app.route("/api/<cam_name>/<cam_cmd>/<path:payload>")
    @auth_required
    def api_cam_control(cam_name: str, cam_cmd: str, payload: str = ""):
        """Control camera via API commands."""
        if cam_name not in wb._cameras:
            return jsonify({"error": f"Camera '{cam_name}' not found"}), 404

        # Extract payload from various sources
        if not payload and (args := request.values.to_dict()):
            args.pop("api", None)
            payload = next(iter(args.values())) if len(args) == 1 else args
        elif not payload and request.is_json:
            json_data = request.get_json()
            if isinstance(json_data, dict):
                payload = json_data if len(json_data) > 1 else list(json_data.values())[0]
            else:
                payload = json_data
        elif not payload and request.data:
            payload = request.data.decode()

        # Control the camera
        result = wb.control_camera(cam_name, cam_cmd, payload)
        
        # Update MQTT if available
        if wb.mqtt_controller:
            wb.mqtt_controller.publish_command_result(cam_name, cam_cmd, result)
            
        return jsonify(result)

    @app.route("/thumb/<string:img_file>")
    @auth_required
    def thumbnail(img_file: str):
        """Serve camera thumbnail."""
        cam_name = Path(img_file).stem
        
        # Update thumbnail from Wyze cloud
        if wb.api.save_thumbnail(cam_name, ""):
            return send_from_directory(config.IMG_PATH, img_file)
        
        # Return placeholder if no thumbnail available
        return redirect("/static/notavailable.svg", code=307)

    @app.route("/img/<string:img_file>")
    @auth_required
    def img(img_file: str):
        """Serve camera images with expiry check."""
        try:
            if exp := request.args.get("exp"):
                created_at = os.path.getmtime(config.IMG_PATH + img_file)
                if time.time() - created_at > int(exp):
                    raise NotFound
            return send_from_directory(config.IMG_PATH, img_file)
        except (NotFound, FileNotFoundError, ValueError):
            return thumbnail(img_file)

    @app.route("/restart/<string:restart_cmd>", methods=["POST"])
    @auth_required
    def restart_bridge(restart_cmd: str):
        """Restart bridge components."""
        if restart_cmd == "cameras":
            wb.refresh_cameras()
            return jsonify({"result": "ok", "restart": "cameras"})
        elif restart_cmd == "api":
            wb.restart(fresh_data=False)
            return jsonify({"result": "ok", "restart": "api"})  
        elif restart_cmd == "all":
            wb.restart(fresh_data=True)
            return jsonify({"result": "ok", "restart": "all"})
        else:
            return jsonify({"result": "error", "message": f"Unknown restart command: {restart_cmd}"}), 400

    @app.route("/status")
    @auth_required
    def bridge_status():
        """Get bridge status information."""
        return jsonify({
            "mode": "api_only",
            "version": VERSION,
            "health": wb.health(),
            "cameras": len(wb._cameras),
            "mqtt_enabled": wb.mqtt_controller is not None
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app


def main():
    """Main entry point for API-only Flask app."""
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()