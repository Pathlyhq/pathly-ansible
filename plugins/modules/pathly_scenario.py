#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pathly_scenario
short_description: Manage a Pathly HTTP scenario
description:
  - Create, update, or delete a Pathly HTTP monitoring scenario.
  - Idempotent by C(id) or by C(name).
  - Browser journeys are not managed (credentials would remain in state).
version_added: "0.1.0"
author:
  - Pathly (@pathlyhq)
options:
  state:
    description: Desired state of the scenario.
    type: str
    choices: [present, absent]
    default: present
  id:
    description: Scenario identifier (C(mon_…)). Used for lookup when set.
    type: str
  name:
    description: Display name (1–120 characters). Required when C(state=present).
    type: str
  type:
    description: Scenario type. Only C(http) is supported by this module.
    type: str
    choices: [http]
    default: http
  url:
    description: Monitored HTTP(S) URL. Required for HTTP scenarios when creating.
    type: str
  interval_sec:
    description: Period between runs in seconds (0–2592000).
    type: int
  method:
    description: HTTP method.
    type: str
    choices: [GET, HEAD]
  expected_status:
    description: Expected HTTP status (100–599).
    type: int
  max_latency_ms:
    description: Latency threshold in milliseconds (100–600000).
    type: int
  expect_text:
    description: Text expected in the HTTP response (max 500 characters).
    type: str
  regions:
    description: Probe regions (max 8).
    type: list
    elements: str
  tags:
    description: Free-form tags (max 10).
    type: list
    elements: str
  folder:
    description: Console folder (max 60 characters).
    type: str
  severity:
    description: Alert severity.
    type: str
    choices: [critical, major, minor]
  runbook:
    description: On-call instructions (max 2000 characters).
    type: str
  cron:
    description: Optional cron schedule.
    type: str
  enabled:
    description: When false, the scenario exists but does not run.
    type: bool
extends_documentation_fragment:
  - pathlyhq.pathly.auth
requirements:
  - python >= 3.9
"""

EXAMPLES = r"""
- name: Ensure an HTTP scenario exists
  pathlyhq.pathly.pathly_scenario:
    name: Home page
    url: https://shop.example.com/
    interval_sec: 300
    expect_text: Our products
    severity: major
    folder: Shop
    tags:
      - prod
  register: home

- name: Disable a scenario by id
  pathlyhq.pathly.pathly_scenario:
    id: "{{ home.scenario.id }}"
    name: Home page
    url: https://shop.example.com/
    interval_sec: 300
    enabled: false

- name: Remove a scenario by name
  pathlyhq.pathly.pathly_scenario:
    name: Home page
    state: absent
"""

RETURN = r"""
changed:
  description: Whether the scenario was created, updated, or deleted.
  type: bool
  returned: always
scenario:
  description: Scenario object in snake_case (null when absent and missing).
  type: dict
  returned: when a scenario is known
  contains:
    id:
      description: Pathly scenario id.
      type: str
    name:
      description: Display name.
      type: str
    url:
      description: Monitored URL.
      type: str
    last_status:
      description: Last known run verdict.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import (
    PathlyAPIError,
    auth_argument_spec,
)
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_common import (
    ensure_scenario,
    fail_from_api,
    get_client,
)


def argument_spec():
    spec = auth_argument_spec()
    spec.update(
        {
            "state": {
                "type": "str",
                "choices": ["present", "absent"],
                "default": "present",
            },
            "id": {"type": "str"},
            "name": {"type": "str"},
            "type": {"type": "str", "choices": ["http"], "default": "http"},
            "url": {"type": "str"},
            "interval_sec": {"type": "int"},
            "method": {"type": "str", "choices": ["GET", "HEAD"]},
            "expected_status": {"type": "int"},
            "max_latency_ms": {"type": "int"},
            "expect_text": {"type": "str"},
            "regions": {"type": "list", "elements": "str"},
            "tags": {"type": "list", "elements": "str"},
            "folder": {"type": "str"},
            "severity": {
                "type": "str",
                "choices": ["critical", "major", "minor"],
            },
            "runbook": {"type": "str"},
            "cron": {"type": "str"},
            "enabled": {"type": "bool"},
        }
    )
    return spec


def run_module(module, client=None):
    if module.params.get("state") == "present":
        if not module.params.get("name"):
            module.fail_json(msg="name is required when state=present")
        if not module.params.get("id") and module.params.get("interval_sec") is None:
            module.fail_json(
                msg="interval_sec is required when creating a scenario (state=present without id)"
            )
    client = client or get_client(module)
    try:
        result = ensure_scenario(client, module.params, check_mode=module.check_mode)
    except PathlyAPIError as exc:
        fail_from_api(module, exc)
        return  # pragma: no cover
    module.exit_json(**result)


def main():
    module = AnsibleModule(
        argument_spec=argument_spec(),
        supports_check_mode=True,
        required_one_of=[["id", "name"]],
    )
    run_module(module)


if __name__ == "__main__":
    main()
