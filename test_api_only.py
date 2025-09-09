#!/usr/bin/env python3
"""
Test script for API-only mode functionality.
This script validates the basic functionality without requiring actual Wyze credentials.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

class TestAPIOnlyMode(unittest.TestCase):
    """Test suite for API-only mode components."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.token_path = os.path.join(self.temp_dir, 'tokens')
        self.img_path = os.path.join(self.temp_dir, 'img')
        os.makedirs(self.token_path, exist_ok=True)
        os.makedirs(self.img_path, exist_ok=True)
        
        # Set required environment variables
        os.environ.update({
            'API_ONLY_MODE': 'true',
            'TOKEN_PATH': self.token_path,
            'IMG_PATH': self.img_path,
            'MQTT_ENABLED': 'false',
            'LOG_LEVEL': 'ERROR',  # Reduce noise in tests
            'WB_AUTH': 'false',
        })

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_imports(self):
        """Test that all required modules can be imported."""
        try:
            # Test core imports
            from wyzebridge.wyze_api import WyzeApi
            from wyzebridge.logging import logger
            from wyzebridge.config import BRIDGE_IP
            from wyzecam.api_models import WyzeCamera
            print("✅ Core imports successful")
            
            # Test API-only specific imports
            from wyze_api_bridge import WyzeApiBridge
            from api_only import create_app
            print("✅ API-only imports successful")
            
        except ImportError as e:
            self.fail(f"Import failed: {e}")

    @patch('wyzebridge.wyze_api.WyzeApi')
    def test_wyze_api_bridge_initialization(self, mock_api_class):
        """Test WyzeApiBridge initialization."""
        # Mock the WyzeApi
        mock_api = MagicMock()
        mock_api.auth = None
        mock_api.total_cams = 0
        mock_api_class.return_value = mock_api
        
        # Import after mocking
        from wyze_api_bridge import WyzeApiBridge
        
        # Test initialization
        bridge = WyzeApiBridge()
        self.assertIsNotNone(bridge)
        self.assertIsNotNone(bridge.api)
        self.assertFalse(bridge.running)
        print("✅ WyzeApiBridge initialization test passed")

    def test_health_status(self):
        """Test health status functionality."""
        with patch('wyzebridge.wyze_api.WyzeApi') as mock_api_class:
            mock_api = MagicMock()
            mock_api.auth = None
            mock_api.get_cameras.return_value = []
            mock_api_class.return_value = mock_api
            
            from wyze_api_bridge import WyzeApiBridge
            
            bridge = WyzeApiBridge()
            health = bridge.health()
            
            # Check health structure
            self.assertIn('wyze_authed', health)
            self.assertIn('mqtt_connected', health)
            self.assertIn('total_cameras', health)
            self.assertIn('api_only_mode', health)
            self.assertTrue(health['api_only_mode'])
            print("✅ Health status test passed")

    @patch('wyzebridge.wyze_api.WyzeApi')
    @patch('flask.Flask')
    def test_flask_app_creation(self, mock_flask, mock_api_class):
        """Test Flask app creation."""
        # Mock Flask app
        mock_app = MagicMock()
        mock_flask.return_value = mock_app
        
        # Mock WyzeApi
        mock_api = MagicMock()
        mock_api.auth = MagicMock()
        mock_api.auth.access_token = "test_token"
        mock_api_class.return_value = mock_api
        
        # Mock WyzeApiBridge start method to avoid actual startup
        with patch('wyze_api_bridge.WyzeApiBridge.start'):
            from api_only import create_app
            app = create_app()
            
            # Verify Flask was called
            mock_flask.assert_called_once()
            print("✅ Flask app creation test passed")

    def test_environment_variables(self):
        """Test environment variable configuration."""
        from wyzebridge.bridge_utils import env_bool
        
        # Test API_ONLY_MODE detection
        self.assertTrue(env_bool('API_ONLY_MODE'))
        
        # Test other configurations
        self.assertFalse(env_bool('MQTT_ENABLED'))
        print("✅ Environment variables test passed")

    def test_mqtt_controller_import(self):
        """Test MQTT controller can be imported when needed."""
        try:
            from wyzebridge.mqtt_controller import MqttController
            self.assertIsNotNone(MqttController)
            print("✅ MQTT controller import test passed")
        except ImportError as e:
            self.fail(f"MQTT controller import failed: {e}")

    def test_docker_build_files(self):
        """Test that Docker build files exist and are valid."""
        dockerfile_api = os.path.join(os.path.dirname(__file__), 'docker', 'Dockerfile.api')
        compose_api = os.path.join(os.path.dirname(__file__), 'docker-compose.api.yml')
        
        self.assertTrue(os.path.exists(dockerfile_api), "Dockerfile.api not found")
        self.assertTrue(os.path.exists(compose_api), "docker-compose.api.yml not found")
        
        # Check Dockerfile.api contains API-only specific content
        with open(dockerfile_api, 'r') as f:
            dockerfile_content = f.read()
            self.assertIn('API-ONLY', dockerfile_content)
            self.assertIn('requirements-api.txt', dockerfile_content)
            self.assertIn('run-api', dockerfile_content)
        
        print("✅ Docker build files test passed")

    def test_home_assistant_config(self):
        """Test Home Assistant addon configuration."""
        ha_config = os.path.join(os.path.dirname(__file__), 'home_assistant', 'api', 'config.yml')
        ha_translations = os.path.join(os.path.dirname(__file__), 'home_assistant', 'api', 'translations', 'en.yml')
        
        self.assertTrue(os.path.exists(ha_config), "HA config.yml not found")
        self.assertTrue(os.path.exists(ha_translations), "HA translations not found")
        
        print("✅ Home Assistant config test passed")

def run_tests():
    """Run all tests and display results."""
    print("\n🧪 Running API-Only Mode Tests...")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAPIOnlyMode)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("🎉 All tests passed! API-Only mode is ready for deployment.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)