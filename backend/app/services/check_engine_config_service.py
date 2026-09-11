"""Resolve the optional checking route consistently for probes, jobs and health."""
import os
from fastapi import HTTPException
from app.schemas.config import CheckEngineConfig, CheckEngineConfigResponse


class CheckEngineConfigService:
    KEY = "check_engine_config"

    def __init__(self, repository):
        self.repository = repository

    def get(self) -> CheckEngineConfigResponse:
        from app.config.settings import settings
        external = settings.ACE_CHECK_ENGINE_URL.strip()
        if external and not external.startswith(('http://', 'https://')):
            external = 'http://' + external
        managed = os.environ.get("ENABLE_ACESTREAM_CHECK_ENGINE", "false").lower() == "true"
        if managed:
            config = CheckEngineConfig(use_dedicated=True, url=external or "http://127.0.0.1:6880")
        else:
            raw = self.repository.get_setting(self.KEY)
            config = CheckEngineConfig.model_validate_json(raw) if raw else CheckEngineConfig(
                use_dedicated=bool(external), url=external,
            )
        return CheckEngineConfigResponse(**config.model_dump(), managed=managed)

    def save(self, config: CheckEngineConfig) -> CheckEngineConfigResponse:
        if self.get().managed:
            raise HTTPException(409, "The bundled checking engine is controlled by the container configuration.")
        if not self.repository.set_setting(self.KEY, config.model_dump_json(), "Stream checking engine"):
            raise HTTPException(500, "Could not save the checking engine")
        return self.get()

    def effective_url(self) -> str:
        config = self.get()
        return config.url if config.use_dedicated else (self.repository.get_setting(self.repository.ACE_ENGINE_URL) or "").strip()
