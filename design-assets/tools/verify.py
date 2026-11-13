"""Read-only integrity/media checks for the combined design deliverables."""
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root, relative):
    path = root / relative
    check(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), f'Unsafe path: {path}')
    return path


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'href', 'src', 'poster'} and value:
                self.urls.append(value)
            if key == 'id':
                self.ids.append(value)


def verify_links(path):
    content = path.read_text()
    parsed = Links()
    if path.suffix == '.html':
        parsed.feed(content)
        check(len(parsed.ids) == len(set(parsed.ids)), f'Duplicate HTML IDs: {path}')
    urls = parsed.urls + re.findall(r'url\([\s\'"]*([^\)\'"\s]+)', content)
    urls += re.findall(r'fetch\([\'"]([^\'"]+)', content)
    count = 0
    for url in urls:
        parts = urlsplit(url)
        if parts.scheme or parts.netloc:
            check(parts.scheme == 'data', f'Unexpected external runtime resource: {url}')
            continue
        target = inside(ROOT, str((path.parent / unquote(parts.path)).relative_to(ROOT))) if parts.path else path
        check(target.is_file(), f'Broken local reference from {path}: {url}')
        if parts.fragment:
            if target.suffix == '.svg':
                ids = {el.get('id') for el in ET.parse(target).getroot().iter()}
            elif target.suffix == '.html':
                other = Links()
                other.feed(target.read_text())
                ids = set(other.ids)
            else:
                ids = {parts.fragment}
            check(unquote(parts.fragment) in ids, f'Missing fragment: {url}')
        count += 1
    return count


def main():
    manifest = json.loads((ROOT / 'integration-manifest.json').read_text())
    report = {'scope': 'Design-asset integration, not full application CI', 'files': 0,
              'images_decoded': 0, 'svg_files': 0, 'json_files': 0, 'local_references': 0}
    for collection in manifest['collections']:
        root = inside(ROOT, collection['path'])
        entries = [e for e in manifest['files'] if e['collection'] == collection['path']]
        expected = {e['path'] for e in entries}
        actual = {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() or p.is_symlink()}
        check(actual == expected, f'Inventory mismatch: {collection["path"]}: {actual ^ expected}')
        for entry in entries:
            p = inside(root, entry['path'])
            check(p.stat().st_size == entry['bytes'] and sha(p) == entry['sha256'], f'Copy checksum mismatch: {p}')
            check(entry['bytes'] < 100 * 1024 * 1024, f'GitHub oversized file: {p}')
            check(p.suffix not in {'.zip', '.pyc', '.pid', '.log'}, f'Forbidden runtime/archive file: {p}')
            report['files'] += 1
            if p.suffix in {'.png', '.jpg', '.webp'}:
                with Image.open(p) as image:
                    image.load()
                report['images_decoded'] += 1
            elif p.suffix == '.json':
                json.loads(p.read_text())
                report['json_files'] += 1
            elif p.suffix == '.svg':
                svg = ET.parse(p).getroot()
                ids = [el.attrib['id'] for el in svg.iter() if 'id' in el.attrib]
                check(len(ids) == len(set(ids)), f'Duplicate SVG IDs: {p}')
                check(not any(el.tag.split('}')[-1] == 'script' for el in svg.iter()), f'Scripted SVG: {p}')
                report['svg_files'] += 1
            elif p.suffix in {'.html', '.css'}:
                report['local_references'] += verify_links(p)
            for existing in entry.get('identical_existing_paths', []):
                check(sha(ROOT.parent / existing) == entry['sha256'], f'Existing asset changed: {existing}')
    for entry in manifest['excluded']:
        check(not (ROOT / entry['collection'] / entry['path']).exists(), f'Excluded file copied: {entry["path"]}')

    library = ROOT / 'sportzz/visual-library-v1'
    promo = ROOT / 'sportzz/brand-promo-10s'
    for root, name in [(library, 'assets/magnific/manifests/sportzz-file-index.json'), (promo, 'file-manifest.json')]:
        entries = json.loads((root / name).read_text())['files']
        for e in entries:
            p = inside(root, e['path'])
            check(p.is_file() and sha(p) == e['sha256'] and p.stat().st_size == e['bytes'], f'Supplied manifest mismatch: {p}')
    report['supplied_checksum_entries'] = 204 + 59

    assets = json.loads((library / 'assets/magnific/manifests/sportzz-visual-assets.json').read_text())
    check([sum(a['category'] == c for a in assets['assets']) for c in ['photography', 'mockups', 'graphics']] == [8, 8, 5], 'Primary asset counts')

    def dimensions(value):
        if isinstance(value, dict):
            if 'path' in value and isinstance(value.get('resolution'), list) and len(value['resolution']) == 2:
                p = inside(library, value['path'])
                with Image.open(p) as image:
                    check(list(image.size) == value['resolution'], f'Manifest dimensions: {p}')
            for child in value.values():
                dimensions(child)
        elif isinstance(value, list):
            for child in value:
                dimensions(child)
    dimensions(assets)

    icons = json.loads((library / 'assets/icons/icon-manifest.json').read_text())['icons']
    check(len(icons) == len({e['id'] for e in icons}) == 70, 'Icon count/uniqueness')
    sprite = ET.parse(library / 'assets/icons/sprite.svg').getroot()
    symbols = {el.attrib['id']: el for el in sprite}
    check(len(sprite) == len(symbols) == 70 and set(symbols) == {e['id'] for e in icons}, 'Sprite IDs')
    for e in icons:
        svg = ET.parse(library / e['path']).getroot()
        check(svg.get('viewBox') == '0 0 24 24', f'Icon viewBox: {e["id"]}')
        for key, value in [('stroke', 'currentColor'), ('stroke-width', '1.75'), ('fill', 'none')]:
            check(svg.get(key) == value and symbols[e['id']].get(key) == value, f'Icon/sprite style: {e["id"]}')
        check(all(el.tag.split('}')[-1] in {'svg', 'path'} for el in svg.iter()), f'Non-vector icon: {e["id"]}')
        check(len(svg) == 1 and len(symbols[e['id']]) == 1 and svg[0].attrib == symbols[e['id']][0].attrib, f'Icon/sprite geometry: {e["id"]}')
    report['primary_assets'] = 21
    report['individual_icons_and_matching_symbols'] = 70
    tile = Image.open(library / 'assets/magnific/graphics/textures/sportzz-graphic-carbon-texture-tile.webp')
    w, h = tile.size
    check(tile.crop((0, 0, 1, h)).tobytes() == tile.crop((w-1, 0, w, h)).tobytes(), 'Tile left/right edges')
    check(tile.crop((0, 0, w, 1)).tobytes() == tile.crop((0, h-1, w, h)).tobytes(), 'Tile top/bottom edges')

    manual = ROOT / 'zztream/manual-v1/zztream-manual-identidad-v1.pdf'
    with pymupdf.open(manual) as pdf:
        check(len(pdf) == 20, 'Manual page count')
        embedded = set()
        used_fonts = set()
        for page in pdf:
            check(tuple(page.rect)[2:] == (960, 600), 'Manual page dimensions')
            check(len(page.get_text().strip()) > 10, 'Manual selectable text')
            check(page.get_pixmap(matrix=pymupdf.Matrix(0.25, 0.25)).width == 240, 'Manual page rendering')
            for font in page.get_fonts():
                if pdf.extract_font(font[0])[3]:
                    embedded.add(font[3].split('+')[-1])
            for block in page.get_text('dict')['blocks']:
                if block['type'] == 0:
                    used_fonts.update(span['font'] for line in block['lines'] for span in line['spans'])
        check(used_fonts and used_fonts <= embedded, 'Manual uses a nonembedded font')
        report['pdf'] = {'pages_rendered': 20, 'page_size_points': [960, 600], 'embedded_fonts': sorted(embedded)}

    probe = shutil.which('ffprobe')
    check(probe is not None, 'FFprobe is required')
    report['media'] = {}
    expected_audio = {'master': True, 'web': True, 'silent': False, 'clean': False}
    for p in sorted(promo.glob('sportzz-brand-promo-10s-*')):
        if p.suffix not in {'.mp4', '.webm'}:
            continue
        result = subprocess.run([probe, '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(p)], check=True, capture_output=True, text=True)
        check(not result.stderr.strip(), f'Media decode warning: {p}')
        data = json.loads(result.stdout)
        videos = [s for s in data['streams'] if s['codec_type'] == 'video']
        audios = [s for s in data['streams'] if s['codec_type'] == 'audio']
        check(len(videos) == 1, f'Video stream count: {p}')
        v = videos[0]
        check((v['width'], v['height']) == (1280, 720) and v['r_frame_rate'] == '24/1' and v['avg_frame_rate'] == '24/1', f'Media dimensions/frame rate: {p}')
        check(int(v['nb_read_frames']) == 240 and abs(float(data['format']['duration']) - 10) < 0.0001, f'Media frames/duration: {p}')
        want_audio = expected_audio[p.stem.rsplit('-', 1)[1]] if p.suffix == '.mp4' else False
        check(len(audios) == int(want_audio), f'Audio stream count: {p}')
        check(v['codec_name'] == ('h264' if p.suffix == '.mp4' else 'vp9'), f'Codec: {p}')
        report['media'][p.name] = {'width': v['width'], 'height': v['height'], 'fps': v['r_frame_rate'], 'frames': int(v['nb_read_frames']), 'seconds': float(data['format']['duration']), 'audio': bool(audios), 'codec': v['codec_name']}
    check(len(report['media']) == 5, 'Five final video exports required')
    report['status'] = 'passed'
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
