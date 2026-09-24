# -*- coding: utf-8 -*-
"""Unit tests for pathly_common ensure_* helpers."""

from __future__ import absolute_import, division, print_function

import pytest

from ansible_collections.pathlyhq.pathly.plugins.module_utils import pathly_common as common
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import PathlyAPIError
from tests.conftest import AnsibleFailJson, FakeModule


class FakeClient(object):
    def __init__(self):
        self.scenarios = {}
        self.webhooks = {}
        self.windows = {}
        self.slas = {}
        self.deleted = []
        self.created_webhooks = []
        self.upserts = []

    def get_scenario(self, sid):
        if sid not in self.scenarios:
            raise PathlyAPIError("missing", status_code=404)
        return dict(self.scenarios[sid])

    def find_scenario_by_name(self, name):
        matches = [s for s in self.scenarios.values() if s.get("name") == name]
        if len(matches) > 1:
            raise PathlyAPIError("multiple")
        return dict(matches[0]) if matches else None

    def create_scenario(self, payload):
        item = dict(payload)
        item["id"] = "mon_new"
        self.scenarios[item["id"]] = item
        return item

    def update_scenario(self, sid, payload):
        self.scenarios[sid].update(payload)
        return dict(self.scenarios[sid])

    def delete_scenario(self, sid):
        self.deleted.append(("scenario", sid))
        self.scenarios.pop(sid, None)

    def get_webhook(self, wid):
        if wid not in self.webhooks:
            raise PathlyAPIError("missing", status_code=404)
        return dict(self.webhooks[wid])

    def create_webhook(self, payload):
        item = {
            "id": "wh_new",
            "events": payload.get("events") or ["run.failed", "run.recovered"],
            "secret": "sec",
            "urlFingerprint": "fp",
        }
        self.created_webhooks.append(payload)
        self.webhooks[item["id"]] = item
        return item

    def delete_webhook(self, wid):
        self.deleted.append(("webhook", wid))
        self.webhooks.pop(wid, None)

    def get_maintenance_window(self, wid):
        if wid not in self.windows:
            raise PathlyAPIError("missing", status_code=404)
        return dict(self.windows[wid])

    def create_maintenance_window(self, payload):
        item = dict(payload)
        item["id"] = "mw_new"
        self.windows[item["id"]] = item
        return item

    def delete_maintenance_window(self, wid):
        self.deleted.append(("mw", wid))
        self.windows.pop(wid, None)

    def get_sla_target(self, tid):
        if tid not in self.slas:
            raise PathlyAPIError("missing", status_code=404)
        return dict(self.slas[tid])

    def upsert_sla_target(self, payload):
        self.upserts.append(payload)
        item = dict(payload)
        item["id"] = "sla_new"
        self.slas[item["id"]] = item
        return item

    def delete_sla_target(self, tid):
        self.deleted.append(("sla", tid))
        self.slas.pop(tid, None)

    def list_scenarios(self):
        return [dict(v) for v in self.scenarios.values()]


def test_fail_from_api_and_get_client():
    module = FakeModule(params={})
    with pytest.raises(AnsibleFailJson):
        common.fail_from_api(module, PathlyAPIError("x", status_code=400))

    with pytest.raises(AnsibleFailJson):
        common.get_client(FakeModule(params={}), client_factory=lambda *a, **k: (_ for _ in ()).throw(PathlyAPIError("no token")))

    class C(object):
        pass

    built = common.get_client(
        FakeModule(params={"api_token": "sp_x"}),
        client_factory=lambda params, warn_callback=None: C(),
    )
    assert isinstance(built, C)


def test_scenario_desired_and_needs_update():
    payload = common.scenario_desired_payload(
        {
            "name": "Home",
            "url": "https://x",
            "interval_sec": 60,
            "tags": ["a"],
            "enabled": True,
        }
    )
    assert payload["name"] == "Home"
    assert payload["intervalSec"] == 60
    assert payload["type"] == "http"

    with pytest.raises(PathlyAPIError):
        common.scenario_desired_payload({"type": "browser", "name": "x"})

    current = {
        "name": "Home",
        "tags": ["a"],
        "intervalSec": 60,
        "url": "https://x",
        "enabled": True,
        "type": "http",
    }
    assert common.scenario_needs_update(current, payload) is False
    assert common.scenario_needs_update(current, {"name": "Other"}) is True
    assert common.scenario_needs_update(current, {"tags": ["b"]}) is True
    assert common.scenario_needs_update(current, {"missing": None}) is False
    assert common.scenario_needs_update(current, {"tags": ["a"]}) is False


def test_ensure_scenario_paths():
    client = FakeClient()
    # neither id nor name: skip lookup
    assert common.ensure_scenario(client, {"state": "absent"})["changed"] is False

    client.scenarios["mon_1"] = {
        "id": "mon_1",
        "name": "Home",
        "url": "https://x",
        "intervalSec": 60,
        "tags": ["a"],
    }

    # absent missing
    assert common.ensure_scenario(client, {"state": "absent", "id": "nope"})["changed"] is False

    # get by id non-404 error
    def boom(_id):
        raise PathlyAPIError("nope", status_code=500)

    client.get_scenario = boom
    with pytest.raises(PathlyAPIError):
        common.ensure_scenario(client, {"state": "present", "id": "mon_1", "name": "Home"})

    client = FakeClient()
    client.scenarios["mon_1"] = {
        "id": "mon_1",
        "name": "Home",
        "url": "https://x",
        "intervalSec": 60,
        "tags": ["a"],
    }

    # absent check mode
    out = common.ensure_scenario(
        client, {"state": "absent", "id": "mon_1"}, check_mode=True
    )
    assert out["changed"] is True
    assert "mon_1" in client.scenarios

    # absent real
    out = common.ensure_scenario(client, {"state": "absent", "name": "Home"})
    assert out["changed"] is True
    assert client.deleted

    # create check mode
    out = common.ensure_scenario(
        client,
        {
            "state": "present",
            "name": "New",
            "url": "https://y",
            "interval_sec": 30,
        },
        check_mode=True,
    )
    assert out["changed"] is True

    # create real
    out = common.ensure_scenario(
        client,
        {
            "state": "present",
            "name": "New",
            "url": "https://y",
            "interval_sec": 30,
            "tags": ["t"],
        },
    )
    assert out["changed"] is True
    assert out["scenario"]["id"] == "mon_new"

    # no update
    out = common.ensure_scenario(
        client,
        {
            "state": "present",
            "id": "mon_new",
            "name": "New",
            "url": "https://y",
            "interval_sec": 30,
            "tags": ["t"],
            "type": "http",
        },
    )
    assert out["changed"] is False

    # update check mode
    out = common.ensure_scenario(
        client,
        {
            "state": "present",
            "id": "mon_new",
            "name": "New",
            "url": "https://y",
            "interval_sec": 90,
            "tags": ["t"],
        },
        check_mode=True,
    )
    assert out["changed"] is True

    # update real
    out = common.ensure_scenario(
        client,
        {
            "state": "present",
            "id": "mon_new",
            "name": "New",
            "url": "https://y",
            "interval_sec": 90,
            "tags": ["t"],
        },
    )
    assert out["changed"] is True
    assert out["scenario"]["interval_sec"] == 90

    # find by name present when missing id
    client.scenarios.clear()
    client.scenarios["mon_2"] = {
        "id": "mon_2",
        "name": "Named",
        "intervalSec": 10,
        "url": "https://z",
        "type": "http",
    }
    out = common.ensure_scenario(
        client,
        {
            "state": "present",
            "name": "Named",
            "url": "https://z",
            "interval_sec": 10,
            "type": "http",
        },
    )
    assert out["changed"] is False


def test_ensure_webhook_paths():
    client = FakeClient()
    assert common.ensure_webhook(client, {"state": "absent", "id": "no"})["changed"] is False

    def boom(_id):
        raise PathlyAPIError("x", status_code=500)

    client.get_webhook = boom
    with pytest.raises(PathlyAPIError):
        common.ensure_webhook(client, {"state": "absent", "id": "wh_1"})

    client = FakeClient()
    client.webhooks["wh_1"] = {
        "id": "wh_1",
        "events": ["run.failed", "run.recovered"],
    }
    out = common.ensure_webhook(
        client, {"state": "absent", "id": "wh_1"}, check_mode=True
    )
    assert out["changed"] is True
    out = common.ensure_webhook(client, {"state": "absent", "id": "wh_1"})
    assert out["changed"] is True

    out = common.ensure_webhook(
        client,
        {"state": "present", "url": "https://hooks.example/x", "events": ["run.failed"]},
        check_mode=True,
    )
    assert out["changed"] is True

    out = common.ensure_webhook(
        client,
        {
            "state": "present",
            "url": "https://hooks.example/x",
            "events": ["run.failed", "run.recovered"],
        },
    )
    assert out["changed"] is True
    assert out["webhook"]["secret"] == "sec"
    assert out["webhook"]["url"] == "https://hooks.example/x"

    client.webhooks["wh_1"] = {
        "id": "wh_1",
        "events": ["run.failed", "run.recovered"],
    }
    out = common.ensure_webhook(
        client,
        {
            "state": "present",
            "id": "wh_1",
            "url": "https://hooks.example/x",
            "events": ["run.failed", "run.recovered"],
        },
    )
    assert out["changed"] is False

    out = common.ensure_webhook(
        client,
        {
            "state": "present",
            "id": "wh_1",
            "url": "https://hooks.example/x",
            "events": ["run.failed"],
        },
        check_mode=True,
    )
    assert out["changed"] is True

    out = common.ensure_webhook(
        client,
        {
            "state": "present",
            "id": "wh_1",
            "url": "https://hooks.example/x",
            "events": ["run.failed"],
        },
    )
    assert out["changed"] is True
    assert ("webhook", "wh_1") in client.deleted


def test_ensure_maintenance_window_paths():
    client = FakeClient()
    assert common.ensure_maintenance_window(
        client, {"state": "absent", "id": "no"}
    )["changed"] is False

    def boom(_id):
        raise PathlyAPIError("x", status_code=500)

    client.get_maintenance_window = boom
    with pytest.raises(PathlyAPIError):
        common.ensure_maintenance_window(client, {"state": "absent", "id": "mw"})

    client = FakeClient()
    client.windows["mw_1"] = {
        "id": "mw_1",
        "weekday": 7,
        "startMinute": 180,
        "durationMin": 120,
    }
    assert common.ensure_maintenance_window(
        client, {"state": "absent", "id": "mw_1"}, check_mode=True
    )["changed"] is True
    assert common.ensure_maintenance_window(
        client, {"state": "absent", "id": "mw_1"}
    )["changed"] is True

    with pytest.raises(PathlyAPIError):
        common.ensure_maintenance_window(
            client,
            {
                "state": "present",
                "starts_at": "2026-01-01T00:00:00Z",
                "weekday": 1,
            },
        )
    with pytest.raises(PathlyAPIError):
        common.ensure_maintenance_window(client, {"state": "present"})

    assert common.ensure_maintenance_window(
        client,
        {
            "state": "present",
            "weekday": 7,
            "start_minute": 180,
            "duration_min": 120,
            "reason": "backup",
        },
        check_mode=True,
    )["changed"] is True

    out = common.ensure_maintenance_window(
        client,
        {
            "state": "present",
            "weekday": 7,
            "start_minute": 180,
            "duration_min": 120,
            "reason": "backup",
        },
    )
    assert out["changed"] is True

    client.windows["mw_1"] = {
        "id": "mw_1",
        "weekday": 7,
        "startMinute": 180,
        "durationMin": 120,
        "reason": "backup",
    }
    out = common.ensure_maintenance_window(
        client,
        {
            "state": "present",
            "id": "mw_1",
            "weekday": 7,
            "start_minute": 180,
            "duration_min": 120,
            "reason": "backup",
        },
    )
    assert out["changed"] is False

    out = common.ensure_maintenance_window(
        client,
        {
            "state": "present",
            "id": "mw_1",
            "weekday": 1,
            "start_minute": 0,
            "duration_min": 30,
        },
        check_mode=True,
    )
    assert out["changed"] is True

    out = common.ensure_maintenance_window(
        client,
        {
            "state": "present",
            "id": "mw_1",
            "starts_at": "2026-10-04T22:00:00Z",
            "ends_at": "2026-10-05T02:00:00Z",
            "scenario_id": "mon_1",
            "reason": "mig",
        },
    )
    assert out["changed"] is True
    assert ("mw", "mw_1") in client.deleted


def test_ensure_sla_target_paths():
    client = FakeClient()
    assert common.ensure_sla_target(client, {"state": "absent", "id": "no"})[
        "changed"
    ] is False

    def boom(_id):
        raise PathlyAPIError("x", status_code=500)

    client.get_sla_target = boom
    with pytest.raises(PathlyAPIError):
        common.ensure_sla_target(client, {"state": "absent", "id": "sla"})

    client = FakeClient()
    client.slas["sla_1"] = {
        "id": "sla_1",
        "objectivePct": 99.9,
        "windowDays": 30,
        "monitorId": "mon_1",
    }
    assert common.ensure_sla_target(
        client, {"state": "absent", "id": "sla_1"}, check_mode=True
    )["changed"] is True
    assert common.ensure_sla_target(client, {"state": "absent", "id": "sla_1"})[
        "changed"
    ] is True

    with pytest.raises(PathlyAPIError):
        common.ensure_sla_target(client, {"state": "present", "name": "x"})

    out = common.ensure_sla_target(
        client,
        {
            "state": "present",
            "scenario_id": "mon_1",
            "objective_pct": 99.9,
            "window_days": 30,
            "name": "SLA",
        },
        check_mode=True,
    )
    assert out["changed"] is True

    out = common.ensure_sla_target(
        client,
        {
            "state": "present",
            "monitor_id": "mon_1",
            "objective_pct": 99.9,
            "window_days": 30,
            "exclude_maintenance": True,
            "warn_at_budget_ratio": 0.8,
            "enabled": True,
        },
    )
    assert out["changed"] is True
    assert client.upserts

    client.slas["sla_1"] = {
        "id": "sla_1",
        "objectivePct": 99.9,
        "windowDays": 30,
        "monitorId": "mon_1",
        "excludeMaintenance": True,
        "warnAtBudgetRatio": 0.8,
        "enabled": True,
    }
    out = common.ensure_sla_target(
        client,
        {
            "state": "present",
            "id": "sla_1",
            "scenario_id": "mon_1",
            "objective_pct": 99.9,
            "window_days": 30,
            "exclude_maintenance": True,
            "warn_at_budget_ratio": 0.8,
            "enabled": True,
        },
    )
    assert out["changed"] is False

    out = common.ensure_sla_target(
        client,
        {
            "state": "present",
            "id": "sla_1",
            "scenario_id": "mon_1",
            "objective_pct": 99.5,
            "window_days": 30,
        },
        check_mode=True,
    )
    assert out["changed"] is True


def test_gather_scenario_info():
    client = FakeClient()
    client.scenarios["mon_1"] = {"id": "mon_1", "name": "Home"}
    client.scenarios["mon_2"] = {"id": "mon_2", "name": "Other"}

    out = common.gather_scenario_info(client, {"id": "mon_1"})
    assert len(out["scenarios"]) == 1
    assert out["changed"] is False

    out = common.gather_scenario_info(client, {"id": "missing"})
    assert out["scenarios"] == []

    def boom(_id):
        raise PathlyAPIError("x", status_code=500)

    client.get_scenario = boom
    with pytest.raises(PathlyAPIError):
        common.gather_scenario_info(client, {"id": "mon_1"})

    client = FakeClient()
    client.scenarios["mon_1"] = {"id": "mon_1", "name": "Home"}
    client.scenarios["mon_2"] = {"id": "mon_2", "name": "Other"}
    out = common.gather_scenario_info(client, {})
    assert len(out["scenarios"]) == 2
    out = common.gather_scenario_info(client, {"name": "Home"})
    assert len(out["scenarios"]) == 1


def test_mw_matches_and_sla_needs():
    assert common._mw_matches({"weekday": 1}, {"weekday": 1, "reason": None}) is True
    assert common._mw_matches({"weekday": 1}, {"weekday": 2}) is False
    assert common._sla_needs_update({"objectivePct": 99.9}, {"objectivePct": 99.9}) is False
    assert common._sla_needs_update({"objectivePct": 99.9}, {"objectivePct": 99.0}) is True
    assert common._sla_needs_update({}, {"x": None}) is False
