#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pathly_scenario_info
short_description: List or fetch Pathly scenarios
description:
  - Retrieve one scenario by C(id), filter by C(name), or list all scenarios.
  - Always returns C(changed=false).
version_added: "0.1.0"
author:
  - Pathly (@pathlyhq)
options:
  id:
    description: Scenario identifier to fetch.
    type: str
  name:
    description: Filter the listing by exact name.
    type: str
extends_documentation_fragment:
  - pathlyhq.pathly.auth
"""

EXAMPLES = r"""
- name: List all scenarios
  pathlyhq.pathly.pathly_scenario_info:
  register: all_scenarios

- name: Fetch one scenario by id
  pathlyhq.pathly.pathly_scenario_info:
    id: mon_01H8ZKEXAMPLE
  register: one

- name: Find scenarios named Home page
  pathlyhq.pathly.pathly_scenario_info:
    name: Home page
"""

RETURN = r"""
changed:
  description: Always false.
  type: bool
  returned: always
scenarios:
  description: List of scenario objects in snake_case.
  type: list
  elements: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import (
    PathlyAPIError,
    auth_argument_spec,
)
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_common import (
    fail_from_api,
    gather_scenario_info,
    get_client,
)


def argument_spec():
    spec = auth_argument_spec()
    spec.update(
        {
            "id": {"type": "str"},
            "name": {"type": "str"},
        }
    )
    return spec


def run_module(module, client=None):
    client = client or get_client(module)
    try:
        result = gather_scenario_info(client, module.params)
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
