# pathlyhq.pathly

[English](README.md) · [Français](README.fr.md) · **Español**


[![Powered by Pathly](https://img.shields.io/badge/Powered%20by-Pathly-0B5FFF?style=flat-square)](https://pathlyhq.com)
[![Website](https://img.shields.io/badge/Website-pathlyhq.com-111827?style=flat-square)](https://pathlyhq.com)
[![API docs](https://img.shields.io/badge/API-developers-2563eb?style=flat-square)](https://pathlyhq.com/es/developers)
[![Start free](https://img.shields.io/badge/Solo-start%20free-16a34a?style=flat-square)](https://pathlyhq.com/es/login?mode=signup)

> **Empiece en un clic.** Cree una cuenta gratuita en [Pathly](https://pathlyhq.com) ([registro](https://pathlyhq.com/es/login?mode=signup)), genere una clave API en la consola y exporte `PATHLY_API_TOKEN`. Este repositorio es el puente oficial hacia [la monitorización Pathly](https://pathlyhq.com): comprobaciones HTTP y de navegador (carrito, login, disponibilidad), con datos en la UE. Referencia API: [pathlyhq.com/es/developers](https://pathlyhq.com/es/developers).

Colección Ansible para gestionar recursos de monitorización [Pathly](https://pathlyhq.com) a través de la API pública (`https://api.pathlyhq.com`).

**La documentación canónica está en inglés** (`README.md`, `docs/modules/`). Este archivo y `docs/es/` son traducciones.

## Requisitos

- Ansible `>= 2.14`
- Python `>= 3.9`
- Un token de API Pathly (`sp_…`) en `PATHLY_API_TOKEN`

## Instalación

```bash
ansible-galaxy collection install pathlyhq.pathly
```

Desde este repositorio:

```bash
ansible-galaxy collection build
ansible-galaxy collection install pathlyhq-pathly-0.1.0.tar.gz
```

## Autenticación

Prefiera variables de entorno (nunca haga commit de tokens):

```bash
export PATHLY_API_TOKEN="sp_…"
# anulación opcional
export PATHLY_API_URL="https://api.pathlyhq.com"
```

Los parámetros de módulo `api_token` / `api_url` existen para usos puntuales. `api_token` está marcado `no_log`. Prefiera la variable de entorno para que los tokens no aparezcan en los playbooks.

## Módulos

| Módulo | Función |
|--------|---------|
| `pathly_scenario` | Escenario HTTP present/absent (idempotente por `id` o `name`) |
| `pathly_webhook` | Webhook saliente present/absent |
| `pathly_maintenance_window` | Ventana de mantenimiento puntual o semanal |
| `pathly_sla_target` | Objetivo SLA (upsert) / eliminación |
| `pathly_scenario_info` | Listar o leer escenarios |

Los recorridos de navegador **no** se gestionan con esta colección (las credenciales permanecerían en el estado). Solo escenarios HTTP, coherente con los ejemplos HTTP del provider Terraform.

## Ejemplo rápido

```yaml
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Garantizar un control HTTP
      pathlyhq.pathly.pathly_scenario:
        name: Página de inicio
        url: https://shop.example.com/
        interval_sec: 300
        severity: major
```

Véase `examples/playbooks/complete.yml` para un flujo completo.

## Idempotencia y reintentos

- Las creaciones envían una cabecera `Idempotency-Key`.
- HTTP `429` y `5xx` respetan `Retry-After` (máximo 90 s), hasta 4 intentos.
- `GET /v1/usage` se usa como comprobación de conectividad. HTTP `403` se trata como éxito (token válido, falta `org:read`).

## Desarrollo

```bash
make test
```


## Paquetes relacionados

| Package | Role |
|---|---|
| [terraform-provider-pathly](https://github.com/Pathlyhq/terraform-provider-pathly) | Terraform / OpenTofu |
| [pathly-sdk-python](https://github.com/pathlyhq/pathly-sdk-python) | Python SDK |
| [pathly-pulumi](https://github.com/pathlyhq/pathly-pulumi) | Pulumi |
| [pathly-crossplane](https://github.com/pathlyhq/pathly-crossplane) | Crossplane |
| [Pathly product](https://pathlyhq.com) | [Pathly monitoring](https://pathlyhq.com) |
## Acerca de Pathly

[Pathly](https://pathlyhq.com) es monitorización sintética para agencias y e-commerce: reproduce el recorrido del cliente, detecta un checkout roto antes de la llamada, y deja la prueba (captura, paso, runbook) lista para la factura. Producto: [pathlyhq.com](https://pathlyhq.com) · Desarrolladores: [pathlyhq.com/es/developers](https://pathlyhq.com/es/developers) · Precios: [pathlyhq.com/es/pricing](https://pathlyhq.com/es/pricing).

## Autor

| | |
|---|---|
| **Empresa** | Pathly |
| **Autor** | Simon Raynaud / keyral |

Véase [AUTHORS](AUTHORS).

## Licencia
Apache-2.0
