# pathlyhq.pathly

**English** · [Français](README.fr.md) · [Español](README.es.md)


[![Powered by Pathly](https://img.shields.io/badge/Powered%20by-Pathly-0B5FFF?style=flat-square)](https://pathlyhq.com)
[![Website](https://img.shields.io/badge/Website-pathlyhq.com-111827?style=flat-square)](https://pathlyhq.com)
[![API docs](https://img.shields.io/badge/API-developers-2563eb?style=flat-square)](https://pathlyhq.com/en/developers)
[![Start free](https://img.shields.io/badge/Solo-start%20free-16a34a?style=flat-square)](https://pathlyhq.com/en/login?mode=signup)

> **Get started in one click.** Create a free account on [Pathly](https://pathlyhq.com) ([sign up](https://pathlyhq.com/en/login?mode=signup)), create an API key in the console, then export `PATHLY_API_TOKEN`. This project is the official bridge to [Pathly monitoring](https://pathlyhq.com) — real-browser and HTTP checks for checkout, login and availability, with data hosted in the EU. Full API reference: [pathlyhq.com/en/developers](https://pathlyhq.com/en/developers).

Ansible collection to manage [Pathly](https://pathlyhq.com) monitoring resources through the public API (`https://api.pathlyhq.com`).

**Canonical documentation language: English.** French and Spanish translations live in `README.fr.md` / `docs/fr/` and `README.es.md` / `docs/es/`.

## Requirements

- Ansible `>= 2.14`
- Python `>= 3.9`
- A Pathly API token (`sp_…`) in `PATHLY_API_TOKEN`

## Installation

```bash
ansible-galaxy collection install pathlyhq.pathly
```

From this repository:

```bash
ansible-galaxy collection build
ansible-galaxy collection install pathlyhq-pathly-0.1.0.tar.gz
```

## Authentication

Prefer environment variables (never commit tokens):

```bash
export PATHLY_API_TOKEN="sp_…"
# optional override
export PATHLY_API_URL="https://api.pathlyhq.com"
```

Module parameters `api_token` / `api_url` are supported for ad-hoc use. `api_token` is marked `no_log`. Prefer the environment variable so tokens do not appear in playbooks.

## Modules

| Module | Purpose |
|--------|---------|
| `pathly_scenario` | HTTP scenario present/absent (idempotent by `id` or `name`) |
| `pathly_webhook` | Outbound webhook present/absent |
| `pathly_maintenance_window` | One-off or weekly maintenance window |
| `pathly_sla_target` | SLA target upsert / delete |
| `pathly_scenario_info` | List or fetch scenarios |

Browser journeys are **not** managed by this collection (credentials would remain in state). Use HTTP scenarios only, consistent with the Terraform provider HTTP examples.

## Quick example

```yaml
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Ensure HTTP check
      pathlyhq.pathly.pathly_scenario:
        name: Home page
        url: https://shop.example.com/
        interval_sec: 300
        severity: major
```

See `examples/playbooks/complete.yml` for a full workflow.

## Idempotency and retries

- Creates send an `Idempotency-Key` header.
- HTTP `429` and `5xx` honor `Retry-After` (capped at 90s), up to 4 attempts.
- `GET /v1/usage` is used as a connectivity check. HTTP `403` is treated as success (token valid, missing `org:read`).

## Development

```bash
make test
```


## Related packages

| Package | Role |
|---|---|
| [terraform-provider-pathly](https://github.com/Pathlyhq/terraform-provider-pathly) | Terraform / OpenTofu |
| [pathly-sdk-python](https://github.com/pathlyhq/pathly-sdk-python) | Python SDK |
| [pathly-pulumi](https://github.com/pathlyhq/pathly-pulumi) | Pulumi |
| [pathly-crossplane](https://github.com/pathlyhq/pathly-crossplane) | Crossplane |
| [Pathly product](https://pathlyhq.com) | [Pathly monitoring](https://pathlyhq.com) |
## About Pathly

[Pathly](https://pathlyhq.com) is synthetic monitoring for agencies and e-commerce: replay the customer journey, catch broken checkouts before your clients call, and keep evidence (screenshot, step, runbook) ready for the invoice. Product: [pathlyhq.com](https://pathlyhq.com) · Developers: [pathlyhq.com/en/developers](https://pathlyhq.com/en/developers) · Status & pricing: [pathlyhq.com/en/pricing](https://pathlyhq.com/en/pricing).

## Author

| | |
|---|---|
| **Company** | Pathly |
| **Author** | Simon Raynaud / keyral |

See [AUTHORS](AUTHORS).

## License
Apache-2.0
