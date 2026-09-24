# pathly_webhook

Gestionar un webhook saliente Pathly.

La API nunca devuelve la URL en lectura. El `secret` HMAC solo se devuelve en la creación.

Documentación canónica: [pathly_webhook.md](../../modules/pathly_webhook.md).

## Ejemplo

```yaml
- pathlyhq.pathly.pathly_webhook:
    url: "{{ lookup('env', 'PATHLY_WEBHOOK_URL') }}"
    events: [run.failed, run.recovered]
  no_log: true
```
