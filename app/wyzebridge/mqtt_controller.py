"""
MQTT Controller for API-Only mode.
Handles MQTT integration and Home Assistant discovery without video streaming.
"""

import contextlib
import json
from typing import Optional, Dict, Any
from time import sleep

import paho.mqtt.client

from wyzecam.api_models import WyzeCamera
from wyzebridge.bridge_utils import env_bool
from wyzebridge.config import IMG_PATH, MQTT_ENABLED, MQTT_DISCOVERY, IMG_TYPE
from wyzebridge.logging import logger
from wyzebridge.mqtt import (
    mqtt_enabled, publish_discovery, mqtt_sub_topic, bridge_status,
    publish_topic, update_mqtt_state, update_preview, cam_control
)
from wyzebridge.wyze_api import WyzeApi
from wyzebridge.wyze_commands import GET_CMDS, SET_CMDS, CMD_VALUES, PARAMS


class MqttController:
    """MQTT Controller for API-only bridge mode."""
    
    def __init__(self, api: WyzeApi, cameras: Dict[str, WyzeCamera]):
        self.api = api
        self.cameras = cameras
        self.mqtt_client: Optional[paho.mqtt.client.Client] = None
        self.running = False

    def start(self) -> Optional[paho.mqtt.client.Client]:
        """Start MQTT controller for API-only mode."""
        if not MQTT_ENABLED:
            logger.info("📡 MQTT is disabled")
            return None
            
        logger.info("📡 Starting MQTT controller for API-only mode...")
        
        # Publish discovery messages for all cameras
        self._publish_discovery_all()
        
        # Setup MQTT subscriptions for camera control
        self.mqtt_client = cam_control(self._format_cameras(), self._handle_mqtt_command)
        
        if self.mqtt_client:
            self.running = True
            bridge_status(self.mqtt_client)
            logger.info("✅ MQTT controller started successfully!")
        else:
            logger.error("❌ Failed to start MQTT controller")
            
        return self.mqtt_client

    def stop(self):
        """Stop MQTT controller."""
        if self.mqtt_client and self.running:
            logger.info("⏹️ Stopping MQTT controller...")
            self.running = False
            
            # Publish offline status for all cameras
            for cam_uri in self.cameras:
                update_mqtt_state(cam_uri, "stopped")
                
            # Publish bridge offline status
            if self.mqtt_client:
                self.mqtt_client.publish("wyze-bridge/state", "offline", retain=True)
                self.mqtt_client.disconnect()

    def update_cameras(self, cameras: Dict[str, WyzeCamera]):
        """Update camera list and republish discovery."""
        self.cameras = cameras
        self._publish_discovery_all()

    def publish_command_result(self, cam_uri: str, command: str, result: Dict[str, Any]):
        """Publish command result to MQTT."""
        if not self.running or not self.mqtt_client:
            return
            
        topic = f"{cam_uri}/{command}"
        
        if result.get("status") == "success":
            # Publish successful command result
            if command in ["power", "state"]:
                state = "online" if result.get("response") == "on" else "stopped"
                update_mqtt_state(cam_uri, state)
            else:
                payload = result.get("response", result.get("value", ""))
                publish_topic(topic, payload, retain=True)
        else:
            # Log failed commands
            logger.warning(f"[MQTT] Command failed for {cam_uri}/{command}: {result}")

    def update_preview(self, cam_name: str):
        """Update camera preview/thumbnail via MQTT."""
        if not self.running:
            return
            
        update_preview(cam_name)

    def _format_cameras(self) -> Dict[str, Any]:
        """Format cameras for MQTT controller."""
        formatted = {}
        for uri, cam in self.cameras.items():
            # Create a mock stream object with camera info
            formatted[uri] = type('MockStream', (), {
                'camera': cam,
                'enabled': True,
                'status': 'online'
            })()
            
        return formatted

    def _publish_discovery_all(self):
        """Publish Home Assistant discovery for all cameras."""
        if not MQTT_DISCOVERY:
            return
            
        logger.info("📢 Publishing MQTT discovery for API-only cameras...")
        
        for cam_uri, cam in self.cameras.items():
            try:
                # Publish discovery for API-only mode (no streaming)
                publish_discovery(cam_uri, cam, stopped=False)
                
                # Update camera state to indicate API control is available
                update_mqtt_state(cam_uri, "online")
                
                logger.debug(f"📢 Published discovery for {cam_uri}")
            except Exception as ex:
                logger.error(f"❌ Failed to publish discovery for {cam_uri}: {ex}")

    def _handle_mqtt_command(self, cam_name: str, topic: str, payload: Any) -> Dict[str, Any]:
        """Handle MQTT command for camera control."""
        logger.info(f"[MQTT] Received command: {cam_name}/{topic} = {payload}")
        
        # Get camera object
        if not (cam := self.cameras.get(cam_name)):
            return {"status": "error", "response": f"Camera '{cam_name}' not found"}

        try:
            # Handle special commands
            if topic == "state":
                return self._handle_state_command(cam_name, cam, payload)
            elif topic == "power":
                return self._handle_power_command(cam_name, cam, payload)
            elif topic == "update_snapshot":
                return self._handle_snapshot_command(cam_name, cam)
            elif topic in GET_CMDS:
                return self._handle_get_command(cam, topic, payload)
            elif topic in SET_CMDS:
                return self._handle_set_command(cam, topic, payload)
            elif topic in PARAMS:
                return self._handle_param_command(cam, topic, payload)
            else:
                return {"status": "error", "response": f"Unknown command: {topic}"}
                
        except Exception as ex:
            logger.error(f"[MQTT] Command error for {cam_name}/{topic}: [{type(ex).__name__}] {ex}")
            return {"status": "error", "response": str(ex)}

    def _handle_state_command(self, cam_name: str, cam: WyzeCamera, payload: Any) -> Dict[str, Any]:
        """Handle camera state command (API-only mode doesn't control streaming)."""
        if payload in ["start", "online"]:
            # In API-only mode, "start" means camera is available for control
            update_mqtt_state(cam_name, "online")
            return {"status": "success", "response": "Camera available for API control"}
        elif payload in ["stop", "stopped"]:
            # In API-only mode, "stop" means camera control is disabled
            update_mqtt_state(cam_name, "stopped")
            return {"status": "success", "response": "Camera API control disabled"}
        else:
            return {"status": "error", "response": f"Invalid state: {payload}"}

    def _handle_power_command(self, cam_name: str, cam: WyzeCamera, payload: Any) -> Dict[str, Any]:
        """Handle camera power command."""
        if payload == "restart":
            # Use API to restart camera
            result = self.api.run_action(cam, "restart")
            if result.get("status") == "success":
                update_mqtt_state(cam_name, "online")
            return result
        elif payload in ["on", "off"]:
            # Power on/off through API
            action = "power_on" if payload == "on" else "power_off"
            result = self.api.run_action(cam, action)
            if result.get("status") == "success":
                state = "online" if payload == "on" else "stopped"
                update_mqtt_state(cam_name, state)
            return result
        else:
            return {"status": "error", "response": f"Invalid power command: {payload}"}

    def _handle_snapshot_command(self, cam_name: str, cam: WyzeCamera) -> Dict[str, Any]:
        """Handle snapshot update command."""
        try:
            # Update thumbnail from Wyze cloud
            if self.api.save_thumbnail(cam_name, ""):
                # Publish updated image to MQTT
                self.update_preview(cam_name)
                return {"status": "success", "response": "Snapshot updated"}
            else:
                return {"status": "error", "response": "Failed to update snapshot"}
        except Exception as ex:
            return {"status": "error", "response": str(ex)}

    def _handle_get_command(self, cam: WyzeCamera, topic: str, payload: Any) -> Dict[str, Any]:
        """Handle GET command via API."""
        if topic in ["state", "power", "notifications", "update_snapshot", "motion_detection"]:
            # These are handled by the bridge, return success
            return {"status": "success", "response": "online"}
        
        # Use API to get camera info/property
        cmd = GET_CMDS.get(topic)
        if cmd:
            return self.api.run_action(cam, cmd)
        elif topic in PARAMS:
            # Get device parameter
            pid = PARAMS[topic]
            return self.api.get_device_info(cam, pid=pid)
        else:
            return {"status": "error", "response": f"Unknown GET command: {topic}"}

    def _handle_set_command(self, cam: WyzeCamera, topic: str, payload: Any) -> Dict[str, Any]:
        """Handle SET command via API."""
        if topic in ["state", "power"]:
            # Handled by special command handlers
            return {"status": "error", "response": f"Use specific handler for {topic}"}
        
        # Convert payload to API values
        if isinstance(payload, str) and payload.lower() in CMD_VALUES:
            payload = CMD_VALUES[payload.lower()]
        
        # Use API to set camera property
        cmd = SET_CMDS.get(topic)
        if cmd:
            # Direct TUTK command
            return self.api.run_action(cam, f"{cmd}:{payload}")
        elif topic in PARAMS:
            # Set device parameter
            pid = PARAMS[topic]
            return self.api.set_property(cam, pid, str(payload))
        elif topic in ["fps", "bitrate"]:
            # Special video parameters (API-only mode)
            pid = PARAMS.get(topic, "")
            if pid:
                return self.api.set_property(cam, pid, str(payload))
            else:
                return {"status": "error", "response": f"Parameter not available for {topic}"}
        else:
            return {"status": "error", "response": f"Unknown SET command: {topic}"}

    def _handle_param_command(self, cam: WyzeCamera, topic: str, payload: Any) -> Dict[str, Any]:
        """Handle parameter-based command via API."""
        pid = PARAMS.get(topic)
        if not pid:
            return {"status": "error", "response": f"Unknown parameter: {topic}"}
        
        if payload == "" or payload == "get":
            # Get parameter value
            return self.api.get_device_info(cam, pid=pid)
        else:
            # Set parameter value
            return self.api.set_property(cam, pid, str(payload))