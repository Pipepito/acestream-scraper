"""Document middleware-enforced conditional access without changing enforcement.

OpenAPI security cannot express installation mode, permission, private transport,
or media ownership. The extensions describe those constraints; semantic tests must
exercise the real middleware in addition to schema validation.
"""
from fastapi.openapi.utils import get_openapi
from app.schemas.errors import ErrorResponse, HTTPErrorCodeHeader
from app.services.access_service import COOKIE


def installation_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    components = schema.setdefault('components', {})
    models = components.setdefault('schemas', {})
    error = ErrorResponse.model_json_schema(ref_template='#/components/schemas/{model}')
    models.update(error.pop('$defs', {}))
    models['ErrorResponse'] = error
    models['HTTPProblem'] = {
        'type': 'object', 'required': ['detail'], 'properties': {
            'detail': {'anyOf': [{'type': 'string'}, {'type': 'object', 'additionalProperties': True},
                                  {'type': 'array', 'items': {'type': 'object', 'additionalProperties': True}}]},
            'status': {'type': 'string'},
        },
    }
    components['securitySchemes'] = {
        'HeaderToken': {'type': 'apiKey', 'in': 'header', 'name': 'X-Api-Token', 'description': 'Legacy API token or scoped administrative credential; scopes depend on access mode.'},
        'BearerToken': {'type': 'http', 'scheme': 'bearer', 'description': 'Legacy API token or scoped credential; not interchangeable with viewer capabilities.'},
        'LegacyQueryToken': {'type': 'apiKey', 'in': 'query', 'name': 'token', 'description': 'Legacy open-mode token or playback credential. Never grants account-mode management access.'},
        'AccountSession': {'type': 'apiKey', 'in': 'cookie', 'name': COOKIE},
        'CSRF': {'type': 'apiKey', 'in': 'header', 'name': 'X-CSRF-Token', 'description': 'Must match the CSRF cookie; account writes also require same-origin requests.'},
    }
    schema['security'] = [{}, {'HeaderToken': []}, {'BearerToken': []}, {'LegacyQueryToken': []}, {'AccountSession': []}]
    schema['x-installation-access'] = {
        'open': 'No credential only when accounts and API_TOKEN are disabled.',
        'accounts': 'Management is default-deny; administrator required unless an explicit viewer/media capability applies.',
        'csrf': 'Cookie-authenticated mutations require X-CSRF-Token matching scraper_csrf and same origin. Login/bootstrap always require CSRF.',
        'constraints': 'Account transport, permission scopes, IPTV and exact media ownership are enforced independently of schema validation.',
    }
    code_header = HTTPErrorCodeHeader.model_json_schema(by_alias=True)['properties']['X-Error-Code']
    shared_responses = components.setdefault('responses', {})
    for path, item in schema['paths'].items():
        if not path.startswith('/api/'):
            continue
        for method, operation in item.items():
            if method not in {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}:
                continue
            if path == '/api/v1/health':
                operation['security'] = []
                continue
            operation['x-access-class'] = 'delegated' if path.startswith(('/api/v1/auth/', '/api/v1/view/', '/api/v1/viewers/', '/api/v1/cast/', '/api/v1/startup')) else 'management'
            if path in {'/api/v1/auth/login', '/api/v1/auth/bootstrap'} and method == 'post':
                operation['security'] = [{'CSRF': []}]
            responses = operation.setdefault('responses', {})
            statuses = {401: 'Missing or invalid credentials', 403: 'Permission, origin, CSRF or transport denied',
                        503: 'Startup, access storage or required service unavailable', 500: 'Unexpected application failure'}
            if path.startswith(('/api/v1/recordings', '/api/v1/tv-channels', '/api/v1/acestream-channels', '/api/v1/channels', '/api/v1/setup')):
                statuses.update({400: 'Invalid operation or empty update', 404: 'Resource not found', 409: 'Stale state, conflict or admission rejected', 422: 'Invalid request fields'})
            if path.startswith(('/api/v1/auth/', '/api/v1/cast/')):
                statuses.update({404: 'Resource not found', 408: 'Request timed out', 409: 'State conflict or confirmation required',
                                 413: 'Request too large', 422: 'Invalid request fields', 429: 'Rate or capacity limit',
                                 502: 'Receiver rejected the operation', 504: 'Receiver preparation timed out'})
            for status, description in statuses.items():
                # Preserve explicit route documentation and validation schemas.
                existing = responses.get(str(status), {})
                declared = existing.get('content', {}).get('application/json', {}).get('schema')
                alternatives = [{'$ref': '#/components/schemas/HTTPProblem'}, {'$ref': '#/components/schemas/ErrorResponse'}]
                if declared and declared not in alternatives:
                    alternatives.append(declared)
                response = {**existing, 'description': existing.get('description', description),
                    'content': {'application/json': {'schema': {'anyOf': alternatives}}},
                    'headers': {**existing.get('headers', {}), 'X-Error-Code': {'schema': code_header, 'required': False}}}
                if not existing or (status == 422 and declared == {'$ref': '#/components/schemas/HTTPValidationError'}):
                    key = f'ApplicationProblem{status}' + ('Validation' if existing else '')
                    shared_responses[key] = response
                    responses[str(status)] = {'$ref': f'#/components/responses/{key}'}
                else:
                    responses[str(status)] = response
    app.openapi_schema = schema
    return schema
