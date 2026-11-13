"""Design reference integrity against pinned OpenAPI 3.1. No API execution.
--check compares generated references; --self-test tests rejection of bad references.
This is NOT a JSON Schema validator or proof of provider/consumer conformance.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REV = 'cf952afc6b4489c02b7a675ff3d634cc13d98e0b'
# Human-reviewed mappings from existing service boundaries to available operations.
MAP = {
    'accessService.bootstrap': ['POST /auth/bootstrap'],
    'accessService.createUser': ['POST /auth/users'],
    'accessService.disable': ['POST /auth/disable'],
    'accessService.issueCredential': ['POST /auth/credentials'],
    'accessService.login': ['POST /auth/login'],
    'accessService.password': ['PUT /auth/password'],
    'accessService.savePolicy': ['PUT /auth/policy'],
    'accessService.updateUser': ['PUT /auth/users/{user_id}'],
    'baseUrlService.createBaseUrl': ['POST /base-urls'],
    'baseUrlService.updateBaseUrl': ['PATCH /base-urls/{base_url_id}'],
    'castService.command': ['POST /cast/sessions/{cast_id}/commands'],
    'castService.saveSettings': ['PUT /cast/settings'],
    'castService.trustHome': ['POST /cast/home-connection'],
    'catalogueService folder assignment': ['POST /catalogues/{catalogue_id}/folders/{entry_id}/tv-channel'],
    'catalogueService preview': ['POST /catalogues/preview'],
    'catalogueService save': ['POST /catalogues'],
    'channelService bulk commands': ['POST /channels/bulk_activate', 'POST /channels/bulk_delete'],
    'channelService query': ['GET /channels/'],
    'channelService.create': ['POST /channels/'],
    'BulkChannelEditRequest': ['PUT /channels/bulk_edit'],
    'configService ace-engine-url': ['PUT /config/ace_engine_url'],
    'configService check-engine': ['PUT /config/check-engine'],
    'configService epg-matching': ['PUT /config/epg-matching'],
    'configService independent setting: links.add_pid': ['PUT /config/addpid'],
    'configService independent setting: links.app_id': ['PUT /config/appid'],
    'configService independent setting: schedule.channel_status_interval': ['PUT /config/{key}'],
    'configService independent setting: schedule.epg_refresh_interval': ['PUT /config/epg_refresh_interval'],
    'configService independent setting: schedule.rescrape_interval': ['PUT /config/rescrape_interval'],
    'configService notification-webhook': ['PUT /config/notification_webhook_url'],
    'configService offline-cleanup': ['PUT /config/offline-cleanup'],
    'configService playback-routing': ['PUT /config/playback-routing'],
    'configService public-base-url': ['PUT /config/public_base_url'],
    'configService schedule-anchors': ['PUT /config/schedule-anchors'],
    'configService stream-check-scope': ['PUT /config/stream-check-scope'],
    'epgService inventory': ['GET /epg/channels/{channel_id}/programs'],
    'epgService stringMappings': ['POST /epg/channels/{channel_id}/mappings', 'PATCH /epg/mappings/{mapping_id}'],
    'epgService.createSource / updateSource': ['POST /epg/sources', 'PATCH /epg/sources/{source_id}'],
    'epgService.generateXml': ['POST /epg/xml'],
    'EventApply.refresh_source': ['POST /events/apply'],
    'eventService broadcaster mapping': ['PATCH /events/{event_id}/broadcast'],
    'eventService overlay preview': ['POST /events/{event_id}/guide-overlays/preview'],
    'eventService preview': ['POST /events/preview'],
    'eventService provider preview': ['POST /events/preview'],
    'eventService retention': ['PATCH /events/retention'],
    'eventService.update': ['PATCH /events/{event_id}'],
    'guideSetupService preview': ['POST /tv-channels/automatch/preview'],
    'TVMatchOptions preview': ['GET /tv-channels/{tv_channel_id}/acestream-matches'],
    'importExclusionService save': ['POST /import-exclusions', 'PATCH /import-exclusions/{rule_id}'],
    'mediaServerService create / update': ['POST /media-servers', 'PATCH /media-servers/{server_id}'],
    'playerService shared viewer lifecycle': ['POST /viewers', 'GET /viewers/{viewer_id}', 'DELETE /viewers/{viewer_id}'],
    'recipeService.fetch': ['POST /scrapers/recipes/sample'],
    'recipeService.preview / standalone worker': ['POST /scrapers/recipes/preview'],
    'recordingService.configure': ['PUT /config/recordings'],
    'recordingService.convert': ['POST /recordings/{rid}/conversions'],
    'recordingService.create': ['POST /recordings'],
    'recordingService.create / edit': ['POST /recordings', 'PATCH /recordings/{rid}'],
    'recordingService.edit': ['PATCH /recordings/{rid}'],
    'recordingService.list': ['GET /recordings'],
    'remotePlayerService create / update': ['POST /remote-players', 'PATCH /remote-players/{player_id}'],
    'remotePlayerService.command': ['POST /remote-players/{player_id}/command'],
    'remotePlayerService.finishAndroidPairing': ['POST /remote-players/android/pair/finish'],
    'remotePlayerService.scan': ['POST /remote-players/scan'],
    'runtime setup API': ['GET /setup', 'PUT /setup'],
    'setupService.update expected_revision': ['PUT /setup'],
    'startupService recovery': ['POST /startup/recover'],
    'savedSearchService save': ['POST /saved-searches', 'PATCH /saved-searches/{search_id}'],
    'scraperService createURL / updateURL': ['POST /scrapers/urls', 'PATCH /scrapers/urls/{url_id}'],
    'DELETE scrapers/urls/{id}?delete_streams=': ['DELETE /scrapers/urls/{url_id}'],
    'searchService.resolve + import tv_channel_id': ['POST /search/{infohash}/resolve', 'POST /search/import'],
    'searchService.search': ['GET /search'],
    'SetupGuide → EPGSourceDialog': ['POST /epg/sources'],
    'SetupSources → source editor': ['POST /scrapers/urls'],
    'telegramService code': ['POST /telegram/code'],
    'telegramService login': ['POST /telegram/login'],
    'telegramService password': ['POST /telegram/password'],
    'telegramService source': ['POST /telegram/sources', 'PUT /telegram/sources/{source_id}'],
    'tunerService.updateSettings': ['PUT /tuner/settings'],
    'tvChannelService.create / update': ['POST /tv-channels/', 'PUT /tv-channels/{tv_channel_id}'],
    'TVChannelUpdate.channel_number': ['PUT /tv-channels/{tv_channel_id}'],
    'TVChannelUpdate.is_favorite': ['POST /tv-channels/{tv_channel_id}/favorite'],
    'usePlaylistLink / playlistService': ['GET /playlists/m3u', 'POST /view/playlists'],
    'warpService exclusions': ['PUT /warp/exclusions'],
    'warpService.registerLicense': ['POST /warp/license'],
    'warpService.setMode': ['POST /warp/mode'],
    'source-only contract mismatch → TVChannelUpdate': ['PUT /tv-channels/{tv_channel_id}'],
}
LOCAL = {
    'LiveTV URL state',
    'RecipeBuilder source selection',
    'apiToken browser credential',
    'eventPreferences',
    'local URL / catalogue query',
    'local catalogue view',
    'player channel picker',
    'proposed browser preference resource',
    'proposed form dirty guard',
    'readEventPreferences / writeEventPreferences',
    'standalone recipe worker',
}
# Non-form commands, read-only resources and binary/media boundaries are tracked too.
EXTRA = {
    'channel-reorder': ['POST /tv-channels/reorder'],
    'channel-preferences': ['POST /tv-channels/{tv_channel_id}/acestreams/reorder'],
    'guide-match': ['POST /tv-channels/automatch/preview', 'POST /tv-channels/automatch/apply'],
    'guide-choice': ['GET /epg/channels/resolve'],
    'guide-coverage': ['GET /playlists/guide-coverage'],
    'live': ['GET /view/live', 'GET /tv-channels/now-next', 'POST /viewers', 'DELETE /viewers/{viewer_id}'],
    'dashboard': ['GET /view/live', 'GET /tv-channels/now-next'],
    'event-detail': ['GET /events/{event_id}/artwork'],
    'recording-cancel': ['POST /recordings/{rid}/cancel'],
    'recording-active': ['POST /recordings/{rid}/stop'],
    'recording-delete': ['DELETE /recordings/{rid}'],
    'recording-parts': ['POST /recordings/{rid}/playback-sessions', 'GET /recordings/{rid}/files/{fid}'],
    'access-sessions': ['GET /auth/sessions', 'DELETE /auth/sessions/{session_id}'],
    'access-credentials': ['GET /auth/credentials', 'DELETE /auth/credentials/{credential_id}'],
    'storage': ['GET /system/storage'],
    'diagnostics': ['GET /system/diagnostics'],
    'jobs': ['GET /background-tasks/status'],
    'services': ['GET /system/services', 'POST /system/services/{name}/restart'],
    'warp': ['GET /warp/status', 'POST /warp/connect', 'POST /warp/disconnect'],
    'sources-orphans': ['GET /scrapers/orphaned-sources', 'POST /scrapers/orphaned-sources/cleanup'],
    'source-results': ['POST /scrapers/urls/{url_id}/scrape'],
}


def pointer(doc, ref):
    assert ref.startswith('#/'), ref
    value = doc
    for bit in ref[2:].split('/'):
        value = value[bit.replace('~1', '/').replace('~0', '~')]
    return value


def operation(doc, ref):
    method, path = ref.split(' ', 1)
    path = '/api/v1' + path
    assert path in doc['paths'], ref
    assert method.lower() in doc['paths'][path], ref
    return method, path, doc['paths'][path][method.lower()]


def refs(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if k == '$ref':
                yield v
            else:
                yield from refs(v)
    elif isinstance(value, list):
        for v in value:
            yield from refs(v)


def build():
    raw = subprocess.check_output(['git', 'show', REV + ':backend/openapi.json'], cwd=ROOT)
    doc = json.loads(raw)
    workflows = json.loads((ROOT / 'workflow-data.json').read_text())
    schemas = doc['components']['schemas']
    ops = []
    bindings = []
    fields = []
    for path, methods in doc['paths'].items():
        for method, op in methods.items():
            if method not in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                continue
            for ref in refs(op):
                pointer(doc, ref)
            ops.append(dict(method=method.upper(), path=path, operationId=op['operationId'], parameters=op.get('parameters', []), requestBody=op.get('requestBody'), responses=op.get('responses'), security=op.get('security', doc.get('security', 'not described in schema'))))
    for s in workflows['screens']:
        for b in s['blocks']:
            if 'api' not in b:
                continue
            api = b['api']
            assert api in MAP or api in LOCAL, api
            mapped = []
            for ref in MAP.get(api, []):
                method, path, op = operation(doc, ref)
                mapped.append(dict(method=method, path=path, operationId=op['operationId']))
            bindings.append(
                dict(
                    workflow=s['id'],
                    editor=b.get('id'),
                    adapter=api,
                    kind='local presentation/worker; no endpoint' if api in LOCAL else 'available operation reference; adapter still requires future executable contract test',
                    operations=mapped,
                    saveTiming=b.get('saveTiming', 'explicit action'),
                    owner=s['owner'],
                    notes='Generic config key is channel_status_interval' if 'channel_status_interval' in api else 'Installed preview only; standalone worker remains local' if 'standalone worker' in api else '',
                )
            )
            for f in b.get('fields', []):
                matches = []
                contract = f.get('contract', '')
                if contract:
                    _, model, key = contract.rsplit('.', 2)
                    for schema_name, schema in schemas.items():
                        if (schema_name == model or schema_name.endswith('__' + model)) and key in schema.get('properties', {}):
                            ref = '#/components/schemas/' + schema_name + '/properties/' + key
                            pointer(doc, ref)
                            matches.append(ref)
                fields.append(
                    dict(
                        workflow=s['id'],
                        editor=b.get('id'),
                        field=f['key'],
                        source_contract=contract or None,
                        schema_properties=matches,
                        interpretation='Exact source-model field reference; request envelope/transformation still follows adapter' if matches else 'Presentation/derived/runtime field or adapter mapping documented in workflow specification; no inferred wire key',
                        owner=s['owner'],
                    )
                )
        if s['id'] in EXTRA:
            bindings.append(dict(workflow=s['id'], editor='context / commands', adapter='source-backed resource', kind='available operation reference', operations=[dict(method=operation(doc, x)[0], path=operation(doc, x)[1], operationId=operation(doc, x)[2]['operationId']) for x in EXTRA[s['id']]], owner=s['owner']))
    return doc, dict(source_revision=REV, openapi_version=doc['openapi'], schema_sha256=hashlib.sha256(raw).hexdigest(), scope='Design reference integrity only; no provider, consumer, payload or runtime validation', operations=ops, bindings=bindings, fields=fields)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    doc, data = build()
    path = ROOT / 'openapi-contract-map.json'
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert path.read_text() == text, 'Contract reference drift; regenerate and review'
    else:
        path.write_text(text)
    rejected = 0
    if args.self_test:
        for fn in [lambda: operation(doc, 'POST /made-up'), lambda: operation(doc, 'DELETE /config/playback-routing'), lambda: pointer(doc, '#/components/schemas/PlaybackRouting/properties/imaginary')]:
            try:
                fn()
            except (AssertionError, KeyError):
                rejected += 1
        assert rejected == 3
    print(json.dumps(dict(operations=len(data['operations']), bindings=len(data['bindings']), field_references=len(data['fields']), exact_schema_fields=sum(bool(f['schema_properties']) for f in data['fields']), negative_reference_checks=rejected, scope=data['scope']), indent=2))


if __name__ == '__main__':
    main()
