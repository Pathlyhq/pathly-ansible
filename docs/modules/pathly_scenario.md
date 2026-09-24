# pathly_scenario

Manage a Pathly HTTP monitoring scenario (`present` / `absent`).

Idempotent by `id` or by `name`. Browser journeys are not supported.

## Synopsis

- Create, update, or delete an HTTP scenario.
- Auth via `PATHLY_API_TOKEN` / `PATHLY_API_URL` (preferred) or `api_token` / `api_url`.

## Parameters

| Parameter | Type | Required | Default | Comments |
|-----------|------|----------|---------|----------|
| state | str | no | present | `present` or `absent` |
| id | str | no | | Scenario id (`mon_…`) |
| name | str | when present | | Display name |
| type | str | no | http | Only `http` |
| url | str | no | | Monitored URL |
| interval_sec | int | when creating | | Period between runs |
| method | str | no | | `GET` or `HEAD` |
| expected_status | int | no | | Expected HTTP status |
| max_latency_ms | int | no | | Latency threshold |
| expect_text | str | no | | Expected body text |
| regions | list | no | | Probe regions |
| tags | list | no | | Tags |
| folder | str | no | | Console folder |
| severity | str | no | | `critical`, `major`, `minor` |
| runbook | str | no | | On-call text |
| cron | str | no | | Cron schedule |
| enabled | bool | no | | Run flag |
| api_token | str | no | | Prefer env `PATHLY_API_TOKEN` |
| api_url | str | no | | Prefer env `PATHLY_API_URL` |

## Examples

```yaml
- pathlyhq.pathly.pathly_scenario:
    name: Home page
    url: https://shop.example.com/
    interval_sec: 300
    severity: major
```

## Return values

- `changed` (bool)
- `scenario` (dict) — snake_case projection of the API object
