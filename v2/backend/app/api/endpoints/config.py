"""API endpoints for configuration management."""
import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.schemas.config import (
    AceEngineUrlUpdate,
    AddPidUpdate,
    AppIdUpdate,
    BaseUrlUpdate,
    ConfigKeyUpdate,
    ConfigUpdateResponse,
    DashboardConfigResponse,
    DashboardConfigUpdate,
    RescrapeIntervalUpdate,
    SettingResponse,
    SettingsResponse,
)
from app.services.config_service import ConfigService
from app.services.dashboard_config_service import DashboardConfigService

router = APIRouter(tags=["config"])
logger = logging.getLogger(__name__)


def get_config_service(db: Session = Depends(get_db)) -> ConfigService:
    settings_repo = SettingsRepository(db)
    return ConfigService(settings_repo)


def _validate_boolean_string(value: str, setting_name: str) -> None:
    valid_values = {"true", "false", "True", "False", "1", "0"}
    if value not in valid_values:
        raise HTTPException(status_code=422, detail=f"Invalid boolean value for {setting_name}")


@router.get("/appid", response_model=SettingResponse)
def get_appid(config_service: ConfigService = Depends(get_config_service)):
    """Get whether to use AppID in Acestream links."""
    value = config_service.settings_repo.get_setting(
        getattr(config_service.settings_repo, "APPID", "appid"),
        "false",
    )
    return {"key": "appid", "value": value}


@router.put("/appid", response_model=ConfigUpdateResponse)
def update_appid(
    update: AppIdUpdate,
    config_service: ConfigService = Depends(get_config_service),
):
    """Update whether to use AppID in Acestream links."""
    _validate_boolean_string(update.value, "appid")
    config_service.settings_repo.set_setting(
        getattr(config_service.settings_repo, "APPID", "appid"),
        update.value,
        "Use AppID in Acestream links",
    )
    return {"message": "Setting updated successfully", "value": update.value}


@router.get("/base_url", response_model=SettingResponse)
def get_base_url(config_service: ConfigService = Depends(get_config_service)):
    """Get the base URL for Acestream links."""
    return {"key": "base_url", "value": config_service.get_base_url()}


@router.put("/base_url", response_model=ConfigUpdateResponse)
def update_base_url(
    update: BaseUrlUpdate,
    config_service: ConfigService = Depends(get_config_service),
):
    """Update the base URL for Acestream links."""
    base_url = update.resolved_value()
    if not base_url:
        raise HTTPException(status_code=422, detail="Missing base_url value")
    success = config_service.set_base_url(base_url)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update base URL")
    return {"message": "Base URL updated successfully", "value": base_url}


@router.get("/ace_engine_url", response_model=SettingResponse)
def get_ace_engine_url(config_service: ConfigService = Depends(get_config_service)):
    """Get the Acestream Engine URL."""
    return {"key": "ace_engine_url", "value": config_service.get_ace_engine_url()}


@router.put("/ace_engine_url", response_model=ConfigUpdateResponse)
def update_ace_engine_url(
    update: AceEngineUrlUpdate,
    config_service: ConfigService = Depends(get_config_service),
):
    """Update the Acestream Engine URL."""
    success = config_service.set_ace_engine_url(update.value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update Acestream Engine URL")
    return {"message": "Setting updated successfully", "value": update.value}


@router.get("/rescrape_interval", response_model=SettingResponse)
def get_rescrape_interval(config_service: ConfigService = Depends(get_config_service)):
    """Get the interval between automatic rescrapes in hours."""
    return {"key": "rescrape_interval", "value": str(config_service.get_rescrape_interval())}


@router.put("/rescrape_interval", response_model=ConfigUpdateResponse)
def update_rescrape_interval(
    update: RescrapeIntervalUpdate,
    config_service: ConfigService = Depends(get_config_service),
):
    """Update the interval between automatic rescrapes in hours."""
    value = update.resolved_value()
    if not value:
        raise HTTPException(status_code=422, detail="Missing rescrape_interval value")
    try:
        hours = int(value)
        if hours < 1:
            raise HTTPException(status_code=422, detail="Rescrape interval must be positive")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Rescrape interval must be a valid number") from exc
    success = config_service.set_rescrape_interval(hours)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update rescrape interval")
    return {"message": "Setting updated successfully", "value": str(hours)}


@router.get("/addpid", response_model=SettingResponse)
def get_addpid(config_service: ConfigService = Depends(get_config_service)):
    """Get whether to add PID to Acestream links."""
    return {"key": "addpid", "value": config_service.get_addpid()}


@router.put("/addpid", response_model=ConfigUpdateResponse)
def update_addpid(
    update: AddPidUpdate,
    config_service: ConfigService = Depends(get_config_service),
):
    """Update whether to add PID to Acestream links."""
    _validate_boolean_string(update.value, "addpid")
    enabled = update.value.lower() in {"true", "1"}
    config_service.set_addpid(enabled)
    # Preserve exact string representation for compatibility with existing tests.
    config_service.settings_repo.set_setting(
        config_service.settings_repo.ADDPID,
        update.value,
        "Add PID to Acestream links",
    )
    return {"message": "Setting updated successfully", "value": update.value}


@router.get("/all", response_model=SettingsResponse)
def get_all_settings(config_service: ConfigService = Depends(get_config_service)):
    """Get all settings."""
    return {"settings": config_service.get_all_settings()}


@router.get("/acestream_status")
def check_acestream_status(config_service: ConfigService = Depends(get_config_service)):
    """Check the status of the Acestream Engine."""
    return config_service.check_acestream_status()


@router.get("/dashboard", response_model=DashboardConfigResponse)
def get_dashboard_config(db: Session = Depends(get_db)):
    service = DashboardConfigService(db)
    config = service.get_config()
    return {
        "retention_days": config.retention_days,
        "auto_refresh_interval": config.auto_refresh_interval,
    }


@router.put("/dashboard", response_model=DashboardConfigResponse)
def update_dashboard_config(
    update: DashboardConfigUpdate = Body(...),
    db: Session = Depends(get_db),
):
    service = DashboardConfigService(db)
    config = service.update_config(
        retention_days=update.retention_days,
        auto_refresh_interval=update.auto_refresh_interval,
    )
    return {
        "retention_days": config.retention_days,
        "auto_refresh_interval": config.auto_refresh_interval,
    }


@router.get("/{key}", response_model=SettingResponse)
def get_config_key(key: str, config_service: ConfigService = Depends(get_config_service)):
    """Generic GET for config keys."""
    if key == "base_url":
        value = config_service.get_base_url()
    elif key == "ace_engine_url":
        value = config_service.get_ace_engine_url()
    elif key == "rescrape_interval":
        value = str(config_service.get_rescrape_interval())
    elif key == "addpid":
        value = config_service.get_addpid()
    else:
        raise HTTPException(status_code=404, detail=f"Unknown config key: {key}")
    return {"key": key, "value": value}


@router.put("/{key}", response_model=ConfigUpdateResponse)
def update_config_key(
    key: str,
    update: ConfigKeyUpdate,
    config_service: ConfigService = Depends(get_config_service),
):
    """Generic PUT for config keys."""
    logger.info("PUT /config/{key}: key=%s, update=%s", key, update.model_dump(exclude_none=True))
    value = update.get_value_for_key(key)

    if key == "base_url":
        if not value:
            raise HTTPException(status_code=422, detail="Missing base_url value")
        success = config_service.set_base_url(value)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update base_url")
        return {"message": "Base URL updated successfully", "value": value}

    if key == "ace_engine_url":
        if not value:
            raise HTTPException(status_code=422, detail="Missing ace_engine_url value")
        success = config_service.set_ace_engine_url(value)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update ace_engine_url")
        return {"message": "Setting updated successfully", "value": value}

    if key == "rescrape_interval":
        if not value:
            raise HTTPException(status_code=422, detail="Missing rescrape_interval value")
        try:
            hours = int(value)
            if hours < 1:
                raise HTTPException(status_code=422, detail="Rescrape interval must be positive")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Rescrape interval must be a valid number") from exc
        success = config_service.set_rescrape_interval(hours)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update rescrape_interval")
        return {"message": "Setting updated successfully", "value": str(hours)}

    if key == "addpid":
        if not value:
            raise HTTPException(status_code=422, detail="Missing addpid value")
        _validate_boolean_string(value, "addpid")
        enabled = value.lower() in {"true", "1"}
        config_service.set_addpid(enabled)
        config_service.settings_repo.set_setting(
            config_service.settings_repo.ADDPID,
            value,
            "Add PID to Acestream links",
        )
        return {"message": "Setting updated successfully", "value": value}

    raise HTTPException(status_code=404, detail=f"Unknown config key: {key}")
