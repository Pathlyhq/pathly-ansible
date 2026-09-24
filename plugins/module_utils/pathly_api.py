# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0
"""HTTP client for the Pathly public API (stdlib urllib only)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, build_opener

DEFAULT_API_URL = "https://api.pathlyhq.com"
MAX_ATTEMPTS = 4
MAX_RETRY_WAIT = 90.0
PAGE_SIZE = 200
MAX_PAGES = 200
USER_AGENT = "pathly-ansible/0.1.0"


class PathlyAPIError(Exception):
    """Error returned by the Pathly API or the transport layer."""

    def __init__(self, message, status_code=None, path=None):
        super(PathlyAPIError, self).__init__(message)
        self.message = message
        self.status_code = status_code
        self.path = path

    @property
    def not_found(self):
        return self.status_code == 404


def is_not_found(exc):
    return isinstance(exc, PathlyAPIError) and exc.not_found


def _field_of(path):
    if not path:
        return "body"
    parts = []
    for item in path:
        if isinstance(item, float):
            parts.append(str(int(item)))
        else:
            parts.append(str(item))
    return ".".join(parts) if parts else "body"


def _parse_api_error(status, path, body_bytes):
    text = (body_bytes or b"").decode("utf-8", errors="replace").strip()
    message = text
    try:
        parsed = json.loads(text) if text else {}
    except ValueError:
        parsed = {}
    if isinstance(parsed, dict) and parsed.get("error"):
        message = parsed["error"]
        for detail in parsed.get("details") or []:
            if not isinstance(detail, dict):
                continue
            message += " [%s: %s]" % (
                _field_of(detail.get("path") or []),
                detail.get("message") or "",
            )
    if not message:
        message = "HTTP %s" % status
    if status == 401:
        message += (
            " Check PATHLY_API_TOKEN: an expired, revoked or truncated key"
            " gives the same response."
        )
    elif status == 403:
        message += (
            " Widen the scopes of the key, or check that the plan includes"
            " the feature."
        )
    return PathlyAPIError(message, status_code=status, path=path)


def _backoff(attempt):
    return float(attempt) * 0.5


def _headers_to_dict(headers):
    if headers is None:
        return {}
    if isinstance(headers, dict):
        return headers
    try:
        return dict(headers)
    except (TypeError, ValueError):
        return {}


def _wait_for_retry(headers, attempt):
    raw = None
    if headers is not None:
        raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is not None:
        try:
            secs = int(str(raw).strip())
            if secs > 0:
                return float(min(secs, int(MAX_RETRY_WAIT)))
        except (TypeError, ValueError):
            pass
    return _backoff(attempt)


def resolve_auth(params=None, environ=None):
    """Resolve api_token and api_url from module params then environment."""
    params = params or {}
    environ = environ if environ is not None else os.environ
    token = (params.get("api_token") or environ.get("PATHLY_API_TOKEN") or "").strip()
    url = (params.get("api_url") or environ.get("PATHLY_API_URL") or DEFAULT_API_URL).strip()
    url = url.rstrip("/")
    return token, url


def auth_argument_spec():
    return {
        "api_token": {"type": "str", "no_log": True, "required": False},
        "api_url": {"type": "str", "required": False},
    }


def snake_to_camel(name):
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def to_api_payload(data, drop_none=True):
    """Convert snake_case dict keys to camelCase for the Pathly API."""
    if data is None:
        return None
    if isinstance(data, list):
        return [to_api_payload(item, drop_none=drop_none) for item in data]
    if not isinstance(data, dict):
        return data
    out = {}
    for key, value in data.items():
        if drop_none and value is None:
            continue
        out[snake_to_camel(key)] = to_api_payload(value, drop_none=drop_none)
    return out


def camel_to_snake(name):
    result = []
    for char in name:
        if char.isupper():
            result.append("_")
            result.append(char.lower())
        else:
            result.append(char)
    return "".join(result)


def from_api_object(data):
    """Convert camelCase API objects to snake_case dicts for Ansible returns."""
    if data is None:
        return None
    if isinstance(data, list):
        return [from_api_object(item) for item in data]
    if not isinstance(data, dict):
        return data
    out = {}
    for key, value in data.items():
        out[camel_to_snake(key)] = from_api_object(value)
    return out


class PathlyClient(object):
    """Pathly `/v1` client with retries, idempotency keys, and injectable I/O."""

    def __init__(
        self,
        token,
        base_url=None,
        opener=None,
        sleep=None,
        user_agent=None,
        timeout=30,
    ):
        if not token:
            raise PathlyAPIError("PATHLY_API_TOKEN is required")
        self.token = token.strip()
        self.base_url = (base_url or DEFAULT_API_URL).rstrip("/")
        self.opener = opener or build_opener()
        self.sleep = sleep or time.sleep
        self.user_agent = user_agent or USER_AGENT
        self.timeout = timeout

    def ping(self):
        """Validate the token. HTTP 403 counts as success (missing org:read)."""
        try:
            self.request("GET", "/v1/usage")
        except PathlyAPIError as exc:
            if exc.status_code == 403:
                return True
            raise
        return True

    def request(self, method, path, body=None, idempotency_key=None, expect_json=True):
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")

        for attempt in range(1, MAX_ATTEMPTS + 1):
            last = attempt == MAX_ATTEMPTS
            retry_in, result, error = self._attempt(
                method,
                path,
                payload,
                idempotency_key,
                expect_json,
                attempt,
                last,
            )
            if retry_in <= 0:
                if error is not None:
                    raise error
                return result
            self.sleep(retry_in)
        # Unreachable when MAX_ATTEMPTS >= 1: the last attempt never retries.
        raise PathlyAPIError("request failed after retries", path=path)  # pragma: no cover

    def _response_status(self, response):
        status = getattr(response, "status", None)
        if status is None and hasattr(response, "getcode"):
            status = response.getcode()
        return status

    def _attempt(self, method, path, payload, idempotency_key, expect_json, attempt, last):
        headers = {
            "Authorization": "Bearer %s" % self.token,
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        url = self.base_url + path
        req = Request(url, data=payload, headers=headers, method=method)
        try:
            response = self.opener.open(req, timeout=self.timeout)
            body = response.read()
            status = self._response_status(response)
            headers_map = _headers_to_dict(getattr(response, "headers", None))
            return self._handle_response(
                status, path, body, headers_map, expect_json, attempt, last
            )
        except HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            headers_map = _headers_to_dict(getattr(exc, "headers", None))
            return self._handle_response(
                exc.code, path, body, headers_map, expect_json, attempt, last
            )
        except URLError as exc:
            wrapped = PathlyAPIError(
                "calling %s %s: %s" % (method, path, exc.reason),
                path=path,
            )
            if last:
                return 0, None, wrapped
            return _backoff(attempt), None, wrapped

    def _handle_response(self, status, path, body, headers, expect_json, attempt, last):
        if status in (429,) or (status is not None and status >= 500):
            failure = _parse_api_error(status, path, body)
            if last:
                return 0, None, failure
            return _wait_for_retry(headers, attempt), None, failure
        if status is not None and status >= 400:
            return 0, None, _parse_api_error(status, path, body)
        if not expect_json or not body:
            return 0, None, None
        try:
            return 0, json.loads(body.decode("utf-8")), None
        except ValueError as exc:
            return 0, None, PathlyAPIError(
                "unreadable response from %s: %s" % (path, exc),
                path=path,
            )

    def new_idempotency_key(self):
        return str(uuid.uuid4())

    # --- Scenarios ---------------------------------------------------------

    def create_scenario(self, payload, idempotency_key=None):
        return self.request(
            "POST",
            "/v1/scenarios",
            body=payload,
            idempotency_key=idempotency_key or self.new_idempotency_key(),
        )

    def get_scenario(self, scenario_id):
        return self.request(
            "GET",
            "/v1/scenarios/%s" % quote(str(scenario_id), safe=""),
        )

    def update_scenario(self, scenario_id, payload):
        return self.request(
            "PATCH",
            "/v1/scenarios/%s" % quote(str(scenario_id), safe=""),
            body=payload,
        )

    def delete_scenario(self, scenario_id):
        return self.request(
            "DELETE",
            "/v1/scenarios/%s" % quote(str(scenario_id), safe=""),
            expect_json=False,
        )

    def list_scenarios(self):
        return self._list_paged("/v1/scenarios")

    def find_scenario_by_name(self, name):
        matches = [s for s in self.list_scenarios() if s.get("name") == name]
        if len(matches) > 1:
            raise PathlyAPIError(
                "multiple scenarios named %r; set id explicitly" % name
            )
        return matches[0] if matches else None

    # --- Webhooks ----------------------------------------------------------

    def create_webhook(self, payload, idempotency_key=None):
        return self.request(
            "POST",
            "/v1/webhooks",
            body=payload,
            idempotency_key=idempotency_key or self.new_idempotency_key(),
        )

    def get_webhook(self, webhook_id):
        return self.request(
            "GET",
            "/v1/webhooks/%s" % quote(str(webhook_id), safe=""),
        )

    def delete_webhook(self, webhook_id):
        return self.request(
            "DELETE",
            "/v1/webhooks/%s" % quote(str(webhook_id), safe=""),
            expect_json=False,
        )

    # --- Maintenance windows -----------------------------------------------

    def create_maintenance_window(self, payload, idempotency_key=None):
        return self.request(
            "POST",
            "/v1/maintenance-windows",
            body=payload,
            idempotency_key=idempotency_key or self.new_idempotency_key(),
        )

    def get_maintenance_window(self, window_id):
        return self.request(
            "GET",
            "/v1/maintenance-windows/%s" % quote(str(window_id), safe=""),
        )

    def delete_maintenance_window(self, window_id):
        return self.request(
            "DELETE",
            "/v1/maintenance-windows/%s" % quote(str(window_id), safe=""),
            expect_json=False,
        )

    # --- SLA targets -------------------------------------------------------

    def upsert_sla_target(self, payload, idempotency_key=None):
        return self.request(
            "PUT",
            "/v1/sla-targets",
            body=payload,
            idempotency_key=idempotency_key or self.new_idempotency_key(),
        )

    def get_sla_target(self, target_id):
        return self.request(
            "GET",
            "/v1/sla-targets/%s" % quote(str(target_id), safe=""),
        )

    def delete_sla_target(self, target_id):
        return self.request(
            "DELETE",
            "/v1/sla-targets/%s" % quote(str(target_id), safe=""),
            expect_json=False,
        )

    def _list_paged(self, base):
        all_items = []
        cursor = ""
        for _page in range(MAX_PAGES):
            query = {"limit": str(PAGE_SIZE)}
            if cursor:
                query["cursor"] = cursor
            path = "%s?%s" % (base, urlencode(query))
            out = self.request("GET", path)
            items = (out or {}).get("items") or []
            all_items.extend(items)
            next_cursor = (out or {}).get("nextCursor")
            if not next_cursor:
                return all_items
            cursor = next_cursor
        raise PathlyAPIError(
            "%s pagination: too many pages, stopping on purpose" % base,
            path=base,
        )


def build_client(params, warn_callback=None, environ=None, client_cls=None, **client_kwargs):
    """Build a PathlyClient from module params / environment."""
    token, url = resolve_auth(params, environ=environ)
    if not token:
        raise PathlyAPIError(
            "api_token is required (module parameter or PATHLY_API_TOKEN env)"
        )
    if params and params.get("api_token") and warn_callback:
        warn_callback(
            "Passing api_token as a module parameter may expose it in logs;"
            " prefer the PATHLY_API_TOKEN environment variable."
        )
    cls = client_cls or PathlyClient
    return cls(token=token, base_url=url, **client_kwargs)
