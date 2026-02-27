"""
API endpoints for Cloudflare WARP
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi import status as http_status, Request
import asyncio

from app.schemas.warp import (
    WarpStatusResponse,
    WarpResponse,
    WarpLicenseRequest,
    WarpModeRequest,
    WarpModeEnum
)
from app.services.warp_service import warp_service, WarpMode

router = APIRouter()

@router.get("/status", summary="Get WARP status")
async def get_warp_status():
    """
    Get the current status of the WARP client.

    Returns:
        Information about the current WARP status.
    """
    try:
        result = await warp_service.get_status()
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={
            "detail": "Internal Server Error",
            "success": False,
            "error": str(e),
            "message": str(e)
        }, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/connect", summary="Connect to WARP")
async def connect_to_warp(request: Request):
    """
    Connect to the WARP network.

    Returns:
        Success message if the connection was successful.
    """
    try:
        try:
            body = await request.json() if request.method == "POST" else {}
        except Exception:
            body = {}
        mode = body.get("mode") if isinstance(body, dict) else None
        if mode:
            result = await warp_service.connect(mode=mode)
        else:
            result = await warp_service.connect()
        # Robustly await result until it is not a coroutine (handles AsyncMock double-async)
        import asyncio
        while asyncio.iscoroutine(result):
            result = await result
        if not result.get("success", False):
            return JSONResponse(content={
                "detail": result.get("message", "Failed to connect to WARP"),
                "success": False,
                "error": result.get("error", result.get("message", "Failed to connect to WARP")),
                "message": result.get("message", "Failed to connect to WARP")
            }, status_code=http_status.HTTP_400_BAD_REQUEST)
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={
            "detail": "Internal Server Error",
            "success": False,
            "error": str(e),
            "message": str(e)
        }, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/disconnect", summary="Disconnect from WARP")
async def disconnect_from_warp():
    """
    Disconnect from the WARP network.

    Returns:
        Success message if the disconnection was successful.
    """
    try:
        result = await warp_service.disconnect()
        if asyncio.iscoroutine(result):
            result = await result
        if not result.get("success", False):
            return JSONResponse(content={
                "detail": result.get("message", "Failed to disconnect from WARP"),
                "success": False,
                "error": result.get("error", result.get("message", "Failed to disconnect from WARP")),
                "message": result.get("message", "Failed to disconnect from WARP")
            }, status_code=http_status.HTTP_400_BAD_REQUEST)
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={
            "detail": "Internal Server Error",
            "success": False,
            "error": str(e),
            "message": str(e)
        }, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/mode", summary="Set WARP mode")
async def set_warp_mode(request: WarpModeRequest):
    """
    Set the WARP mode (warp, dot, proxy, or off).

    Args:
        request: The mode to set WARP to.

    Returns:
        Success message if the mode was set successfully.
    """
    try:
        mode = request.mode.value if hasattr(request.mode, 'value') else str(request.mode)
        result = await warp_service.set_mode(mode)
        if asyncio.iscoroutine(result):
            result = await result
        if not result.get("success", False):
            return JSONResponse(content={
                "detail": result.get("message", f"Failed to change WARP mode"),
                "success": False,
                "error": result.get("error", result.get("message", f"Failed to change WARP mode")),
                "message": result.get("message", f"Failed to change WARP mode")
            }, status_code=http_status.HTTP_400_BAD_REQUEST)
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={
            "detail": "Internal Server Error",
            "success": False,
            "error": str(e),
            "message": str(e)
        }, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/license", summary="Register WARP license")
async def register_warp_license(request: dict):
    """
    Register a license key with the WARP client.

    Args:
        request: The license key to register.

    Returns:
        Success message if the license was registered successfully.
    """
    try:
        license_key = request.get("license")
        if not license_key:
            return JSONResponse(content={
                "detail": "Missing license key",
                "success": False,
                "error": "Missing license key",
                "message": "Missing license key"
            }, status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY)
        result = await warp_service.register_license(license_key)
        if asyncio.iscoroutine(result):
            result = await result
        if not result.get("success", False):
            return JSONResponse(content={
                "detail": result.get("message", "Failed to register WARP license"),
                "success": False,
                "error": result.get("error", result.get("message", "Failed to register WARP license")),
                "message": result.get("message", "Failed to register WARP license")
            }, status_code=http_status.HTTP_400_BAD_REQUEST)
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except Exception as e:
        return JSONResponse(content={
            "detail": "Internal Server Error",
            "success": False,
            "error": str(e),
            "message": str(e)
        }, status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR)
