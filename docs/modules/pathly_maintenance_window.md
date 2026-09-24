# pathly_maintenance_window

Manage a Pathly maintenance window (one-off or weekly).

Forms are mutually exclusive:

- one-off: `starts_at` + `ends_at`
- weekly: `weekday` + `start_minute` + `duration_min`

The API does not support in-place updates. Changes delete and recreate.

## Parameters

| Parameter | Type | Comments |
|-----------|------|----------|
| state | str | `present` / `absent` |
| id | str | Required for `absent` |
| scenario_id / monitor_id | str | Optional scope |
| starts_at / ends_at | str | One-off ISO 8601 |
| weekday / start_minute / duration_min | int | Weekly form |
| reason | str | Displayed reason |
| api_token / api_url | str | Prefer env vars |

## Examples

```yaml
- pathlyhq.pathly.pathly_maintenance_window:
    weekday: 7
    start_minute: 180
    duration_min: 120
    reason: Weekly backup
```

## Return values

- `changed` (bool)
- `maintenance_window` (dict)
