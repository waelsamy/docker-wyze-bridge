#!/usr/bin/env python3

import signal
import sys
import threading
from time import sleep
from typing import Optional

from wyzebridge.build_config import BUILD_STR, VERSION
from wyzebridge.config import BRIDGE_IP, HASS_TOKEN, IMG_PATH, TOKEN_PATH
from wyzebridge.auth import WbAuth
from wyzebridge.bridge_utils import env_bool, migrate_path
from wyzebridge.hass import setup_hass
from wyzebridge.logging import logger
from wyzebridge.wyze_api import WyzeApi
# Import MqttController after class definition to avoid circular imports
from wyzecam.api_models import WyzeAccount, WyzeCamera

from os import makedirs
import paho.mqtt.client


setup_hass(HASS_TOKEN)

makedirs(TOKEN_PATH, exist_ok=True)
makedirs(IMG_PATH, exist_ok=True)

if HASS_TOKEN:
    migrate_path("/config/wyze-bridge/", "/config/")


class WyzeApiBridge(threading.Thread):
    """API-Only version of WyzeBridge focusing on camera control and MQTT integration."""
    
    __slots__ = "api", "mqtt_controller", "running", "mqtt_client"

    def __init__(self) -> None:
        threading.Thread.__init__(self)
        self.daemon = True
        
        for sig in ["SIGTERM", "SIGINT"]:
            signal.signal(getattr(signal, sig), self.clean_up)

        print(f"\n🚀 DOCKER-WYZE-BRIDGE API-ONLY v{VERSION} {BUILD_STR}\n")
        print("📡 API-Only Mode: Video streaming disabled, camera control enabled\n")
        
        self.api: WyzeApi = WyzeApi()
        self.mqtt_controller: Optional[MqttController] = None
        self.mqtt_client: Optional[paho.mqtt.client.Client] = None
        self.running = False

    def health(self) -> dict:
        """Return health status for API-only mode."""
        wyze_authed = self.api.auth is not None and self.api.auth.access_token is not None
        mqtt_connected = self.mqtt_client is not None and self.mqtt_client.is_connected() if self.mqtt_client else False
        total_cameras = len(self.api.get_cameras() or [])
        
        return {
            "wyze_authed": wyze_authed,
            "mqtt_connected": mqtt_connected,
            "total_cameras": total_cameras,
            "api_only_mode": True
        }

    def run(self, fresh_data: bool = False) -> None:
        """Main run loop for API-only bridge."""
        self._initialize(fresh_data)

    def _initialize(self, fresh_data: bool = False) -> None:
        """Initialize API-only bridge components."""
        logger.info("🔧 Initializing API-only bridge...")
        
        # Login to Wyze API
        self.api.login(fresh_data=fresh_data)
        WbAuth.set_email(email=self.api.get_user().email, force=fresh_data)
        
        # Setup camera discovery and control
        self.setup_cameras()
        
        if self.api.total_cams < 1:
            logger.warning("❌ No cameras found!")
            return signal.raise_signal(signal.SIGINT)
        
        # Initialize MQTT controller for camera commands and Home Assistant integration
        self.setup_mqtt()
        
        logger.info("✅ API-only bridge initialized successfully!")
        self.running = True
        
        # Keep the bridge running
        self.monitor_loop()

    def setup_cameras(self):
        """Discover and setup cameras for API control."""
        logger.info("📷 Setting up cameras for API control...")
        
        user = self.api.get_user()
        cameras = {}
        
        for cam in self.api.filtered_cams():
            logger.info(f"[+] Adding {cam.nickname} [{cam.product_model}] for API control")
            cameras[cam.name_uri] = cam
            
            # Save thumbnail for Home Assistant integration
            self.api.save_thumbnail(cam.name_uri, "")
        
        # Store camera references for MQTT controller
        self._cameras = cameras

    def setup_mqtt(self):
        """Initialize MQTT controller for camera commands and HA integration."""
        if not env_bool("MQTT_ENABLED"):
            logger.info("📡 MQTT disabled - camera control via REST API only")
            return
            
        logger.info("📡 Setting up MQTT controller...")
        
        try:
            from wyzebridge.mqtt_controller import MqttController
            self.mqtt_controller = MqttController(self.api, self._cameras)
            self.mqtt_client = self.mqtt_controller.start()
            logger.info("✅ MQTT controller started successfully!")
        except Exception as ex:
            logger.error(f"❌ Failed to start MQTT controller: [{type(ex).__name__}] {ex}")
            logger.info("🔧 Camera control will be available via REST API only")

    def monitor_loop(self):
        """Main monitoring loop for API-only bridge."""
        logger.info("🔄 Starting API-only bridge monitor loop...")
        
        try:
            while self.running:
                # Periodic health checks and maintenance
                sleep(30)
                
                # Check if we need to refresh camera list
                if self.api.total_cams != len(self._cameras):
                    logger.info("🔄 Camera count changed, refreshing...")
                    self.refresh_cameras()
                    
                # Update camera thumbnails periodically
                self.update_thumbnails()
                
        except KeyboardInterrupt:
            logger.info("⏹️ Received stop signal")
        except Exception as ex:
            logger.error(f"❌ Error in monitor loop: [{type(ex).__name__}] {ex}")
        finally:
            self.clean_up()

    def refresh_cameras(self):
        """Refresh camera list and update MQTT configuration."""
        logger.info("🔄 Refreshing camera configuration...")
        
        self.api.get_cameras(fresh_data=True)
        self.setup_cameras()
        
        if self.mqtt_controller:
            self.mqtt_controller.update_cameras(self._cameras)

    def update_thumbnails(self):
        """Update camera thumbnails for Home Assistant integration."""
        for cam_uri in self._cameras:
            try:
                self.api.save_thumbnail(cam_uri, "")
                if self.mqtt_controller:
                    self.mqtt_controller.update_preview(cam_uri)
            except Exception as ex:
                logger.debug(f"Failed to update thumbnail for {cam_uri}: {ex}")

    def restart(self, fresh_data: bool = False) -> None:
        """Restart the API-only bridge."""
        logger.info("🔄 Restarting API-only bridge...")
        self.stop()
        self._initialize(fresh_data)

    def stop(self):
        """Stop all bridge components."""
        logger.info("⏹️ Stopping API-only bridge...")
        self.running = False
        
        if self.mqtt_controller:
            self.mqtt_controller.stop()
            
        if self.mqtt_client:
            self.mqtt_client.disconnect()

    def clean_up(self, *_):
        """Clean up before shutdown."""
        if not self.running:
            sys.exit(0)
            
        logger.info("🧹 Cleaning up API-only bridge...")
        self.stop()
        logger.info("👋 goodbye!")
        sys.exit(0)

    def get_camera(self, uri: str) -> Optional[WyzeCamera]:
        """Get camera by URI."""
        return self._cameras.get(uri) or self.api.get_camera(uri)

    def control_camera(self, uri: str, command: str, value: str = "") -> dict:
        """Control camera via API."""
        if not (cam := self.get_camera(uri)):
            return {"status": "error", "response": f"Camera '{uri}' not found"}
            
        logger.info(f"🎮 Controlling camera {uri}: {command}={value}")
        
        try:
            return self.api.run_action(cam, command)
        except Exception as ex:
            logger.error(f"❌ Camera control error: [{type(ex).__name__}] {ex}")
            return {"status": "error", "response": str(ex)}


def main():
    """Main entry point for API-only bridge."""
    if env_bool("API_ONLY_MODE", default="true"):
        bridge = WyzeApiBridge()
        bridge.run()
    else:
        logger.error("❌ API_ONLY_MODE must be enabled to use this entry point")
        sys.exit(1)


if __name__ == "__main__":
    main()