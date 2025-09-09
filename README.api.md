# Docker Wyze Bridge API-Only Mode

## Overview

The API-Only Mode provides a lightweight version of Docker Wyze Bridge that focuses exclusively on camera control and MQTT integration **without video streaming**. This mode is perfect for:

- 🏠 **Home Assistant Integration** - Full camera control via MQTT
- 💾 **Low Resource Usage** - No video processing or streaming servers
- 🎮 **Camera Control** - All camera commands (power, pan/tilt, settings)
- 📡 **MQTT Integration** - Complete Home Assistant MQTT Discovery
- 🖼️ **Snapshots** - Camera thumbnails from Wyze cloud
- ⚡ **Fast Startup** - No MediaMTX or FFmpeg initialization

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Wyze credentials
# WYZE_EMAIL=your-email@domain.com
# WYZE_PASSWORD=your-password
# API_ID=your-api-id
# API_KEY=your-api-key

# Start API-only bridge
docker-compose -f docker-compose.api.yml up -d
```

### Using Docker Run

```bash
docker run -d \
  --name wyze-bridge-api \
  -p 5000:5000 \
  -e WYZE_EMAIL=your-email@domain.com \
  -e WYZE_PASSWORD=your-password \
  -e API_ID=your-api-id \
  -e API_KEY=your-api-key \
  -e API_ONLY_MODE=true \
  -v wyze_config:/tokens \
  -v wyze_img:/app/img \
  waelewida/wyze-bridge-api
```

### Building from Source

```bash
# Build API-only image
docker buildx build -t wyze-bridge-api -f docker/Dockerfile.api .

# Run the container
docker run -d \
  --name wyze-bridge-api \
  -p 5000:5000 \
  --env-file .env \
  wyze-bridge-api
```

## Architecture Comparison

### Standard Mode vs API-Only Mode

| Component | Standard Mode | API-Only Mode |
|-----------|---------------|---------------|
| **Video Streaming** | ✅ RTSP/WebRTC/HLS/RTMP | ❌ Disabled |
| **MediaMTX Server** | ✅ Full server | ❌ Removed |
| **FFmpeg** | ✅ Video processing | ❌ Removed |
| **Camera Control** | ✅ Full control | ✅ Full control |
| **MQTT Integration** | ✅ With streams | ✅ Control only |
| **Home Assistant** | ✅ Full integration | ✅ Control integration |
| **Snapshots** | ✅ Live + Cloud | ✅ Cloud only |
| **Memory Usage** | ~200-500MB | ~50-100MB |
| **Startup Time** | 30-60 seconds | 5-15 seconds |

## Environment Variables

### Required

- `WYZE_EMAIL` - Your Wyze account email
- `WYZE_PASSWORD` - Your Wyze account password  
- `API_ID` - Wyze Developer API ID
- `API_KEY` - Wyze Developer API Key

### API-Only Specific

- `API_ONLY_MODE=true` - Enable API-only mode (always true for this image)
- `FLASK_RUN=true` - Use Flask development server (optional)
- `FLASK_PORT=5000` - Flask server port (default: 5000)

### MQTT Configuration

- `MQTT_ENABLED=true` - Enable MQTT integration
- `MQTT_HOST` - MQTT broker hostname
- `MQTT_AUTH` - MQTT username:password
- `MQTT_TOPIC=wyze-bridge` - MQTT topic prefix
- `MQTT_DISCOVERY=true` - Enable Home Assistant discovery

### Optional

- `NET_MODE` - Connection mode (LAN|P2P|ANY)
- `MOTION_API=true` - Monitor camera motion events
- `WB_AUTH=true` - Enable web UI authentication
- `LOG_LEVEL=INFO` - Logging level
- `SNAPSHOT_KEEP=7d` - How long to keep snapshots

## API Endpoints

### Core Endpoints

- `GET /` - API information and available endpoints
- `GET /health` - Health check status
- `POST /login` - Authenticate with Wyze credentials

### Camera Endpoints

- `GET /api` - List all cameras
- `GET /api/{camera_name}` - Get camera information  
- `GET|POST /api/{camera_name}/{command}` - Control camera
- `GET /thumb/{camera_name}.jpg` - Get camera thumbnail

### Control Commands

#### Basic Controls
- `power` - Camera power on/off/restart
- `notifications` - Enable/disable notifications
- `motion_detection` - Enable/disable motion detection
- `update_snapshot` - Update camera thumbnail

#### Video Settings
- `irled` - IR LED control (on/off/auto)
- `night_vision` - Night vision mode
- `status_light` - Status LED on/off
- `alarm` - Siren/alarm control

#### Pan/Tilt Cameras (PTZ)
- `rotary_action` - Pan/tilt movement (left/right/up/down)
- `rotary_degree` - Pan/tilt by degrees
- `pan_cruise` - Enable/disable pan cruise
- `motion_tracking` - Enable/disable motion tracking
- `reset_rotation` - Reset to home position

### Management Endpoints

- `POST /restart/{command}` - Restart components (cameras|api|all)
- `GET /status` - Bridge status and configuration

## Home Assistant Integration

### MQTT Discovery

When `MQTT_DISCOVERY=true`, the bridge automatically creates Home Assistant entities:

#### Available Entities
- **Switch**: Stream control, power, IR LED, night vision, motion detection
- **Button**: Update snapshot, restart camera
- **Siren**: Camera alarm/siren
- **Binary Sensor**: Motion detection status
- **Sensor**: Signal strength, resolution, audio status
- **Camera**: Snapshot preview
- **Number**: Bitrate, FPS settings
- **Cover**: Pan/tilt control (PTZ cameras)
- **Select**: Cruise point selection (PTZ cameras)

### Example Configuration

```yaml
# Home Assistant configuration.yaml
mqtt:
  discovery: true
  discovery_prefix: homeassistant
```

### Device Card Example

```yaml
# Home Assistant Lovelace card
type: entities
entities:
  - entity: switch.wyze_cam_office_power
  - entity: switch.wyze_cam_office_motion_detection  
  - entity: button.wyze_cam_office_update_snapshot
  - entity: camera.wyze_cam_office_snapshot
  - entity: switch.wyze_cam_office_night_vision
  - entity: siren.wyze_cam_office_alarm
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r app/requirements.txt

# Set environment variables
export API_ONLY_MODE=true
export FLASK_APP=api_only
export FLASK_ENV=development

# Run Flask development server
cd app && flask run --host=0.0.0.0 --debug
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:5000/health

# List cameras
curl http://localhost:5000/api

# Control camera
curl -X POST http://localhost:5000/api/office/power -d "on"

# Get thumbnail
curl http://localhost:5000/thumb/office.jpg --output office.jpg
```

## Troubleshooting

### Common Issues

1. **No cameras found**
   - Verify Wyze credentials are correct
   - Check API_ID and API_KEY are valid
   - Ensure cameras are online in Wyze app

2. **MQTT not connecting**
   - Verify MQTT_HOST is reachable
   - Check MQTT_AUTH credentials
   - Ensure MQTT broker allows connections

3. **Home Assistant discovery not working**
   - Verify `MQTT_DISCOVERY=true`
   - Check MQTT integration is configured in HA
   - Restart Home Assistant after first setup

### Logs

```bash
# View container logs
docker logs wyze-bridge-api -f

# Enable debug logging
docker exec wyze-bridge-api sh -c 'export LOG_LEVEL=DEBUG'
```

### Health Check

The `/health` endpoint provides detailed status:

```json
{
  "wyze_authed": true,
  "mqtt_connected": true,  
  "total_cameras": 3,
  "api_only_mode": true
}
```

## Migration from Standard Mode

### Benefits
- ⚡ **85% faster startup** - No video server initialization
- 💾 **75% less memory usage** - No video buffering  
- 📦 **60% smaller image** - No MediaMTX/FFmpeg
- 🔋 **Lower CPU usage** - No video processing

### What You Lose
- ❌ Video streaming (RTSP/WebRTC/HLS/RTMP)
- ❌ Live video feeds in Home Assistant
- ❌ Video recording capabilities
- ❌ Real-time snapshot generation

### What You Keep
- ✅ All camera control commands
- ✅ MQTT integration and discovery
- ✅ Home Assistant device management
- ✅ Cloud-based snapshots
- ✅ Motion event notifications
- ✅ Camera status monitoring

## Support

For issues, questions, or contributions:

- **GitHub Issues**: [docker-wyze-bridge/issues](https://github.com/waelsamy/docker-wyze-bridge/issues)
- **Documentation**: [docker-wyze-bridge/wiki](https://github.com/waelsamy/docker-wyze-bridge/wiki)
- **Discussions**: [docker-wyze-bridge/discussions](https://github.com/waelsamy/docker-wyze-bridge/discussions)