# Visual resources and immersive third interface

7 November 2026. **Owner-confirmed direction:** keep three interfaces and make the third substantially more immersive. The existing cyan proposal is its starting reference. This is approval of the direction and interface count, not approval of final artwork, tokens, typography or a rebrand. Asset production and the third interface's rendered composition remain implementation deliverables in #316/#319 and their feature owners.

## What the reference review established

The owner's authenticated supplier reference was inspected read-only in an isolated browser: login, viewing homepage and browsing rows, categories, category detail, channel/player detail without starting media, Sources, Dashboard, and the homepage at a 390 CSS-pixel phone viewport. The loaded Sources/Dashboard content was inspected as well as loading states. Only authentication was allowed to submit a request; no playback, favorites, extraction, settings or device action was performed. Browser credentials/cookies were discarded afterward. Raw captures, installation data and access details remain outside public artifacts.

Observed: a large photographic viewing banner; image-backed category tiles; portrait artwork cards in horizontal rows; warm primary controls on dark navy surfaces; a compact bottom navigation on phones; simpler forms/tables in administration. The visual vocabulary matches the previously supplied coral/navy frontend. The reference strengthens the case for meaningful artwork and composition; its appeal is not explained by palette alone.

Observed limits: generic sports imagery repeats across unrelated channel cards, some catalogue content is repeated between rows, and category detail changes to plain rows after the more visual category index. The large image treatment makes discovery inviting, but repeated generic pictures are weak channel identifiers. These are design observations, not measured usability or performance regressions. Dark desktop and an emulated phone were inspected; light theme, actual assistive technology, real-device performance and mutation/error paths were not assessed. No whole-product heuristic score or accessibility-conformance claim is assigned to this limited review.

Owner preference: the current proposals need more visual resources, and a richer experience is welcome despite the reference being somewhat excessive. The current 144-workflow package remains useful for fields, transactions and states, but does not by itself satisfy this visual ambition. Existing coral/lime prototype controls are not three completed interfaces.

## Confirmed scope and proposed composition

Keep the lime and coral/navy references and develop the **third, cyan-based interface as the immersive choice**. Share an artwork library, content identity, components and services across all three. Vary image prominence, density and composition; do not build three disconnected catalogues or hide management capabilities in the immersive choice. The first two also need deliberate logos, programme artwork and useful empty states where appropriate.

| Surface | Concrete third-interface treatment | Guardrails |
|---|---|---|
| Home | One featured programme/channel with a wide still, original title, channel identity, time/availability and one clear Watch action. Follow with Favorites and On now, then a short category section. | Keep search and the route to the full catalogue obvious. Feature selection must be explained by real data or explicit editorial choice, not invented personalization. No automatic video or rotating essential content. |
| Browse/categories | Landscape genre artwork, readable category names and channel counts; compact channel/logo rows within a chosen category, with optional richer programme cards where actual artwork exists. | Represent general TV, including news, film, documentary, family, culture and music. Preserve the source's actual taxonomy; broad artwork families do not rename or merge user categories. |
| Live TV | A deliberate player-and-catalogue composition with channel logos, Now/Next and current programme imagery where available. | The media player retains ownership and mount continuity when artwork, filters, locale or interface choice changes. Artwork must not look like a verified live frame. |
| Programme/channel detail | A landscape artwork header, legible title/metadata, schedule and clearly grouped Watch/Record/remote actions. Channel identity stays distinct from programme artwork. | Preserve all actual actions and permissions. Opening details must not start playback or recording. Artwork failure leaves the programme, schedule and actions usable. |
| Events/recordings | Richer event and recording cards using trustworthy associated artwork; source-qualified schedule and ready/partial/protected states remain prominent. | Preserve the existing explicit event-artwork load action. Do not silently generate recording thumbnails or use unrelated photos as recording frames. |
| Phone | A deliberately cropped still above compact title/actions; nearby Favorites and catalogue/search access; horizontally browsable rows only where their controls remain reachable. | Keep the primary action and next navigation choice within a practical first screen. Use declared focal points, visible keyboard focus, scroll padding and no background video. Test long EN/ES titles. |
| Settings/management | Retain the third interface's type, spacing, controls and color roles in a calmer layout. Use small original illustrations only for useful setup/empty/error explanations. | Photographic backgrounds must not compete with fields, operational status or consequential confirmations. All administration remains fully supported. |

The initial review set within #316/#319 must show **Home, Browse/categories, Live TV, programme detail, recordings/events and one representative management screen**, with populated and missing-artwork examples. Compose the same synthetic content in all three interfaces for comparison, in both themes and languages and on desktop/phone. This is part of implementation, not a new prerequisite standalone audit round.

## Initial asset set to produce

This is a concrete production brief, not a claim that the assets already exist. Reuse supplied material only after its provenance and redistribution rights are verified; otherwise commission, license or generate original alternatives. Keep the application identity and avoid copying the supplier's brand mark.

| Asset family | Initial deliverable | Intended use and art direction |
|---|---|---|
| General-TV genre artwork | Eight original concepts: news/current affairs, film/drama, documentary/nature, entertainment/culture, family, music, sport, regional/community; plus one neutral fallback | Recognizable subjects and a cohesive photographic/illustrative treatment. Avoid sports scenes for unrelated genres and baked-in interface text. These are broad visual families, not a new mandatory category taxonomy. |
| Featured viewing | Three reviewed wide compositions from appropriate genre concepts, with separately checked phone crops | Reserve quiet space for real text; establish focal points. Example fictional content: a coastal documentary, a studio music performance and a community/culture programme. Generic imagery is labelled as illustrative when its role could be mistaken. |
| Card crops | Reviewed 16:9 landscape and, where useful, 3:4 portrait treatments | Do not blindly crop every image into every ratio. Distinct channel identity comes from the actual logo/name, not randomly assigned generic art. |
| Operational illustrations | Four small original SVG illustrations: first source, no guide data, no recordings and connection unavailable | Explain a next step. Use simple shapes consistent with the selected interface; no large decorative illustration above every form. |
| Identity and controls | Existing trusted icon system, genuine channel logos where supplied, and neutral logo placeholders | Keep logos readable on light and dark surfaces without recoloring third-party marks. Do not use an illustration to imply availability, permission or verified signal. |

For every shipped asset record a stable ID, purpose, origin/creator, redistribution terms, attribution requirements, selected source, dimensions/aspect ratio, focal point, crop variants, byte size, light/dark treatment, decorative versus informative role, and fallback. Keep masters and production-size exports separate; commit only selected distributable web assets and their provenance manifest. Do not import the supplier archive or its full media library.

Use responsive static WebP or another already-supported format with explicit dimensions and sensible `srcset`/`sizes`. Load the selected hero deliberately; defer offscreen artwork. Measure transferred bytes, decode cost, image-driven layout shift and request duplication on fixed small/large synthetic catalogues before setting final budgets. Background video is not part of the default requirement. Respect reduced motion and data-saving choices; a static image must convey everything needed.

## Identity, fallback and security contract

Choose artwork by stable channel/programme/event identity. For programme cards prefer the actual programme's artwork, then a valid channel logo or an explicitly illustrative genre fallback, then a neutral placeholder. A channel logo remains a logo; do not stretch it into a photographic background. Provider artwork and generic editorial art have different meanings and must remain distinguishable.

Cover absent, rejected, blocked, slow, oversized, failed-to-decode, expired and changed artwork. Reserve dimensions before loading. Keep names and primary actions usable independently. Preserve original content titles; translate surrounding labels and informative alternative text with EN/ES resources. Decorative images use empty alternative text, and informative ones must not repeat the same caption needlessly. Never embed translated interface text into the artwork.

All themes and crops need readable overlays, non-color status cues and visible focus. Artwork must not be used as a full-screen background behind operational forms. Keep remote image handling bounded and authenticated where appropriate; never expose credentials/source URLs in public captures or introduce an unrestricted image proxy.

## Current source support and backend work

Source evidence at `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`:

- [TV channel `logo_url`](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/types/tvChannelTypes.ts#L5) already exists. Preserve TV-channel versus underlying-stream identity when choosing it.
- [EPG programme `image_url`](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L72) is already represented; [XMLTV ingestion](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/services/epg_xmltv.py#L127) reads programme icons and export retains them. End-to-end delivery through the selected viewing queries still needs implementation verification.
- [Event observations](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L110) carry `artwork_url`; an existing [artwork endpoint](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/api/endpoints/events.py#L164) uses the bounded [fetcher](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/services/event_artwork.py). It allows small PNG/JPEG/static WebP, caps bytes at 512 KiB, dimensions at 4096 per side and four million pixels, uses two slots and a ten-second fetch timeout, and preserves the guarded outbound boundary.
- [EventArtwork](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventArtwork.tsx) currently loads only after an explicit action and handles load/decode failure. Preserve this behavior in all three interfaces unless an intentional policy change is separately reviewed. Richer design is not permission to make every remote image load automatically.

Therefore, do not assume a new artwork backend is necessary. First connect and test existing capabilities, then fix demonstrated gaps in ingestion, identity, response mapping, security, caching or rendering. New contracts still require schemas/generated clients/tests; persisted crop/attribution metadata, if actually needed, requires the normal schema/migration review. Synthetic hero rendering is not proof that real programme metadata reaches the application correctly.

## Existing task ownership and acceptance

| Task | Added deliverable / evidence |
|---|---|
| #316 | Produce the selected artwork library/provenance manifest and shared image treatments; develop the immersive third interface and concrete comparison compositions. Keep three interfaces. |
| #317 | EN/ES captions, appropriate alternative text and original-title preservation; test expansion over every relevant image crop. |
| #318 | Selector preview/descriptions must explain the real differences in image prominence/density. Preserve preference, drafts, focus and pending operations during switching. |
| #319 | Implement richer Home/browsing/Live TV/event/recording compositions using actual metadata and honest missing-art states; preserve media ownership and explicit event-artwork loading. |
| #320 | Verify channel logos, programme image ingestion/query/export and stable identity; correct demonstrated supporting API/service gaps. |
| #321/#322 | Apply the third interface consistently to sources, integrations and system administration with restrained imagery and complete functional parity. |
| #323 | Measure artwork transfer/decode/layout cost, lazy loading and three-interface switching; verify no duplicate downloads/media sessions. No measured slowdown is claimed by this review. |
| #324 | Verify representative compositions and every image state across three interfaces, languages/themes and responsive layouts; include rights, contrast/crops, real AT/device evidence and unavailable-artwork behavior. Recheck the existing Pages release-status 404 separately. |

Read-only reference review and source inspection are complete. **The new asset pack, final art direction and rendered immersive interface are still to be produced and validated during implementation.** The current public prototype and its previous test counts do not establish those results.
