# Stable categories and live genre discovery

Migration `20261109_1300` follows shared EPG identities (`20261109_1200`). It adds category ownership,
revision and evidence to TV channels, and ordered `epg_program_categories` rows
keyed by `(program_id, position)`. Existing scalar categories are backfilled;
deferred v1 programme migration backfills each resumable batch too. XML refresh
reconciles observations without replacing unchanged programme IDs. Cleanup removes
observations with their programmes. Downgrade retains the compatible first category
but necessarily drops additional observations and ownership.

`category_taxonomy.py` is the versioned classification authority. Exact reviewed
aliases and fully recognized compound labels produce genres; unknown source text
is retained. Channel identity and programme genres remain separate. Suggestions
use a UTC-midnight-anchored ±7-day window, at least twelve programmes over three
days, and at least 80% consistent broad classification for schedule evidence.
Neither programme titles nor arbitrary channel-name fragments classify a channel.

## API

- `GET /tv-channels/category-definitions`: standard editable channel categories.
- `GET /tv-channels/categories`: inventory under the usual browse filters, with
  `category_basis=channel|now`, server reference time and next guide boundary.
- `GET /tv-channels/browse`: accepts `category_id`, `category_basis` and `as_of`;
  membership is applied before sorting/counting/pagination.
- `GET /tv-channels/now-next`: accepts the same `as_of` as the live inventory.
- `POST /tv-channels/category-suggestions/preview`: read-only, ≤500 selected IDs.
- `POST /tv-channels/category-suggestions/apply`: exact selected fingerprints,
  revalidated under sorted database write claims; all rows commit or none do.
- `PUT /tv-channels/{id}/category`: manual assignment/clear or explicit automatic
  reset, with mandatory expected revision. The existing channel editor also sends
  an expected category revision and omits unchanged categories.
- `GET /tv-channels/category-coverage`: paged raw label/source counts, distinct
  programme/channel counts, normalized genres and artwork coverage over −7/+14 days.

All paths retain the standard management/authentication policy. Reference times
must be timezone-aware and within fifteen minutes. Catalogue membership is bounded
to 50,000 channels and guide reads to 100,000 programmes, failing explicitly rather
than returning partial totals. Guide projections share source-qualified enabled
mappings and reviewed event overlays with displayed Now/Next. Image lookup does not
perform server-side network requests.

Observation bounds are 64 categories per programme, 1024 characters per label and
50 per language. Exceeding them rolls back the source import, preserving existing
guide data. Recordings and event-overlay clipping retain the full observations.

The frontend's illustration registry remains a fallback library, not a classifier.
New taxonomy categories can ship before their specific artwork. Generated assets
in the current private preview remain subject to their separate publication hold.

## Focused checks

Run category/migration, EPG, event-overlay, recording and TV browse tests, then
frontend LiveTV, ChannelArtwork, ScheduleView, form and service-contract tests.
The full repository completion gate remains required. Use isolated data for
browser assignment/apply checks and preserve the selected viewer across filters.
