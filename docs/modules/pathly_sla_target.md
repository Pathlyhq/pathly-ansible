# pathly_sla_target

Manage a Pathly SLA target.

Creation and update use the same API upsert (`PUT /v1/sla-targets`), keyed by the measured scenario (`scenario_id` / `monitor_id`).

## Parameters

| Parameter | Type | Required | Comments |
|-----------|------|----------|----------|
| state | str | no | `present` / `absent` |
| id | str | for absent | Target id (`sla_…`) |
| scenario_id / monitor_id | str | no | Measured scenario |
| name | str | no | Report label |
| objective_pct | float | for present | 50–100 |
| window_days | int | for present | 1–365 |
| exclude_maintenance | bool | no | Exclude MW from budget |
| warn_at_budget_ratio | float | no | 0.1–1 |
| enabled | bool | no | Warning flag |
| api_token / api_url | str | no | Prefer env vars |

## Examples

```yaml
- pathlyhq.pathly.pathly_sla_target:
    scenario_id: "{{ home.scenario.id }}"
    name: Home page — 99.9 %
    objective_pct: 99.9
    window_days: 30
```

## Return values

- `changed` (bool)
- `sla_target` (dict)
