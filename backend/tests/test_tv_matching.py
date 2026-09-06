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
    assert data['candidates'][0]['reason'] == 'Exact EPG ID'
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
    assert len(data['candidates']) == 1
    assert data['candidates'][0]['recommended'] is False
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
def test_inferred_aliases_are_never_strong_matches(target, stream):
    result = name_score(normalize_name(target), normalize_name(stream))
    assert result == (0.96, 'Catalog alias; review required')


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
    assert matches['g'*40]['recommended'] is False
    assert matches['h'*40]['recommended'] is False
    request = {'assignments': [{'acestream_channel_id': 'e'*40, 'tv_channel_id': spanish.id}]}
    assert client.post('/api/v1/tv-channels/automatch/apply', json=request).json()['skipped_count'] == 1



def test_alias_in_one_stream_name_does_not_become_exact_via_another(client, db_session):
    from app.models.models import AcestreamChannel, TVChannel
    db_session.add(TVChannel(name='DAZN LaLiga'))
    db_session.add(AcestreamChannel(id='i'*40, name='DAZN LaLiga 1', tvg_name='DAZN LaLiga'))
    db_session.commit()
    matches = client.post('/api/v1/tv-channels/automatch/preview').json()['candidates']
    assert len(matches) == 1
    assert matches[0]['recommended'] is False
