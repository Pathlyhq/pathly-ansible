#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: pathly_webhook
short_description: Manage a Pathly outbound webhook
description:
  - Create or delete a signed outbound webhook.
  - The API never returns the destination URL on read. The HMAC C(secret) is
    returned only at creation time.
  - There is no in-place update. Changing C(events) deletes and recreates the
    webhook when C(id) is provided.
version_added: "0.1.0"
author:
  - Pathly (@pathlyhq)
options:
  state:
    description: Desired state of the webhook.
    type: str
    choices: [present, absent]
    default: present
  id:
    description: Webhook identifier (C(wh_…)). Required for C(state=absent).
    type: str
  url:
    description:
      - Destination HTTPS URL.
      - Required when C(state=present).
    type: str
    no_log: true
  events:
    description: Events to subscribe to.
    type: list
    elements: str
    choices: [run.failed, run.recovered]
extends_documentation_fragment:
  - pathlyhq.pathly.auth
"""

EXAMPLES = r"""
- name: Create an alert webhook
  pathlyhq.pathly.pathly_webhook:
    url: "{{ lookup('env', 'PATHLY_WEBHOOK_URL') }}"
    events:
      - run.failed
      - run.recovered
  register: alerts
  no_log: true

- name: Remove a webhook
  pathlyhq.pathly.pathly_webhook:
    id: "{{ alerts.webhook.id }}"
    state: absent
"""

RETURN = r"""
changed:
  description: Whether the webhook was created, replaced, or deleted.
  type: bool
  returned: always
webhook:
  description: Webhook object (secret only present after create).
  type: dict
  returned: when known
  contains:
    id:
      description: Webhook id.
      type: str
    secret:
      description: HMAC signing secret (create only).
      type: str
    url_fingerprint:
      description: Fingerprint of the destination URL.
      type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_api import (
    PathlyAPIError,
    auth_argument_spec,
)
from ansible_collections.pathlyhq.pathly.plugins.module_utils.pathly_common import (
    ensure_webhook,
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
            "url": {"type": "str", "no_log": True},
            "events": {
                "type": "list",
                "elements": "str",
                "choices": ["run.failed", "run.recovered"],
            },
        }
    )
    return spec


def run_module(module, client=None):
    if module.params.get("state") == "present" and not module.params.get("url"):
        module.fail_json(msg="url is required when state=present")
    if module.params.get("state") == "absent" and not module.params.get("id"):
        module.fail_json(msg="id is required when state=absent")
    client = client or get_client(module)
    try:
        result = ensure_webhook(client, module.params, check_mode=module.check_mode)
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
