# pathly_scenario

Gérer un scénario HTTP Pathly (`present` / `absent`).

Idempotent par `id` ou par `name`. Les parcours navigateur ne sont pas pris en charge.

## Paramètres

Voir la [documentation anglaise](../../modules/pathly_scenario.md) (canonique) pour le tableau complet des paramètres.

## Exemple

```yaml
- pathlyhq.pathly.pathly_scenario:
    name: Page d'accueil
    url: https://shop.example.com/
    interval_sec: 300
    severity: major
```

## Valeurs de retour

- `changed` (bool)
- `scenario` (dict)
