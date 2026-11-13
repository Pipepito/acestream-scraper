"""The stream check timeout, settable through the API like the check interval.

It existed only as a database row (acestream_check_timeout, default 10 s).
The box starts some acestreams cold in 15-20 s: checked with 10 s they were
marked offline and the relay hardly tried them.
"""
from app.services.channel_status_service import ChannelStatusService


def test_POR_DEFECTO_10(client):
    assert client.get('/api/v1/config/acestream_check_timeout').json()['value'] == '10'


def test_SE_CAMBIA_Y_EL_CHEQUEO_LO_USA(client, db_session):
    response = client.put('/api/v1/config/acestream_check_timeout', json={'value': '30'})
    assert response.status_code == 200
    assert client.get('/api/v1/config/acestream_check_timeout').json()['value'] == '30'
    assert ChannelStatusService(db_session)._get_timeout() == 30.0


def test_FUERA_DE_RANGO_SE_RECHAZA(client):
    for bad in ('4', '121', 'treinta', ''):
        assert client.put('/api/v1/config/acestream_check_timeout', json={'value': bad}).status_code == 422
    assert client.get('/api/v1/config/acestream_check_timeout').json()['value'] == '10'


def test_UN_VALOR_GUARDADO_QUE_NO_ES_UN_NUMERO_VUELVE_A_10(db_session):
    # The row could be edited by hand before the setting had a form.
    from app.repositories.settings_repository import SettingsRepository
    from app.services.config_service import ConfigService
    repo = SettingsRepository(db_session)
    repo.set_setting(SettingsRepository.ACESTREAM_CHECK_TIMEOUT, 'treinta', 'by hand')
    assert ConfigService(repo).get_acestream_check_timeout() == 10
    repo.set_setting(SettingsRepository.ACESTREAM_CHECK_TIMEOUT, '900', 'by hand')
    assert ConfigService(repo).get_acestream_check_timeout() == 10
    repo.set_setting(SettingsRepository.ACESTREAM_CHECK_TIMEOUT, '45.0', 'by hand')
    assert ConfigService(repo).get_acestream_check_timeout() == 45


def test_SI_NO_SE_PUEDE_GUARDAR_SE_DICE(client, monkeypatch):
    from app.services.config_service import ConfigService
    monkeypatch.setattr(ConfigService, 'set_acestream_check_timeout', lambda self, seconds: False)
    response = client.put('/api/v1/config/acestream_check_timeout', json={'value': '30'})
    assert response.status_code == 500
    assert client.get('/api/v1/config/acestream_check_timeout').json()['value'] == '10'
