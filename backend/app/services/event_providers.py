"""Built-in schedule adapters. Provider data never supplies playable media.

WOSTI has no fixture IDs: exact published occurrences are reviewable snapshots,
not evidence that similarly named occurrences or rescheduled rows are one event.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import re
import unicodedata
from zoneinfo import ZoneInfo

import aiohttp
from bs4 import BeautifulSoup

from app.schemas.events import EventBroadcast, EventInterestChoices, EventObservation, EventProviderOptions
from app.utils.outbound_http import source_session

FEEDS = {
    'all': 'All sports · short-range guide', 'football': 'Football',
    'automovilismo': 'Motorsport', 'baloncesto': 'Basketball', 'tenis': 'Tennis',
    'motociclismo': 'Motorcycling', 'balonmano': 'Handball', 'beisbol': 'Baseball',
    'boxeo': 'Boxing', 'futbol-americano': 'American football', 'futbol-sala': 'Futsal',
    'ciclismo': 'Cycling', 'golf': 'Golf', 'padel': 'Padel', 'mma': 'MMA',
}
SPORT_NAMES = {
    'Fútbol': 'Football', 'Automovilismo': 'Motorsport', 'Baloncesto': 'Basketball',
    'Tenis': 'Tennis', 'Motociclismo': 'Motorcycling', 'Balonmano': 'Handball',
    'Béisbol': 'Baseball', 'Boxeo': 'Boxing', 'Fútbol Americano': 'American football',
    'Fútbol Sala': 'Futsal', 'Ciclismo': 'Cycling', 'Pádel': 'Padel',
}
LEAGUES = {
    'en.1': ('Premier League', 'Europe/London'), 'en.2': ('Championship', 'Europe/London'),
    'es.1': ('La Liga', 'Europe/Madrid'), 'de.1': ('Bundesliga', 'Europe/Berlin'),
    'fr.1': ('Ligue 1', 'Europe/Paris'), 'it.1': ('Serie A', 'Europe/Rome'),
    'nl.1': ('Eredivisie', 'Europe/Amsterdam'), 'pt.1': ('Primeira Liga', 'Europe/Lisbon'),
}


def folded(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', value.casefold())
                           if not unicodedata.combining(c)).split())


def matches_interests(data, interests):
    """Union of exact sport/competition/team selections; empty means everything."""
    if not any((interests.sports, interests.competitions, interests.teams)):
        return True
    return (folded(data['sport']) in {folded(v) for v in interests.sports}
            or folded(data['competition']) in {folded(v) for v in interests.competitions}
            or bool({folded(v) for v in data['participants']} & {folded(v) for v in interests.teams}))


def digest(parts):
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()


def provider_location(options):
    if options.provider == 'wosti_es':
        if any(feed not in FEEDS for feed in options.feeds):
            raise ValueError('Choose a supported sports feed')
        return 'https://www.futbolenlatv.es/deporte', 'provider:wosti:es', 'Fútbol en la TV · Spain'
    start, end = map(int, options.season.split('-'))
    if (start + 1) % 100 != end:
        raise ValueError('Choose a consecutive season, such as 2026-27')
    return (f'https://raw.githubusercontent.com/openfootball/football.json/master/{options.season}/{options.league}.json',
            f'provider:openfootball:{options.season}:{options.league}',
            f'OpenFootball · {LEAGUES[options.league][0]} · {options.season}')


def parse_openfootball(raw, options, zone):
    _, identity, name = provider_location(options)
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get('matches'), list) or len(data['matches']) > 2000:
        raise ValueError('Unsupported OpenFootball schedule')
    observations = []
    seen = set()
    for match in data['matches']:
        round_name, home, away = (match.get(key) for key in ('round', 'team1', 'team2'))
        if not all(isinstance(value, str) and value.strip() for value in (round_name, home, away)):
            raise ValueError('Fixture needs round and team identities')
        key = digest([options.season, options.league, round_name, home, away])
        if key in seen:
            raise ValueError('Ambiguous fixture identity')
        seen.add(key)
        day = date.fromisoformat(match['date'])
        clock = match.get('time')
        start = f'{day.isoformat()}T{clock}:00' if clock and re.fullmatch(r'\d{2}:\d{2}', clock) else None
        if clock and not start:
            raise ValueError('Unsupported kickoff time')
        observations.append(EventObservation(source_id=identity, source_name=name, source_kind='guide', external_id=key,
            title=f'{home} vs {away}', sport='Football', competition=LEAGUES[options.league][0], participants=[home, away],
            starts_at=start, scheduled_date=day, timezone=zone, state='scheduled',
            time_notes=f'{round_name}. ' + ('Kickoff uses the configured source timezone.' if start else 'Kickoff time not supplied.')))
    return observations


def parse_wosti(raw, *, feed='all'):
    soup = BeautifulSoup(raw, 'html.parser')
    tables = soup.select('table.tablaPrincipal')
    if not tables:
        raise ValueError('Sports guide markup changed')
    observations = []
    for table in tables:
        day = None
        section_competition = ""
        for row in table.select('tr'):
            if 'cabeceraTabla' in row.get('class', []):
                section_competition = ''
                found = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', row.get_text(' ', strip=True))
                day = datetime.strptime(found[1], '%d/%m/%Y').date() if found else None
                continue
            if 'cabeceraCompericion' in row.get('class', []):
                section_competition = row.get_text(' ', strip=True)
                continue
            clock_node = row.select_one('td.hora')
            if not clock_node:
                continue
            competition_node = row.select_one('.detalles .ajusteDoslineas')
            sport_node = row.select_one('.contenedorImgCompeticion > a > img') if feed == 'all' else None
            if feed == 'all' and not sport_node:
                sport_node = row.select_one('.contenedorImgCompeticion > img')
            sport = sport_node.get('alt', '') if sport_node else ('Fútbol' if feed == 'football' else FEEDS[feed])
            sport = SPORT_NAMES.get(sport, sport)
            competition = section_competition or (competition_node.get_text(' ', strip=True) if competition_node else '')
            teams = [node.get_text(' ', strip=True) for node in row.select('td.local > span, td.local > a > span, td.visitante > span, td.visitante > a > span')]
            single = row.select_one('.eventoUnico')
            title = ' vs '.join(teams) if len(teams) == 2 else single.get_text(' · ', strip=True) if single else ''
            if not day or not title or not competition or not sport:
                raise ValueError('Incomplete guide row; review the provider format')
            clock = clock_node.get_text(' ', strip=True)
            start = f'{day.isoformat()}T{clock}:00' if re.fullmatch(r'\d{2}:\d{2}', clock) else None
            # Preserve the edition, remove only known dial positions / affiliate wording.
            labels = list(dict.fromkeys(re.sub(r'\s*\((?:Ver en directo|M\d+(?: O\d+)?)\)\s*$', '',
                node.get('title') or node.get_text(' ', strip=True)).strip() for node in row.select('.listaCanales > li')))
            observations.append(EventObservation(source_id='provider:wosti:es', source_name='Fútbol en la TV · Spain',
                source_kind='guide', external_id='snapshot:' + digest([folded(sport), competition, title, day.isoformat(), clock]),
                title=title, sport=sport, competition=competition, participants=teams, starts_at=start,
                scheduled_date=day, timezone='Europe/Madrid', state='scheduled',
                time_notes='Published occurrence. A changed date or time needs a new review.',
                broadcasts=[EventBroadcast(id=digest([label])[:32], label=label, country='es') for label in labels if label]))
    return observations


@dataclass
class ProviderSchedule:
    observations: list[EventObservation]
    available_interests: EventInterestChoices = field(default_factory=EventInterestChoices)
    warnings: list[str] = field(default_factory=list)


async def fetch_provider(options, *, zone, timeout=15, now=None):
    options = EventProviderOptions.model_validate(options)
    url, _, _ = provider_location(options)
    if options.provider == 'wosti_es':
        urls = [('https://www.futbolenlatv.es' + ('/deporte' if feed == 'all' else '/' if feed == 'football' else '/deporte/' + feed), feed)
                for feed in dict.fromkeys(options.feeds)]
        zone = 'Europe/Madrid'
    else:
        urls = [(url, '')]
    semaphore = asyncio.Semaphore(3)
    total_bytes = 0
    async with asyncio.timeout(timeout):
        async with source_session(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async def load(url, feed):
                nonlocal total_bytes
                async with semaphore:
                    async with session.get(url, max_redirects=5) as response:
                        response.raise_for_status()
                        data = bytearray()
                        async for chunk in response.content.iter_chunked(65536):
                            data.extend(chunk)
                            total_bytes += len(chunk)
                            if len(data) > 2 * 1024 * 1024 or total_bytes > 12 * 1024 * 1024:
                                raise ValueError('Provider response exceeds size limit')
                    raw = data.decode('utf-8-sig')
                    return parse_wosti(raw, feed=feed) if options.provider == 'wosti_es' else parse_openfootball(raw, options, zone)
            # TaskGroup cancels sibling requests on failure, before closing the session.
            async with asyncio.TaskGroup() as group:
                tasks = [group.create_task(load(url, feed)) for url, feed in urls]
    return select_provider_rows([o for task in tasks for o in task.result()], options, zone=zone, now=now)


def select_provider_rows(observations, options, *, zone, now=None):
    today = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(zone)).date()
    end = today + timedelta(days=options.window_days)
    unique = {}
    for observation in observations:
        prior = unique.get(observation.external_id)
        if prior:
            broadcasts = {b.id: b for b in [*prior.broadcasts, *observation.broadcasts]}
            if len(broadcasts) > 50:
                raise ValueError('Too many broadcasts for one occurrence')
            observation = observation.model_copy(update={'broadcasts': list(broadcasts.values())})
        unique[observation.external_id] = observation
    observations = list(unique.values())
    in_window = [o for o in observations if today <= (o.starts_at.astimezone(ZoneInfo(zone)).date() if o.starts_at else o.scheduled_date) < end]
    # Discovery is bounded separately from the selected import (at most 500 rows).
    choices = EventInterestChoices(sports=sorted({o.sport for o in in_window})[:2000],
        competitions=sorted({o.competition for o in in_window})[:2000],
        teams=sorted({team for o in in_window for team in o.participants})[:2000])
    selected = [o for o in in_window if matches_interests(o.model_dump(), options.interests)]
    selected.sort(key=lambda o: (o.scheduled_date, o.starts_at.isoformat() if o.starts_at else '', o.external_id))
    warnings = ['The window starts today in the source timezone. Providers may publish fewer days; nothing outside it is deleted.']
    if options.provider == 'wosti_es':
        warnings += ['Spain selects the broadcast market, not the countries of the teams or competition.',
            'This guide has no stable fixture IDs. Changed dates/times appear as new occurrences for review; archive the old occurrence if it was rescheduled.']
    else:
        warnings.append('OpenFootball has no TV listings. Dates and kickoff times may be incomplete; verify the configured source timezone.')
    if len(selected) > 500:
        warnings.append(f'{len(selected)} events match. Only the first 500 are shown; narrow your interests and preview again.')
    return ProviderSchedule(selected[:500], choices, warnings)
