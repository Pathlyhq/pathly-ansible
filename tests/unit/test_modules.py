# -*- coding: utf-8 -*-
"""Unit tests for module run_module / main entrypoints."""

from __future__ import absolute_import, division, print_function

import importlib
import importlib.util
import sys

import pytest

from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import PathlyAPIError
from tests.conftest import AnsibleExitJson, AnsibleFailJson, FakeModule, PLUGINS
from tests.unit.test_pathly_common import FakeClient


def _load_module(name):
    path = PLUGINS / "modules" / ("%s.py" % name)
    # Reload-friendly unique name
    mod_name = "pathly_test_mod_%s" % name
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    module = importlib.util.module_from_spec(spec)
    # Provide ansible.module_utils.basic stub before exec
    if "ansible" not in sys.modules:
        ansible = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("ansible", loader=None)
        )
        ansible.__path__ = []
        sys.modules["ansible"] = ansible
    if "ansible.module_utils" not in sys.modules:
        mu = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("ansible.module_utils", loader=None)
        )
        mu.__path__ = []
        sys.modules["ansible.module_utils"] = mu
    if "ansible.module_utils.basic" not in sys.modules:
        basic = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("ansible.module_utils.basic", loader=None)
        )

        class AnsibleModule(object):
            def __init__(self, *args, **kwargs):
                self.params = {}
                self.check_mode = False

            def exit_json(self, **kwargs):
                raise AnsibleExitJson(kwargs)

            def fail_json(self, **kwargs):
                raise AnsibleFailJson(kwargs)

            def warn(self, msg):
                pass

        basic.AnsibleModule = AnsibleModule
        sys.modules["ansible.module_utils.basic"] = basic

    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def scenario_mod():
    return _load_module("pathly_scenario")


@pytest.fixture(scope="module")
def webhook_mod():
    return _load_module("pathly_webhook")


@pytest.fixture(scope="module")
def mw_mod():
    return _load_module("pathly_maintenance_window")


@pytest.fixture(scope="module")
def sla_mod():
    return _load_module("pathly_sla_target")


@pytest.fixture(scope="module")
def info_mod():
    return _load_module("pathly_scenario_info")


def test_scenario_run_validation_and_success(scenario_mod):
    with pytest.raises(AnsibleFailJson):
        scenario_mod.run_module(
            FakeModule({"state": "present", "url": "https://x"}),
            client=FakeClient(),
        )
    with pytest.raises(AnsibleFailJson):
        scenario_mod.run_module(
            FakeModule({"state": "present", "name": "Home"}),
            client=FakeClient(),
        )

    client = FakeClient()
    with pytest.raises(AnsibleExitJson) as ctx:
        scenario_mod.run_module(
            FakeModule(
                {
                    "state": "present",
                    "name": "Home",
                    "url": "https://x",
                    "interval_sec": 60,
                }
            ),
            client=client,
        )
    assert ctx.value.kwargs["changed"] is True

    # present with id skips interval_sec requirement
    client.scenarios["mon_1"] = {
        "id": "mon_1",
        "name": "Home",
        "url": "https://x",
        "intervalSec": 60,
        "type": "http",
    }
    with pytest.raises(AnsibleExitJson):
        scenario_mod.run_module(
            FakeModule(
                {
                    "state": "present",
                    "id": "mon_1",
                    "name": "Home",
                    "url": "https://x",
                    "interval_sec": 60,
                    "type": "http",
                }
            ),
            client=client,
        )

    # absent path (state != present validation branch)
    with pytest.raises(AnsibleExitJson) as ctx:
        scenario_mod.run_module(
            FakeModule({"state": "absent", "id": "mon_1"}),
            client=client,
        )
    assert ctx.value.kwargs["changed"] is True

    with pytest.raises(AnsibleFailJson):
        scenario_mod.run_module(
            FakeModule(
                {
                    "state": "present",
                    "name": "Home",
                    "url": "https://x",
                    "interval_sec": 60,
                    "type": "browser",
                }
            ),
            client=FakeClient(),
        )


def test_scenario_main(monkeypatch, scenario_mod):
    calls = {}

    class AM(object):
        def __init__(self, *args, **kwargs):
            self.params = {
                "state": "present",
                "name": "Home",
                "url": "https://x",
                "interval_sec": 60,
                "api_token": "sp_t",
            }
            self.check_mode = False

        def exit_json(self, **kwargs):
            calls["exit"] = kwargs
            raise AnsibleExitJson(kwargs)

        def fail_json(self, **kwargs):
            raise AnsibleFailJson(kwargs)

        def warn(self, msg):
            pass

    monkeypatch.setattr(scenario_mod, "AnsibleModule", AM)
    monkeypatch.setattr(
        scenario_mod,
        "get_client",
        lambda module: FakeClient(),
    )
    with pytest.raises(AnsibleExitJson):
        scenario_mod.main()
    assert calls["exit"]["changed"] is True


def test_webhook_run(webhook_mod):
    with pytest.raises(AnsibleFailJson):
        webhook_mod.run_module(FakeModule({"state": "present"}), client=FakeClient())
    with pytest.raises(AnsibleFailJson):
        webhook_mod.run_module(FakeModule({"state": "absent"}), client=FakeClient())

    with pytest.raises(AnsibleExitJson) as ctx:
        webhook_mod.run_module(
            FakeModule(
                {
                    "state": "present",
                    "url": "https://hooks.example/x",
                    "events": ["run.failed"],
                }
            ),
            client=FakeClient(),
        )
    assert ctx.value.kwargs["changed"] is True

    with pytest.raises(AnsibleFailJson):
        client = FakeClient()

        def boom(*a, **k):
            raise PathlyAPIError("x", status_code=500)

        client.create_webhook = boom
        webhook_mod.run_module(
            FakeModule({"state": "present", "url": "https://hooks.example/x"}),
            client=client,
        )


def test_webhook_main(monkeypatch, webhook_mod):
    class AM(object):
        def __init__(self, *args, **kwargs):
            self.params = {"state": "present", "url": "https://hooks.example/x"}
            self.check_mode = False

        def exit_json(self, **kwargs):
            raise AnsibleExitJson(kwargs)

        def fail_json(self, **kwargs):
            raise AnsibleFailJson(kwargs)

        def warn(self, msg):
            pass

    monkeypatch.setattr(webhook_mod, "AnsibleModule", AM)
    monkeypatch.setattr(webhook_mod, "get_client", lambda m: FakeClient())
    with pytest.raises(AnsibleExitJson):
        webhook_mod.main()


def test_mw_run(mw_mod):
    with pytest.raises(AnsibleFailJson):
        mw_mod.run_module(FakeModule({"state": "absent"}), client=FakeClient())

    with pytest.raises(AnsibleExitJson) as ctx:
        mw_mod.run_module(
            FakeModule(
                {
                    "state": "present",
                    "weekday": 7,
                    "start_minute": 180,
                    "duration_min": 120,
                }
            ),
            client=FakeClient(),
        )
    assert ctx.value.kwargs["changed"] is True

    with pytest.raises(AnsibleFailJson):
        mw_mod.run_module(
            FakeModule({"state": "present"}),
            client=FakeClient(),
        )


def test_mw_main(monkeypatch, mw_mod):
    class AM(object):
        def __init__(self, *args, **kwargs):
            self.params = {
                "state": "present",
                "weekday": 1,
                "start_minute": 0,
                "duration_min": 30,
            }
            self.check_mode = False

        def exit_json(self, **kwargs):
            raise AnsibleExitJson(kwargs)

        def fail_json(self, **kwargs):
            raise AnsibleFailJson(kwargs)

        def warn(self, msg):
            pass

    monkeypatch.setattr(mw_mod, "AnsibleModule", AM)
    monkeypatch.setattr(mw_mod, "get_client", lambda m: FakeClient())
    with pytest.raises(AnsibleExitJson):
        mw_mod.main()


def test_sla_run(sla_mod):
    with pytest.raises(AnsibleFailJson):
        sla_mod.run_module(FakeModule({"state": "absent"}), client=FakeClient())
    with pytest.raises(AnsibleFailJson):
        sla_mod.run_module(
            FakeModule({"state": "present", "window_days": 30}),
            client=FakeClient(),
        )
    with pytest.raises(AnsibleFailJson):
        sla_mod.run_module(
            FakeModule({"state": "present", "objective_pct": 99.9}),
            client=FakeClient(),
        )

    with pytest.raises(AnsibleExitJson) as ctx:
        sla_mod.run_module(
            FakeModule(
                {
                    "state": "present",
                    "objective_pct": 99.9,
                    "window_days": 30,
                    "scenario_id": "mon_1",
                }
            ),
            client=FakeClient(),
        )
    assert ctx.value.kwargs["changed"] is True

    client = FakeClient()
    client.slas["sla_1"] = {"id": "sla_1", "objectivePct": 99.9, "windowDays": 30}
    with pytest.raises(AnsibleExitJson) as ctx:
        sla_mod.run_module(
            FakeModule({"state": "absent", "id": "sla_1"}),
            client=client,
        )
    assert ctx.value.kwargs["changed"] is True

    with pytest.raises(AnsibleFailJson):
        bad = FakeClient()

        def boom(*a, **k):
            raise PathlyAPIError("x", status_code=500)

        bad.upsert_sla_target = boom
        sla_mod.run_module(
            FakeModule(
                {
                    "state": "present",
                    "objective_pct": 99.9,
                    "window_days": 30,
                }
            ),
            client=bad,
        )


def test_sla_main(monkeypatch, sla_mod):
    class AM(object):
        def __init__(self, *args, **kwargs):
            self.params = {
                "state": "present",
                "objective_pct": 99.9,
                "window_days": 30,
            }
            self.check_mode = False

        def exit_json(self, **kwargs):
            raise AnsibleExitJson(kwargs)

        def fail_json(self, **kwargs):
            raise AnsibleFailJson(kwargs)

        def warn(self, msg):
            pass

    monkeypatch.setattr(sla_mod, "AnsibleModule", AM)
    monkeypatch.setattr(sla_mod, "get_client", lambda m: FakeClient())
    with pytest.raises(AnsibleExitJson):
        sla_mod.main()


def test_info_run(info_mod):
    client = FakeClient()
    client.scenarios["mon_1"] = {"id": "mon_1", "name": "Home"}
    with pytest.raises(AnsibleExitJson) as ctx:
        info_mod.run_module(FakeModule({}), client=client)
    assert ctx.value.kwargs["changed"] is False

    with pytest.raises(AnsibleFailJson):

        def boom(*a, **k):
            raise PathlyAPIError("x", status_code=500)

        client.list_scenarios = boom
        info_mod.run_module(FakeModule({}), client=client)


def test_info_main(monkeypatch, info_mod):
    class AM(object):
        def __init__(self, *args, **kwargs):
            self.params = {}
            self.check_mode = True

        def exit_json(self, **kwargs):
            raise AnsibleExitJson(kwargs)

        def fail_json(self, **kwargs):
            raise AnsibleFailJson(kwargs)

        def warn(self, msg):
            pass

    monkeypatch.setattr(info_mod, "AnsibleModule", AM)
    client = FakeClient()
    monkeypatch.setattr(info_mod, "get_client", lambda m: client)
    with pytest.raises(AnsibleExitJson):
        info_mod.main()


def test_argument_specs(scenario_mod, webhook_mod, mw_mod, sla_mod, info_mod):
    assert "api_token" in scenario_mod.argument_spec()
    assert "url" in webhook_mod.argument_spec()
    assert "weekday" in mw_mod.argument_spec()
    assert "objective_pct" in sla_mod.argument_spec()
    assert "name" in info_mod.argument_spec()


def test_doc_fragment_loaded():
    from ansible_collections.pathlyhq.pathly.plugins.doc_fragments import auth

    assert "api_token" in auth.ModuleDocFragment.DOCUMENTATION
