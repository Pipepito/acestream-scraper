"""Opt-in guide matching after successful ingestion; no startup work."""
import logging
from datetime import datetime, timezone
from pydantic import ValidationError
from app.repositories.settings_repository import SettingsRepository
from app.schemas.config import EPGMatchingConfig, EPGMatchingRun

logger = logging.getLogger(__name__)
CONFIG_KEY = 'epg_matching'
RESULT_KEY = 'epg_matching_last_run'


class EPGMatchingAutomation:
    def __init__(self, db):
        self.db = db
        self.settings = SettingsRepository(db)

    def get(self):
        try:
            return EPGMatchingConfig.model_validate_json(self.settings.get_setting(CONFIG_KEY) or '{}')
        except (ValueError, ValidationError):
            return EPGMatchingConfig()  # malformed settings never opt in

    def save(self, config):
        return self.settings.set_setting(CONFIG_KEY, config.model_dump_json(), 'Automatic guide matching')

    def last_run(self):
        try:
            return EPGMatchingRun.model_validate_json(self.settings.get_setting(RESULT_KEY) or '{}')
        except (ValueError, ValidationError):
            return EPGMatchingRun()

    def run(self):
        from app.services.epg_match_service import EPGMatchService
        from app.services.tvchannel_service import TVChannelService, _MATCH_APPLY_LOCK
        # The same lock covers reviewed applies. Repository assignments also
        # condition their writes on the stream still being unassigned.
        with _MATCH_APPLY_LOCK:
            if not self.get().enabled:
                return None
            result = EPGMatchingRun(status='success', finished_at=datetime.now(timezone.utc))
            try:
                analysis = EPGMatchService(self.db).analyze_matches('strict')
                safe = [row for row in analysis['rows'] if row['automation_safe']]
                # Bound writes as well as comparisons; later ingestions continue.
                selected = safe[:1000]
                result.review_needed = sum(row['ambiguous_count'] for row in analysis['rows']) + sum(
                    row['candidate_count'] for row in analysis['rows'] if not row['automation_safe'])
                if selected:
                    applied = TVChannelService(self.db).create_tv_channels_from_epg_analysis(
                        'strict', [row['epg_channel_id'] for row in selected], automatic=True,
                        expected_previews={row['epg_channel_id']: row['review_token'] for row in selected})
                    result.created = applied['created_count']
                    result.assigned = applied['associated_count']
                    if applied['failure_count']:
                        result.status = 'partial'
                self.db.commit()
            except Exception:
                # Ingestion was committed before this optional follow-up. Its
                # success and existing assignments survive any matching failure.
                self.db.rollback()
                result.status = 'error'
                logger.warning('Automatic guide matching failed; review matches in EPG.')
            result.finished_at = datetime.now(timezone.utc)
            self.settings.set_setting(RESULT_KEY, result.model_dump_json(), 'Last automatic guide matching result')
            return result
