# pathly_maintenance_window

Gestionar una ventana de mantenimiento Pathly (puntual o semanal).

Las dos formas son excluyentes. Sin actualización in situ: cualquier cambio recrea el recurso.

Documentación canónica: [pathly_maintenance_window.md](../../modules/pathly_maintenance_window.md).

## Ejemplo

```yaml
- pathlyhq.pathly.pathly_maintenance_window:
    weekday: 7
    start_minute: 180
    duration_min: 120
    reason: Copia semanal
```
