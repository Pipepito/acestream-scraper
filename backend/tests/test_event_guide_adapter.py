import json
from pathlib import Path
import pytest
from app.services.event_guide_adapter import parse_guide

HTML = Path(__file__).parent / 'fixtures/events/structured-guide.html'


def parse(raw):
    return parse_guide(raw, source_id='guide:sample', source_name='Sample guide', zone='Europe/Madrid')


def test_structured_html_preserves_identity_broadcasts_unknown_time_and_no_false_signal():
    data = parse(HTML.read_text())
    first = next(row for row in data.observations if row.external_id == 'fixture-101')
    assert first.starts_at.isoformat() == '2026-10-24T21:30:00+00:00'
    assert first.ends_at is None and first.state == 'scheduled'
    assert first.participants == ['North United', 'South City']
    assert len(first.broadcasts) == 3
    unresolved = next(b for b in first.broadcasts if b.label == 'DAZN')
    assert unresolved.url is None and unresolved.channel_id is None
    assert all('tickets' not in (b.url or '') for b in first.broadcasts)
    postponed = next(row for row in data.observations if row.external_id == 'fixture-102')
    assert postponed.starts_at is None and postponed.state == 'postponed'
    updated = parse(HTML.read_text().replace('2026-10-24T23:30:00', '2026-10-26T00:30:00'))
    assert {o.external_id for o in updated.observations} == {o.external_id for o in data.observations}


@pytest.mark.parametrize('changes', [
    {'@id': None}, {'startDate': 'today'}, {'startDate': '2026-10-25'},
    {'startDate': '2026-10-25T02:30:00'}, {'startDate': '2026-03-29T02:30:00'},
])
def test_no_guessed_identity_dates_or_dst(changes):
    row = {'@type': 'SportsEvent', '@id': 'stable', 'name': 'Match', **changes}
    with pytest.raises(ValueError):
        parse(json.dumps(row))


def test_same_title_stays_separate_and_duplicate_ids_must_agree():
    rows = [{'@type': 'SportsEvent', '@id': str(i), 'name': 'Match'} for i in range(2)]
    assert len(parse(json.dumps(rows)).observations) == 2
    rows[1].update({'@id': '0', 'name': 'Other event'})
    with pytest.raises(ValueError, match='Conflicting'):
        parse(json.dumps(rows))


def test_remote_contexts_not_fetched_and_nesting_bounded():
    row = {'@context': 'https://private.invalid/context', '@type': 'SportsEvent', '@id': '0', 'name': 'Match'}
    assert parse(json.dumps(row)).observations[0].title == 'Match'
    for _ in range(34):
        row = {'nested': row}
    with pytest.raises(ValueError, match='nesting'):
        parse(json.dumps(row))
    with pytest.raises(ValueError, match='No supported'):
        parse('<html><script>fetch("https://private.invalid")</script>Today: Match</html>')
