# pathly_maintenance_window

Gérer une fenêtre de maintenance Pathly (ponctuelle ou hebdomadaire).

Les deux formes sont exclusives. Pas de mise à jour en place : tout changement recrée la ressource.

Documentation canonique : [pathly_maintenance_window.md](../../modules/pathly_maintenance_window.md).

## Exemple

```yaml
- pathlyhq.pathly.pathly_maintenance_window:
    weekday: 7
    start_minute: 180
    duration_min: 120
    reason: Sauvegarde hebdomadaire
```
