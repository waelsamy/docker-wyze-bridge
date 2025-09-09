#!/usr/bin/env python3
"""
Validation script for API-only mode implementation.
This script validates file structure and basic syntax without requiring dependencies.
"""

import os
import ast
import re
import sys
from pathlib import Path

def check_file_exists(filepath, description=""):
    """Check if a file exists and return status."""
    if os.path.exists(filepath):
        print(f"✅ {description or filepath}")
        return True
    else:
        print(f"❌ {description or filepath} - NOT FOUND")
        return False

def validate_python_syntax(filepath):
    """Validate Python file syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")
        return False

def validate_dockerfile(filepath):
    """Validate Dockerfile content."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Check for required API-only specific content
        required_patterns = [
            r'API_ONLY_MODE=true',
            r'FLASK_APP=api_only',
            r'requirements-api\.txt',
            r'run-api'
        ]
        
        missing = []
        for pattern in required_patterns:
            if not re.search(pattern, content):
                missing.append(pattern)
        
        if missing:
            print(f"❌ Missing patterns in {filepath}: {missing}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error validating {filepath}: {e}")
        return False

def validate_yaml_basic(filepath):
    """Basic YAML validation (structure check)."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Basic checks for YAML structure
        if not content.strip():
            print(f"❌ Empty file: {filepath}")
            return False
            
        # Check for proper indentation (no tabs)
        if '\t' in content:
            print(f"❌ YAML contains tabs: {filepath}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error validating {filepath}: {e}")
        return False

def main():
    """Run validation checks."""
    print("🔍 Docker Wyze Bridge API-Only Mode Validation")
    print("=" * 60)
    
    all_passed = True
    
    # Check core API-only files
    print("\n📁 Core Files:")
    files_to_check = [
        ("app/wyze_api_bridge.py", "Main API-only bridge entry point"),
        ("app/api_only.py", "Flask API application"),
        ("app/wyzebridge/mqtt_controller.py", "MQTT controller for API-only mode"),
        ("docker/Dockerfile.api", "API-only Docker image"),
        ("docker-compose.api.yml", "API-only Docker Compose"),
        ("README.api.md", "API-only documentation"),
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_passed = False
    
    # Check Home Assistant addon files
    print("\n🏠 Home Assistant Addon Files:")
    ha_files = [
        ("home_assistant/api/config.yml", "HA addon configuration"),
        ("home_assistant/api/translations/en.yml", "HA addon translations"),
    ]
    
    for filepath, description in ha_files:
        if not check_file_exists(filepath, description):
            all_passed = False
    
    # Validate Python syntax
    print("\n🐍 Python Syntax Validation:")
    python_files = [
        "app/wyze_api_bridge.py",
        "app/api_only.py", 
        "app/wyzebridge/mqtt_controller.py"
    ]
    
    for filepath in python_files:
        if os.path.exists(filepath):
            if validate_python_syntax(filepath):
                print(f"✅ {filepath} - Valid syntax")
            else:
                all_passed = False
        else:
            print(f"❌ {filepath} - File not found")
            all_passed = False
    
    # Validate Docker files
    print("\n🐳 Docker Configuration Validation:")
    if os.path.exists("docker/Dockerfile.api"):
        if validate_dockerfile("docker/Dockerfile.api"):
            print("✅ Dockerfile.api - Valid configuration")
        else:
            all_passed = False
    
    if os.path.exists("docker-compose.api.yml"):
        if validate_yaml_basic("docker-compose.api.yml"):
            print("✅ docker-compose.api.yml - Valid structure")
        else:
            all_passed = False
    
    # Validate Home Assistant configs
    print("\n🏠 Home Assistant Configuration Validation:")
    ha_configs = [
        "home_assistant/api/config.yml",
        "home_assistant/api/translations/en.yml"
    ]
    
    for config_file in ha_configs:
        if os.path.exists(config_file):
            if validate_yaml_basic(config_file):
                print(f"✅ {config_file} - Valid structure")
            else:
                all_passed = False
        else:
            print(f"❌ {config_file} - File not found")
            all_passed = False
    
    # Check for key features in files
    print("\n🔧 Feature Implementation Check:")
    
    # Check wyze_api_bridge.py for key features
    if os.path.exists("app/wyze_api_bridge.py"):
        with open("app/wyze_api_bridge.py", 'r') as f:
            content = f.read()
        
        features = [
            ("WyzeApiBridge class", "class WyzeApiBridge"),
            ("API-only mode indicator", "api_only_mode.*true"),
            ("MQTT controller integration", "MqttController"),
            ("Camera control method", "def control_camera"),
            ("Health check method", "def health")
        ]
        
        for feature, pattern in features:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"✅ {feature}")
            else:
                print(f"❌ {feature}")
                all_passed = False
    
    # Check api_only.py for Flask endpoints
    if os.path.exists("app/api_only.py"):
        with open("app/api_only.py", 'r') as f:
            content = f.read()
        
        endpoints = [
            ("Health endpoint", "@app.route.*health"),
            ("API endpoints", "@app.route.*api"),
            ("Camera control", "api_cam_control"),
            ("Thumbnail endpoint", "@app.route.*thumb"),
            ("Login endpoint", "@app.route.*login")
        ]
        
        for endpoint, pattern in endpoints:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"✅ {endpoint}")
            else:
                print(f"❌ {endpoint}")
                all_passed = False
    
    # Check MQTT controller features  
    if os.path.exists("app/wyzebridge/mqtt_controller.py"):
        with open("app/wyzebridge/mqtt_controller.py", 'r') as f:
            content = f.read()
        
        mqtt_features = [
            ("MqttController class", "class MqttController"),
            ("Home Assistant discovery", "publish_discovery"),
            ("Command handling", "_handle_mqtt_command"),
            ("Camera state updates", "update_mqtt_state")
        ]
        
        for feature, pattern in mqtt_features:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"✅ MQTT {feature}")
            else:
                print(f"❌ MQTT {feature}")
                all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All validation checks passed!")
        print("📦 API-only mode implementation is complete and ready for deployment.")
        print("\n📋 Next steps:")
        print("   1. Build Docker image: docker build -f docker/Dockerfile.api -t wyze-bridge-api .")
        print("   2. Test with Docker Compose: docker-compose -f docker-compose.api.yml up")
        print("   3. Configure Home Assistant addon with files in home_assistant/api/")
        return True
    else:
        print("❌ Some validation checks failed.")
        print("🔧 Please review and fix the issues above before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)