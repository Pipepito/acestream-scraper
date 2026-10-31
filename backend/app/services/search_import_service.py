"""Authoritative, additive catalogue import shared with saved searches."""
from app.schemas.search import SearchImportOutcome, SearchImportResponse
from app.services.search_catalogue_client import SearchCatalogueClient, CatalogueReadError
from app.services.import_exclusion_service import ImportExclusionService
from app.services.import_pipeline import ImportEntry, ImportPipeline, ImportReference
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
    decisions, pending = [], []
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
            pending.append(len(decisions))
        decisions.append((decision, rules))
    result = ImportPipeline.apply(db, ImportReference(provenance, dry_run=dry_run), [
        ImportEntry(candidates[index]['content_id'], candidates[index]['name'],
                    group=candidates[index].get('category') or None)
        for index in pending], 'insert_only', policy=policy)
    for index, item in zip(pending, result.items):
        decisions[index] = (item.outcome, decisions[index][1])
    outcomes = [SearchImportOutcome(infohash=item['infohash'], content_id=item.get('content_id'),
                                    outcome=decision, rule_ids=rules)
                for item, (decision, rules) in zip(candidates, decisions)]
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
