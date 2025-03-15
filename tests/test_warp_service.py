import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to path to be able to import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.warp_service import WarpService, WarpMode

class TestWarpService(unittest.TestCase):
    
    @patch('app.services.warp_service.subprocess.Popen')
    def setUp(self, mock_popen):
        # Set up the mock process
        self.process_mock = MagicMock()
        self.process_mock.returncode = 0
        self.process_mock.communicate.return_value = ("Success", "")
        mock_popen.return_value = self.process_mock
        
        # Create service instance
        self.service = WarpService()
        
    @patch('app.services.warp_service.subprocess.Popen')
    def test_is_running(self, mock_popen):
        # Set up the mock process
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ("Status: Running", "")
        mock_popen.return_value = process_mock
        
        # Test is_running returns True when command succeeds
        self.assertTrue(self.service.is_running())
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "status"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        # Test is_running returns False when command fails
        process_mock.returncode = 1
        self.assertFalse(self.service.is_running())
        
        # Test is_running handles exceptions
        mock_popen.side_effect = Exception("Failed to run command")
        self.assertFalse(self.service.is_running())
        
    @patch('app.services.warp_service.subprocess.Popen')
    def test_connect(self, mock_popen):
        # Set up the mock process
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ("Connecting...", "")
        mock_popen.return_value = process_mock
        
        # Test connect returns True when command succeeds
        self.assertTrue(self.service.connect())
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "connect"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        # Test connect returns False when command fails
        process_mock.returncode = 1
        self.assertFalse(self.service.connect())
        
    @patch('app.services.warp_service.subprocess.Popen')
    def test_disconnect(self, mock_popen):
        # Set up the mock process
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ("Disconnecting...", "")
        mock_popen.return_value = process_mock
        
        # Test disconnect returns True when command succeeds
        self.assertTrue(self.service.disconnect())
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "disconnect"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        # Test disconnect returns False when command fails
        process_mock.returncode = 1
        self.assertFalse(self.service.disconnect())
        
    @patch('app.services.warp_service.subprocess.Popen')
    def test_set_mode(self, mock_popen):
        # Set up the mock process
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ("Mode changed to warp", "")
        mock_popen.return_value = process_mock
        
        # Test setting different modes
        self.assertTrue(self.service.set_mode(WarpMode.WARP))
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "mode", "warp"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        self.assertTrue(self.service.set_mode(WarpMode.DOT))
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "mode", "dot"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        self.assertTrue(self.service.set_mode(WarpMode.PROXY))
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "mode", "proxy"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        self.assertTrue(self.service.set_mode(WarpMode.OFF))
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "mode", "off"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        # Test failure case
        process_mock.returncode = 1
        self.assertFalse(self.service.set_mode(WarpMode.WARP))
        
    @patch('app.services.warp_service.subprocess.Popen')
    def test_get_mode(self, mock_popen):
        # Set up the mock process
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = (
            "Settings:\n" +
            "  Mode: warp\n" +
            "  Proxy Port: 40000\n",
            ""
        )
        mock_popen.return_value = process_mock
        
        # Test getting mode
        self.assertEqual(self.service.get_mode(), WarpMode.WARP)
        
        # Test different mode
        process_mock.communicate.return_value = (
            "Settings:\n" +
            "  Mode: dot\n" +
            "  Proxy Port: 40000\n",
            ""
        )
        self.assertEqual(self.service.get_mode(), WarpMode.DOT)
        
        # Test proxy mode
        process_mock.communicate.return_value = (
            "Settings:\n" +
            "  Mode: proxy\n" +
            "  Proxy Port: 40000\n",
            ""
        )
        self.assertEqual(self.service.get_mode(), WarpMode.PROXY)
        
        # Test off mode
        process_mock.communicate.return_value = (
            "Settings:\n" +
            "  Mode: off\n" +
            "  Proxy Port: 40000\n",
            ""
        )
        self.assertEqual(self.service.get_mode(), WarpMode.OFF)
        
        # Test failure case
        process_mock.returncode = 1
        self.assertIsNone(self.service.get_mode())
        
        # Test invalid mode
        process_mock.returncode = 0
        process_mock.communicate.return_value = (
            "Settings:\n" +
            "  Mode: invalid\n" +
            "  Proxy Port: 40000\n",
            ""
        )
        self.assertIsNone(self.service.get_mode())
    
    @patch('app.services.warp_service.WarpService.is_running')
    @patch('app.services.warp_service.WarpService.get_mode')
    @patch('app.services.warp_service.subprocess.Popen')
    def test_get_status(self, mock_popen, mock_get_mode, mock_is_running):
        # Set up mocks
        mock_is_running.return_value = True
        mock_get_mode.return_value = WarpMode.WARP
        
        # Configure process_mock for different commands
        def command_side_effect(*args, **kwargs):
            process_mock = MagicMock()
            process_mock.returncode = 0
            
            # Match specific command
            if len(args[0]) > 2:
                cmd = args[0][2]
                
                if cmd == "status":
                    process_mock.communicate.return_value = (
                        "Status update: Connected\n" +
                        "Connection: Connected",
                        ""
                    )
                elif cmd == "account":
                    process_mock.communicate.return_value = (
                        "Account type: Premium\n" +
                        "Type: Premium",
                        ""
                    )
                elif cmd == "warp-stats":
                    process_mock.communicate.return_value = (
                        "Connection:\n" +
                        "  WAN IP: 1.2.3.4",
                        ""
                    )
            
            return process_mock
            
        mock_popen.side_effect = command_side_effect
        
        # Test getting status when connected
        status = self.service.get_status()
        self.assertTrue(status["running"])
        self.assertTrue(status["connected"])
        self.assertEqual(status["mode"], "warp")
        self.assertEqual(status["account_type"], "premium")
        self.assertEqual(status["ip"], "1.2.3.4")
        
        # Test when not running
        mock_is_running.return_value = False
        status = self.service.get_status()
        self.assertFalse(status["running"])
        self.assertFalse(status["connected"])
        self.assertIsNone(status["mode"])
        
        # Test disconnected state
        mock_is_running.return_value = True
        def disconnected_side_effect(*args, **kwargs):
            process_mock = MagicMock()
            process_mock.returncode = 0
            
            # Match specific command
            if len(args[0]) > 2:
                cmd = args[0][2]
                
                if cmd == "status":
                    process_mock.communicate.return_value = (
                        "Status update: Disconnected\n" +
                        "Connection: Disconnected",
                        ""
                    )
                elif cmd == "account":
                    process_mock.communicate.return_value = (
                        "Account type: Free\n" +
                        "Type: Free",
                        ""
                    )
            
            return process_mock
            
        mock_popen.side_effect = disconnected_side_effect
        
        status = self.service.get_status()
        self.assertTrue(status["running"])
        self.assertFalse(status["connected"])
        self.assertEqual(status["account_type"], "free")
        self.assertIsNone(status["ip"])
        
    @patch('app.services.warp_service.subprocess.Popen')
    def test_register_license(self, mock_popen):
        # Set up the mock process
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ("License registered", "")
        mock_popen.return_value = process_mock
        
        # Test successful license registration
        self.assertTrue(self.service.register_license("abc-123-def-456"))
        mock_popen.assert_called_with(
            ["warp-cli", "--accept-tos", "registration", "license", "abc-123-def-456"],
            stdout=-1,
            stderr=-1,
            text=True
        )
        
        # Test failed license registration
        process_mock.returncode = 1
        process_mock.communicate.return_value = ("", "Invalid license key")
        self.assertFalse(self.service.register_license("invalid-key"))

if __name__ == '__main__':
    unittest.main()
