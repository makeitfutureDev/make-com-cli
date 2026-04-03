# make-cli Architecture

## Overview

make-cli is a Python command-line interface for the Make.com automation platform (formerly Integromat). It wraps the Make.com REST API v2 to enable scripted management of organizations, teams, scenario folders, and scenarios — and provides a powerful sync engine to download an entire organization's scenario library to a local folder for analysis, version control, and offline inspection.

**Target users**: Make.com power users, automation engineers, DevOps teams managing large Make.com deployments.

**Key use cases**:
- Sync all scenarios from an org to a local folder for analysis and version control
- Inspect scenario blueprints (the JSON automation graphs) locally with any tool
- Manage orgs/teams/folders/scenarios from the terminal or scripts
- Pipe `--json` output into `jq`, scripts, or AI agents

---

## Directory Structure

```
make.com-cli/
├── pyproject.toml                  # Package metadata and dependencies
├── DOCS/
│   └── architecture.md             # This document (continuously updated)
├── make_cli/                       # Main Python package (installed as make-cli)
│   ├── __init__.py
│   ├── cli.py                      # Root Click group, command registration
│   ├── context.py                  # CliContext dataclass shared across commands
│   └── commands/
│       ├── __init__.py
│       ├── config_cmd.py           # make-cli config show/set/unset
│       ├── orgs.py                 # make-cli org list/get/create/update/delete/usage
│       ├── teams.py                # make-cli team list/get/create/delete/usage
│       ├── folders.py              # make-cli folder list/create/update/delete
│       ├── scenarios.py            # make-cli scenario list/get/create/update/delete/run/...
│       ├── sync.py                 # make-cli sync pull (the core sync engine)
│       └── analyze.py              # make-cli analyze stats/apps/connections/errors/tree/search
├── utils/
│   ├── __init__.py
│   └── make_backend.py             # MakeClient HTTP client wrapping requests
├── core/
│   ├── __init__.py
│   ├── config.py                   # Config file + env var resolution
│   └── output.py                   # print_table, print_kv, print_json, error, success
└── tests/
    └── __init__.py
```

---

## Technology Stack

| Library | Version | Why |
|---|---|---|
| click | >=8.1 | Industry-standard Python CLI framework. Command groups, options, args, context passing. |
| rich | >=13.0 | Beautiful terminal output: tables, progress bars, styled text. |
| requests | >=2.31 | HTTP client for Make.com API calls. Session-based for connection reuse. |
| prompt-toolkit | >=3.0 | Interactive REPL with tab-completion and history (Phase 7). |
| pyyaml | >=6.0 | Config file (YAML) read/write. |

---

## Make.com API v2 Reference

### Base URL
```
https://{zone}.make.com/api/v2
```
Zones: `eu1`, `eu2`, `us1`, `us2`. Must match the zone where your Make.com account is hosted.

### Authentication
Header: `Authorization: Token {your_api_token}`
Token format: UUID-like, e.g. `12345678-12ef-abcd-1234-1234567890ab`
Obtain from: Make.com → Profile → API Tokens

### Pagination
Query parameters use bracket notation (`pg[offset]`, `pg[limit]`, etc.):
- `pg[offset]` — skip N records (default: 0)
- `pg[limit]` — max records per page (MakeClient uses 100)
- `pg[sortBy]` — field name to sort by
- `pg[sortDir]` — `asc` or `desc`

The `MakeClient.paginate()` method handles auto-pagination automatically.

### Response Envelopes
All responses are JSON-wrapped:
- Single object: `{ "scenario": { ... } }`
- List: `{ "scenarios": [ ... ], "pg": { ... } }`

### Zones
| Zone | Base URL |
|---|---|
| EU1 | https://eu1.make.com/api/v2 |
| EU2 | https://eu2.make.com/api/v2 |
| US1 | https://us1.make.com/api/v2 |
| US2 | https://us2.make.com/api/v2 |

---

## Command Groups

| Group | Commands | API Endpoints Used |
|---|---|---|
| config | show, set, unset | (local config file only) |
| org | list, get, create, update, delete, usage | GET/POST/PATCH/DELETE /organizations |
| team | list, get, create, delete, usage | GET/POST/DELETE /teams |
| folder | list, create, update, delete | GET/POST/PATCH/DELETE /scenarios-folders |
| scenario | list, get, create, update, delete, activate, deactivate, run, blueprint, versions, clone, logs | GET/POST/PATCH/DELETE /scenarios + sub-resources |
| sync | pull | All of the above, orchestrated with progress display |
| analyze | stats, apps, connections, errors, tree, search | (reads local synced files — no API calls) |

---

## Configuration System

Resolution precedence (highest to lowest):
1. CLI flag (`--token`, `--zone`)
2. Environment variable (`MAKE_API_TOKEN`, `MAKE_ZONE`)
3. Config file (`~/.make-cli/config.yaml`)
4. Default (`zone` defaults to `eu1`)

Config file location: `~/.make-cli/config.yaml`

Supported keys:
| Key | Description | Example |
|---|---|---|
| api_token | Make.com API token | `abc123-...` |
| zone | API zone | `eu1` |
| default_org_id | Default organization ID | `12345` |

Manage with:
```bash
make-cli config set api_token YOUR_TOKEN
make-cli config set zone eu1
make-cli config show
```

---

## Key API Gotchas

1. **Blueprint is a JSON string**: `POST/PATCH /scenarios` requires `"blueprint"` as a *stringified* JSON string, not a raw object. Use `json.dumps(blueprint_dict)`.
2. **Scheduling is a JSON string**: Same pattern — `json.dumps({"type": "indefinitely", "interval": 900})`.
3. **teamId required for scenarios**: `GET /scenarios` requires `?teamId=X`. Always need team context.
4. **No single-GET for folders**: `GET /scenarios-folders/{id}` does not exist. Must list all folders for a team and filter client-side.
5. **Zone matters**: Your API token only works against the zone where your account is hosted. Wrong zone = 401/404.
6. **No PATCH /teams in public API**: Updating a team name requires the admin API (`/admin/teams/{id}`).
7. **cols[] parameter**: Most list endpoints support `?cols[]=field1&cols[]=field2` to limit response fields.

---

## Adding a New Command Group

1. Create `make_cli/commands/<name>.py`
2. Define a Click group:
```python
@click.group("<name>")
def <name>():
    """Group description."""
    pass
```
3. Add subcommands with `@<name>.command("<cmd>")` and `@click.pass_obj` to receive `CliContext`
4. Use `ctx.client` to get an authenticated `MakeClient` instance
5. Use `core.output` helpers based on `ctx.json_mode`
6. Handle `MakeAPIError` and call `error(str(e))` + `raise SystemExit(1)`
7. Register in `make_cli/cli.py`:
```python
from make_cli.commands.<name> import <name>
main.add_command(<name>)
```

Example skeleton:
```python
import click
from core.output import print_table, print_json, error
from utils.make_backend import MakeAPIError

@click.group("widget")
def widget():
    """Manage widgets."""
    pass

@widget.command("list")
@click.option("--org", required=True, type=int, help="Organization ID")
@click.pass_obj
def widget_list(ctx, org: int):
    """List all widgets."""
    try:
        items = ctx.client.paginate("/widgets", "widgets", params={"organizationId": org})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(["ID", "Name"], [[w["id"], w["name"]] for w in items])
```

---

## Sync Engine Design (Phase 5)

The sync engine (`make-cli sync pull --org <id>`) downloads an entire org's structure to a local directory.

### Algorithm
1. Fetch org details → save `org.json`, auto-detect zone from org
2. List all teams in org → for each team create directory + `team.json`
3. For each team, list all folders → save `folder.json` per folder
4. For each team, list all scenarios → group by `folderId`
5. For each scenario:
   - Save `<name> - YYYY-MM-DD HH:MM.scenario.json` (metadata)
   - Fetch blueprint → save `<name> - YYYY-MM-DD HH:MM.json` (blueprint)
6. Scenarios with no folder → go to `folders/No Folder/`
7. Metadata (hooks, connections, datastores, etc.) → `_metadata/`
8. Write `manifest.json` mapping local paths ↔ remote IDs + `lastEdit` timestamps
9. Incremental mode: skip scenarios where `lastEdit` matches manifest entry

### Filesystem Layout
```
sync/<org-name>-<org-id>/
├── manifest.json
├── org.json
└── teams/
    └── {team-name}-{team-id}/
        ├── team.json
        ├── folders/
        │   ├── No Folder/
        │   │   └── {scenario-name}-{scenario-id}/
        │   │       ├── <name> - YYYY-MM-DD HH:MM.json           ← blueprint
        │   │       └── <name> - YYYY-MM-DD HH:MM.scenario.json  ← metadata
        │   └── {folder-name}-{folder-id}/
        │       ├── folder.json
        │       └── {scenario-name}-{scenario-id}/
        │           ├── <name> - YYYY-MM-DD HH:MM.json           ← blueprint
        │           └── <name> - YYYY-MM-DD HH:MM.scenario.json  ← metadata
        └── _metadata/
            ├── hooks.json
            ├── connections.json
            ├── datastructures.json
            ├── functions.json
            ├── keys.json
            └── datastores/{name}-{id}/
                ├── datastore.json
                └── records.json
```

### manifest.json Schema
```json
{
  "org_id": 123,
  "zone": "eu1",
  "last_sync": "2026-04-01T10:00:00Z",
  "scenarios": {
    "456": {
      "path": "teams/alpha-1/folders/crm-2/my-scenario-456",
      "last_edit": "2026-03-15T08:30:00Z"
    }
  }
}
```

---

## Analysis Commands Design (Phase 6)

All analysis commands read from the local sync directory. **No API calls.**

| Command | What it does |
|---|---|
| `analyze stats` | Counts: teams, folders, scenarios total, active, inactive, invalid |
| `analyze apps` | Extracts all `module` IDs from blueprint `flow[]` arrays — which Make apps are used |
| `analyze connections` | Finds connection references (`connection.id`) across all blueprints |
| `analyze errors` | Lists scenarios where `isinvalid: true` in `*.scenario.json` |
| `analyze tree` | Pretty-prints org→team→folder→scenario hierarchy using `rich.tree.Tree` |
| `analyze search <term>` | Full-text search across scenario names and blueprint JSON content |

---

## Development Setup

```bash
cd ~/Code/make.com-cli
pip install -e .

# Configure
make-cli config set api_token YOUR_TOKEN_HERE
make-cli config set zone eu1   # or eu2, us1, us2

# Verify
make-cli --help
make-cli config show

# Sync an org
make-cli sync pull --org 12345 --output ./my-org-backup
make-cli analyze tree --dir ./my-org-backup
```
