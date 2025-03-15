import subprocess
import logging
import requests
from enum import Enum
from typing import Dict, Optional, Tuple, List, Any

class WarpMode(Enum):
    """Available WARP modes"""
    WARP = "warp"  # Full tunnel mode
    DOT = "dot"    # DNS-over-TLS mode
    PROXY = "proxy"  # Proxy mode
    OFF = "off"    # WARP disabled

class WarpService:
    """Service for interacting with Cloudflare WARP client"""
    
    def __init__(self, accept_tos: bool = True):
        """
        Initialize the WARP service
        
        Args:
            accept_tos: Whether to automatically accept the Terms of Service
        """
        self.logger = logging.getLogger(__name__)
        self.accept_tos = accept_tos
        
    def _run_command(self, args: List[str]) -> Tuple[int, str, str]:
        """
        Run a warp-cli command and return the result
        
        Args:
            args: List of arguments to pass to warp-cli
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = ["warp-cli"]
        if self.accept_tos:
            cmd.append("--accept-tos")
        cmd.extend(args)
        
        self.logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f"Command failed: {stderr.strip()}")
            else:
                self.logger.debug(f"Command output: {stdout.strip()}")
                
            return process.returncode, stdout.strip(), stderr.strip()
        except Exception as e:
            self.logger.error(f"Error executing warp-cli: {str(e)}")
            return 1, "", str(e)
    
    def is_running(self) -> bool:
        """Check if the WARP daemon is running"""
        try:
            code, _, _ = self._run_command(["status"])
            return code == 0
        except Exception:
            return False
            
    def connect(self) -> bool:
        """Connect to WARP"""
        code, _, _ = self._run_command(["connect"])
        return code == 0
        
    def disconnect(self) -> bool:
        """Disconnect from WARP"""
        code, _, _ = self._run_command(["disconnect"])
        return code == 0
        
    def set_mode(self, mode: WarpMode) -> bool:
        """
        Set the WARP mode
        
        Args:
            mode: The mode to set WARP to
            
        Returns:
            True if successful, False otherwise
        """
        code, _, _ = self._run_command(["mode", mode.value])
        return code == 0
        
    def get_mode(self) -> Optional[WarpMode]:
        """Get the current WARP mode"""
        code, stdout, _ = self._run_command(["settings"])
        
        if code != 0:
            return None
            
        # Parse the mode from settings output
        for line in stdout.splitlines():
            if "Mode:" in line:
                mode_str = line.split("Mode:")[1].strip().lower()
                for mode in WarpMode:
                    if mode.value == mode_str:
                        return mode
        return None
    
    def get_cf_trace(self) -> Dict[str, str]:
        """
        Get trace information from Cloudflare to verify WARP connection
        
        Returns:
            Dictionary containing trace information
        """
        try:
            response = requests.get("https://www.cloudflare.com/cdn-cgi/trace/", timeout=5)
            if not response.ok:
                self.logger.error(f"Failed to get Cloudflare trace: {response.status_code}")
                return {}
            
            # Parse the response text into a dictionary
            trace_data = {}
            for line in response.text.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    trace_data[key] = value
                    
            return trace_data
        except Exception as e:
            self.logger.error(f"Error getting Cloudflare trace: {str(e)}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of WARP"""
        status = {
            "running": False,
            "connected": False,
            "mode": None,
            "account_type": "free",
            "ip": None,
            "cf_trace": {}
        }
        
        # Check if running
        if not self.is_running():
            return status
            
        status["running"] = True
        
        # Get connection status
        code, stdout, _ = self._run_command(["status"])
        if code == 0:
            for line in stdout.splitlines():
                if "Status update:" in line and "Connected" in line:
                    status["connected"] = True
                elif "Status update:" in line and "Disconnected" in line:
                    status["connected"] = False
                    
        # Get current mode
        mode = self.get_mode()
        status["mode"] = mode.value if mode else None
        
        # Get account type
        code, stdout, _ = self._run_command(["account"])
        if code == 0:
            for line in stdout.splitlines():
                if "Type:" in line and "Team" in line:
                    status["account_type"] = "team"
                elif "Type:" in line and "Premium" in line:
                    status["account_type"] = "premium"
        
        # Get current IP
        if status["connected"]:
            code, stdout, _ = self._run_command(["warp-stats"])
            for line in stdout.splitlines():
                if "WAN IP:" in line:
                    status["ip"] = line.split("WAN IP:")[1].strip()
            
            # Get Cloudflare trace information if connected
            status["cf_trace"] = self.get_cf_trace()
        
        return status
    
    def register_license(self, license_key: str) -> bool:
        """
        Register a license key with WARP
        
        Args:
            license_key: The license key to register
            
        Returns:
            True if successful, False otherwise
        """
        code, _, _ = self._run_command(["registration", "license", license_key])
        return code == 0
