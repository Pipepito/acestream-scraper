"""MARCA's dated, server-rendered Spain TV agenda (no executable content)."""
import re
from datetime import date

from bs4 import BeautifulSoup, SoupStrainer

from app.schemas.events import EventBroadcast, EventObservation

MONTHS = {name: index for index, name in enumerate((
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
    'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'), 1)}
SPORTS = {
    'futbol': 'Football', 'f. sala': 'Futsal', 'futbol sala': 'Futsal',
    'nba': 'Basketball', 'baloncesto': 'Basketball', 'nfl': 'American football',
    'tenis': 'Tennis', 'balonmano': 'Handball', 'ciclismo': 'Cycling',
    'golf': 'Golf', 'padel': 'Padel', 'rugby': 'Rugby', 'boxeo': 'Boxing',
    'formula 1': 'Motorsport', 'f1': 'Motorsport', 'motogp': 'Motorcycling',
    'motociclismo': 'Motorcycling', 'automovilismo': 'Motorsport',
}


def parse_marca(raw):
    from app.services.event_providers import digest, folded

    soup = BeautifulSoup(raw, 'html.parser', parse_only=SoupStrainer('div', class_='schedule'))
    days = soup.select('.daylist > .content-item')
    if not days:
        raise ValueError('MARCA agenda markup changed')
    observations = {}
    for section in days:
        heading = section.select_one('.title-section-widget')
        match = re.search(r'(\d{1,2}) de (\w+) de (\d{4})', folded(heading.get_text(' ', strip=True))) if heading else None
        if not match or match[2] not in MONTHS:
            raise ValueError('MARCA agenda date is missing')
        day = date(int(match[3]), MONTHS[match[2]], int(match[1]))
        for row in section.select('.dailyevent'):
            def value(selector):
                node = row.select_one(selector)
                return node.get_text(' ', strip=True) if node else ''
            label, competition, title, clock = (value(selector) for selector in
                ('.dailyday', '.dailycompetition', '.dailyteams', '.dailyhour'))
            if not all((label, competition, title)) or not re.fullmatch(r'\d{2}:\d{2}', clock):
                raise ValueError('Incomplete MARCA agenda row')
            sport = SPORTS.get(folded(label), label)
            # NBA/NFL identify the competition; their subheading is a round/phase.
            if folded(label) in ('nba', 'nfl'):
                competition = label.upper()
            key = 'daily:' + digest([day.isoformat(), folded(sport), folded(competition), folded(title)])
            labels = list(dict.fromkeys(node.get_text(' ', strip=True) for node in row.select('.dailychannel')))
            observation = EventObservation(source_id='provider:marca:es', source_name='MARCA · Spain',
                source_kind='guide', external_id=key, title=title, sport=sport, competition=competition,
                participants=re.split(r' (?:-|@|vs) ', title) if re.search(r' (?:-|@|vs) ', title) else [],
                starts_at=f'{day.isoformat()}T{clock}:00', scheduled_date=day, timezone='Europe/Madrid', state='scheduled',
                time_notes='MARCA daily listing. Same-day time changes update this occurrence; changed dates or titles are separate occurrences.',
                broadcasts=[EventBroadcast(id=digest([name])[:32], label=name, country='es') for name in labels if name])
            prior = observations.get(key)
            if prior:
                if prior.starts_at != observation.starts_at:
                    raise ValueError('Ambiguous MARCA daily occurrence')
                broadcasts = {b.id: b for b in [*prior.broadcasts, *observation.broadcasts]}
                observation = EventObservation.model_validate({**observation.model_dump(), 'broadcasts': list(broadcasts.values())})
            observations[key] = observation
            if len(observations) > 2000:
                raise ValueError('MARCA agenda exceeds event limit')
    return list(observations.values())
