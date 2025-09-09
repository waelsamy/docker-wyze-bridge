# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Docker Wyze Bridge is a WebRTC/RTSP/RTMP/HLS bridge for streaming Wyze cameras without requiring special firmware modifications. It creates local streams from Wyze cameras and exposes them through standard streaming protocols.

## Common Development Commands

### Building the Docker Image

```bash
# Build standard image
docker buildx build -t wyze-bridge -f docker/Dockerfile . --platform=linux/amd64

# Build hardware accelerated image
docker buildx build -t wyze-bridge -f docker/Dockerfile.hwaccel . --platform=linux/amd64

# Build multiarch image
docker buildx build -t wyze-bridge -f docker/Dockerfile.multiarch . --platform=linux/amd64,linux/arm64,linux/arm/v7
```

### Running the Bridge

```bash
# Quick run with docker
docker run -p 8554:8554 -p 8888:8888 -p 5050:5000 -e WB_AUTH=false waelewida/wyze-bridge

# Run with docker-compose (recommended)
docker-compose up

# Run test build
./test.sh
```

### Development Environment

```bash
# Install Python dependencies locally
pip install -r app/requirements.txt

# Run Flask development server
cd app && flask run --host=0.0.0.0
```

## High-Level Architecture

The bridge consists of several key components that work together:

### Core Components

1. **WyzeBridge** (`app/wyze_bridge.py`): Main orchestrator that manages the Wyze API connection, stream manager, and MediaMTX server.

2. **StreamManager** (`app/wyzebridge/stream_manager.py`): Manages individual camera streams, handles stream lifecycle, snapshots, and maintains active streams.

3. **WyzeStream** (`app/wyzebridge/wyze_stream.py`): Represents individual camera streams, manages connection to cameras using TUTK protocol, and pipes video data to MediaMTX.

4. **MtxServer** (`app/wyzebridge/mtx_server.py`): Manages the MediaMTX process which handles RTSP/RTMP/HLS/WebRTC protocol conversion and stream distribution.

5. **WyzeApi** (`app/wyzebridge/wyze_api.py`): Handles authentication with Wyze cloud services and camera discovery.

### Web Interface

- **Flask Web UI** (`app/frontend.py`, `app/wyzebridge/web_ui.py`): Provides web interface at port 5000 for camera preview and configuration
- **WebRTC Support**: Enables low-latency browser-based streaming

### Protocol Support

The bridge uses MediaMTX to expose streams via:
- RTSP (port 8554)
- RTMP (ports 1935, 1936, 2935, 2936)  
- HLS (port 8888)
- WebRTC (ports 8889, 8189)
- SRT (port 8890)

### Camera Communication

- Uses TUTK protocol (via `wyzecam` library) to communicate with cameras
- Supports various Wyze camera models through device-specific configurations
- Handles P2P and relay connections for local/remote streaming

### Key Features

- **MQTT Integration**: Publishes camera status and accepts commands
- **Snapshot Support**: Periodic snapshots with sunrise/sunset automation
- **Recording**: Stream recording through MediaMTX
- **Authentication**: Optional stream and web UI authentication
- **Home Assistant Integration**: Can run as HA add-on with auto-discovery

## Important Environment Variables

- `WYZE_EMAIL`, `WYZE_PASSWORD`: Wyze account credentials
- `API_ID`, `API_KEY`: Required API credentials from Wyze developer portal
- `WB_AUTH`: Enable/disable authentication (default: true)
- `WB_IP`: Host IP for WebRTC configuration
- `RECORD_ALL` or `RECORD_<CAM_NAME>`: Enable recording
- `MQTT_HOST`, `MQTT_AUTH`: MQTT broker configuration

## Key Implementation Details

- Camera streams are managed as separate threads/processes
- FFmpeg is used for video transcoding when needed
- MediaMTX handles protocol conversion and client connections
- Snapshots are managed with automatic pruning based on retention settings
- MQTT commands allow remote camera control (pan/tilt, night vision, etc.)