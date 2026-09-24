# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0
"""Shared helpers for Pathly Ansible modules (injectable for unit tests)."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import (
    PathlyAPIError,
    build_client,
    from_api_object,
    is_not_found,
    to_api_payload,
)


def fail_from_api(module, exc):
    module.fail_json(msg=str(exc), status_code=getattr(exc, "status_code", None))


def get_client(module, client_factory=None):
    factory = client_factory or build_client
    try:
        return factory(module.params, warn_callback=module.warn)
    except PathlyAPIError as exc:
        fail_from_api(module, exc)
        raise  # pragma: no cover - fail_json exits; kept for type checkers


def scenario_desired_payload(params):
    """Build camelCase create/update body for HTTP scenarios only."""
    raw = {
        "name": params.get("name"),
        "type": params.get("type") or "http",
        "url": params.get("url"),
        "interval_sec": params.get("interval_sec"),
        "method": params.get("method"),
        "expected_status": params.get("expected_status"),
        "max_latency_ms": params.get("max_latency_ms"),
        "expect_text": params.get("expect_text"),
        "regions": params.get("regions"),
        "tags": params.get("tags"),
        "folder": params.get("folder"),
        "severity": params.get("severity"),
        "runbook": params.get("runbook"),
        "cron": params.get("cron"),
        "enabled": params.get("enabled"),
    }
    if raw["type"] == "browser":
        raise PathlyAPIError(
            "browser scenarios are not managed by this collection"
            " (credentials would remain in state); use HTTP scenarios only"
        )
    return to_api_payload(raw)


def scenario_needs_update(current, desired):
    """Compare API object (camelCase) to desired payload (camelCase)."""
    for key, value in desired.items():
        if value is None:
            continue
        current_value = current.get(key)
        if isinstance(value, list):
            left = list(current_value or [])
            right = list(value)
            if left != right:
                return True
        elif current_value != value:
            return True
    return False


def ensure_scenario(client, params, check_mode=False):
    state = params.get("state") or "present"
    scenario_id = params.get("id")
    name = params.get("name")
    existing = None

    if scenario_id:
        try:
            existing = client.get_scenario(scenario_id)
        except PathlyAPIError as exc:
            if not is_not_found(exc):
                raise
            existing = None
    elif name:
        existing = client.find_scenario_by_name(name)

    if state == "absent":
        if existing is None:
            return {"changed": False, "scenario": None}
        if check_mode:
            return {"changed": True, "scenario": from_api_object(existing)}
        client.delete_scenario(existing["id"])
        return {"changed": True, "scenario": from_api_object(existing)}

    desired = scenario_desired_payload(params)
    if existing is None:
        if check_mode:
            return {"changed": True, "scenario": from_api_object(desired)}
        created = client.create_scenario(desired)
        return {"changed": True, "scenario": from_api_object(created)}

    if not scenario_needs_update(existing, desired):
        return {"changed": False, "scenario": from_api_object(existing)}

    if check_mode:
        merged = dict(existing)
        merged.update(desired)
        return {"changed": True, "scenario": from_api_object(merged)}

    updated = client.update_scenario(existing["id"], desired)
    return {"changed": True, "scenario": from_api_object(updated)}


def ensure_webhook(client, params, check_mode=False):
    state = params.get("state") or "present"
    webhook_id = params.get("id")
    existing = None

    if webhook_id:
        try:
            existing = client.get_webhook(webhook_id)
        except PathlyAPIError as exc:
            if not is_not_found(exc):
                raise
            existing = None

    if state == "absent":
        if existing is None:
            return {"changed": False, "webhook": None}
        if check_mode:
            return {"changed": True, "webhook": from_api_object(existing)}
        client.delete_webhook(existing["id"])
        return {"changed": True, "webhook": from_api_object(existing)}

    url = params.get("url")
    events = params.get("events")
    payload = to_api_payload({"url": url, "events": events})

    if existing is None:
        if check_mode:
            return {"changed": True, "webhook": {"url": url, "events": events}}
        created = client.create_webhook(payload)
        result = from_api_object(created)
        # URL is never returned on read; echo the configured value.
        result["url"] = url
        return {"changed": True, "webhook": result}

    # API has no PATCH: events are force-replace. Recreate when events differ.
    current_events = list(existing.get("events") or [])
    desired_events = list(events) if events is not None else current_events
    if sorted(current_events) == sorted(desired_events):
        result = from_api_object(existing)
        result["url"] = url
        return {"changed": False, "webhook": result}

    if check_mode:
        return {
            "changed": True,
            "webhook": {"id": existing.get("id"), "url": url, "events": desired_events},
        }
    client.delete_webhook(existing["id"])
    created = client.create_webhook(payload)
    result = from_api_object(created)
    result["url"] = url
    return {"changed": True, "webhook": result}


def _mw_desired(params):
    return to_api_payload(
        {
            "monitor_id": params.get("scenario_id") or params.get("monitor_id"),
            "starts_at": params.get("starts_at"),
            "ends_at": params.get("ends_at"),
            "weekday": params.get("weekday"),
            "start_minute": params.get("start_minute"),
            "duration_min": params.get("duration_min"),
            "reason": params.get("reason"),
        }
    )


def _mw_matches(existing, desired):
    for key, value in desired.items():
        if value is None:
            continue
        if existing.get(key) != value:
            return False
    return True


def ensure_maintenance_window(client, params, check_mode=False):
    state = params.get("state") or "present"
    window_id = params.get("id")
    existing = None

    if window_id:
        try:
            existing = client.get_maintenance_window(window_id)
        except PathlyAPIError as exc:
            if not is_not_found(exc):
                raise
            existing = None

    if state == "absent":
        if existing is None:
            return {"changed": False, "maintenance_window": None}
        if check_mode:
            return {
                "changed": True,
                "maintenance_window": from_api_object(existing),
            }
        client.delete_maintenance_window(existing["id"])
        return {"changed": True, "maintenance_window": from_api_object(existing)}

    desired = _mw_desired(params)
    one_off = desired.get("startsAt") is not None or desired.get("endsAt") is not None
    weekly = (
        desired.get("weekday") is not None
        or desired.get("startMinute") is not None
        or desired.get("durationMin") is not None
    )
    if one_off and weekly:
        raise PathlyAPIError(
            "maintenance window must be either one-off (starts_at/ends_at)"
            " or weekly (weekday/start_minute/duration_min), not both"
        )
    if not one_off and not weekly:
        raise PathlyAPIError(
            "maintenance window requires one-off or weekly fields"
        )

    if existing is None:
        if check_mode:
            return {"changed": True, "maintenance_window": from_api_object(desired)}
        created = client.create_maintenance_window(desired)
        return {"changed": True, "maintenance_window": from_api_object(created)}

    if _mw_matches(existing, desired):
        return {"changed": False, "maintenance_window": from_api_object(existing)}

    # No in-place update: delete then recreate.
    if check_mode:
        return {"changed": True, "maintenance_window": from_api_object(desired)}
    client.delete_maintenance_window(existing["id"])
    created = client.create_maintenance_window(desired)
    return {"changed": True, "maintenance_window": from_api_object(created)}


def ensure_sla_target(client, params, check_mode=False):
    state = params.get("state") or "present"
    target_id = params.get("id")
    existing = None

    if target_id:
        try:
            existing = client.get_sla_target(target_id)
        except PathlyAPIError as exc:
            if not is_not_found(exc):
                raise
            existing = None

    if state == "absent":
        if existing is None:
            return {"changed": False, "sla_target": None}
        if check_mode:
            return {"changed": True, "sla_target": from_api_object(existing)}
        client.delete_sla_target(existing["id"])
        return {"changed": True, "sla_target": from_api_object(existing)}

    desired = to_api_payload(
        {
            "monitor_id": params.get("scenario_id") or params.get("monitor_id"),
            "name": params.get("name"),
            "objective_pct": params.get("objective_pct"),
            "window_days": params.get("window_days"),
            "exclude_maintenance": params.get("exclude_maintenance"),
            "warn_at_budget_ratio": params.get("warn_at_budget_ratio"),
            "enabled": params.get("enabled"),
        },
        drop_none=True,
    )
    if "objectivePct" not in desired or "windowDays" not in desired:
        raise PathlyAPIError("objective_pct and window_days are required when state=present")

    if existing is not None and not _sla_needs_update(existing, desired):
        return {"changed": False, "sla_target": from_api_object(existing)}

    if check_mode:
        base = dict(existing or {})
        base.update(desired)
        return {"changed": True, "sla_target": from_api_object(base)}

    upserted = client.upsert_sla_target(desired)
    return {"changed": True, "sla_target": from_api_object(upserted)}


def _sla_needs_update(existing, desired):
    for key, value in desired.items():
        if value is None:
            continue
        if existing.get(key) != value:
            return True
    return False


def gather_scenario_info(client, params):
    scenario_id = params.get("id")
    name = params.get("name")
    if scenario_id:
        try:
            item = client.get_scenario(scenario_id)
        except PathlyAPIError as exc:
            if is_not_found(exc):
                return {"changed": False, "scenarios": []}
            raise
        return {"changed": False, "scenarios": [from_api_object(item)]}

    scenarios = client.list_scenarios()
    if name:
        scenarios = [s for s in scenarios if s.get("name") == name]
    return {
        "changed": False,
        "scenarios": [from_api_object(s) for s in scenarios],
    }
