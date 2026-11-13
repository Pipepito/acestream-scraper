"""Read-only verification of published static files against a staged manifest.

No application or installation requests. Use only the public Pages origin and a
reviewed local staging directory. Reports belong outside Git.
"""

from pathlib import Path, PurePosixPath
from urllib.request import Request, urlopen
from urllib.parse import quote, urlsplit
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import ssl

ap = argparse.ArgumentParser()
ap.add_argument('--staged-root', type=Path, required=True)
ap.add_argument('--output', type=Path, required=True)
ap.add_argument('--ca-bundle', type=Path)
a = ap.parse_args()
tls = ssl.create_default_context(cafile=str(a.ca_bundle) if a.ca_bundle else None)
base = 'https://pipepito.github.io/acestream-scraper/'
manifest_path = 'design/ux-review-314/publication-manifest.json'
manifest = json.loads((a.staged_root / manifest_path).read_text())
expected = dict(manifest['sha256'])
expected[manifest_path] = hashlib.sha256((a.staged_root / manifest_path).read_bytes()).hexdigest()


def check(item):
    path, wanted = item
    p = PurePosixPath(path)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Unsafe manifest path')
    request = Request(base + quote(path, safe='/'), headers={'User-Agent': 'AceStream-design-review-static-verification', 'Cache-Control': 'no-cache'})
    try:
        with urlopen(request, timeout=25, context=tls) as r:
            if urlsplit(r.url).netloc != 'pipepito.github.io':
                raise ValueError('Unexpected redirect')
            body = r.read()
            actual = hashlib.sha256(body).hexdigest()
            return dict(path=path, status=r.status, bytes=len(body), expected=wanted, actual=actual, match=actual == wanted)
    except Exception as e:
        return dict(path=path, match=False, error=str(e))


results = []
with ThreadPoolExecutor(max_workers=8) as pool:
    for future in as_completed([pool.submit(check, item) for item in expected.items()]):
        results.append(future.result())
    failed = [r for r in results if not r['match']]
    # One bounded retry handles transient CDN/fetch errors; retain first results.
    retries = list(pool.map(check, [(r['path'], expected[r['path']]) for r in failed]))
final = {r['path']: r for r in results}
final.update({r['path']: r for r in retries})
report = dict(design_source=manifest['design_source'], site_source=manifest['site_source'], first_failures=failed, retries=retries, files=sorted(final.values(), key=lambda r: r['path']))
report['summary'] = dict(files=len(final), matching=sum(r['match'] for r in final.values()), failures=sum(not r['match'] for r in final.values()), preserved_site_files=manifest['preserved_site_files'], bytes=sum(r.get('bytes', 0) for r in final.values()))
a.output.mkdir(parents=True, exist_ok=True)
(a.output / 'hosted-checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['summary'], indent=2))
raise SystemExit(bool(report['summary']['failures']))
