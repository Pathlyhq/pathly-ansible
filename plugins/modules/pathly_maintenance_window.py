#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pathly_maintenance_window
short_description: Manage a Pathly maintenance window
description:
  - Create or delete a one-off or weekly maintenance window.
  - One-off form uses C(starts_at)/C(ends_at). Weekly form uses
    C(weekday)/C(start_minute)/C(duration_min). The two forms are mutually exclusive.
  - The API does not support in-place updates. Any change deletes and recreates.
version_added: "0.1.0"
author:
  - Pathly (@pathlyhq)
options:
  state:
    description: Desired state.
    type: str
    choices: [present, absent]
    default: present
  id:
    description: Window identifier (C(mw_…)). Required for C(state=absent).
    type: str
  scenario_id:
    description: Targeted scenario id. When omitted, the window is organization-wide.
    type: str
  monitor_id:
    description: Alias of C(scenario_id) (API field name).
    type: str
  starts_at:
    description: One-off start (ISO 8601).
    type: str
  ends_at:
    description: One-off end (ISO 8601). Max duration 90 days.
    type: str
  weekday:
    description: Weekly day, 1 (Monday) through 7 (Sunday).
    type: int
  start_minute:
    description: Start minute within the day UTC (0–1439).
    type: int
  duration_min:
    description: Weekly duration in minutes (15–1440).
    type: int
  reason:
    description: Reason shown in the console (max 500 characters).
    type: str
extends_documentation_fragment:
  - pathlyhq.pathly.auth
"""

EXAMPLES = r"""
- name: Weekly backup window
  pathlyhq.pathly.pathly_maintenance_window:
    weekday: 7
    start_minute: 180
    duration_min: 120
    reason: Weekly backup
  register: backup

- name: One-off migration window
  pathlyhq.pathly.pathly_maintenance_window:
    scenario_id: "{{ home.scenario.id }}"
    starts_at: "2026-10-04T22:00:00Z"
    ends_at: "2026-10-05T02:00:00Z"
    reason: Checkout funnel migration

- name: Remove a window
  pathlyhq.pathly.pathly_maintenance_window:
    id: "{{ backup.maintenance_window.id }}"
    state: absent
"""

RETURN = r"""
changed:
  description: Whether the window was created, replaced, or deleted.
  type: bool
  returned: always
maintenance_window:
  description: Window object in snake_case.
  type: dict
  returned: when known
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import (
    PathlyAPIError,
    auth_argument_spec,
)
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_common import (
    ensure_maintenance_window,
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
            "scenario_id": {"type": "str"},
            "monitor_id": {"type": "str"},
            "starts_at": {"type": "str"},
            "ends_at": {"type": "str"},
            "weekday": {"type": "int"},
            "start_minute": {"type": "int"},
            "duration_min": {"type": "int"},
            "reason": {"type": "str"},
        }
    )
    return spec


def run_module(module, client=None):
    if module.params.get("state") == "absent" and not module.params.get("id"):
        module.fail_json(msg="id is required when state=absent")
    client = client or get_client(module)
    try:
        result = ensure_maintenance_window(
            client, module.params, check_mode=module.check_mode
        )
    except PathlyAPIError as exc:
        fail_from_api(module, exc)
        return  # pragma: no cover
    module.exit_json(**result)


def main():
    module = AnsibleModule(
        argument_spec=argument_spec(),
        supports_check_mode=True,
    )
    run_module(module)


if __name__ == "__main__":
    main()
