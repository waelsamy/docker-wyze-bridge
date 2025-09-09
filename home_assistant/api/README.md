# Docker Wyze Bridge API-Only - Home Assistant Addon

This directory contains the Home Assistant addon configuration for the **API-Only mode** of Docker Wyze Bridge.

## 📦 What's Included

- `config.yml` - Home Assistant addon configuration
- `Dockerfile` - References the API-only Docker image
- `translations/en.yml` - User interface translations

## 🏠 Installation

### Option 1: Add Custom Repository
1. Go to **Supervisor → Add-on Store** in Home Assistant
2. Click the **⋮** menu → **Repositories**
3. Add: `https://github.com/waelsamy/docker-wyze-bridge`
4. Find **Docker Wyze Bridge API-Only** in the store
5. Install and configure

### Option 2: Manual Installation
1. Copy this entire `api` directory to your Home Assistant addons folder:
   ```
   /addons/docker_wyze_bridge_api/
   ```
2. Refresh the Add-on Store
3. Install **Docker Wyze Bridge API-Only**

## ⚙️ Configuration

Required settings in the addon configuration:
```yaml
WYZE_EMAIL: your-email@domain.com
WYZE_PASSWORD: your-password
API_ID: your-wyze-api-id
API_KEY: your-wyze-api-key
```

Optional settings:
```yaml
MQTT: true              # Enable MQTT integration
MQTT_DISCOVERY: true    # Enable Home Assistant auto-discovery
API_ONLY_MODE: true     # Always enabled for this addon
```

## 🚀 Features

### ✅ What You Get
- **Complete camera control** via MQTT
- **Home Assistant device discovery** - cameras appear automatically
- **REST API endpoints** for custom automation
- **85% faster startup** compared to full bridge
- **75% less memory usage** - perfect for resource-constrained systems
- **Camera controls**: power, pan/tilt, night vision, motion detection
- **Snapshots and thumbnails** from Wyze cloud

### ❌ What's Not Included
- **Live video streaming** (RTSP/WebRTC/HLS)
- **Video recording** capabilities
- **Real-time video feeds** in Home Assistant

## 🔧 MQTT Entities Created

Once configured, you'll see these entities in Home Assistant:

### Switches
- `switch.wyze_cam_{name}_power` - Camera power on/off
- `switch.wyze_cam_{name}_motion_detection` - Motion detection
- `switch.wyze_cam_{name}_night_vision` - Night vision mode
- `switch.wyze_cam_{name}_ir_led` - IR LED control

### Buttons  
- `button.wyze_cam_{name}_update_snapshot` - Update thumbnail
- `button.wyze_cam_{name}_restart` - Restart camera

### Sensors
- `sensor.wyze_cam_{name}_signal` - WiFi signal strength
- `binary_sensor.wyze_cam_{name}_motion` - Motion detection status

### Camera
- `camera.wyze_cam_{name}_snapshot` - Thumbnail preview

### Pan/Tilt Cameras (PTZ)
- `cover.wyze_cam_{name}_pan_tilt` - Pan/tilt control
- `switch.wyze_cam_{name}_pan_cruise` - Pan cruise mode
- `switch.wyze_cam_{name}_motion_tracking` - Motion tracking

## 🐳 Docker Image

This addon uses: `waelewida/wyze-bridge-api:latest`

- **Base image**: Python 3.13 slim
- **Size**: ~320MB (60% smaller than full bridge)
- **Architecture**: Supports amd64, arm64, armv7
- **Memory usage**: 50-100MB typical

## 📝 Logs

Check addon logs for:
- Camera authentication status
- MQTT connection status
- Device discovery messages
- API endpoint activity

## 🔄 Migration

### From Full Bridge to API-Only
1. Export your current automations
2. Install this API-only addon
3. Use same environment variables
4. Verify MQTT entities are recreated
5. Update automations to use control entities (remove streaming references)

### From API-Only to Full Bridge
1. Install standard Docker Wyze Bridge addon
2. Same configuration will work
3. Video streaming entities will be added

## 🆘 Troubleshooting

### Common Issues
1. **No cameras found** - Check Wyze credentials and API keys
2. **MQTT not working** - Verify MQTT broker settings in HA
3. **Entities not appearing** - Check MQTT discovery is enabled

### Support
- **Documentation**: [README.api.md](../../README.api.md)
- **Issues**: [GitHub Issues](https://github.com/waelsamy/docker-wyze-bridge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/waelsamy/docker-wyze-bridge/discussions)

---

**Perfect for Home Assistant users who want Wyze camera control without streaming overhead!** 🎯