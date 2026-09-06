"""Conservative matching for existing TV channels; analysis never writes data."""
import re
import unicodedata
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories.channel_repository import ChannelRepository
from app.schemas.tv_matching import TVMatchApplyRequest, TVMatchCandidate, TVMatchPreview

QUALITY = re.compile(r'\b(?:[fus]?hdp?|sd[p]?|uhd|4k|8k|1080[pi]?|720[pi]?|576[pi]?|480[pi]?)\b')
COUNTRIES = 'es|en|fr|de|it|pt|ru|nl|uk|us|pl|tr|be|ar'
REGION = re.compile(rf'^({COUNTRIES})\s*[|:]\s*|[\[(]({COUNTRIES})[\])]|\b(spain)\s*$', re.I)


@dataclass(frozen=True)
class ChannelName:
    text: str
    country: str
    country_conflict: bool = False


def normalize_name(value: str | None, country: str | None = None) -> ChannelName:
    value = (value or '').casefold().split('-->', 1)[0]
    value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))
    regions = [next(v for v in match if v) for match in REGION.findall(value)]
    country_values = [part.strip().casefold() for part in [country, *regions] if part and part.strip()]
    country_values = [{'spain': 'es', 'gb': 'uk'}.get(part, part) for part in country_values]
    region = country_values[0] if country_values else ''
    value = REGION.sub(' ', value)
    value = QUALITY.sub(' ', value)
    value = re.sub(r'^m\s*[+.](?=\s|\w)', 'movistar ', value)
    value = value.replace('+', ' plus ')
    value = re.sub(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)', ' ', value)
    value = ' '.join(re.sub(r'[^\w\s]', ' ', value).split())
    value = re.sub(r'\bla liga\b', 'laliga', value)
    value = re.sub(r'^sky sports\b', 'sky sport', value)
    value = re.sub(r'^movistar plus plus\b', 'movistar plus', value)
    return ChannelName(value, region, len(set(country_values)) > 1)


def name_score(target: ChannelName, candidate: ChannelName) -> tuple[float, str] | None:
    if not target.text or not candidate.text or target.text in {'dazn', 'movistar'}:
        return None
    # A country present on only one side is insufficient evidence of an edition.
    if target.country_conflict or candidate.country_conflict or target.country != candidate.country:
        return None
    if target.text == candidate.text:
        return 0.99, 'Normalized name'
    # Similarity percentages are not evidence that two feeds are the same station.
    # Keep all other spellings and added/dropped words in the manual assign flow.
    return None


class TVMatchingService:
    def __init__(self, db: Session):
        self.repository = ChannelRepository(db)

    def preview(self) -> TVMatchPreview:
        targets, streams = self.repository.get_tv_matching_inventory()
        if len(targets) * len(streams) > 2_000_000:
            raise ValueError('Channel inventory is too large for automatch (maximum 2 million comparisons).')
        names = {tv.id: normalize_name(tv.name, tv.country) for tv in targets}
        candidates = []
        ambiguous = unmatched = 0
        for stream in streams:
            variants = [normalize_name(name) for name in (stream.name, stream.tvg_name) if name]
            claims = []
            id_targets = {tv.id for tv in targets if stream.tvg_id and tv.epg_id == stream.tvg_id}
            # Missing region cannot choose between editions with the same name.
            edition_conflict = any(
                not variant.country and len({names[tv.id].country for tv in targets
                    if names[tv.id].text == variant.text}) > 1
                for variant in variants
            )
            for tv in targets:
                if id_targets and tv.id not in id_targets:
                    continue
                # Every supplied name must identify this exact station. EPG IDs
                # constrain identity but cannot rescue conflicting/missing names.
                scores = [name_score(names[tv.id], variant) for variant in variants]
                if not scores or any(result is None for result in scores):
                    continue
                if tv.epg_id and stream.tvg_id:
                    if stream.tvg_id != tv.epg_id:
                        continue
                    score, reason = 1.0, 'Exact EPG ID and normalized name'
                else:
                    score, reason = 0.99, 'Exact normalized name'
                claims.append(TVMatchCandidate(
                    acestream_channel_id=stream.id, acestream_name=stream.name or stream.tvg_name or stream.id,
                    tv_channel_id=tv.id, tv_channel_name=tv.name, score=score, reason=reason,
                    recommended=score >= 0.99,
                ))
            claims.sort(key=lambda item: (-item.score, item.tv_channel_id))
            if edition_conflict and not id_targets:
                ambiguous += 1
            elif not claims:
                unmatched += 1
            elif len(claims) > 1:
                ambiguous += 1
            else:
                candidates.append(claims[0])
        candidates.sort(key=lambda item: (item.tv_channel_name.casefold(), item.acestream_name.casefold(), item.acestream_channel_id))
        return TVMatchPreview(tv_channels=len(targets), unassigned_streams=len(streams),
                              ambiguous_streams=ambiguous, unmatched_streams=unmatched, candidates=candidates)

    def apply(self, request: TVMatchApplyRequest) -> dict[str, int]:
        selected = {(item.acestream_channel_id, item.tv_channel_id) for item in request.assignments}
        if len({item[0] for item in selected}) != len(selected):
            raise ValueError('A stream can only be assigned to one TV channel.')
        # Recompute against current metadata, including all competing TV channels.
        accepted = {(item.acestream_channel_id, item.tv_channel_id) for item in self.preview().candidates}
        return self.repository.apply_tv_matches(selected, accepted)
