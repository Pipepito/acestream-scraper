"""The pinned source client sends Host first, where an ordinary client puts it.

The connection goes to a pinned address, so urllib3 does not add Host itself
and the adapter sets it. Appended after requests' default headers, a CDN
(Dailymotion's cdndirector) answered 403 to the same request a plain
``requests.get`` -- which sends Host first -- got 200 for.
"""
import requests

from app.utils.outbound_http import PinnedHTTPAdapter


def test_host_is_the_first_header():
    prepared = requests.Request('GET', 'https://cdn.example.com/x.m3u8',
                                headers={'User-Agent': 'UA', 'Sec-Fetch-Mode': 'cors'}).prepare()
    PinnedHTTPAdapter().add_headers(prepared)
    names = list(prepared.headers.keys())
    assert names[0] == 'Host' and prepared.headers['Host'] == 'cdn.example.com'
    assert names[1:] == ['User-Agent', 'Sec-Fetch-Mode']


def test_a_host_already_set_is_replaced_not_duplicated():
    prepared = requests.Request('GET', 'https://cdn.example.com:8443/x', headers={'host': 'other', 'A': '1'}).prepare()
    PinnedHTTPAdapter().add_headers(prepared)
    assert [key.lower() for key in prepared.headers.keys()] == ['host', 'a']
    assert prepared.headers['Host'] == 'cdn.example.com:8443'
