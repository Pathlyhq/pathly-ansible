# pathly_sla_target

Gestionar un objetivo SLA Pathly (upsert `PUT /v1/sla-targets`).

Documentación canónica: [pathly_sla_target.md](../../modules/pathly_sla_target.md).

## Ejemplo

```yaml
- pathlyhq.pathly.pathly_sla_target:
    scenario_id: "{{ home.scenario.id }}"
    name: Página de inicio — 99,9 %
    objective_pct: 99.9
    window_days: 30
```
