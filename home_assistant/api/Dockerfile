# Use existing wyze-bridge image but configure for API-only mode
FROM waelewida/wyze-bridge:latest

# Override environment variables for API-only mode
ENV API_ONLY_MODE=true
ENV FLASK_APP=api_only

# Override the entrypoint to use API-only mode
ENTRYPOINT ["python3", "wyze_api_bridge.py"]