"""Automatch identity boundaries and reviewed assignment contracts."""
import pytest
from app.services.tv_matching_service import normalize_name, name_score


@pytest.mark.parametrize('target,stream', [
    ('M+ Acción', 'MOVISTAR ACCION HD --> NEW ERA III'),
    ('M+ Deportes', 'M. Deportes FHDp ** --> ELCANO'),
    ('Esport 3', 'Esport3 FHDp * --> ELCANO'),
    ('Movistar Plus+', 'MOVISTAR PLUS FHD --> ELCANO'),
    ('Матч! Футбол 1 (RU)', 'Матч! Футбол 1 HD (RU)'),
])
def test_normalization_samples(target, stream):
    assert name_score(normalize_name(target), normalize_name(stream)) == (0.99, 'Normalized name')


@pytest.mark.parametrize('target,stream', [
    ('DAZN 1', 'DAZN 2 HD'), ('DAZN 1', 'DAZN 1 BAR'),
    ('M+ Deportes', 'M+ Deportes 2'), ('ESPN', 'ESPN 2'),
    ('FR | beIN SPORTS 1', 'beIN SPORTS HD 1 (TR)'),
    ('Sport 1', 'Sport1+'), ('M+ Liga de Campeones', 'M+ Liga de Campeones HDR'),
    ('', 'HD'), ('AMC', 'AM'),
])
def test_identity_boundaries(target, stream):
    assert name_score(normalize_name(target), normalize_name(stream)) is None


def test_preview_apply_and_stale_assignments(client, db_session):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name='DAZN 1')
    other = TVChannel(name='Other')
    db_session.add_all([tv, other]); db_session.flush()
    streams = [AcestreamChannel(id=str(i)*40, name='DAZN 1 FHD --> ELCANO') for i in range(1, 4)]
    streams[2].tv_channel_id = other.id
    db_session.add_all(streams); db_session.commit()
    preview = client.post('/api/v1/tv-channels/automatch/preview')
    assert preview.status_code == 200
    data = preview.json()
    assert len(data['candidates']) == 2
    db_session.expire_all()
    assert streams[0].tv_channel_id is None  # Preview has no side effects.
    streams[1].tv_channel_id = other.id
    db_session.commit()
    request = {'assignments': [{'acestream_channel_id': s.id, 'tv_channel_id': tv.id} for s in streams[:2]]}
    response = client.post('/api/v1/tv-channels/automatch/apply', json=request)
    assert response.status_code == 200
    assert response.json() == {'assigned_count': 1, 'skipped_count': 1}
    assert client.post('/api/v1/tv-channels/automatch/apply', json=request).json() == {'assigned_count': 0, 'skipped_count': 2}
    db_session.expire_all()
    assert streams[1].tv_channel_id == streams[2].tv_channel_id == other.id


def test_ambiguity_epg_and_metadata_changes(client, db_session):
    from app.models.models import AcestreamChannel, TVChannel
    tvs = [TVChannel(name='Sport', epg_id='one'), TVChannel(name='Sport HD', epg_id='two')]
    db_session.add_all(tvs); db_session.flush()
    streams = [AcestreamChannel(id='a'*40, name='Sport'), AcestreamChannel(id='b'*40, name='Sport', tvg_id='one'),
               AcestreamChannel(id='c'*40, name='Sport', tvg_id='conflict')]
    db_session.add_all(streams); db_session.commit()
    data = client.post('/api/v1/tv-channels/automatch/preview').json()
    assert data['ambiguous_streams'] == 1
    assert data['unmatched_streams'] == 1
    assert len(data['candidates']) == 1
    assert data['candidates'][0]['reason'] == 'Exact EPG ID and normalized name'
    streams[1].tvg_id = 'changed'; db_session.commit()
    request = {'assignments': [{'acestream_channel_id': streams[1].id, 'tv_channel_id': tvs[0].id}]}
    assert client.post('/api/v1/tv-channels/automatch/apply', json=request).json()['skipped_count'] == 1
    request['assignments'].append({'acestream_channel_id': streams[1].id, 'tv_channel_id': tvs[1].id})
    assert client.post('/api/v1/tv-channels/automatch/apply', json=request).status_code == 422


def test_country_and_typo_guesses_are_withheld():
    assert name_score(normalize_name('FR | beIN Sports 1'), normalize_name('beIN Sports 1')) is None
    assert name_score(normalize_name('Discovery'), normalize_name('Discoveri')) is None
    result = name_score(normalize_name('National Geographic'), normalize_name('National Geographik'))
    assert result is None


def test_tvg_name_fallback_and_workload_limit(client, db_session, monkeypatch):
    from app.models.models import AcestreamChannel, TVChannel
    from app.repositories.channel_repository import ChannelRepository
    db_session.add(TVChannel(name='Canal Cocina'))
    db_session.add(AcestreamChannel(id='d'*40, name='Provider label', tvg_name='Canal Cocina HD'))
    db_session.commit()
    data = client.post('/api/v1/tv-channels/automatch/preview').json()
    assert data['candidates'] == []
    monkeypatch.setattr(ChannelRepository, 'get_tv_matching_inventory', lambda self: ([None] * 1500, [None] * 1500))
    response = client.post('/api/v1/tv-channels/automatch/preview')
    assert response.status_code == 422
    assert 'too large' in response.json()['detail']


@pytest.mark.parametrize('target,stream', [
    ('M+ LaLiga', 'M+ LaLiga TV'),
    ('M+ Deportes', 'M+ Deporte'),
    ('National Geographic', 'National Geographic Wild'),
    ('ESPN', 'ESPN [US]'),
    ('UK | Sky Sport Arena', 'Sky Sports Arena'),
    ('DAZN 1', 'PT | DAZN 1'),
])
def test_rejects_broad_name_and_edition_guesses(target, stream):
    assert name_score(normalize_name(target), normalize_name(stream)) is None


@pytest.mark.parametrize('target,stream', [
    ('DAZN LaLiga', 'DAZN LA LIGA 1 FHD --> ELCANO'),
    ('LaLiga TV Hypermotion 2', 'HYPERMOTION 2 --> ELCANO'),
    ('M+ Liga de Campeones 2', 'LIGA DE CAMPEONES 2 FHD --> ELCANO'),
])
def test_inferred_aliases_are_discarded(target, stream):
    result = name_score(normalize_name(target), normalize_name(stream))
    assert result is None


def test_unknown_edition_is_ambiguous_and_epg_conflicts_need_review(client, db_session):
    from app.models.models import AcestreamChannel, TVChannel
    spanish = TVChannel(name='DAZN 1', epg_id='dazn-es')
    portuguese = TVChannel(name='PT | DAZN 1', epg_id='dazn-pt')
    db_session.add_all([spanish, portuguese]); db_session.flush()
    streams = [
        AcestreamChannel(id='e'*40, name='DAZN 1 HD'),
        AcestreamChannel(id='f'*40, name='DAZN 1 HD', tvg_id='dazn-es'),
        AcestreamChannel(id='g'*40, name='DAZN 2 HD', tvg_id='dazn-es'),
        AcestreamChannel(id='h'*40, name='DAZN 1 HD', tvg_name='DAZN 2 HD', tvg_id='dazn-es'),
    ]
    db_session.add_all(streams); db_session.commit()
    data = client.post('/api/v1/tv-channels/automatch/preview').json()
    assert data['ambiguous_streams'] == 1
    matches = {item['acestream_channel_id']: item for item in data['candidates']}
    assert 'e'*40 not in matches
    assert matches['f'*40]['recommended'] is True
    assert 'g'*40 not in matches
    assert 'h'*40 not in matches
    request = {'assignments': [{'acestream_channel_id': 'e'*40, 'tv_channel_id': spanish.id}]}
    assert client.post('/api/v1/tv-channels/automatch/apply', json=request).json()['skipped_count'] == 1



def test_alias_in_one_stream_name_does_not_become_exact_via_another(client, db_session):
    from app.models.models import AcestreamChannel, TVChannel
    db_session.add(TVChannel(name='DAZN LaLiga'))
    db_session.add(AcestreamChannel(id='i'*40, name='DAZN LaLiga 1', tvg_name='DAZN LaLiga'))
    db_session.commit()
    matches = client.post('/api/v1/tv-channels/automatch/preview').json()['candidates']
    assert matches == []



@pytest.mark.parametrize('brand,variants', [
    ('DAZN', ['DAZN', 'DAZN 1', 'DAZN 2', 'DAZN 3', 'DAZN 4', 'DAZN F1', 'DAZN Liga', 'DAZN LaLiga']),
    ('Movistar', ['Movistar', 'Movistar Acción', 'Movistar Peliculas', 'Movistar Comedia']),
])
def test_brand_only_is_not_a_station(brand, variants):
    for variant in variants:
        assert name_score(normalize_name(brand), normalize_name(variant)) is None


def test_dazn_and_movistar_station_matrix(client, db_session):
    from app.models.models import AcestreamChannel, TVChannel
    names = ['DAZN 1', 'DAZN 2', 'DAZN 3', 'DAZN 4', 'DAZN LaLiga', 'DAZN F1',
             'M+ Acción', 'M+ Peliculas', 'M+ Comedia']
    targets = [TVChannel(name=name) for name in names]
    db_session.add_all(targets); db_session.flush()
    streams = []
    for index, target in enumerate(targets):
        stream_name = target.name.replace('M+', 'Movistar')
        for backup in range(2):
            streams.append(AcestreamChannel(id=f'{index:038d}{backup:02d}', name=f'{stream_name} HD --> Provider'))
    streams.append(AcestreamChannel(id='z'*40, name='DAZN Liga'))
    db_session.add_all(streams); db_session.commit()
    result = client.post('/api/v1/tv-channels/automatch/preview').json()
    assert len(result['candidates']) == 18
    assert result['unmatched_streams'] == 1
    for match in result['candidates']:
        expected_target = targets[int(match['acestream_channel_id'][:38])]
        assert match['tv_channel_id'] == expected_target.id
    request = {'assignments': [{'acestream_channel_id': streams[0].id, 'tv_channel_id': targets[-1].id}]}
    assert client.post('/api/v1/tv-channels/automatch/apply', json=request).json()['skipped_count'] == 1


def test_complete_reviewed_catalog_matches_independent_expectations(client, db_session):
    import json
    from pathlib import Path
    from collections import Counter
    from app.models.models import AcestreamChannel, TVChannel
    fixture = json.loads((Path(__file__).parent / 'fixtures/tv_matching_reviewed_catalog.json').read_text())
    targets = [TVChannel(name=name) for name in fixture['tv_names']]
    db_session.add_all(targets); db_session.flush()
    by_name = {tv.name: tv.id for tv in targets}
    expected = {}
    for group_index, group in enumerate(fixture['stream_groups']):
        for copy in range(group['copies']):
            stream_id = f'{group_index:036d}{copy:04d}'
            db_session.add(AcestreamChannel(id=stream_id, name=group['name'] + ' --> Test provider'))
            expected[stream_id] = by_name.get(group['expected_tv_name'])
    db_session.commit()
    result = client.post('/api/v1/tv-channels/automatch/preview').json()
    actual = {item['acestream_channel_id']: item['tv_channel_id'] for item in result['candidates']}
    assert len(expected) == 393
    assert len(actual) == 125
    assert len(Counter(actual.values())) == 38
    assert all(actual.get(stream_id) == destination for stream_id, destination in expected.items())
    # Reverse insertion order must not resolve ambiguous editions differently.
    from app.services.tv_matching_service import TVMatchingService
    from app.repositories.channel_repository import ChannelRepository
    from unittest.mock import patch
    inventory = ChannelRepository(db_session).get_tv_matching_inventory()
    with patch.object(ChannelRepository, 'get_tv_matching_inventory', return_value=(list(reversed(inventory[0])), list(reversed(inventory[1])))):
        reversed_result = TVMatchingService(db_session).preview()
    assert {item.acestream_channel_id: item.tv_channel_id for item in reversed_result.candidates} == actual


def test_conflicting_country_markers_are_discarded():
    assert name_score(normalize_name('FR | Sports', 'UK'), normalize_name('UK | Sports')) is None
    assert name_score(normalize_name('UK | Sports'), normalize_name('Sports (UK) [FR]')) is None


def test_every_reviewed_tv_station_stays_separate_from_every_other():
    import json
    from pathlib import Path
    names = json.loads((Path(__file__).parent / 'fixtures/tv_matching_reviewed_catalog.json').read_text())['tv_names']
    for target in names:
        for candidate in names:
            if target != candidate:
                assert name_score(normalize_name(target), normalize_name(candidate)) is None, (target, candidate)
        for suffix in (' BAR', ' Kids', ' Extra', ' 99', ' TV'):
            assert name_score(normalize_name(target), normalize_name(target + suffix)) is None
