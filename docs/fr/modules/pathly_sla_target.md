# pathly_sla_target

Gérer une cible SLA Pathly (upsert `PUT /v1/sla-targets`).

Documentation canonique : [pathly_sla_target.md](../../modules/pathly_sla_target.md).

## Exemple

```yaml
- pathlyhq.pathly.pathly_sla_target:
    scenario_id: "{{ home.scenario.id }}"
    name: Page d'accueil — 99,9 %
    objective_pct: 99.9
    window_days: 30
```
