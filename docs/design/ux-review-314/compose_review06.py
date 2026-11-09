"""Generate the current navigation index, galleries and traceable location appendix."""
from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parent

def build():
 data=json.loads((ROOT/'workflow-data.json').read_text());nav=json.loads((ROOT/'navigation-map.json').read_text());by={s['id']:s for s in data['screens']}
 lines=['# Before / after location and save map','', 'Review 06 · proposed composition, not application implementation. Seven primary destinations in every preset. Existing application routes and query aliases remain valid. A workflow ID identifies a reviewable state/editor, not a new application page.','', 'Read [the simplification decisions](simplification-06.md), [shared architecture](shared-foundations-06.md) and [field specification](workflow-specification.md).','', '| Current surface | Proposed location and access path | Treatment / canonical editor | Save boundary | Evidence / acceptance |','|---|---|---|---|---|']
 for w in nav['workflows']:
  s=by[w['id']];dest=by[w['destination']]['title'][0];section=by[w['section']]['title'][0]
  path=' → '.join(dict.fromkeys([dest,section,s['title'][0]]))
  save='; '.join(f"`{x['editor']}`: {x['timing']} · `{x['api']}`" for x in w['save']) or 'Read-only, local view or named command; see workflow-specific consequence.'
  source=w['source'][0]
  lines.append(f"| `{w['current']}` · {s['title'][0]} | [{path}](workflow-prototype.html?screen={w['canonical']}) | {w['presentation']} · `{w['canonical']}` | {save} | [{source.rsplit('/',1)[-1]}](https://github.com/Pipepito/acestream-scraper/blob/{data['revision']}/{source}); #{w['owner']} |")
 (ROOT/'before-after-map.md').write_text('\n'.join(lines)+'\n')
 # Replace current generated verification references and attach destination to each workflow.
 for name in ['workflow-specification.md','traceability-matrix.md']:
  pth=ROOT/name;text=pth.read_text().replace('review 04','review 06').replace('verification-review-04.md','verification-review-06.md')
  if name=='workflow-specification.md':
   text=text.replace('## How to implement this specification','## Future implementation boundary')
   for s in data['screens']:
    marker=f'<a id="{s["id"]}"></a>'
    loc=s['location'];dest=by[loc['destination']]['title'][0];sec=by[loc['section']]['title'][0]
    text=text.replace(marker,marker+'\n\n**Simplified location:** '+dest+' → '+sec+'. **Composition:** '+loc['presentation']+'. **Canonical editor:** `'+loc['canonical']+'`. The same fields/actions are used by lime, coral/navy and immersive cyan.\n')
   text+='\n## Presentation-only blocks\n\nThe Watch featured area, programme cards, category navigation, recording continuation card, event category illustration and interface selector are composed by `workflow-engine.js` and styled by `presentation-presets.css`. They introduce no endpoint or permission. Watch actions enter the existing viewer lifecycle; programme details open the canonical recording/guide context. Generic art is labelled and distinct from real artwork. See [shared foundations](shared-foundations-06.md) and [resource selection](asset-selection-06.md).\n'
  else:
   for s in data['screens']:
    sid=s['id'];text=text.replace(f'workflow-exports/{sid}-en.jpg',f'workflow-exports/{sid}-cyan-en.jpg').replace(f'workflow-exports/{sid}-es.jpg',f'workflow-exports/{sid}-cyan-es.jpg')
   text+='\n## Preset parity and simplified location\n\nEvery row above maps to the exact location, canonical editor and independent save boundary in [before/after map](before-after-map.md). The [gallery](workflow-gallery.html) links all three presets and the new exports. See [OpenAPI references](openapi-contracts-06.md) for endpoint evidence. Rendered checks are design evidence only. Owner-approved: three presets, one shared product, seven-destination plan, Watch consolidation and immersive default. Individual final palettes/assets and participant acceptance remain proposed. Implemented: none.\n'
  pth.write_text(text)
 render_pages(data,nav)

def render_pages(data,nav):
 head='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\'; font-src \'self\'; connect-src \'none\'; base-uri \'none\'"><title>ZZSTREAMS · design review</title><link rel="stylesheet" href="admin-prototype.css"><link rel="stylesheet" href="sportzz-tokens.css"><link rel="stylesheet" href="sportzz-system.css"><link rel="stylesheet" href="brand-reference.css"></head><body class="brand-index"><a class="skip" href="#main">Skip to content</a><header class="reference-header"><div><a class="sportzz-brand" href="index.html"><img class="sportzz-wordmark" src="assets/zztreams/wordmark-ink.png" alt="ZZSTREAMS design home"></a><nav aria-label="Design review"><a href="workflow-prototype.html?screen=dashboard">Mockups</a><a href="workflow-gallery.html">Workflows</a><a href="brand-system.html">Brand system</a><a href="components.html">Components</a></nav></div></header><main id="main" tabindex="-1">'
 notice='<p class="notice">Design-only review · synthetic examples · no installation connection. Interactive actions simulate outcomes. No application code or runtime has been redesigned.</p>'
 cards=[]
 for preset,title,copy in [('lime','01 · Lime','Compact broadcast rhythm, condensed headings and channel rows.'),('coral','02 · Coral / navy','Warm editorial composition, balanced images and generous reading space.'),('cyan','03 · Immersive','A featured viewing area, visual categories and deliberate phone layouts. Proposed first-visit default.')]:
  cards.append(f'<article class="card"><a href="workflow-prototype.html?screen=dashboard&preset={preset}"><img src="workflow-exports/dashboard-{preset}-en.jpg" alt="{title} desktop composition"></a><h2>{title}</h2><p>{copy}</p><div class="links"><a href="workflow-prototype.html?screen=dashboard&preset={preset}">Explore</a><a href="workflow-prototype.html?screen=recording-settings&preset={preset}">Administration</a><a href="workflow-prototype.html?screen=dashboard&preset={preset}&lang=es&theme=dark">Español / dark</a></div></article>')
 page=head+'<p class="eyebrow">ACESTREAM SCRAPER · REVIEW 06</p><h1>One product.<br>Three ways to watch.</h1><p>Find a channel, record a programme and connect your devices through one shared structure. Choose a presentation that feels right.</p>'+notice+'<a class="primary" href="workflow-prototype.html?screen=dashboard">Explore the interactive design</a><div class="grid">'+''.join(cards)+'</div><h2>Seven familiar places</h2><nav aria-label="Proposed destinations">'+''.join(f'<a href="workflow-prototype.html?screen={n["id"]}">{n["label"][0]}</a>' for n in nav['navigation'])+'</nav><h2>Review the whole application</h2><div class="links"><a href="workflow-gallery.html">All composed workflows</a><a href="simplification-06.md">Before / after journeys</a><a href="shared-foundations-06.md">One shared application</a><a href="openapi-contracts-06.md">OpenAPI contract testing</a><a href="workflow-specification.md">Fields and consequential states</a><a href="verification-review-06.md">Verification and limitations</a><a href="asset-selection-06.md">Graphics and notices</a></div><footer><p>Three presets and the shared architecture are the approved design scope. Visual details remain proposals. Application implementation needs separate authorization.</p><details><summary>Historical studies</summary><a href="admin-prototype.html">Earlier administration prototype</a> · <a href="prototype.html">Earlier viewing concept (illustrative actions)</a></details><p><a href="README.md">Complete package</a> · <a href="https://github.com/Pipepito/acestream-scraper/issues/314">Epic #314</a></p></footer></main></body></html>'
 page=page.replace('ACESTREAM SCRAPER · REVIEW 06','ZZSTREAMS · DESIGN STUDY').replace('One product.<br>Three ways to watch.','One identity.<br>Three ways to watch.')
 (ROOT/'index.html').write_text(page+'\n')
 parts=[head,'<a href="index.html">← Design home</a><h1>Whole-app compositions</h1>',notice,f'<p>{len(data["screens"])} workflow contexts share one field catalogue and interaction model. Each has lime, coral/navy and immersive treatments. Review controls expose consequential states. These are not {len(data["screens"])} navigation destinations.</p>','<nav aria-label="Workflow groups">'+''.join(f'<a href="#{n["id"]}">{n["label"][0]}</a>' for n in nav['navigation'])+'</nav>']
 for n in nav['navigation']:
  aliases={'dashboard':['viewing'],'channels':['guides','sources','extraction'],'connections':['playlists','integrations'],'settings':['access','shell'],'system':['runtime','setup']}
  parts.append(''.join(f'<span id="{alias}"></span>' for alias in aliases.get(n['id'],[])))
  parts.append(f'<section class="group" id="{n["id"]}"><h2>{n["label"][0]} / {n["label"][1]}</h2><div class="workflow-grid">')
  for s in data['screens']:
   if s['destination']!=n['id']:continue
   sid=s['id'];title=html.escape(s['title'][0]);parts.append(f'<article class="card"><img src="workflow-exports/{sid}-cyan-en.jpg" loading="lazy" alt="{title} composed reference"><h3>{title}</h3><p>{html.escape(s["goal"][0])}</p><div class="links">'+''.join(f'<a href="workflow-prototype.html?screen={sid}&preset={preset}&review=1">{preset.title()}</a>' for preset in ['lime','coral','cyan'])+'</div><details><summary>Desktop / teléfono exports</summary>'+''.join(f'<p>{preset.title()}: <a href="workflow-exports/{sid}-{preset}-en.jpg">EN desktop</a> · <a href="workflow-exports/{sid}-{preset}-es.jpg">ES teléfono</a></p>' for preset in ['lime','coral','cyan'])+f'</details><p class="compact">{s["presentation"]} · #{s["owner"]} · <a href="workflow-specification.md#{sid}">Fields and states</a></p></article>')
  parts.append('</div></section>')
 parts.append('<footer><a href="verification-review-06.md">Current rendered evidence</a> · <a href="before-after-map.md">Location and save ownership</a></footer></main></body></html>')
 (ROOT/'workflow-gallery.html').write_text('\n'.join(parts)+'\n')
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--pages-only',action='store_true',help='Refresh index/gallery without rebuilding historical specification appendices')
 if parser.parse_args().pages_only:
  render_pages(json.loads((ROOT/'workflow-data.json').read_text()),json.loads((ROOT/'navigation-map.json').read_text()))
 else:build()
