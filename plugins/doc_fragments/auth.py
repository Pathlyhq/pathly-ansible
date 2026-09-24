# -*- coding: utf-8 -*-
# Copyright 2026 Pathly
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  api_token:
    description:
      - Pathly API token (prefix C(sp_)).
      - Prefer the environment variable C(PATHLY_API_TOKEN).
      - When set as a module parameter, Ansible marks it C(no_log), but the
        environment variable remains the recommended approach.
    type: str
    required: false
  api_url:
    description:
      - Base URL of the Pathly API.
      - Defaults to C(https://api.pathlyhq.com) or C(PATHLY_API_URL).
    type: str
    required: false
"""
