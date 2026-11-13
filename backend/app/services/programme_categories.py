"""Lossless bounded XMLTV category observations and shared DTO projection."""
from app.services.category_taxonomy import classify_genres

MAX_CATEGORIES = 64
MAX_LABEL_LENGTH = 1024


def observations(program) -> list[dict[str, str | None]]:
    rows = getattr(program, 'category_observations', None)
    if rows:
        return [{'label': row.label, 'language': row.language} for row in rows]
    explicit = getattr(program, 'categories', None)
    if explicit is not None:
        return explicit
    return [{'label': program.category, 'language': None}] if program.category is not None else []


def genres(program) -> list[str]:
    return classify_genres([item['label'] for item in observations(program)])


def xml_categories(element) -> list[dict[str, str | None]]:
    result = []
    for child in element.findall('category'):
        label, language = child.text or '', child.get('lang')
        if len(result) >= MAX_CATEGORIES or len(label) > MAX_LABEL_LENGTH or (language and len(language) > 50):
            raise ValueError('EPG category metadata exceeds supported bounds')
        result.append({'label': label, 'language': language})
    return result
