"""Render reviewed Markdown and linked source as inert, self-contained Pages HTML.

Used only by prepare_pages_preview.py --local-docs. Install Markdown==3.11.3
in the checkout environment; this is not an application runtime dependency.
"""
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import PurePosixPath
import posixpath
import re
from urllib.parse import quote, unquote, urlsplit, urlunsplit

DESIGN = 'docs/design/ux-review-314'
STATIC = {'.json', '.txt', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.gif'}
SOURCE = {'.py', '.ts', '.tsx'}
ATTR = re.compile(r'\b(href|src)="([^"]*)"')


def heading_slug(value):
    return re.sub(r'[^\w\s-]', '', value.lower()).replace(' ', '-')


def document(title, body, revision):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'">
<title>{escape(title)} · ZZSTREAMS reference</title>
<link rel="stylesheet" href="admin-prototype.css">
<link rel="stylesheet" href="sportzz-tokens.css">
<link rel="stylesheet" href="sportzz-system.css">
<link rel="stylesheet" href="brand-reference.css">
<link rel="stylesheet" href="pages-documents.css"></head>
<body class="brand-index"><a class="skip" href="#main">Skip to content</a>
<header class="reference-header"><div>
<a class="sportzz-brand" href="index.html"><img class="sportzz-wordmark" src="assets/zztreams/wordmark-ink.png" alt="ZZSTREAMS design home"></a>
<nav aria-label="Design review"><a href="workflow-prototype.html?screen=dashboard">Mockups</a><a href="brand-system.html">Brand system</a><a href="components.html">Components</a><a href="README.md.html">Reference index</a></nav>
</div></header><main id="main" class="document-main" tabindex="-1">
<p class="eyebrow">DESIGN REFERENCE / STATIC SNAPSHOT</p>{body}
</main><footer class="document-footer">Design source <code>{escape(revision)}</code>. Historical reports retain their original scope; this snapshot is not production acceptance.</footer></body></html>
'''


def export_documents(preview, revision, files, read_blob):
    """Read only immutable, tracked blobs supplied by the caller."""
    import markdown

    inventory = set(files)
    docs = sorted(p for p in inventory if p.startswith(DESIGN + '/')
                  and PurePosixPath(p).parent.as_posix() == DESIGN and p.endswith('.md'))
    snapshots = {}
    copied = set()

    def rewrite(value, origin):
        url = urlsplit(unescape(value))
        if url.scheme or url.netloc or not url.path or '${' in url.path:
            return value
        target = posixpath.normpath(posixpath.join(posixpath.dirname(origin), unquote(url.path)))
        if target not in inventory:
            raise ValueError(f'Missing tracked reference: {origin}: {value}')
        suffix = PurePosixPath(target).suffix
        if target in docs:
            destination = PurePosixPath(target).name + '.html'
        elif suffix in SOURCE:
            destination = 'source-' + target.replace('/', '--') + '.html'
            snapshots[target] = destination
        elif target.startswith(DESIGN + '/'):
            destination = target[len(DESIGN) + 1:]
            output = preview / destination
            if not output.is_file():
                if suffix not in STATIC:
                    raise ValueError(f'Non-static reference: {target}')
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(read_blob(target))
                copied.add(destination)
        else:
            raise ValueError(f'Reference outside reviewed design/source: {target}')
        return escape(urlunsplit(('', '', quote(destination), url.query, url.fragment)), quote=True)

    for source in docs:
        text = read_blob(source).decode()
        body = markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists'])
        counts = {}

        def heading(match):
            tag, content = match.groups()
            slug = heading_slug(unescape(re.sub(r'<[^>]+>', '', content)))
            count = counts.get(slug, 0)
            counts[slug] = count + 1
            anchor = slug + ('-' + str(count) if count else '')
            return f'<{tag} id="{escape(anchor, quote=True)}">{content}</{tag}>'

        body = re.sub(r'<(h[1-6])>(.*?)</\1>', heading, body, flags=re.S)
        body = ATTR.sub(lambda m: m[1] + '="' + rewrite(m[2], source) + '"', body)
        body = re.sub(r'style="text-align: (left|right|center);"', r'class="document-align-\1"', body)
        body = body.replace('<pre>', '<pre tabindex="0" aria-label="Code example">')
        body = body.replace('<table>', '<div class="document-table" role="region" aria-label="Reference table" tabindex="0"><table>')
        body = body.replace('</table>', '</table></div>')
        title = re.search(r'^#\s+(.+)', text, flags=re.M)
        output = preview / (PurePosixPath(source).name + '.html')
        output.write_text(document(title[1] if title else PurePosixPath(source).stem, body, revision))

    for source, destination in snapshots.items():
        lines = read_blob(source).decode().splitlines()
        code = '\n'.join(f'<span id="L{i}">{escape(line)}</span>' for i, line in enumerate(lines, 1))
        body = f'<h1>Source snapshot</h1><p><code>{escape(source)}</code></p><p>Read-only design-source reference. This file is displayed as text and is never executed.</p><pre tabindex="0" aria-label="Source code"><code>{code}</code></pre>'
        (preview / destination).write_text(document(source, body, revision))

    # Runtime template links need the same rewrite as static navigation.
    for path in [*preview.glob('*.html'), preview / 'workflow-engine.js']:
        if path.name.endswith('.md.html') or path.name.startswith('source-'):
            continue
        path.write_text(ATTR.sub(lambda m: m[1] + '="' + rewrite(m[2], DESIGN + '/' + path.name) + '"', path.read_text()))
    return {'documents': len(docs), 'source_snapshots': len(snapshots), 'reference_assets': sorted(copied)}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {'src', 'href', 'poster'} and value:
                self.links.append(value)
            if key == 'id':
                self.ids.add(value)


def validate_links(preview):
    """Fail export on missing local assets/anchors, including generated docs."""
    preview = preview.resolve()
    pages = {}
    links = []
    for path in preview.rglob('*'):
        if path.suffix == '.html':
            parser = Links()
            parser.feed(path.read_text())
            pages[path] = parser.ids
            if path.name == 'admin-prototype.html':
                pages[path].update(re.findall(r'\bid=[\'"]([\w-]+)', path.read_text()))
            links.extend((path, link) for link in parser.links)
        elif path.suffix == '.css':
            links.extend((path, link) for link in re.findall(r'url\([\'"]?([^\'"\)]+)', path.read_text()))
    # The workflow main landmark is supplied by its checked runtime template.
    pages[preview / 'workflow-prototype.html'].update(
        re.findall(r'\bid=[\'"]([\w-]+)', (preview / 'workflow-engine.js').read_text()))
    local = fragments = 0
    failures = []
    for origin, link in links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = (origin.parent / unquote(url.path)).resolve() if url.path else origin
        local += 1
        if not target.is_relative_to(preview) or not target.is_file():
            failures.append(f'{origin.name}: missing or escaping local link {link}')
        elif url.fragment and target.suffix == '.html':
            fragments += 1
            if unquote(url.fragment) not in pages[target]:
                failures.append(f'{origin.name}: missing fragment {link}')
    if failures:
        raise ValueError('\n'.join(failures))
    return {'local_links': local, 'fragments': fragments}
