"""ImportPipeline contract: modes, caller-owned sessions and the exclusion policy."""
import pytest

from app.schemas.import_exclusions import ExclusionInput
from app.services.import_exclusion_service import ImportExclusionService, PolicySnapshot
from app.services.import_pipeline import ImportEntry, ImportPipeline, ImportReference

A, B, C = ('a' * 40, 'b' * 40, 'c' * 40)
SOURCE = 'https://lists.example.invalid/channels.m3u'


@pytest.mark.parametrize('reference,mode', [
    (ImportReference(SOURCE), 'replace'),
    (ImportReference(SOURCE, allow_excluded=True), 'snapshot'),
    (ImportReference(SOURCE, allow_excluded=True), 'insert_only'),
    (ImportReference(SOURCE, touch_existing=True), 'snapshot'),
    (ImportReference(SOURCE, dry_run=True), 'manual'),
    (ImportReference(SOURCE, status='Partial'), 'insert_only'),
    (ImportReference(SOURCE, custom_recipe=True), 'manual'),
    (ImportReference(SOURCE, aliases=(SOURCE + '?a',)), 'insert_only'),
])
def test_options_belong_to_their_mode(db_session, reference, mode):
    with pytest.raises(ValueError):
        ImportPipeline.apply(db_session, reference, [ImportEntry(A, 'Name')], mode)


@pytest.mark.parametrize('mode,reference', [
    ('snapshot', ImportReference(SOURCE)),
    ('insert_only', ImportReference(SOURCE)),
    ('manual', ImportReference(SOURCE)),
])
def test_apply_leaves_commit_and_rollback_to_the_caller(db_session, mode, reference):
    from app.models.models import AcestreamChannel
    db_session.add(AcestreamChannel(id=C, name='Absent', source_url=SOURCE))
    db_session.commit()
    result = ImportPipeline.apply(db_session, reference, [ImportEntry(A, 'New')], mode)
    assert [item.outcome for item in result.items] == [{'snapshot': 'upserted'}.get(mode, 'added')]
    db_session.rollback()
    assert db_session.get(AcestreamChannel, A) is None
    assert db_session.get(AcestreamChannel, C) is not None


def test_given_policy_is_used_instead_of_the_stored_rules(db_session):
    from app.models.models import AcestreamChannel
    ImportExclusionService(db_session).save(ExclusionInput(kind='name_equals', value='Stored rule'))
    given = PolicySnapshot(7, ((3, 'name_equals', 'given rule'),))
    result = ImportPipeline.apply(db_session, ImportReference('telegram-source:1'),
                                  [ImportEntry(A, 'Given rule'), ImportEntry(B, 'Stored rule')], 'insert_only', policy=given)
    assert [(i.outcome, i.rule_ids) for i in result.items] == [('excluded', [3]), ('added', [])]
    assert result.policy is given
    db_session.commit()
    assert db_session.get(AcestreamChannel, A) is None and db_session.get(AcestreamChannel, B) is not None


def test_without_policy_the_stored_rules_apply(db_session):
    rule = ImportExclusionService(db_session).save(ExclusionInput(kind='name_equals', value='Stored rule')).rule
    result = ImportPipeline.apply(db_session, ImportReference('telegram-source:1'),
                                  [ImportEntry(A, 'Stored rule')], 'insert_only')
    assert [(i.outcome, i.rule_ids) for i in result.items] == [('excluded', [rule.id])]
    assert result.policy.revision == 1


def test_manual_override_admits_and_reports_the_matching_rules(db_session):
    from app.api.error_handlers import APIError
    rule = ImportExclusionService(db_session).save(ExclusionInput(kind='name_equals', value='Blocked')).rule
    with pytest.raises(APIError) as refused:
        ImportPipeline.apply(db_session, ImportReference(None), [ImportEntry(A, 'Blocked')], 'manual')
    assert refused.value.code == 'IMPORT_EXCLUDED'
    result = ImportPipeline.apply(db_session, ImportReference(None, allow_excluded=True),
                                  [ImportEntry(A, 'Blocked')], 'manual')
    assert [(i.outcome, i.rule_ids, i.channel.id) for i in result.items] == [('added', [rule.id], A)]


def test_snapshot_reports_excluded_and_protected_identities(db_session):
    from app.models.models import AcestreamChannel
    db_session.add(AcestreamChannel(id=C, name='Blocked stored', source_url=SOURCE))
    db_session.commit()
    ImportExclusionService(db_session).save(ExclusionInput(kind='name_contains', value='blocked'))
    result = ImportPipeline.apply(db_session, ImportReference(SOURCE),
                                  [ImportEntry.from_scrape(A, 'Blocked', {}), ImportEntry.from_scrape(B, 'Allowed', {})],
                                  'snapshot')
    assert (result.excluded_ids, result.protected_ids) == ({A}, {A, C})
    assert [c.id for c in result.channels] == [B]
    assert result.count('excluded') == 1


def test_insert_only_dry_run_and_touch(db_session):
    from datetime import datetime, timezone
    from app.models.models import AcestreamChannel
    old = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db_session.add(AcestreamChannel(id=A, name='Existing', last_seen=old))
    db_session.commit()
    entries = [ImportEntry(A, 'Publisher'), ImportEntry(B, 'New'), ImportEntry(B, 'New')]
    dry = ImportPipeline.apply(db_session, ImportReference('x', dry_run=True, touch_existing=True), entries, 'insert_only')
    assert [i.outcome for i in dry.items] == ['existing', 'added', 'duplicate']
    db_session.commit()
    row = db_session.get(AcestreamChannel, A)
    assert row.last_seen.replace(tzinfo=timezone.utc) == old and db_session.get(AcestreamChannel, B) is None
    ImportPipeline.apply(db_session, ImportReference('x', touch_existing=True), entries, 'insert_only')
    db_session.commit()
    db_session.expire_all()
    row = db_session.get(AcestreamChannel, A)
    assert row.name == 'Existing' and row.last_seen.replace(tzinfo=timezone.utc) > old
