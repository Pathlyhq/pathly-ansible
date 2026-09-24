# -*- coding: utf-8 -*-
"""Unit tests for pathly_api HTTP client and helpers."""

from __future__ import absolute_import, division, print_function

import json
from io import BytesIO
from urllib.error import HTTPError, URLError

import pytest

from ansible_collections.pathlyhq.pathly.plugins.module_utils import pathly_api as api


class FakeResponse(object):
    def __init__(self, body=b"{}", status=200, headers=None, use_getcode=False):
        if isinstance(body, dict):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self._body = body
        self.headers = headers if headers is not None else {}
        if use_getcode:
            self._code = status
        else:
            self.status = status

    def read(self):
        return self._body

    def getcode(self):
        return self._code


class FakeOpener(object):
    def __init__(self, queue):
        self.queue = list(queue)
        self.requests = []

    def open(self, req, timeout=None):
        self.requests.append((req, timeout))
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _http_error(code, body=b"{}", headers=None):
    return HTTPError(
        "https://api.pathlyhq.com/v1/x",
        code,
        "err",
        headers or {},
        BytesIO(body if isinstance(body, bytes) else body.encode("utf-8")),
    )


def test_pathly_api_error_not_found():
    err = api.PathlyAPIError("missing", status_code=404, path="/v1/x")
    assert err.not_found is True
    assert api.is_not_found(err) is True
    assert api.is_not_found(ValueError("x")) is False
    assert api.PathlyAPIError("no", status_code=400).not_found is False


def test_field_of_variants():
    assert api._field_of([]) == "body"
    assert api._field_of(None) == "body"
    assert api._field_of(["events", 0.0, "name"]) == "events.0.name"
    assert api._field_of(["only"]) == "only"


def test_parse_api_error_shapes():
    err = api._parse_api_error(
        400,
        "/v1/x",
        json.dumps(
            {
                "error": "Invalid body",
                "details": [
                    {"path": ["events", 0], "message": "bad"},
                    "skip-me",
                    {"path": [], "message": "root"},
                ],
            }
        ).encode("utf-8"),
    )
    assert "Invalid body" in err.message
    assert "events.0" in err.message
    assert "body" in err.message

    raw = api._parse_api_error(500, "/v1/x", b"not-json{")
    assert "not-json" in raw.message

    empty = api._parse_api_error(418, "/v1/x", b"   ")
    assert "HTTP 418" in empty.message

    unauth = api._parse_api_error(401, "/v1/x", b'{"error":"no"}')
    assert "PATHLY_API_TOKEN" in unauth.message

    forbid = api._parse_api_error(403, "/v1/x", b'{"error":"no"}')
    assert "scopes" in forbid.message


def test_backoff_and_wait_for_retry():
    assert api._backoff(2) == 1.0
    assert api._wait_for_retry(None, 1) == 0.5
    assert api._wait_for_retry({}, 2) == 1.0
    assert api._wait_for_retry({"Retry-After": "10"}, 1) == 10.0
    assert api._wait_for_retry({"retry-after": "100"}, 1) == 90.0
    assert api._wait_for_retry({"Retry-After": "0"}, 3) == 1.5
    assert api._wait_for_retry({"Retry-After": "nope"}, 1) == 0.5
    assert api._wait_for_retry({"Retry-After": None}, 1) == 0.5


def test_headers_to_dict():
    assert api._headers_to_dict(None) == {}
    assert api._headers_to_dict({"a": "1"}) == {"a": "1"}

    class BadMapping(object):
        def keys(self):
            raise TypeError("no")

    assert api._headers_to_dict(BadMapping()) == {}

    class OkMapping(object):
        def keys(self):
            return ["a"]

        def __getitem__(self, key):
            return "1"

    assert api._headers_to_dict(OkMapping()) == {"a": "1"}


def test_resolve_auth_and_build_client():
    token, url = api.resolve_auth(
        {}, environ={"PATHLY_API_TOKEN": " sp_x ", "PATHLY_API_URL": "https://example/"}
    )
    assert token == "sp_x"
    assert url == "https://example"

    token2, url2 = api.resolve_auth(
        {"api_token": "sp_p", "api_url": "https://custom"},
        environ={},
    )
    assert token2 == "sp_p"
    assert url2 == "https://custom"

    token3, url3 = api.resolve_auth({}, environ={})
    assert token3 == ""
    assert url3 == api.DEFAULT_API_URL

    warnings = []
    client = api.build_client(
        {"api_token": "sp_y"},
        warn_callback=warnings.append,
        environ={},
        opener=FakeOpener([]),
        sleep=lambda _t: None,
    )
    assert client.token == "sp_y"
    assert warnings

    with pytest.raises(api.PathlyAPIError):
        api.build_client({}, environ={})

    with pytest.raises(api.PathlyAPIError):
        api.PathlyClient("")


def test_snake_camel_conversions():
    assert api.snake_to_camel("interval_sec") == "intervalSec"
    assert api.camel_to_snake("intervalSec") == "interval_sec"
    assert api.to_api_payload(None) is None
    assert api.to_api_payload([{"a_b": 1}]) == [{"aB": 1}]
    assert api.to_api_payload({"x": None, "y": 1}) == {"y": 1}
    assert api.to_api_payload({"x": None}, drop_none=False) == {"x": None}
    assert api.to_api_payload("raw") == "raw"
    assert api.from_api_object(None) is None
    assert api.from_api_object([{"fooBar": 1}]) == [{"foo_bar": 1}]
    assert api.from_api_object("x") == "x"
    assert api.auth_argument_spec()["api_token"]["no_log"] is True


def test_client_success_getcode_and_idempotency():
    opener = FakeOpener(
        [FakeResponse({"id": "mon_1", "name": "n"}, status=200, use_getcode=True)]
    )
    sleeps = []
    client = api.PathlyClient(
        "sp_t",
        base_url="https://api.pathlyhq.com/",
        opener=opener,
        sleep=sleeps.append,
    )
    out = client.create_scenario({"name": "n"}, idempotency_key="fixed-key")
    assert out["id"] == "mon_1"
    req, timeout = opener.requests[0]
    assert req.get_header("Idempotency-key") == "fixed-key" or req.headers.get(
        "Idempotency-Key"
    ) == "fixed-key"
    assert timeout == 30
    assert sleeps == []


def test_client_delete_empty_body():
    opener = FakeOpener([FakeResponse(b"", status=204)])
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    assert client.delete_scenario("mon_1") is None


def test_client_retry_429_then_success():
    opener = FakeOpener(
        [
            _http_error(429, b'{"error":"slow"}', headers={"Retry-After": "1"}),
            FakeResponse({"ok": True}),
        ]
    )
    sleeps = []
    client = api.PathlyClient("sp_t", opener=opener, sleep=sleeps.append)
    assert client.request("GET", "/v1/usage") == {"ok": True}
    assert sleeps == [1.0]


def test_client_retry_exhausted_5xx():
    opener = FakeOpener(
        [
            _http_error(503, b"down"),
            _http_error(503, b"down"),
            _http_error(503, b"down"),
            _http_error(503, b"down"),
        ]
    )
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    with pytest.raises(api.PathlyAPIError) as ctx:
        client.request("GET", "/v1/usage")
    assert ctx.value.status_code == 503


def test_client_urlerror_retries_then_fails():
    opener = FakeOpener(
        [
            URLError("boom"),
            URLError("boom"),
            URLError("boom"),
            URLError("boom"),
        ]
    )
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    with pytest.raises(api.PathlyAPIError) as ctx:
        client.request("GET", "/v1/usage")
    assert "boom" in str(ctx.value)


def test_client_urlerror_recovers():
    opener = FakeOpener([URLError("tmp"), FakeResponse({"planId": "pro"})])
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    assert client.request("GET", "/v1/usage")["planId"] == "pro"


def test_client_4xx_no_retry():
    opener = FakeOpener([_http_error(400, b'{"error":"bad"}')])
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    with pytest.raises(api.PathlyAPIError) as ctx:
        client.request("GET", "/v1/usage")
    assert ctx.value.status_code == 400


def test_client_invalid_json():
    opener = FakeOpener([FakeResponse(b"{not-json", status=200)])
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    with pytest.raises(api.PathlyAPIError) as ctx:
        client.request("GET", "/v1/usage")
    assert "unreadable" in str(ctx.value)


def test_client_http_error_headers_none():
    err = HTTPError("u", 400, "x", None, BytesIO(b'{"error":"bad"}'))
    opener = FakeOpener([err])
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    with pytest.raises(api.PathlyAPIError) as ctx:
        client.request("GET", "/v1/x")
    assert ctx.value.status_code == 400


def test_build_client_without_warn_callback():
    client = api.build_client(
        {"api_token": "sp_y"},
        warn_callback=None,
        environ={},
        opener=FakeOpener([]),
        sleep=lambda _t: None,
    )
    assert client.token == "sp_y"

def test_ping_ok_and_403():
    opener = FakeOpener([FakeResponse({"planId": "pro"})])
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    assert client.ping() is True

    opener2 = FakeOpener([_http_error(403, b'{"error":"scope"}')])
    client2 = api.PathlyClient("sp_t", opener=opener2, sleep=lambda _t: None)
    assert client2.ping() is True

    opener3 = FakeOpener([_http_error(401, b'{"error":"no"}')])
    client3 = api.PathlyClient("sp_t", opener=opener3, sleep=lambda _t: None)
    with pytest.raises(api.PathlyAPIError):
        client3.ping()


def test_crud_wrappers_and_list_pagination():
    opener = FakeOpener(
        [
            FakeResponse({"id": "mon_1"}),
            FakeResponse({"id": "mon_1", "name": "a"}),
            FakeResponse({"id": "mon_1", "name": "b"}),
            FakeResponse(b"", status=204),
            FakeResponse({"items": [{"id": "1", "name": "a"}], "nextCursor": "c1"}),
            FakeResponse({"items": [{"id": "2", "name": "b"}], "nextCursor": None}),
            FakeResponse({"id": "wh_1", "secret": "s"}),
            FakeResponse({"id": "wh_1"}),
            FakeResponse(b"", status=204),
            FakeResponse({"id": "mw_1"}),
            FakeResponse({"id": "mw_1"}),
            FakeResponse(b"", status=204),
            FakeResponse({"id": "sla_1"}),
            FakeResponse({"id": "sla_1"}),
            FakeResponse(b"", status=204),
        ]
    )
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    assert client.create_scenario({"name": "a"})["id"] == "mon_1"
    assert client.get_scenario("mon_1")["id"] == "mon_1"
    assert client.update_scenario("mon_1", {"name": "b"})["name"] == "b"
    client.delete_scenario("mon_1")
    listed = client.list_scenarios()
    assert [i["id"] for i in listed] == ["1", "2"]
    assert client.create_webhook({"url": "https://x"})["secret"] == "s"
    assert client.get_webhook("wh_1")["id"] == "wh_1"
    client.delete_webhook("wh_1")
    assert client.create_maintenance_window({"weekday": 1})["id"] == "mw_1"
    assert client.get_maintenance_window("mw_1")["id"] == "mw_1"
    client.delete_maintenance_window("mw_1")
    assert client.upsert_sla_target({"objectivePct": 99.9, "windowDays": 30})["id"] == "sla_1"
    assert client.get_sla_target("sla_1")["id"] == "sla_1"
    client.delete_sla_target("sla_1")
    assert client.new_idempotency_key()


def test_find_scenario_by_name():
    opener = FakeOpener(
        [
            FakeResponse(
                {
                    "items": [
                        {"id": "1", "name": "a"},
                        {"id": "2", "name": "b"},
                    ]
                }
            ),
            FakeResponse(
                {
                    "items": [
                        {"id": "1", "name": "dup"},
                        {"id": "2", "name": "dup"},
                    ]
                }
            ),
            FakeResponse({"items": []}),
        ]
    )
    client = api.PathlyClient("sp_t", opener=opener, sleep=lambda _t: None)
    assert client.find_scenario_by_name("a")["id"] == "1"
    with pytest.raises(api.PathlyAPIError):
        client.find_scenario_by_name("dup")
    assert client.find_scenario_by_name("missing") is None


def test_list_paged_too_many(monkeypatch):
    monkeypatch.setattr(api, "MAX_PAGES", 2)

    class Endless(object):
        def open(self, req, timeout=None):
            return FakeResponse({"items": [{"id": "x"}], "nextCursor": "more"})

    client = api.PathlyClient("sp_t", opener=Endless(), sleep=lambda _t: None)
    with pytest.raises(api.PathlyAPIError) as ctx:
        client.list_scenarios()
    assert "too many pages" in str(ctx.value)


def test_response_status_helper():
    client = api.PathlyClient("sp_t", opener=FakeOpener([]), sleep=lambda _t: None)

    class OnlyGetCode(object):
        def getcode(self):
            return 201

    assert client._response_status(OnlyGetCode()) == 201
    assert client._response_status(FakeResponse(status=200)) == 200
