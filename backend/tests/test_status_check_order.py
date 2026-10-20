"""The status pass checks first what was never checked.

It used to walk the table in insertion order and restart from row 1 on every
start. A box switched on for an hour or two never finished a pass (about 3 h
for 1,000 sources): it kept checking the same first rows and never reached
the last ones. On a real box 58% were checked and the tail never was.
"""
from datetime import datetime, timedelta, timezone

from app.models.models import AcestreamChannel, TVChannel
from app.tasks.channel_status_task import channels_in_check_order as ordered_ids

T0 = datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)


def channels_in_check_order(db, *, now=T0):
    return ordered_ids(db, now=now)


def _stream(db, cid, last_checked=None, tv=None, active=True):
    db.add(AcestreamChannel(id=cid, name=cid, is_active=active,
                            last_checked=last_checked,
                            tv_channel_id=tv.id if tv else None))


def _tv(db, name, favourite):
    t = TVChannel(name=name, is_favorite=favourite)
    db.add(t)
    db.flush()
    return t


def test_never_checked_goes_first_even_when_inserted_last(db_session):
    """The case seen on a box: the last rows added were never checked."""
    _stream(db_session, "old", T0 - timedelta(days=1))
    _stream(db_session, "recent", T0)
    _stream(db_session, "never")                      # inserted last
    db_session.commit()
    assert channels_in_check_order(db_session)[0] == "never"


def test_then_favourites(db_session):
    fav = _tv(db_session, "M+ Liga de Campeones", True)
    other = _tv(db_session, "Other", False)
    _stream(db_session, "of_other", T0 - timedelta(minutes=5), tv=other)
    _stream(db_session, "of_favourite", T0, tv=fav)
    db_session.commit()
    assert channels_in_check_order(db_session) == ["of_favourite", "of_other"]


def test_never_checked_beats_even_a_favourite(db_session):
    """The tail that was never reached goes before everything.

    Without this case the "never checked" tier could not be told apart:
    SQLite already sorts NULL first in ASC, and only against a favourite
    that WAS checked does it show whether the tier is there.
    """
    fav = _tv(db_session, "Favourite", True)
    _stream(db_session, "checked_favourite", T0, tv=fav)
    _stream(db_session, "never_not_favourite")
    db_session.commit()
    assert channels_in_check_order(db_session) == [
        "never_not_favourite", "checked_favourite"]


def test_then_least_recently_checked(db_session):
    _stream(db_session, "yesterday", T0 - timedelta(days=1))
    _stream(db_session, "today", T0)
    _stream(db_session, "two_days_ago", T0 - timedelta(days=2))
    db_session.commit()
    assert channels_in_check_order(db_session) == ["two_days_ago", "yesterday", "today"]


def test_a_cut_pass_resumes_by_itself(db_session):
    """What was just checked moves to the end: a restart does not repeat it."""
    for i in range(4):
        _stream(db_session, f"s{i}")
    db_session.commit()
    first = channels_in_check_order(db_session)
    # switched off after checking the first two
    for cid in first[:2]:
        db_session.get(AcestreamChannel, cid).last_checked = T0
    db_session.commit()
    second = channels_in_check_order(db_session)
    assert second[:2] == first[2:], (first, second)


def test_inactive_streams_stay_out(db_session):
    """Guard: what was already filtered stays filtered."""
    _stream(db_session, "active")
    _stream(db_session, "inactive", active=False)
    db_session.commit()
    assert channels_in_check_order(db_session) == ["active"]


def test_streams_of_a_tv_channel_before_loose_ones(db_session):
    """With no favourites (one box had 0), the 613 streams of TV channels were
    mixed with 935 loose ones that the relay playlist cannot open."""
    other = _tv(db_session, "La 1", False)
    _stream(db_session, "old_loose", T0 - timedelta(minutes=5))
    _stream(db_session, "recent_of_channel", T0, tv=other)
    db_session.commit()
    assert channels_in_check_order(db_session) == ["recent_of_channel", "old_loose"]


def test_a_favourite_still_goes_before_another_channel(db_session):
    fav = _tv(db_session, "Favourite", True)
    other = _tv(db_session, "Other", False)
    _stream(db_session, "old_of_other", T0 - timedelta(minutes=5), tv=other)
    _stream(db_session, "recent_of_favourite", T0, tv=fav)
    db_session.commit()
    assert channels_in_check_order(db_session) == ["recent_of_favourite", "old_of_other"]


def test_repeated_short_passes_reach_old_loose_streams(db_session):
    """An hourly restart cannot repeatedly check favorites and starve the tail."""
    favorite = _tv(db_session, "Favorite", True)
    for number in range(3):
        _stream(db_session, f"favorite-{number}", T0 - timedelta(hours=2), tv=favorite)
    for number in range(3):
        _stream(db_session, f"loose-{number}", T0 - timedelta(hours=2))
    db_session.commit()
    seen = set()
    for run in range(6):
        now = T0 + timedelta(hours=run)
        selected = channels_in_check_order(db_session, now=now)[0]
        seen.add(selected)
        db_session.get(AcestreamChannel, selected).last_checked = now
        db_session.commit()
    assert seen == {f"{kind}-{n}" for kind in ("favorite", "loose") for n in range(3)}


def test_older_age_group_precedes_favorite_and_uses_saved_interval(db_session):
    from app.services.config_service import ConfigService
    from app.repositories.settings_repository import SettingsRepository
    favorite = _tv(db_session, "Favorite", True)
    _stream(db_session, "favorite", T0, tv=favorite)
    _stream(db_session, "overdue", T0 - timedelta(minutes=90))
    db_session.commit()
    assert channels_in_check_order(db_session) == ["overdue", "favorite"]
    ConfigService(SettingsRepository(db_session)).set_channel_status_interval(120)
    assert channels_in_check_order(db_session) == ["favorite", "overdue"]


def test_age_boundary_and_stable_id_ties(db_session):
    favorite = _tv(db_session, "Favorite", True)
    _stream(db_session, "favorite", T0, tv=favorite)
    _stream(db_session, "b", T0 - timedelta(hours=1))
    _stream(db_session, "a", T0 - timedelta(hours=1))
    db_session.commit()
    assert channels_in_check_order(db_session) == ["a", "b", "favorite"]
