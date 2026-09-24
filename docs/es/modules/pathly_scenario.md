# pathly_scenario

Gestionar un escenario HTTP Pathly (`present` / `absent`).

Idempotente por `id` o por `name`. Los recorridos de navegador no están soportados.

## Parámetros

Véase la [documentación en inglés](../../modules/pathly_scenario.md) (canónica) para la tabla completa de parámetros.

## Ejemplo

```yaml
- pathlyhq.pathly.pathly_scenario:
    name: Página de inicio
    url: https://shop.example.com/
    interval_sec: 300
    severity: major
```

## Valores de retorno

- `changed` (bool)
- `scenario` (dict)
