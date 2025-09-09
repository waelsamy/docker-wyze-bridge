# Home Assistant API-Only Addon for Docker Wyze Bridge
# Provides camera control and MQTT integration without video streaming
FROM waelewida/wyze-bridge:latest

LABEL maintainer="Wael Ewida <waelsamy@mail.com>"
LABEL description="Home Assistant addon for API-only camera control"

# Configure API-only mode environment
ENV API_ONLY_MODE=true \
    FLASK_APP=api_only \
    FLASK_ENV=production \
    FLASK_DEBUG=false \
    PYTHONUNBUFFERED=1

# Use the API-only bridge entrypoint
ENTRYPOINT ["python3", "wyze_api_bridge.py"]

# Expose only the web interface port (no streaming ports needed)
EXPOSE 5000