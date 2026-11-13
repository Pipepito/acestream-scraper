"""Telegram names from pasted M3U lines, and new streams joining their TV channel."""
from app.repositories import telegram_repository as repo
from app.schemas.telegram import TelegramSourceConfig
from app.services.telegram import ingestion
from app.services.telegram.extraction import Message, m3u_label, preview_message

A, B, C, D, E, F, G, H, J = (str(n) * 40 for n in range(1, 10))


def config(**kwargs):
    return TelegramSourceConfig(name='Example', chat_id='-100123', **kwargs)


def test_m3u_labels_give_the_display_name_and_metadata():
    assert m3u_label('#EXTINF:-1 tvg-id="example.one" tvg-logo="https://example.com/one.png" '
                     'group-title="Sports, live",Example One HD') == (
        'Example One HD', {'tvg-id': 'example.one', 'tvg-logo': 'https://example.com/one.png',
                           'group-title': 'Sports, live'})
    assert m3u_label('TVG-NAME="Example Two"') == ('Example Two', {'tvg-name': 'Example Two'})
    assert m3u_label('#EXTINF:-1 tvg-name="Example Three",') == ('Example Three', {'tvg-name': 'Example Three'})
    assert m3u_label('Example, with a comma') == ('Example, with a comma', {})


def test_default_extraction_cleans_pasted_m3u_lines():
    text = (f'#EXTINF:-1 tvg-id="example.one" group-title="Sports",Example One\nacestream://{A}\n\n'
            f'tvg-name="Example Two"\n{B}\n\nExample Three\n{C}')
    outcome, result = preview_message(config(), Message(1, text))
    assert outcome == 'matched'
    assert [(c.name, c.channel_id) for c in result.channels] == [
        ('Example One', A), ('Example Two', B), ('Example Three', C)]
    assert result.channels[0].metadata['tvg_id'] == 'example.one'
    assert result.channels[0].metadata['group_title'] == 'Sports'


def test_new_streams_join_the_only_tv_channel_with_that_name(alembic_backend_runtime):
    from app.models.models import AcestreamChannel, TVChannel
    with alembic_backend_runtime.SessionLocal() as db:
        one = TVChannel(name='Example One', is_active=True)
        twin_a = TVChannel(name='Example Twin', is_active=True)
        twin_b = TVChannel(name='Example Twin HD', is_active=True)
        db.add_all([TVChannel(name='Example Region', is_active=True),
                    TVChannel(name='PT | Example Region', is_active=True)])
        guided = TVChannel(name='Example Guided', is_active=True, epg_id='guided.example')
        db.add_all([one, twin_a, twin_b, guided, TVChannel(name='Example Off', is_active=False)])
        db.add(AcestreamChannel(id=E, name='Example One'))
        db.commit()
        one_id = one.id
        region_id = db.query(TVChannel.id).filter_by(name='Example Region').scalar()
    text = (f'#EXTINF:-1,Example One 1080p\n{A}\n\nExample Twin\n{B}\n\nExample Off\n{C}\n\n'
            f'#EXTINF:-1 tvg-id="other.example",Example Guided\n{D}\n\nExample One\n{E}\n\ntvg-name="Example Region 720p"\n{F}')
    source = repo.save_source('account', config(), 'Example chat', {}, 0)
    _, generation = repo.snapshot(source.id, 'account')
    result = preview_message(config(), Message(1, text))[1]
    assert ingestion.record(source.id, 'account', generation, 1, 'one', result, True)
    with alembic_backend_runtime.SessionLocal() as db:
        owners = {cid: db.get(AcestreamChannel, cid).tv_channel_id for cid in (A, B, C, D, E, F)}
    assert owners[A] == one_id      # same name once normalized
    assert owners[B] is None        # two TV channels qualify: ambiguous
    assert owners[C] is None        # only an inactive TV channel
    assert owners[D] is None        # the tvg-id names another guide channel
    assert owners[E] is None        # existed before this message: left alone
    assert owners[F] == region_id   # a country on one side only is another edition
    with alembic_backend_runtime.SessionLocal() as db:
        assert db.query(TVChannel).count() == 7


def test_film_entries_never_join_a_channel_of_the_same_title(alembic_backend_runtime):
    """Chats also post films as «Title (year) quality [rating]»; a title that
    happens to be a channel name must stay a loose stream."""
    from app.models.models import AcestreamChannel, TVChannel
    with alembic_backend_runtime.SessionLocal() as db:
        db.add_all([TVChannel(name=name, is_active=True) for name in ('Example', 'Example Plus', 'Example Two')])
        db.commit()
    text = (f'Example (2008) 1080p [6.1]\n{G}\n\nExample Plus (2015) 720p [7.4]\n{H}\n\n'
            f'#EXTINF:-1,Example Two (2020) 4K [5.9]\n{J}')
    source = repo.save_source('account', config(), 'Example chat', {}, 0)
    _, generation = repo.snapshot(source.id, 'account')
    result = preview_message(config(), Message(1, text))[1]
    assert [c.channel_id for c in result.channels] == [G, H, J]
    assert ingestion.record(source.id, 'account', generation, 1, 'one', result, True)
    with alembic_backend_runtime.SessionLocal() as db:
        assert [db.get(AcestreamChannel, cid).tv_channel_id for cid in (G, H, J)] == [None, None, None]
