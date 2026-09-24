# pathlyhq.pathly

[English](README.md) · **Français** · [Español](README.es.md)


[![Powered by Pathly](https://img.shields.io/badge/Powered%20by-Pathly-0B5FFF?style=flat-square)](https://pathlyhq.com)
[![Website](https://img.shields.io/badge/Website-pathlyhq.com-111827?style=flat-square)](https://pathlyhq.com)
[![API docs](https://img.shields.io/badge/API-developers-2563eb?style=flat-square)](https://pathlyhq.com/fr/developers)
[![Start free](https://img.shields.io/badge/Solo-start%20free-16a34a?style=flat-square)](https://pathlyhq.com/fr/login?mode=signup)

> **Démarrage en un clic.** Créez un compte gratuit sur [Pathly](https://pathlyhq.com) ([inscription](https://pathlyhq.com/fr/login?mode=signup)), générez une clé API dans la console, puis exportez `PATHLY_API_TOKEN`. Ce dépôt est le pont officiel vers [la surveillance Pathly](https://pathlyhq.com) — contrôles HTTP et parcours navigateur (panier, connexion, disponibilité), données hébergées dans l’UE. Référence API : [pathlyhq.com/fr/developers](https://pathlyhq.com/fr/developers).

Collection Ansible pour gérer les ressources de monitoring [Pathly](https://pathlyhq.com) via l’API publique (`https://api.pathlyhq.com`).

**La documentation canonique est en anglais** (`README.md`, `docs/modules/`). Ce fichier et `docs/fr/` sont des traductions.

## Prérequis

- Ansible `>= 2.14`
- Python `>= 3.9`
- Un jeton API Pathly (`sp_…`) dans `PATHLY_API_TOKEN`

## Installation

```bash
ansible-galaxy collection install pathlyhq.pathly
```

## Authentification

Préférez les variables d’environnement (ne jamais committer de jetons) :

```bash
export PATHLY_API_TOKEN="sp_…"
export PATHLY_API_URL="https://api.pathlyhq.com"   # optionnel
```

Les paramètres de module `api_token` / `api_url` existent pour les usages ponctuels. `api_token` est marqué `no_log`. Préférez la variable d’environnement.

## Modules

| Module | Rôle |
|--------|------|
| `pathly_scenario` | Scénario HTTP present/absent (idempotent par `id` ou `name`) |
| `pathly_webhook` | Webhook sortant present/absent |
| `pathly_maintenance_window` | Fenêtre de maintenance ponctuelle ou hebdomadaire |
| `pathly_sla_target` | Cible SLA (upsert) / suppression |
| `pathly_scenario_info` | Liste ou lecture de scénarios |

Les parcours navigateur **ne sont pas** gérés (les identifiants resteraient dans l’état). HTTP uniquement.

## Exemple rapide

```yaml
- hosts: localhost
  gather_facts: false
  tasks:
    - name: Garantir un contrôle HTTP
      pathlyhq.pathly.pathly_scenario:
        name: Page d'accueil
        url: https://shop.example.com/
        interval_sec: 300
        severity: major
```

Voir `examples/playbooks/complete.yml`.


## Packages associés

| Package | Role |
|---|---|
| [pathly-terraform-provider](https://github.com/pathlyhq/pathly-terraform-provider) | Terraform / OpenTofu |
| [pathly-sdk-python](https://github.com/pathlyhq/pathly-sdk-python) | Python SDK |
| [pathly-pulumi](https://github.com/pathlyhq/pathly-pulumi) | Pulumi |
| [pathly-crossplane](https://github.com/pathlyhq/pathly-crossplane) | Crossplane |
| [Pathly product](https://pathlyhq.com) | [Pathly monitoring](https://pathlyhq.com) |
## À propos de Pathly

[Pathly](https://pathlyhq.com) surveille les parcours clients des agences et e-commerçants : rejoue le tunnel, détecte un checkout cassé avant l’appel du client, et joint la preuve (capture, étape, consigne) à la facture de maintenance. Produit : [pathlyhq.com](https://pathlyhq.com) · Développeurs : [pathlyhq.com/fr/developers](https://pathlyhq.com/fr/developers) · Tarifs : [pathlyhq.com/fr/pricing](https://pathlyhq.com/fr/pricing).

## Auteur

| | |
|---|---|
| **Entreprise** | Pathly |
| **Auteur** | Simon Raynaud / keyral |

Voir [AUTHORS](AUTHORS).

## Licence
Apache-2.0
