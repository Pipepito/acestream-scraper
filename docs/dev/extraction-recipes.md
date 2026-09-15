# Extraction recipe implementation

The user guide is [Extraction recipes](../../wiki/Extraction-Recipes.md).

## Shared authoring UI

`frontend/src/recipes/RecipeBuilder.tsx` provides authoring, catalogue selection,
raw/visual/JSON selection, review and import/export. The installed page supplies
fetch, backend-preview and save adapters. The standalone entry supplies a local
worker-preview adapter and has no API client or connection to a user installation.
`npm --prefix frontend run build:recipes` outputs `frontend/dist-recipes/`.
The normal frontend build validates both entry points.

`docs/index.html` is the user hub. Its Docker setup, Extraction builder and Docs
sections use hash navigation managed by `docs/builder/hub.js`. The extraction
section lazily mounts `recipes/?embedded=1` in a same-origin iframe and retains
it when switching sections. The embedded entry shares the host's color preference
and reports its content height; the host checks message origin and source before
resizing. Direct `/recipes/` access remains supported. Docs link to the wiki
until a separate documentation migration moves that content into the hub.

The static catalogue lives in `frontend/src/recipes/catalogue.json`. Entries have
an ID, description, author, minimum app version, recipe version, dated fixture
check, sanitized sample and expected channel pairs. Backend and browser unit tests
consume the same fixtures. Add a reviewed contribution there; never add secrets or
real authenticated page dumps. Catalogue recipes are copied on import, not remotely
executed or automatically updated.

## Runtime contract

`ExtractionRecipe` schema version 1 contains `name`, `version`, `mode`
(`html|regex|json`), `records`, `flags`, and `fields`. Required fields are `name` and
`id`; optional fields are `group`, `logo`, `epg_id`. Each field contains `selector`,
`attribute`, `path`, `pattern`. Unknown properties and unsupported versions fail.
A nullable JSON `scraped_urls.extraction_recipe` column is introduced by revision
`20260914_1200`; null preserves automatic scraping. PATCH with null restores auto.
Re-adding an existing URL without a recipe property preserves its recipe.

`POST /api/v1/scrapers/recipes/sample` accepts `url` and `url_type`, returns a
bounded `sample`, and writes nothing. Native IPFS/IPNS and ZeroNet sources resolve
through their configured gateways. Source fetches reject URL userinfo, validate
redirects, and pin the exact validated resolver addresses to aiohttp connections.
Requests use normal API-token enforcement, two concurrent slots and 20-second
per-request deadlines, at most six requests, and 32 MiB of decompressed data.
All source transports share `app/utils/outbound_http.py`: its async client covers
HTTP, gateway, iframe and nested playlist requests; its synchronous adapter covers
EPG. The final resolved addresses are validated before connection, redirects are
checked, and original Host/SNI/certificate identity is preserved. Source sessions
do not inherit environment proxies. Private-source defaults and gateway exemptions
remain compatible with existing LAN installations.

`POST /api/v1/scrapers/recipes/preview` accepts `recipe` and `sample`, returns
channels, counts and row issues, and writes nothing. Normal custom source scraping
uses the same production extractor. Failed or partially invalid extraction stops
before persistence; successful recipes upsert without deleting absent source IDs.

Python matching runs in a disposable child with a 15-second wall deadline,
two concurrent slots, and on Linux 1 GiB address-space/10-second CPU limits.
The child receives only the recipe/sample and a minimal environment. No DB or
network client is imported by the worker. The subprocess is killed and reaped on
timeout. The standalone uses a terminable Web Worker with a 15-second deadline;
HTML record materialization occurs in an inert DOM before field matching, only
after a 2 MiB/20,000-markup-delimiter preflight. Larger samples use raw regex,
manual JSON paths or the installed extractor. Preview request admission (two slots),
optional token checking, bounded temporary spooling and a 30-second upload deadline
precede JSON parsing. The envelope cap is 64 MiB + 128 KiB; decoded source remains 32 MiB. Both
runtimes cap output to 1,000 channel IDs. Python uses ASCII regex character classes
for browser compatibility. Browser/Python parsing differences remain possible for
malformed HTML; the installed backend is authoritative, and sample tests are never
labelled as live-source verification.

## Preview isolation

The visual picker reconstructs an allowlisted HTML snapshot in an iframe with
`sandbox="allow-same-origin"` and no `allow-scripts`. Parent-owned handlers inspect
selections. CSP blocks scripts, network resources, form submission and base URLs.
Untrusted event handlers, embedded documents, forms and hidden/password fields are
removed. Links retain their values as data for the picker but cannot navigate.
Original input is retained separately for extraction; sanitized DOM is presentation
only. Do not add `allow-scripts` or fetch remote styles without a new security review.

## Publication

GitHub Pages serves the committed `docs/` folder on `main`. Run
`bash scripts/ci/prepare_pages.sh` after installing frontend dependencies to build
and replace `docs/recipes/`; commit that generated payload with its source changes.
Full CI compares it with the fresh frontend build using `prepare_pages.sh --check`.
Recipe UI, theme, entry/config and frontend dependency changes require application
validation. Jenkins does not publish Pages or write a production version label;
the tools page keeps its neutral release hint when no promotion metadata exists.
No public URL-fetch proxy is provided.

Checks:

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_extraction_recipes.py
npm --prefix frontend test -- --runInBand src/recipes/engine.test.ts src/__tests__/RecipeBuilder.test.tsx
npm --prefix frontend run build:recipes
```
