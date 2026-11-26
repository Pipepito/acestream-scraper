"""Versioned, deterministic metadata classification. Unknown source text is retained."""
from dataclasses import dataclass
import hashlib
import re
import unicodedata

TAXONOMY_VERSION = 1


@dataclass(frozen=True)
class Category:
    id: str
    label: str
    label_es: str
    artwork: str = 'neutral'
    parent: str | None = None


CHANNEL_CATEGORIES = (
    Category('general', 'General TV', 'Generalista'),
    Category('movies', 'Movies', 'Cine', 'film-drama'),
    Category('series', 'Series', 'Series', 'film-drama'),
    Category('sports', 'Sports', 'Deportes', 'sports-general'),
    Category('news', 'News', 'Noticias', 'news'),
    Category('kids', 'Kids', 'Infantil', 'children'),
    Category('documentaries', 'Documentaries', 'Documentales', 'documentary'),
    Category('music', 'Music', 'Música', 'music'),
    Category('lifestyle', 'Lifestyle', 'Estilo de vida', 'lifestyle'),
    Category('regional', 'Regional/local', 'Regional/local'),
    Category('other', 'Other', 'Otros'),
)
GENRES = (*CHANNEL_CATEGORIES,
    Category('football', 'Football', 'Fútbol', 'football', 'sports'),
    Category('tennis', 'Tennis', 'Tenis', 'tennis', 'sports'),
    Category('motorsport', 'Motorsport', 'Motor', 'motorsport', 'sports'),
    Category('basketball', 'Basketball', 'Baloncesto', 'sports-general', 'sports'),
    Category('cricket', 'Cricket', 'Críquet', 'sports-general', 'sports'),
    Category('rugby', 'Rugby', 'Rugby', 'sports-general', 'sports'),
    Category('american-football', 'American football', 'Fútbol americano', 'sports-general', 'sports'),
    Category('cycling', 'Cycling', 'Ciclismo', 'sports-general', 'sports'),
    Category('hockey', 'Ice hockey', 'Hockey hielo', 'sports-general', 'sports'),
    Category('golf', 'Golf', 'Golf', 'sports-general', 'sports'),
    Category('combat', 'Combat sports', 'Deportes de combate', 'sports-general', 'sports'),
    Category('winter', 'Winter sports', 'Deportes de invierno', 'sports-general', 'sports'),
    Category('water', 'Water sports', 'Deportes acuáticos', 'sports-general', 'sports'),
    Category('athletics', 'Athletics', 'Atletismo', 'sports-general', 'sports'),
    Category('equestrian', 'Equestrian', 'Hípica', 'sports-general', 'sports'),
    Category('volleyball', 'Volleyball', 'Voleibol', 'sports-general', 'sports'),
    Category('padel', 'Padel', 'Pádel', 'sports-general', 'sports'),
    Category('snooker', 'Snooker/pool', 'Billar', 'sports-general', 'sports'),
    Category('esports', 'Esports', 'Deportes electrónicos', 'sports-general', 'sports'),
    Category('entertainment', 'Entertainment', 'Entretenimiento', 'entertainment'),
    Category('cooking', 'Cooking', 'Cocina', 'cooking', 'lifestyle'),
    Category('science', 'Science/education', 'Ciencia/educación', 'science'),
    Category('culture', 'Arts/culture', 'Arte/cultura', 'culture'),
    Category('nature', 'Nature', 'Naturaleza', 'nature', 'documentaries'),
    Category('travel', 'Travel', 'Viajes', 'travel', 'documentaries'),
    Category('history', 'History', 'Historia', 'documentary', 'documentaries'),
    Category('health', 'Health', 'Salud', 'lifestyle', 'lifestyle'),
    Category('religion', 'Religion/spirituality', 'Religión/espiritualidad'),
    Category('weather', 'Weather', 'Tiempo', 'news', 'news'),
    Category('shopping', 'Shopping', 'Televenta'),
    Category('comedy', 'Comedy', 'Comedia', 'film-drama', 'movies'),
    Category('action', 'Action/adventure', 'Acción/aventuras', 'film-drama', 'movies'),
    Category('crime', 'Crime/thriller', 'Crimen/suspense', 'film-drama', 'movies'),
    Category('horror', 'Horror', 'Terror', 'film-drama', 'movies'),
    Category('fantasy', 'Science fiction/fantasy', 'Ciencia ficción/fantasía', 'film-drama', 'movies'),
    Category('romance', 'Romance', 'Romántico', 'film-drama', 'movies'),
    Category('western', 'Western', 'Oeste', 'film-drama', 'movies'),
    Category('animation', 'Animation/anime', 'Animación/anime', 'children'),
)
BY_ID = {item.id: item for item in GENRES}
CHANNEL_IDS = {item.id for item in CHANNEL_CATEGORIES}


def normalize_label(value: str) -> str:
    # Some publishers emit literal JSON unicode escapes in XML text.
    value = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1], 16)), value)
    return ' '.join(unicodedata.normalize('NFC', value).casefold().split())


_ALIASES = {
    'general': 'general|generalista|general tv',
    'movies': 'movies|movie / drama|film / cinema|cine|cinema|films|film|película|películas|drama|cine español|cine independiente|cine para televisión|serious / classical / religious / historical movie / drama',
    'series': 'series|serie|série|series/soap|mini-series|telenovela|telenovelas|soap / melodrama / folkloric',
    'sports': 'sports|sport|deportes|deporte|desporto|sports event|sports related|sports talk|sports magazines|sportmagazin|magazine de desporto|magazine sportif|emission sportive|documentaire sportif|special events (olympic games; world cup; etc.)|tennis / squash',
    'news': 'news|noticias|informativo|informativos|notícias|news / current affairs|news magazine|actualidad|información|current affairs|discussion / interview / debate|programas informativos',
    'kids': "kids|children|infantil|infantiles|children's / youth programs|pre-school children's programs|preescolar|infantil y juvenil|entertainment programs for 6 to 14|entertainment programs for 10 to 16|cartoons / puppets|series infantiles españolas",
    'documentaries': 'documentary|documentaries|documentales|documental|documentaire|documentário|doku|dokureihe|dokumentation|dokumentationsreihe|magazines / reports / documentary|factual|reportage|biography|biografía',
    'music': 'music|música|musica|musical|music / ballet / dance|musical / opera|rock / pop|pop & rock|pop / rock|jazz|ópera|ballet|folk / traditional music|serious music / classical music',
    'lifestyle': 'lifestyle|estilo de vida|leisure hobbies|ocio y aficiones|gardening|jardinería|decoración|fashion|moda|consumer|consumer advice|hobbies',
    'regional': 'regional|regional/local|local|autonómicos|autonómicas',
    'other': 'other|otros',
    'football': 'football|soccer|fútbol|futbol|futebol|fußball|fussball|football / soccer|football - club|football - international|fútbol de liga|fútbol de copa|1. bundesliga|2. bundesliga|footballmagazin|fußballmagazin|fußballtalk',
    'tennis': 'tennis|tenis|ténis|tennismagazin',
    'motorsport': 'motorsport|motor sport|motor|automovilismo|auto racing|automobilisme|motociclismo|motorcycling|motorcycle|motorrad|desportos motorizados|formula one|formula 1|fórmula 1|formel 1|formule 1|moto gp|motogp|rally|rallye|rallying',
    'basketball': 'basketball|basket-ball|baloncesto|basquetebol|3x3 basketball',
    'cricket': 'cricket|cricket - domestic|cricket - international',
    'rugby': 'rugby|rugby union - domestic|rugby union - international|rugby league - domestic|rugby league - international',
    'american-football': 'american football|fútbol americano|football américain',
    'cycling': 'cycling|ciclismo|cyclisme|radsport|mountainbiking|mountain biking|mtb|vtt|cyclo-cross',
    'hockey': 'ice hockey|hockey hielo|hockey sur glace|eishockey|hóquei',
    'golf': 'golf|golfe|golfmagazin|golfdoku|indoor-golf',
    'combat': 'boxing|boxeo|boxen|martial arts|martial sports|artes marciais|artes marciales|artes marciales mixtas|mixed martial arts|wrestling|lucha|combat sports (without own categ',
    'winter': 'winter sports|deporte invierno|desportos de inverno|ski|skiing|esquí|esquí alpino|biathlon|snowboarding|wintersportmagazin|patinaje artístico',
    'water': 'water sport|water sports|wassersport|deportes acuáticos|desportos aquáticos|sailing|vela|voile|náuticos|surf',
    'athletics': 'athletics|atletismo|leichtathletik|marathon|triathlon|triatlón|triatlo',
    'equestrian': 'equestrian|equitación|equitation|hipismo|hípica|horse racing|hippisme|pferderennen',
    'volleyball': 'volleyball|volley-ball|voleibol|beach volleyball',
    'padel': 'padel|pádel',
    'snooker': 'snooker|snookerturnier|pool',
    'esports': 'esports|e-sport|esports - moba|esports - strategy und shooter|esports - motorsport',
    'entertainment': 'entertainment|entretenimiento|entretenimento|variety show|variedades|programas de entretenimiento|programas de variedades|programas magazín|game show / quiz / contest|show / game show|talk show|talkshow|reality|reality show|telerrealidad|concurso|concursos|celebridades',
    'cooking': 'cooking|cocina|gastronomía|gastronómico|programas de cocina',
    'science': 'science|ciencia|ciencia y tecnología|ciencia tecnología|technology / natural sciences|education / science / factual topics|educativo|formación|informational / educational / school programs|tecnología|tecnologías',
    'culture': 'culture|cultura|arte|arts|arts / culture (without music)|arte y cultura|popular culture / traditional arts|teatro|literature|literatura|arquitectura|cultural/educativo',
    'nature': 'nature|naturaleza|nature / animals / environment|documentaire nature|animales|medio ambiente|ecología',
    'travel': 'travel|viajes|viajes y aventuras|tourism / travel|reisereportage',
    'history': 'history|historia|histórico|histórica|documentales de historia',
    'health': 'health|salud|salud y bienestar|medicine / physiology / psychology|programas sobre la salud',
    'religion': 'religion|religión|religioso|espiritual|programas sobre religión|estudio bíblico|predicaciones|consejo bíblico|escatología bíblica|crecimiento espiritual|historias bíblicas|enseñanzas bíblicas|reflexiones bíblicas',
    'weather': 'weather|tiempo|meteorología|news / weather report|programas del tiempo',
    'shopping': 'shopping|televenta|teletienda|advertisement / shopping|werbesendung',
    'comedy': 'comedy|comedia|comédia|comedia romántica|comedia dramática|humor negro',
    'action': 'action|acción|adventure|aventura|aventuras|adventure / western / war',
    'crime': 'crime|crimen|true crime|thriller|suspense|policíaco|policíaca|policiaca|detective / thriller',
    'horror': 'horror|terror',
    'fantasy': 'fantasy|fantasía|fantástico|fantástica|science fiction|ciencia ficción|science fiction / fantasy / horror',
    'romance': 'romance|romántico|romántica',
    'western': 'western|oeste',
    'animation': 'animation|animación|anime|dibujos animados|animación para adultos',
}
ALIASES = {normalize_label(label): key for key, labels in _ALIASES.items() for label in labels.split('|')}
PLACEHOLDERS = {'', '0', 'default', 'sin clasificar', 'off-air', 'fin de emisión', 'programme indéterminé'}


def classify_genres(labels: list[str]) -> list[str]:
    result = set()
    for label in labels:
        value = normalize_label(label)
        key = ALIASES.get(value)
        if key:
            result.add(key)
        elif ',' in value:
            # Reviewed compound grammar: accept only known tokens (or placeholders).
            # Never infer from arbitrary fragments or a programme/channel title.
            parts = [part.strip() for part in value.split(',')]
            if all(part in ALIASES or part in PLACEHOLDERS for part in parts):
                result.update(ALIASES[part] for part in parts if part in ALIASES)
    for key in tuple(result):
        parent = BY_ID[key].parent
        if parent:
            result.add(parent)
    return sorted(result)


def channel_category(value: str | None) -> Category:
    if not value or not value.strip():
        return Category('uncategorized', 'Uncategorized', 'Sin categoría')
    key = ALIASES.get(normalize_label(value))
    if key in CHANNEL_IDS:
        return BY_ID[key]
    if key and BY_ID[key].parent == 'sports':
        return BY_ID['sports']
    return Category('custom-' + hashlib.sha256(value.strip().encode()).hexdigest()[:20], value.strip(), value.strip())


def artwork_status(category: Category) -> str:
    if category.artwork == 'neutral':
        return 'neutral'
    if category.parent and category.artwork == BY_ID[category.parent].artwork:
        return 'parent'
    return 'specific'
