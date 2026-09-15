"""Disposable extraction process: never import database, settings or network clients."""
import json
import re
import sys
from itertools import islice
from bs4 import BeautifulSoup
from app.schemas.extraction import ExtractionRecipe, MAX_RECORDS, MAX_SAMPLE_BYTES


def json_path(value, path):
    for part in path.split('.') if path else []:
        if isinstance(value, list) and part.isdigit():
            value = value[int(part)] if int(part) < len(value) else None
        elif isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def extract(recipe: ExtractionRecipe, sample: str) -> dict:
    if len(sample.encode('utf-8')) > MAX_SAMPLE_BYTES:
        raise ValueError('Sample exceeds 32 MiB')
    flags = re.ASCII | sum(flag for key, flag in [('i', re.I), ('m', re.M), ('s', re.S)] if key in recipe.flags)
    if recipe.mode == 'html':
        soup = BeautifulSoup(sample, 'html.parser')
        records = soup.select(recipe.records, limit=MAX_RECORDS + 1)
    elif recipe.mode == 'json':
        records = json_path(json.loads(sample), recipe.records)
        if not isinstance(records, list):
            raise ValueError('The records path must select a JSON array')
    else:
        records = [m.group(0) for m in islice(re.finditer(recipe.records, sample, flags), MAX_RECORDS + 1)]
    if len(records) > MAX_RECORDS:
        raise ValueError('More than 1000 records; narrow the record rule')
    result = {'channels': [], 'record_count': len(records), 'invalid_count': 0, 'duplicate_count': 0, 'issues': []}
    seen = set()
    for index, record in enumerate(records, 1):
        values = {}
        for key, field in recipe.fields.items():
            if recipe.mode == 'html':
                elements = record.select(field.selector) if field.selector else [record]
                raw = [el.get(field.attribute, '') if field.attribute else el.get_text('', strip=False) for el in elements]
            elif recipe.mode == 'json':
                value = json_path(record, field.path)
                raw = value if isinstance(value, list) else [value]
            else:
                raw = [record]
            extracted = []
            for value in raw[:MAX_RECORDS]:
                if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                    continue
                value = str(value)
                if field.pattern:
                    match = re.search(field.pattern, value, flags)
                    if not match:
                        continue
                    value = (match.group(1) if match.re.groups else match.group(0)) or ''
                value = re.sub(r'\s+', ' ', value).strip()
                if value:
                    extracted.append(value)
            values[key] = extracted
        names, ids = values['name'], values['id']
        reason = None
        if len(names) != 1 or len(names[0]) > 200:
            reason = 'Choose exactly one channel name per record (up to 200 characters)'
        elif not ids:
            reason = 'No channel ID found'
        normalized = [value.removeprefix('acestream://').lower() for value in ids]
        if any(not re.fullmatch(r'[0-9a-f]{40}', value) for value in normalized):
            reason = 'Expected a 40-character hexadecimal ID or acestream:// link'
        if reason:
            result['invalid_count'] += 1
            if len(result['issues']) < MAX_RECORDS:
                result['issues'].append({'record': index, 'message': reason})
            continue
        metadata = {}
        for key, target in [('group', 'group_title'), ('logo', 'tvg_logo'), ('epg_id', 'tvg_id')]:
            entries = values.get(key, [])
            if entries:
                value = entries[0][:2048]
                if key != 'logo' or value.startswith(('https://', 'http://')):
                    metadata[target] = value
        for channel_id in normalized:
            if channel_id in seen:
                result['duplicate_count'] += 1
                if len(result['issues']) < MAX_RECORDS:
                    result['issues'].append({'record': index, 'message': 'Duplicate ID ignored'})
            else:
                seen.add(channel_id)
                result['channels'].append({'channel_id': channel_id, 'name': names[0], 'metadata': metadata})
            if len(result['channels']) > MAX_RECORDS:
                raise ValueError('More than 1000 channel IDs; narrow the rule')
    result['issues'] = result['issues'][:1000]
    return result


if __name__ == '__main__':
    try:
        if sys.platform == 'linux':
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
            resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        data = json.loads(sys.stdin.read(MAX_SAMPLE_BYTES * 8))
        recipe = ExtractionRecipe.model_validate(data['recipe'])
        print(json.dumps(extract(recipe, data['sample'])))
    except Exception:
        # Never echo source HTML, regex values or credentials in errors.
        print(json.dumps({'error': 'Invalid recipe or sample. Check selectors, JSON paths, regex and input limits.'}))
        sys.exit(1)
