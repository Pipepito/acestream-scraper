"""Validate actual wire exchanges with the maintained OpenAPI 3.1 validator.

Consumer-only closed object checks detect keys Pydantic would ignore. This changes
neither the provider's compatibility policy nor intentionally extensible maps.
"""
import copy
import json
import sys
from pathlib import Path

import requests
from openapi_core import OpenAPI
from openapi_core.contrib.requests import RequestsOpenAPIRequest, RequestsOpenAPIResponse


def consumer_schema(schema):
    result = copy.deepcopy(schema)

    def close_declared_objects(value):
        if isinstance(value, dict):
            if value.get('type') == 'object' and 'properties' in value:
                value.setdefault('additionalProperties', False)
            for child in value.values():
                close_declared_objects(child)
        elif isinstance(value, list):
            for child in value:
                close_declared_objects(child)

    close_declared_objects(result.get('components', {}).get('schemas', {}))
    return result


def request_adapter(exchange):
    body = exchange.get('body')
    return RequestsOpenAPIRequest(requests.Request(
        method=exchange['method'], url=exchange['url'], headers=exchange.get('headers', {}),
        data=body.encode() if isinstance(body, str) else body,
    ).prepare())


def validate_response(api, request, status, headers, body):
    response = requests.Response()
    response.status_code = status
    response.headers.update(headers)
    response._content = body
    api.validate_response(request, RequestsOpenAPIResponse(response))


def main():
    schema = json.loads((Path(__file__).resolve().parents[1] / 'openapi.json').read_text())
    api = OpenAPI.from_dict(consumer_schema(schema))
    exchanges = json.load(sys.stdin)
    for exchange in exchanges:
        try:
            api.validate_request(request_adapter(exchange))
        except Exception as error:
            raise RuntimeError(f"{exchange.get('scenario', '')}: {exchange['method']} {exchange['url']}: {error}") from error
    print(f'Validated {len(exchanges)} actual consumer requests')


if __name__ == '__main__':
    main()
