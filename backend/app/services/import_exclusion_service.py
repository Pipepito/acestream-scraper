"""Deterministic admission snapshots and operator policy management."""
from dataclasses import dataclass, field
import re
from types import MappingProxyType
from time import monotonic
from sqlalchemy.exc import IntegrityError
from app.api.error_handlers import APIError
from app.models.models import _utcnow
from app.models.import_sources import ImportExclusionRule
from app.repositories.import_exclusion_repository import ImportExclusionRepository
from app.schemas.import_exclusions import (normalized_rule, normalize_name, ExclusionRule,
    ExclusionWrite, ExclusionList, ExclusionPreview, ImportCandidate)


@dataclass(frozen=True)
class PolicySnapshot:
    revision: int
    rules: tuple[tuple[int, str, str], ...]

    exact_ids: object = field(init=False, repr=False)
    exact_names: object = field(init=False, repr=False)
    contains: tuple = field(init=False, repr=False)

    def __post_init__(self):
        ids, names, contains = {}, {}, []
        for rid, kind, value in self.rules:
            if kind == 'stream_id_equals':
                ids.setdefault(value, []).append(rid)
            elif kind == 'name_equals':
                names.setdefault(value, []).append(rid)
            else:
                contains.append((rid, value))
        object.__setattr__(self, 'exact_ids', MappingProxyType({k: tuple(v) for k, v in ids.items()}))
        object.__setattr__(self, 'exact_names', MappingProxyType({k: tuple(v) for k, v in names.items()}))
        object.__setattr__(self, 'contains', tuple(contains))

    def matches(self, channel_id: str, name: str) -> list[int]:
        name = normalize_name(str(name))
        channel_id = channel_id.lower()
        return sorted((*self.exact_ids.get(channel_id, ()), *self.exact_names.get(name, ()),
                       *(rid for rid, value in self.contains if value in name)))


class ImportExclusionService:
    def __init__(self, db):
        self.db = db
        self.repo = ImportExclusionRepository(db)

    def snapshot(self, *, claim=False) -> PolicySnapshot:
        if claim:
            self.repo.claim()
        return PolicySnapshot(self.repo.revision(), tuple(
            (r.id, r.kind, r.match_value) for r in self.repo.rules(True)))

    def require_allowed(self, channel_id, name, *, allow_excluded=False):
        matched = self.snapshot(claim=True).matches(channel_id, name)
        if matched and not allow_excluded:
            raise APIError('IMPORT_EXCLUDED', 'This stream matches an import exclusion.', 409,
                           {'rule_ids': matched})

    def list(self, offset=0, limit=50, enabled=None, rule_id=None):
        query = self.repo.rules(enabled)
        if rule_id is not None:
            query = query.filter(ImportExclusionRule.id == rule_id)
        return ExclusionList(items=[ExclusionRule.model_validate(r) for r in query.offset(offset).limit(limit)],
                             total=query.count(), policy_revision=self.repo.revision())

    def save(self, data, rule_id=None):
        try:
            self.repo.claim()
            row = self.repo.get(rule_id) if rule_id is not None else None
            if rule_id is not None:
                self._check(row, data.expected_revision)
            elif self.repo.rules().count() >= 500:
                raise APIError('IMPORT_RULE_LIMIT', 'At most 500 import exclusions are supported.', 409)
            if row is None:
                row = ImportExclusionRule(revision=0)
                self.db.add(row)
            for key in ('kind', 'value', 'enabled', 'note'):
                setattr(row, key, getattr(data, key))
            row.match_value = normalized_rule(data.kind, data.value)
            row.revision += 1
            row.updated_at = _utcnow()
            self.db.flush()
            revision = self.repo.bump()
            self.db.commit()
            return ExclusionWrite(rule=ExclusionRule.model_validate(row), policy_revision=revision)
        except IntegrityError:
            self.db.rollback()
            raise APIError('IMPORT_RULE_DUPLICATE', 'This exclusion already exists, including disabled rules.', 409) from None
        except Exception:
            self.db.rollback()
            raise

    def _check(self, row, revision):
        if row is None:
            raise APIError('IMPORT_RULE_NOT_FOUND', 'Import exclusion not found.', 404)
        if row.revision != revision:
            raise APIError('IMPORT_POLICY_CHANGED', 'This exclusion changed. Reload before editing.', 409)

    def delete(self, rule_id, revision):
        try:
            self.repo.claim()
            row = self.repo.get(rule_id)
            self._check(row, revision)
            self.db.delete(row)
            self.repo.bump()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def preview(self, data):
        policy = PolicySnapshot(self.repo.revision(), ((0, data.kind, normalized_rule(data.kind, data.value)),))
        scanned = matched = 0
        examples = []
        complete = True
        deadline = monotonic() + 2
        after = ''
        while True:
            rows = ([(c.channel_id, c.name) for c in data.candidates] if data.candidates is not None
                    else self.repo.inventory(after, min(250, 10000 - scanned)))
            for cid, name in rows:
                scanned += 1
                if policy.matches(cid, name):
                    matched += 1
                    if len(examples) < 50:
                        # IDs and display names only; never publisher URLs/headers.
                        examples.append(ImportCandidate(channel_id=cid, name=re.sub(r'https?://\S+', '[URL]', name, flags=re.IGNORECASE)[:512]))
                after = cid
            if data.candidates is not None or len(rows) < 250:
                break
            if scanned >= 10000 or monotonic() >= deadline:
                complete = False
                break
        return ExclusionPreview(policy_revision=policy.revision, scanned=scanned, matched=matched,
                                complete=complete, examples=examples)
