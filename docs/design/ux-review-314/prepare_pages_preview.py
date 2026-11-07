"""Prepare static mockups alongside an unchanged, pinned main/docs snapshot.

No network, build, app imports or publication. Requires an empty output directory.
Only explicit design assets are included; specifications link to immutable GitHub
source. Usage: python3 prepare_pages_preview.py --site-ref origin/main
  --design-ref HEAD --output /tmp/acestream-pages-preview
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[3]
DESIGN = "docs/design/ux-review-314"
FILES = (
    "workflow-gallery.html", "workflow-prototype.html", "workflow-engine.js",
    "workflow-data.js", "workflow-prototype.css", "admin-prototype.html",
    "admin-prototype.css", "prototype.html",
)
ARCHIVE = "https://github.com/Pipepito/acestream-scraper/blob/{sha}/" + DESIGN + "/"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def extract(ref, paths, prefix, destination):
    data = git("archive", "--format=tar", ref, *paths)
    count = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if ".." in name.parts or name.is_absolute():
                raise ValueError("Unsafe archive path")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"Unsupported archive entry: {name}")
            target = destination.joinpath(*name.relative_to(prefix).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
            count += 1
    return count


def hashes(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-ref", required=True)
    parser.add_argument("--design-ref", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error("Output must be empty; existing files will not be overwritten")
    site_sha = git("rev-parse", args.site_ref + "^{commit}").decode().strip()
    design_sha = git("rev-parse", args.design_ref + "^{commit}").decode().strip()
    out.mkdir(parents=True, exist_ok=True)
    site_count = extract(site_sha, ["docs"], "docs", out)
    original = hashes(out)
    preview = out / "design/ux-review-314"
    if preview.exists():
        raise ValueError("The site snapshot already contains this preview; reconcile explicitly")
    assets = [DESIGN + "/" + name for name in FILES]
    assets += [DESIGN + "/assets", DESIGN + "/workflow-exports"]
    preview_count = extract(design_sha, assets, DESIGN, preview)
    source = ARCHIVE.format(sha=design_sha)
    # Markdown remains readable on GitHub and retains its stable heading anchors.
    for name in ("workflow-gallery.html", "workflow-engine.js"):
        path = preview / name
        text = re.sub(r'href="([\w-]+\.md)', lambda m: 'href="' + source + m[1], path.read_text())
        path.write_text(text)
    gallery = preview / "workflow-gallery.html"
    gallery.write_text(gallery.read_text().replace("Earlier gallery", "Preview home"))
    # The old concept predates the no-network policy used by the newer prototypes.
    old = preview / "prototype.html"
    csp = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\' \'unsafe-inline\'; script-src \'self\' \'unsafe-inline\'; font-src \'self\'; img-src \'self\' data:; connect-src \'none\'; media-src \'none\'; object-src \'none\'; frame-src \'none\'; form-action \'none\'; base-uri \'none\'">'
    old.write_text(old.read_text().replace("<head>", "<head>" + csp, 1))
    (preview / "index.html").write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; connect-src 'none'; form-action 'none'; base-uri 'none'">
<title>AceStream Scraper · interactive design previews</title>
<style>body{{margin:0;background:#f5f3ef;color:#202232;font:17px/1.6 system-ui,sans-serif}}main{{max-width:1000px;margin:auto;padding:48px 24px}}h1{{font-size:clamp(32px,5vw,56px);line-height:1.1;letter-spacing:-.035em}}h2{{font-size:24px;line-height:1.25}}a{{color:#843b23;text-underline-offset:4px}}a:focus-visible{{outline:3px solid #744017;outline-offset:4px}}.notice{{border-left:4px solid #843b23;padding:12px 20px;background:#eeece7}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:28px}}section{{border-top:1px solid #85838d;padding-top:12px}}.primary{{display:inline-block;background:#843b23;color:white;padding:12px 18px;border-radius:6px;margin:8px 0}}nav{{display:flex;flex-wrap:wrap;gap:16px}}small{{display:block;margin-top:32px;overflow-wrap:anywhere}}@media(max-width:500px){{main{{padding:28px 18px}}}}</style></head>
<body><main><a href="../../">← Installation tools and guides</a><h1>AceStream Scraper<br>Explore the proposed experience</h1>
<p>Interactive design references for <a href="https://github.com/Pipepito/acestream-scraper/issues/314">epic #314</a>.</p>
<p class="notice">Synthetic data only. These previews cannot connect to an installation, play media, record, discover devices or save settings. They are design proposals, not the implemented app.</p>
<p><a class="primary" href="workflow-prototype.html?screen=dashboard">Open interactive workflows</a></p>
<nav aria-label="Design resources"><a href="workflow-gallery.html">Browse all 144 workflows</a><a href="{source}workflow-specification.md">Field specification</a><a href="{source}verification-review-04.md">Verification and limits</a><a href="{source}implementation-prompt.md">Implementation prompt</a></nav>
<h2>Compare the proposals</h2><p>The current controls compare coral and lime accents with calm and expressive treatments, in English and Spanish and both themes. The planned cyan design and production interface selector still require implementation; they are not demonstrated here.</p>
<div class="cards"><section><h2>Whole-app workflows</h2><p>144 composed screens, including settings, access, sources, recordings and recovery. Use Screen and State to review specific flows.</p><p><a href="workflow-prototype.html?screen=recording-schedule&palette=coral">Explore the current prototype</a></p><p><a href="workflow-gallery.html">288 desktop and phone images</a></p></section>
<section><h2>Earlier administration study</h2><p>Nine earlier families. These demonstrate selected interactions and do not replace the detailed whole-app specification.</p><p><a href="admin-prototype.html?view=recordings">Open administration study</a></p></section>
<section><h2>Earlier viewing concept</h2><p>Live TV, Settings and Channels. Several actions and draft states are illustrative. This is a historical visual reference.</p><p><a href="prototype.html?view=live&palette=lime">Explore lime</a> · <a href="prototype.html?view=live&palette=coral">Explore coral/navy</a></p></section></div>
<p><a href="{source}README.md">Read the complete design package on GitHub</a>. Fonts retain their <a href="assets/Inter-OFL.txt">Inter</a> and <a href="assets/Barlow-OFL.txt">Barlow</a> licence notices.</p>
<small>Design source: {design_sha}<br>Existing site source: {site_sha}<br>No supplier archive, media masters or private installation captures are included in this preview.</small>
</main></body></html>''')
    final = hashes(out)
    changed = [name for name, value in original.items() if final.get(name) != value]
    if changed:
        raise ValueError("Existing Pages content changed: " + str(changed))
    manifest = dict(site_source=site_sha, design_source=design_sha,
                    preserved_site_files=site_count, copied_design_files=preview_count,
                    existing_site_changes=changed, sha256=final)
    (preview / "publication-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({key: value for key, value in manifest.items() if key != "sha256"}, indent=2))


if __name__ == "__main__":
    main()
