"""Repair unavailable EPG links without replacing the curated TV inventory."""
from collections import defaultdict
from functools import cached_property

from sqlalchemy.orm import Session

from app.models.models import EPGChannel, TVChannel
from app.repositories.epg_link_repository import EPGLinkRepository
from app.services.tv_matching_service import normalize_name


class EPGLinkService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EPGLinkRepository(db)

    @cached_property
    def channels(self) -> list[EPGChannel]:
        return self.repository.enabled_channels()

    @cached_property
    def links(self) -> set[tuple[int, str]]:
        return {(ch.epg_source_id, ch.channel_xml_id) for ch in self.channels}

    @cached_property
    def by_id(self) -> dict[str, list[EPGChannel]]:
        index = defaultdict(list)
        for ch in self.channels:
            index[ch.channel_xml_id].append(ch)
        return index

    @cached_property
    def by_name(self) -> dict[str, list[EPGChannel]]:
        index = defaultdict(list)
        for ch in self.channels:
            index[normalize_name(ch.name).text].append(ch)
        return index

    def available(self, tv: TVChannel) -> bool:
        return (tv.epg_source_id, tv.epg_id) in self.links

    def repair(self) -> int:
        repaired = 0
        for tv in self.repository.unlinked_tv_channels():
            candidates = self.by_id.get(tv.epg_id, [])
            if not candidates:
                name = normalize_name(tv.name, tv.country)
                if not name.text:
                    continue
                candidates = [ch for ch in self.by_name.get(name.text, [])
                              if not name.country_conflict and
                              (not normalize_name(ch.name).country or
                               normalize_name(ch.name).country == name.country)]
                # Different XML IDs with the same display name are ambiguous.
                if len({ch.channel_xml_id for ch in candidates}) > 1:
                    continue
            if candidates:
                tv.epg_id = candidates[0].channel_xml_id
                tv.epg_source_id = candidates[0].epg_source_id
                repaired += 1
        self.db.flush()
        return repaired

    def existing(self, channel: EPGChannel) -> list[TVChannel]:
        targets = self.repository.tv_channels()
        exact = [tv for tv in targets if tv.epg_id == channel.channel_xml_id]
        if exact:
            return exact
        name = normalize_name(channel.name)
        if not name.text or name.country_conflict:
            return []
        return [tv for tv in targets if normalize_name(tv.name, tv.country).text == name.text
                and (not name.country or normalize_name(tv.name, tv.country).country == name.country)]
