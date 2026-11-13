"""Edge paths of saved settings, the setup wizard's address display and the favourites guide."""
import pytest

from app.repositories.settings_repository import SettingsRepository
from app.services.setup_service import visible_endpoint


class BrokenSession:
    """A session whose database is unavailable (locked, or mid-recovery)."""

    def query(self, *args, **kwargs):
        raise RuntimeError('database is locked')


def test_a_setting_that_cannot_be_read_falls_back_to_its_default():
    repo = SettingsRepository(BrokenSession())
    assert repo.get_setting(SettingsRepository.ACESTREAM_CHECK_TIMEOUT) == SettingsRepository.DEFAULT_ACESTREAM_CHECK_TIMEOUT
    assert repo.get_setting('unknown_key', 'fallback') == 'fallback'


def test_listing_settings_while_the_database_is_unavailable_returns_nothing():
    assert SettingsRepository(BrokenSession()).get_all_settings() == {}


@pytest.mark.parametrize('saved, shown', [
    ('http://user:secret@engine.lan:6878/path?token=abc', 'http://engine.lan:6878/path'),
    ('http://[fd00::10]:6878/ace?pid=1', 'http://[fd00::10]:6878/ace'),
    ('http://[fd00::10]/', 'http://[fd00::10]/'),
    ('not an address', ''),
    ('http://[fd00::10', 'Invalid saved address; review Settings'),
])
def test_saved_addresses_are_shown_without_credentials_or_query(saved, shown):
    # An IPv6 host keeps its brackets, or the port would read as part of it.
    assert visible_endpoint(saved) == shown


def test_favourites_only_guide_leaves_out_other_channels(db_session):
    from app.models.models import EPGSource, TVChannel
    from app.services.epg_service import EPGService
    source = EPGSource(name='Guide', url='https://example.org/guide.xml')
    db_session.add(source)
    db_session.commit()
    service = EPGService(db_session)
    service._process_epg_xml(source.id, b'''<tv>
      <channel id="one.es"><display-name>One</display-name></channel>
      <channel id="two.es"><display-name>Two</display-name></channel>
      <channel id="three.es"><display-name>Three</display-name></channel></tv>''')
    db_session.add_all([
        TVChannel(name='One', epg_id='one.es', epg_source_id=source.id, is_favorite=True),
        TVChannel(name='Two', epg_id='two.es', epg_source_id=source.id, is_favorite=False),
        # Never marked either way: not a favourite.
        TVChannel(name='Three', epg_id='three.es', epg_source_id=source.id, is_favorite=None),
    ])
    db_session.commit()

    everything = service.generate_epg_xml()
    favourites = service.generate_epg_xml(favorites_only=True)

    assert all(name in everything for name in ('One', 'Two', 'Three'))
    assert 'One' in favourites
    assert 'Two' not in favourites and 'Three' not in favourites
