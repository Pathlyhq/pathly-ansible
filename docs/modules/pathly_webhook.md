# pathly_webhook

Manage a Pathly outbound webhook.

The API never returns the destination URL on read. The HMAC `secret` is returned only at creation time. Prefer storing it in a secret manager immediately.

## Parameters

| Parameter | Type | Required | Comments |
|-----------|------|----------|----------|
| state | str | no | `present` (default) or `absent` |
| id | str | for absent | Webhook id (`wh_…`) |
| url | str | for present | Destination HTTPS URL (`no_log`) |
| events | list | no | `run.failed`, `run.recovered` |
| api_token / api_url | str | no | Prefer environment variables |

## Examples

```yaml
- pathlyhq.pathly.pathly_webhook:
    url: "{{ lookup('env', 'PATHLY_WEBHOOK_URL') }}"
    events: [run.failed, run.recovered]
  no_log: true
```

## Return values

- `changed` (bool)
- `webhook` (dict) — may include `secret` after create only
