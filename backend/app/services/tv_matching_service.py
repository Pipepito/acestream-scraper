"""Conservative matching for existing TV channels; analysis never writes data."""
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

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
    numbers: tuple[str, ...]


def normalize_name(value: str | None, country: str | None = None) -> ChannelName:
    value = (value or '').casefold().split('-->', 1)[0]
    value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))
    regions = [next(v for v in match if v) for match in REGION.findall(value)]
    region = (country or (regions[0] if regions else '')).casefold()
    region = {'spain': 'es', 'gb': 'uk'}.get(region, region)
    value = REGION.sub(' ', value)
    value = QUALITY.sub(' ', value)
    value = re.sub(r'^m\s*[+.](?=\s|\w)', 'movistar ', value)
    value = value.replace('+', ' plus ')
    value = re.sub(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)', ' ', value)
    value = ' '.join(re.sub(r'[^\w\s]', ' ', value).split())
    value = re.sub(r'\bla liga\b', 'laliga', value)
    value = re.sub(r'^sky sports\b', 'sky sport', value)
    value = re.sub(r'^movistar plus plus\b', 'movistar plus', value)
    # Narrow catalog aliases, never generic substring removal.
    value = re.sub(r'^(?:movistar )?liga de campeones\b', 'movistar liga de campeones', value)
    value = re.sub(r'^(?:laliga tv )?hypermotion\b', 'laliga tv hypermotion', value)
    value = re.sub(r'^dazn laliga 1$', 'dazn laliga', value)
    return ChannelName(value, region, tuple(re.findall(r'\d+', value)))


def name_score(target: ChannelName, candidate: ChannelName) -> tuple[float, str] | None:
    if not target.text or not candidate.text or target.numbers != candidate.numbers:
        return None
    if target.country and candidate.country and target.country != candidate.country:
        return None
    # These modifiers identify different feeds even when the rest is very similar.
    for token in ('bar', 'plus', 'hdr', 'extra', 'xtra'):
        if (token in target.text.split()) != (token in candidate.text.split()):
            return None
    region_unknown = target.country != candidate.country
    if target.text == candidate.text:
        return (0.94, 'Normalized name; country needs review') if region_unknown else (0.99, 'Normalized name')
    if min(len(target.text), len(candidate.text)) < 7:
        return None
    ratio = SequenceMatcher(None, target.text, candidate.text).ratio()
    if ratio >= 0.90:
        return min(ratio, 0.93), 'Similar name; review required'
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
            for tv in targets:
                if tv.epg_id and stream.tvg_id == tv.epg_id:
                    score, reason = 1.0, 'Exact EPG ID'
                else:
                    # Conflicting explicit EPG IDs must not be overridden by a name guess.
                    if tv.epg_id and stream.tvg_id:
                        continue
                    scores = [result for name in variants if (result := name_score(names[tv.id], name))]
                    if not scores:
                        continue
                    score, reason = max(scores)
                claims.append(TVMatchCandidate(
                    acestream_channel_id=stream.id, acestream_name=stream.name or stream.tvg_name or stream.id,
                    tv_channel_id=tv.id, tv_channel_name=tv.name, score=score, reason=reason,
                    recommended=score >= 0.99,
                ))
            claims.sort(key=lambda item: (-item.score, item.tv_channel_id))
            if not claims:
                unmatched += 1
            elif len(claims) > 1 and (claims[0].score == claims[1].score or
                    (claims[0].score < 0.99 and claims[0].score - claims[1].score < 0.05)):
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
