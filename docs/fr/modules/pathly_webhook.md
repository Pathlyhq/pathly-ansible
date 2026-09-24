# pathly_webhook

Gérer un webhook sortant Pathly.

L’API ne renvoie jamais l’URL en lecture. Le `secret` HMAC n’est renvoyé qu’à la création.

Documentation canonique : [pathly_webhook.md](../../modules/pathly_webhook.md).

## Exemple

```yaml
- pathlyhq.pathly.pathly_webhook:
    url: "{{ lookup('env', 'PATHLY_WEBHOOK_URL') }}"
    events: [run.failed, run.recovered]
  no_log: true
```
