"""
API endpoints for Cloudflare WARP
"""
import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import status as http_status

from app.api.error_handlers import APIError
from app.schemas.warp import WarpModeRequest
from app.services.warp_service import warp_service

router = APIRouter()


async def _unwrap_result(result: Any) -> Dict[str, Any]:
    while asyncio.iscoroutine(result):
        result = await result
    if not isinstance(result, dict):
        raise APIError(
            code="WARP_INVALID_RESPONSE",
            message="Unexpected WARP service response",
            status_code=http_status.HTTP_502_BAD_GATEWAY,
            context={"result_type": type(result).__name__},
        )
    return result


def _failure_error(operation: str, result: Dict[str, Any], code: str) -> APIError:
    detail = result.get("error") or result.get("message") or "Unknown WARP error"
    return APIError(
        code=code,
        message=f"WARP {operation} failed",
        status_code=http_status.HTTP_400_BAD_REQUEST,
        context={"operation": operation, "error": detail},
    )


def _internal_error(operation: str, exc: Exception, code: str) -> APIError:
    return APIError(
        code=code,
        message=f"WARP {operation} unavailable",
        status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
        context={"operation": operation, "error": str(exc)},
    )


@router.get("/status", summary="Get WARP status")
async def get_warp_status():
    try:
        result = await _unwrap_result(await warp_service.get_status())
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except APIError:
        raise
    except Exception as exc:
        raise _internal_error("status", exc, "WARP_STATUS_UNAVAILABLE") from exc


@router.post("/connect", summary="Connect to WARP")
async def connect_to_warp(request: Request):
    try:
        body = await request.json() if request.method == "POST" else {}
        mode = body.get("mode") if isinstance(body, dict) else None
    except Exception:
        mode = None

    try:
        result = await _unwrap_result(
            await warp_service.connect(mode=mode) if mode else await warp_service.connect()
        )
        if not result.get("success", False):
            raise _failure_error("connect", result, "WARP_CONNECT_FAILED")
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except APIError:
        raise
    except Exception as exc:
        raise _internal_error("connect", exc, "WARP_CONNECT_UNAVAILABLE") from exc


@router.post("/disconnect", summary="Disconnect from WARP")
async def disconnect_from_warp():
    try:
        result = await _unwrap_result(await warp_service.disconnect())
        if not result.get("success", False):
            raise _failure_error("disconnect", result, "WARP_DISCONNECT_FAILED")
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except APIError:
        raise
    except Exception as exc:
        raise _internal_error("disconnect", exc, "WARP_DISCONNECT_UNAVAILABLE") from exc


@router.post("/mode", summary="Set WARP mode")
async def set_warp_mode(request: WarpModeRequest):
    mode = request.mode.value if hasattr(request.mode, "value") else str(request.mode)
    try:
        result = await _unwrap_result(await warp_service.set_mode(mode))
        if not result.get("success", False):
            raise _failure_error("mode", result, "WARP_MODE_CHANGE_FAILED")
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except APIError:
        raise
    except Exception as exc:
        raise _internal_error("mode", exc, "WARP_MODE_CHANGE_UNAVAILABLE") from exc


@router.post("/license", summary="Register WARP license")
async def register_warp_license(request: dict):
    # The schema (WarpLicenseRequest) and the SPA send `license_key`; `license` is the
    # historical key kept for existing callers.
    license_key = (request.get("license_key") or request.get("license")) if isinstance(request, dict) else None
    if not license_key:
        raise APIError(
            code="WARP_LICENSE_REQUIRED",
            message="Missing license key",
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            context={"operation": "license"},
        )

    try:
        result = await _unwrap_result(await warp_service.register_license(license_key))
        if not result.get("success", False):
            raise _failure_error("license registration", result, "WARP_LICENSE_REGISTER_FAILED")
        return JSONResponse(content=result, status_code=http_status.HTTP_200_OK)
    except APIError:
        raise
    except Exception as exc:
        raise _internal_error("license registration", exc, "WARP_LICENSE_REGISTER_UNAVAILABLE") from exc
