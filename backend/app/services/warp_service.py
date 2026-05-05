"""
WARP service for interacting with Cloudflare WARP client
"""
import subprocess
import logging
from enum import Enum
from typing import Dict, Optional, Tuple, List, Any
import httpx

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

    async def _run_command(self, args: List[str]) -> Tuple[int, str, str]:
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

    async def is_running(self) -> bool:
        """Check if the WARP daemon is running"""
        try:
            code, _, _ = await self._run_command(["status"])
            return code == 0
        except Exception:
            return False

    async def connect(self, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to WARP (optionally with a specific mode)
        """
        try:
            args = ["connect"]
            if mode:
                args = ["mode", mode]
            code, stdout, stderr = await self._run_command(args)
            if code == 0:
                status = await self.get_status()
                return {
                    "success": True,
                    "message": f"Connected to WARP{' in ' + mode if mode else ''} successfully",
                    "status": status
                }
            else:
                return {
                    "success": False,
                    "message": stderr or "Failed to connect to WARP",
                    "error": stderr or "Failed to connect to WARP"
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "error": str(e)
            }

    async def disconnect(self) -> Dict[str, Any]:
        """
        Disconnect from WARP
        """
        try:
            code, stdout, stderr = await self._run_command(["disconnect"])
            if code == 0:
                return {
                    "success": True,
                    "message": "Disconnected from WARP successfully"
                }
            else:
                return {
                    "success": False,
                    "message": stderr or "Failed to disconnect from WARP",
                    "error": stderr or "Failed to disconnect from WARP"
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "error": str(e)
            }

    async def set_mode(self, mode: str) -> Dict[str, Any]:
        """
        Set the WARP mode
        """
        try:
            code, stdout, stderr = await self._run_command(["mode", mode])
            if code == 0:
                status = await self.get_status()
                return {
                    "success": True,
                    "message": f"WARP mode set to {mode}",
                    "status": status
                }
            else:
                return {
                    "success": False,
                    "message": stderr or f"Failed to change WARP mode",
                    "error": stderr or f"Failed to change WARP mode"
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "error": str(e)
            }

    async def get_mode(self) -> Optional[WarpMode]:
        """Get the current WARP mode"""
        code, stdout, _ = await self._run_command(["settings"])

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

    async def get_cf_trace(self) -> Dict[str, str]:
        """
        Get trace information from Cloudflare to verify WARP connection

        Returns:
            Dictionary containing trace information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://www.cloudflare.com/cdn-cgi/trace/", timeout=5)
                if response.status_code != 200:
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

    async def get_status(self) -> Dict[str, Any]:
        """Get the current status of WARP"""
        status = {
            "status": "disconnected",  # Add top-level status
            "running": False,
            "connected": False,
            "mode": None,
            "account_type": "free",
            "ip": None,
            "cf_trace": {}
        }

        # Check if running
        if not await self.is_running():
            return status

        status["running"] = True

        # Get connection status
        code, stdout, _ = await self._run_command(["status"])
        if code == 0:
            for line in stdout.splitlines():
                if "Status update:" in line and "Connected" in line:
                    status["connected"] = True
                    status["status"] = "connected"
                elif "Status update:" in line and "Disconnected" in line:
                    status["connected"] = False
                    status["status"] = "disconnected"

        # Get current mode
        mode = await self.get_mode()
        status["mode"] = mode.value if mode else None

        # Get account type
        code, stdout, _ = await self._run_command(["account"])
        if code == 0:
            for line in stdout.splitlines():
                if "Type:" in line and "Team" in line:
                    status["account_type"] = "team"
                elif "Type:" in line and "Premium" in line:
                    status["account_type"] = "premium"

        # Get current IP
        if status["connected"]:
            code, stdout, _ = await self._run_command(["warp-stats"])
            for line in stdout.splitlines():
                if "WAN IP:" in line:
                    status["ip"] = line.split("WAN IP:")[1].strip()

            # Get Cloudflare trace information if connected
            status["cf_trace"] = await self.get_cf_trace()

        return status

    async def register_license(self, license_key: str) -> Dict[str, Any]:
        """
        Register a license key with WARP
        """
        try:
            code, stdout, stderr = await self._run_command(["registration", "license", license_key])
            if code == 0:
                return {
                    "success": True,
                    "message": "WARP license registered successfully"
                }
            else:
                return {
                    "success": False,
                    "message": stderr or "Failed to register WARP license",
                    "error": stderr or "Failed to register WARP license"
                }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "error": str(e)
            }

# Create a singleton instance
warp_service = WarpService()
