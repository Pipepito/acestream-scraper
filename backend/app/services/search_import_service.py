"""Authoritative, additive catalogue import shared with saved searches."""
from app.schemas.search import SearchImportOutcome, SearchImportResponse
from app.services.search_catalogue_client import SearchCatalogueClient, CatalogueReadError
from app.services.import_exclusion_service import ImportExclusionService
from app.repositories.channel_repository import ChannelRepository
from app.api.error_handlers import APIError


def resolve_candidates(client, candidates, policy):
    resolved, seen = [], set()
    for item in candidates:
        item = dict(item)
        ih = item['infohash'].lower()
        item['infohash'] = ih
        if ih in seen:
            item['decision'] = 'duplicate'
        elif policy.matches('', item['name']):
            item['decision'] = 'excluded'
        else:
            try:
                item['content_id'] = client.resolve(ih)
                item['decision'] = 'resolved'
            except CatalogueReadError as exc:
                item['decision'] = 'deferred' if exc.code in ('deadline', 'shutdown') else 'unresolved'
                item['resolution_stop_reason'] = exc.code
        seen.add(ih)
        resolved.append(item)
    return resolved


def apply_candidates(db, candidates, policy, provenance='Acestream Search', *, dry_run=False):
    repo = ChannelRepository(db)
    outcomes, seen = [], set()
    existing_ids = repo.existing_import_ids(c['content_id'] for c in candidates if c.get('content_id'))
    for item in candidates:
        cid = item.get('content_id')
        rules = policy.matches(cid or '', item['name'])
        decision = item['decision']
        if rules:
            decision = 'excluded'
        elif decision == 'excluded':
            # An early exclusion became eligible during network work. It has no
            # authoritative ID: defer rather than saving its infohash.
            decision = 'deferred'
        elif cid:
            if cid in seen:
                decision = 'duplicate'
            else:
                decision = 'existing' if cid in existing_ids else 'added'
                if cid not in existing_ids and not dry_run:
                    repo.create_or_update_channel(cid, item['name'], source_url=provenance,
                        group=item.get('category') or None, is_online=None, commit=False)
                seen.add(cid)
        outcomes.append(SearchImportOutcome(infohash=item['infohash'], content_id=cid,
            outcome=decision, rule_ids=rules))
    return SearchImportResponse(items=outcomes, policy_revision=policy.revision,
        **{key: sum(i.outcome == key for i in outcomes)
           for key in ('added', 'existing', 'excluded', 'unresolved', 'deferred')})


class SearchImportService:
    def __init__(self, db):
        self.db = db

    def import_items(self, request):
        from app.services.config_service import ConfigService
        from app.repositories.settings_repository import SettingsRepository
        url = ConfigService(SettingsRepository(self.db)).get_ace_engine_url()
        policy = ImportExclusionService(self.db).snapshot()
        self.db.rollback()
        try:
            with SearchCatalogueClient(url) as client:
                candidates = resolve_candidates(client, [i.model_dump() for i in request.items], policy)
        except CatalogueReadError as exc:
            raise APIError(exc.code, 'Configure a reachable AceStream engine in Settings → Playback.', 503) from None
        try:
            policy = ImportExclusionService(self.db).snapshot(claim=True)
            result = apply_candidates(self.db, candidates, policy)
            self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            raise
