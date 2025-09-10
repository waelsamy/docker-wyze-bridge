from os import makedirs
import signal
import sys
from dataclasses import replace
from threading import Thread
from time import sleep

from wyzebridge.build_config import BUILD_STR, VERSION
from wyzebridge.config import BRIDGE_IP, HASS_TOKEN, IMG_PATH, LLHLS, ON_DEMAND, STREAM_AUTH, TOKEN_PATH
from wyzebridge.auth import WbAuth
from wyzebridge.bridge_utils import env_bool, env_cam, is_livestream, migrate_path
from wyzebridge.hass import setup_hass
from wyzebridge.logging import logger
from wyzebridge.mtx_server import MtxServer
from wyzebridge.stream_manager import StreamManager
from wyzebridge.wyze_api import WyzeApi
from wyzebridge.wyze_stream import WyzeStream, WyzeStreamOptions
from wyzecam.api_models import WyzeAccount, WyzeCamera

# API-only mode imports (loaded conditionally)
# paho.mqtt.client imported in API-only class when needed

setup_hass(HASS_TOKEN)

makedirs(TOKEN_PATH, exist_ok=True)
makedirs(IMG_PATH, exist_ok=True)

if HASS_TOKEN:
    migrate_path("/config/wyze-bridge/", "/config/")

class WyzeBridge(Thread):
    __slots__ = "api", "streams", "mtx"

    def __init__(self) -> None:
        Thread.__init__(self)

        for sig in ["SIGTERM", "SIGINT"]:
            signal.signal(getattr(signal, sig), self.clean_up)

        print(f"\n🚀 DOCKER-WYZE-BRIDGE v{VERSION} {BUILD_STR}\n")
        self.api: WyzeApi = WyzeApi()
        self.streams: StreamManager = StreamManager(self.api)
        self.mtx: MtxServer = MtxServer()
        self.mtx.setup_webrtc(BRIDGE_IP)
        if LLHLS:
            self.mtx.setup_llhls(TOKEN_PATH, bool(HASS_TOKEN))

    def health(self):
        mtx_alive = self.mtx.sub_process_alive()
        active_streams = len(self.streams.active_streams())
        wyze_authed = self.api.auth is not None and self.api.auth.access_token is not None
        return { "mtx_alive": mtx_alive , "wyze_authed": wyze_authed, "active_streams": active_streams }

    def run(self, fresh_data: bool = False) -> None:
        self._initialize(fresh_data)

    def _initialize(self, fresh_data: bool = False) -> None:
        self.api.login(fresh_data=fresh_data)
        WbAuth.set_email(email=self.api.get_user().email, force=fresh_data)
        self.mtx.setup_auth(WbAuth.api, STREAM_AUTH)
        self.setup_streams()
        if self.streams.total < 1:
            return signal.raise_signal(signal.SIGINT)
        
        if logger.getEffectiveLevel() == 10: #if we're at debug level
            logger.debug(f"[BRIDGE] MTX config:\n{self.mtx.dump_config()}")
            
        self.mtx.start()
        self.streams.monitor_streams(self.mtx.health_check)

    def restart(self, fresh_data: bool = False) -> None:
        self.mtx.stop()
        self.streams.stop_all()
        self._initialize(fresh_data)

    def refresh_cams(self) -> None:
        self.mtx.stop()
        self.streams.stop_all()
        self.api.get_cameras(fresh_data=True)
        self._initialize(False)

    def setup_streams(self):
        """Gather and setup streams for each camera."""
        user = self.api.get_user()

        for cam in self.api.filtered_cams():
            logger.info(f"[+] Adding {cam.nickname} [{cam.product_model}] at {cam.name_uri}")

            options = WyzeStreamOptions(
                quality=env_cam("quality", cam.name_uri),
                audio=bool(env_cam("enable_audio", cam.name_uri)),
                record=bool(env_cam("record", cam.name_uri)),
                reconnect=(not ON_DEMAND) or is_livestream(cam.name_uri),
            )

            stream = WyzeStream(user, self.api, cam, options)
            stream.rtsp_fw_enabled = self.rtsp_fw_proxy(cam, stream)
            self.mtx.add_path(stream.uri, not options.reconnect)
            self.streams.add(stream)

            if env_cam("record", cam.name_uri):
                self.mtx.record(stream.uri)

            self.add_substream(user, self.api, cam, options)

    def rtsp_fw_proxy(self, cam: WyzeCamera, stream: WyzeStream) -> bool:
        if rtsp_fw := env_bool("rtsp_fw").lower():
            if rtsp_path := stream.check_rtsp_fw(rtsp_fw == "force"):
                rtsp_uri = f"{cam.name_uri}-fw"
                logger.info(f"[-->] Adding /{rtsp_uri} as a source")
                self.mtx.add_source(rtsp_uri, rtsp_path)
                return True
        return False

    def add_substream(self, user: WyzeAccount, api: WyzeApi, cam: WyzeCamera, options: WyzeStreamOptions):
        """Setup and add substream if enabled for camera."""
        if env_bool(f"SUBSTREAM_{cam.name_uri}") or (
            env_bool("SUBSTREAM") and cam.can_substream
        ):
            quality = env_cam("sub_quality", cam.name_uri, "sd30")
            record = bool(env_cam("sub_record", cam.name_uri))
            sub_opt = replace(options, substream=True, quality=quality, record=record)
            logger.info(f"[++] Adding {cam.name_uri} substream quality: {quality} record: {record}")
            sub = WyzeStream(user, api, cam, sub_opt)
            self.mtx.add_path(sub.uri, not options.reconnect)
            self.streams.add(sub)

    def clean_up(self, *_):
        """Stop all streams and clean up before shutdown."""
        if self.streams.stop_flag:
            sys.exit(0)
        if self.streams:
            self.streams.stop_all()
        self.mtx.stop()
        logger.info("👋 goodbye!")
        sys.exit(0)


class WyzeApiBridge(Thread):
    """API-Only version of WyzeBridge focusing on camera control and MQTT integration."""
    
    __slots__ = "api", "mqtt_controller", "running", "mqtt_client"

    def __init__(self) -> None:
        Thread.__init__(self)
        self.daemon = True
        
        for sig in ["SIGTERM", "SIGINT"]:
            signal.signal(getattr(signal, sig), self.clean_up)

        print(f"\n🚀 DOCKER-WYZE-BRIDGE API-ONLY v{VERSION} {BUILD_STR}\n")
        print("📡 API-Only Mode: Video streaming disabled, camera control enabled\n")
        
        self.api: WyzeApi = WyzeApi()
        self.mqtt_controller = None
        self.mqtt_client = None
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

    def run(self):
        """Main API-only bridge loop."""
        logger.info("Starting API-Only Bridge...")
        self.running = True
        
        # Initialize MQTT if enabled
        if env_bool("MQTT"):
            try:
                # Import here to avoid circular imports
                from wyzebridge.mqtt_controller import MqttController
                self.mqtt_controller = MqttController(self.api, self.api.get_cameras() or {})
                self.mqtt_controller.start()
                self.mqtt_client = self.mqtt_controller.client
                logger.info("📡 MQTT Controller started")
            except Exception as e:
                logger.error(f"Failed to start MQTT: {e}")

        # Start Flask API if enabled
        if env_bool("FLASK_RUN", default=False):
            from api_only import create_app
            app = create_app()
            app.run(host='0.0.0.0', port=int(env_bool("FLASK_PORT", default="5000")))
        
        # Keep running
        try:
            while self.running:
                sleep(1)
        except KeyboardInterrupt:
            self.clean_up()

    def clean_up(self, *_):
        """Clean up API-only bridge."""
        if not self.running:
            sys.exit(0)
        
        self.running = False
        if self.mqtt_controller:
            self.mqtt_controller.stop()
        logger.info("👋 API-Only Bridge goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    # Check if API-only mode is enabled
    if env_bool("API_ONLY_MODE", default=False):
        logger.info("🎯 Starting in API-Only Mode")
        wb = WyzeApiBridge()
    else:
        logger.info("🚀 Starting in Full Bridge Mode") 
        wb = WyzeBridge()
    
    wb.run()
    sys.exit(0)
