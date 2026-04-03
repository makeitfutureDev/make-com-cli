# make-cli

A full-featured command-line interface for the [Make.com](https://make.com) automation platform.

## Install

```bash
git clone https://github.com/your-org/make.com-cli
cd make.com-cli
uv venv .venv && uv pip install -e .
source .venv/bin/activate
```

## Setup

```bash
make-cli config set api_token YOUR_API_TOKEN
make-cli config set zone eu1   # eu1 · eu2 · us1 · us2
```

Or via environment variables:
```bash
export MAKE_API_TOKEN=your-token
export MAKE_ZONE=eu1
```

Get your API token at: Make.com → Profile → API Tokens

## Quick Start

```bash
# See all orgs
make-cli org list

# Sync your entire org to a local folder
make-cli sync pull --org <org-id> --output ./make-backup

# Explore synced data
make-cli analyze tree --dir ./make-backup
make-cli analyze apps --dir ./make-backup
make-cli analyze stats --dir ./make-backup

# Interactive shell
make-cli repl
```

## Commands

| Group | Description |
|---|---|
| `org` | Organizations — list, get, create, update, delete, usage |
| `team` | Teams — list, get, create, delete, usage |
| `folder` | Scenario folders — list, create, update, delete |
| `scenario` | Scenarios — full CRUD + activate, deactivate, run, blueprint, clone, logs |
| `hook` | Webhooks/mailhooks — list, get, create, update, delete, config |
| `connection` | Connections — list, get |
| `execution` | Execution history — list, get, detail, stop |
| `datastore` | Data stores + records — full CRUD |
| `datastructure` | Data structures — list, get, create, update, delete, generate |
| `function` | Custom functions — list, get, create, update, delete, check |
| `key` | API keys — list, get, delete |
| `credential` | Credential requests — list, get, create, delete, decline, extend |
| `app` | Apps & modules — modules, module, docs, recommend |
| `tool` | AI tools — get, create, update |
| `validate` | Validation — blueprint, scheduling, hook-config, module-config |
| `user` | Current user — me |
| `sync` | **Sync entire org to local folder** |
| `analyze` | **Analyze local synced data** (no API calls) |
| `config` | CLI configuration |
| `repl` | Interactive shell |

All commands support `--json` for machine-readable output.

## Sync

Downloads the full org hierarchy to disk:

```
make-sync/
├── manifest.json       ← ID mappings + last sync timestamp
├── org.json
└── teams/
    └── <team-name>-<id>/
        ├── team.json
        ├── hooks.json
        ├── connections.json
        ├── datastructures.json
        ├── functions.json
        ├── keys.json
        ├── datastores/<name>-<id>/
        │   ├── datastore.json
        │   └── records.json
        ├── _unfiled/<scenario>-<id>/
        │   ├── scenario.json
        │   └── blueprint.json
        └── folders/<folder>-<id>/
            └── <scenario>-<id>/
                ├── scenario.json
                └── blueprint.json
```

Incremental sync (only changed scenarios):
```bash
make-cli sync pull --org <id> --output ./make-backup --incremental
```

## Analyze

All analyze commands work on local files — no API calls needed:

```bash
make-cli analyze stats                          # counts overview
make-cli analyze tree                           # visual hierarchy
make-cli analyze apps --top 20                  # most-used Make apps
make-cli analyze connections                    # connection references
make-cli analyze errors                         # invalid scenarios
make-cli analyze search "notion" --blueprint    # search in blueprints
```

## JSON Output

All commands support `--json` for piping:

```bash
make-cli --json scenario list --team 741170 | jq '.[].name'
make-cli --json scenario blueprint 4575008 | jq '.flow[].module'
make-cli --json org list | jq '.[].id'
```
