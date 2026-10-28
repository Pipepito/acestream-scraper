"""Conservative, read-only programme associations; never replace source metadata."""
from datetime import datetime, time, timedelta, timezone
import re
import unicodedata
from zoneinfo import ZoneInfo

from app.schemas.events import EventProgramMatch, EventChannelTarget


def words(value):
    folded = ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))
    return ' '.join(re.findall(r'\w+', folded))


class EventEPGService:
    def __init__(self, repo):
        self.repo = repo
        self.windows = {}

    def match(self, fields):
        teams = [words(team) for team in fields.get('participants', [])]
        if len(teams) != 2 or teams[0] == teams[1] or any(len(team) < 3 for team in teams):
            return []
        start = fields.get('starts_at')
        day = fields.get('scheduled_date')
        if start:
            start = datetime.fromisoformat(start.replace('Z', '+00:00'))
            lower, upper = start - timedelta(minutes=30), start + timedelta(minutes=30)
        elif day:
            zone = ZoneInfo(fields['timezone'])
            local = datetime.combine(datetime.fromisoformat(day).date(), time(), zone)
            lower, upper = local.astimezone(timezone.utc), (local + timedelta(days=1)).astimezone(timezone.utc)
        else:
            return []
        key = (lower, upper)
        if key not in self.windows:
            if len(self.windows) >= 8:
                self.windows.pop(next(iter(self.windows)))
            self.windows[key] = self.repo.program_candidates(lower, upper)
        candidates = self.windows[key]
        if len(candidates) > 5000:
            return []  # Never claim uniqueness using a truncated inventory.
        matches = []
        for row in candidates:
            title = words(row['title'] + ' ' + (row['subtitle'] or ''))
            if re.search(r'\b(replay|repeticion|resumen|highlights|previa)\b', title):
                continue
            if all(' ' + team + ' ' in ' ' + title + ' ' for team in teams):
                matches.append(row)
        if not matches or len(matches) > 50:
            return []
        # Simulcasts are useful; repeated fixtures or multiple programmes on one
        # guide channel are ambiguous, especially when kickoff was not supplied.
        if len({r['epg_channel_id'] for r in matches}) != len(matches):
            return []
        if max(r['start_time'] for r in matches) - min(r['start_time'] for r in matches) > timedelta(minutes=30):
            return []
        result = []
        for row in matches:
            tv = self.repo.program_tv_targets(row['epg_source_id'], row['channel_xml_id'])
            result.append(EventProgramMatch(program_id=row['id'], title=row['title'], starts_at=row['start_time'],
                ends_at=row['end_time'], epg_channel=EventChannelTarget(kind='epg', id=row['epg_channel_id'],
                    name=row['channel_name'], source_name=row['source_name']),
                tv_channel=EventChannelTarget(kind='tv', id=tv[0]['id'], name=tv[0]['name'], country=tv[0]['country'] or '') if len(tv) == 1 else None))
        return result
