#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pathly_sla_target
short_description: Manage a Pathly SLA target
description:
  - Create or update an SLA target via the API upsert (C(PUT /v1/sla-targets)).
  - Targets are identified by the measured scenario (C(scenario_id) / C(monitor_id)).
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
    description: SLA target id (C(sla_…)). Required for C(state=absent).
    type: str
  scenario_id:
    description: Measured scenario. When omitted, the target is organization-wide.
    type: str
  monitor_id:
    description: Alias of C(scenario_id) (API field name).
    type: str
  name:
    description: Label shown in reports (max 120 characters).
    type: str
  objective_pct:
    description: Availability objective (50–100). Required when C(state=present).
    type: float
  window_days:
    description: Rolling window in days (1–365). Required when C(state=present).
    type: int
  exclude_maintenance:
    description: When true, maintenance windows do not consume the error budget.
    type: bool
  warn_at_budget_ratio:
    description: Budget consumption ratio that triggers a warning (0.1–1).
    type: float
  enabled:
    description: When false, the target stays defined but no longer warns.
    type: bool
extends_documentation_fragment:
  - pathlyhq.pathly.auth
"""

EXAMPLES = r"""
- name: Define a 99.9 percent SLA on a scenario
  pathlyhq.pathly.pathly_sla_target:
    scenario_id: "{{ home.scenario.id }}"
    name: Home page — 99.9 %
    objective_pct: 99.9
    window_days: 30
    exclude_maintenance: true
    warn_at_budget_ratio: 0.8
  register: sla

- name: Remove an SLA target
  pathlyhq.pathly.pathly_sla_target:
    id: "{{ sla.sla_target.id }}"
    state: absent
"""

RETURN = r"""
changed:
  description: Whether the target was upserted or deleted.
  type: bool
  returned: always
sla_target:
  description: SLA target object in snake_case.
  type: dict
  returned: when known
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import (
    PathlyAPIError,
    auth_argument_spec,
)
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_common import (
    ensure_sla_target,
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
            "name": {"type": "str"},
            "objective_pct": {"type": "float"},
            "window_days": {"type": "int"},
            "exclude_maintenance": {"type": "bool"},
            "warn_at_budget_ratio": {"type": "float"},
            "enabled": {"type": "bool"},
        }
    )
    return spec


def run_module(module, client=None):
    if module.params.get("state") == "absent" and not module.params.get("id"):
        module.fail_json(msg="id is required when state=absent")
    if module.params.get("state") == "present":
        if module.params.get("objective_pct") is None:
            module.fail_json(msg="objective_pct is required when state=present")
        if module.params.get("window_days") is None:
            module.fail_json(msg="window_days is required when state=present")
    client = client or get_client(module)
    try:
        result = ensure_sla_target(client, module.params, check_mode=module.check_mode)
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
