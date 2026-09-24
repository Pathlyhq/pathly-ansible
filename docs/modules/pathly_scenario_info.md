# pathly_scenario_info

List or fetch Pathly scenarios. Always returns `changed=false`.

## Parameters

| Parameter | Type | Comments |
|-----------|------|----------|
| id | str | Fetch one scenario |
| name | str | Filter listing by exact name |
| api_token / api_url | str | Prefer env vars |

## Examples

```yaml
- pathlyhq.pathly.pathly_scenario_info:
  register: all_scenarios
```

## Return values

- `changed` (bool) — always `false`
- `scenarios` (list of dict)
