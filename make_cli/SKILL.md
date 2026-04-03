---
name: make-cli
description: CLI for the Make.com automation platform. Manage organizations, teams, folders, scenarios, webhooks, connections, data stores, functions, and sync entire orgs to local disk for analysis. Also covers Make.com MCP server setup, zone configuration, blueprint analysis, and searching for properties across synced scenario blueprints. Use when the user mentions Make.com, syncing scenarios, analyzing blueprints, managing orgs/teams, or needs MCP workarounds for endpoints not in the CLI.
version: 0.1.0
install: uv tool install git+https://github.com/makeitfutureDev/make-com-cli
binary: make-cli
config: make-cli config set api_token <token> && make-cli config set zone <eu1|eu2|us1|us2>
---

# make-cli Skill

A full-featured CLI for the Make.com automation platform (API v2).

## Authentication

```bash
make-cli config set api_token YOUR_TOKEN
make-cli config set zone eu1   # or eu2, us1, us2
```

Or via environment variables:
```bash
export MAKE_API_TOKEN=your-token
export MAKE_ZONE=eu1
```

## Global Flags

| Flag | Description |
|---|---|
| `--json` | Output machine-readable JSON (pipe-safe) |
| `--zone TEXT` | Override default API zone (auto-detected per org) |
| `--token TEXT` | Override API token for this call |

## Command Reference

### `make-cli org` — Organizations
```
make-cli org list
make-cli org get <id>
make-cli org create --name NAME --region-id ID --timezone-id ID --country-id ID
make-cli org update <id> [--name] [--country-id] [--timezone-id]
make-cli org delete <id> [--confirmed]
make-cli org usage <id>
make-cli org regions
make-cli org timezones
make-cli org countries
```

### `make-cli team` — Teams
```
make-cli team list --org <org-id>
make-cli team get <id>
make-cli team create --name NAME --org <org-id> [--ops-limit N]
make-cli team delete <id> [--confirmed]
make-cli team usage <id>
```

### `make-cli folder` — Scenario Folders
```
make-cli folder list --team <team-id>
make-cli folder create --name NAME --team <team-id>
make-cli folder update <id> --name NAME
make-cli folder delete <id>
```

### `make-cli scenario` — Scenarios
```
make-cli scenario list --team <team-id> [--folder ID] [--active]
make-cli scenario get <id>
make-cli scenario create --team <team-id> --blueprint '<json>' --scheduling '<json>'
make-cli scenario update <id> [--name] [--blueprint] [--scheduling] [--folder]
make-cli scenario delete <id>
make-cli scenario activate <id>
make-cli scenario deactivate <id>
make-cli scenario run <id> [--data '<json>'] [--responsive]
make-cli scenario blueprint <id> [--out FILE]
make-cli scenario versions <id>
make-cli scenario clone <id> [--team ID] [--folder ID]
make-cli scenario logs <id> [--limit N]
```

### `make-cli hook` — Webhooks
```
make-cli hook list --team <team-id> [--type web|mail]
make-cli hook get <id>
make-cli hook create --name NAME --team <team-id> [--type web|mail]
make-cli hook update <id> [--name]
make-cli hook delete <id>
make-cli hook config <id>
```

### `make-cli connection` — Connections
```
make-cli connection list --team <team-id> [--type TYPE]
make-cli connection get <id>
```

### `make-cli execution` — Execution History
```
make-cli execution list --scenario <id> [--status success|warning|error] [--limit N]
make-cli execution get <scenario-id> <execution-id>
make-cli execution detail <scenario-id> <execution-id>
make-cli execution stop <scenario-id> <execution-id>
```

### `make-cli datastore` — Data Stores
```
make-cli datastore list --team <team-id>
make-cli datastore get <id>
make-cli datastore create --name NAME --team <team-id>
make-cli datastore update <id> [--name] [--max-size]
make-cli datastore delete <id>
make-cli datastore records list <datastore-id>
make-cli datastore records create <datastore-id> <key> '<json-data>'
make-cli datastore records update <datastore-id> <key> '<json-data>'
make-cli datastore records replace <datastore-id> <key> '<json-data>'
make-cli datastore records delete <datastore-id> <key>
```

### `make-cli datastructure` — Data Structures
```
make-cli datastructure list --team <team-id>
make-cli datastructure get <id>
make-cli datastructure create --name NAME --team <team-id> [--spec '<json>']
make-cli datastructure update <id> [--name] [--spec '<json>']
make-cli datastructure delete <id>
make-cli datastructure generate --team <team-id> --sample '<json>' [--name]
```

### `make-cli function` — Custom Functions
```
make-cli function list --team <team-id>
make-cli function get <id>
make-cli function create --name NAME --team <team-id> --code '<js>' [--description]
make-cli function update <id> [--name] [--code] [--description]
make-cli function delete <id>
make-cli function check <id>
```

### `make-cli key` — Keys
```
make-cli key list --team <team-id>
make-cli key get <id>
make-cli key delete <id>
```

### `make-cli credential` — Credential Requests
```
make-cli credential list --team <team-id>
make-cli credential get <id>
make-cli credential create --name NAME --team <team-id> --type TYPE
make-cli credential delete <id>
make-cli credential decline <id>
make-cli credential extend <request-id> <connection-id>
```

### `make-cli app` — Apps & Modules
```
make-cli app modules <app-name>
make-cli app module <app-name> <module-name>
make-cli app docs <app-name>
make-cli app recommend --query 'description of what you need'
```

### `make-cli tool` — AI Tools
```
make-cli tool get <id>
make-cli tool create --name NAME --scenario-id <id> [--description]
make-cli tool update <id> [--name] [--description]
```

### `make-cli validate` — Validation
```
make-cli validate blueprint '<json>'       # or @file.json
make-cli validate scheduling '<json>'
make-cli validate hook-config <hook-id> '<json>'
make-cli validate module-config <app> <module> '<json>'
```

### `make-cli user` — User
```
make-cli user me
```

### `make-cli sync` — Sync Org to Disk ⭐
```
make-cli sync pull --org <org-id> [--output DIR] [--incremental] [--team ID]
```
Downloads the full org hierarchy: teams → folders → scenarios → blueprints → hooks → connections → datastores → datastructures → functions → keys.

Default output: `sync/<org-name>-<org-id>/` (auto-named from the org).

Output structure:
```
sync/<org-name>-<org-id>/
├── manifest.json
├── org.json
└── teams/
    └── <team-name>-<id>/
        ├── team.json
        ├── folders/
        │   ├── No Folder/
        │   │   └── <scenario-name>-<id>/
        │   │       ├── <name> - YYYY-MM-DD HH:MM.json           ← blueprint
        │   │       └── <name> - YYYY-MM-DD HH:MM.scenario.json  ← metadata
        │   └── <folder-name>-<id>/
        │       └── <scenario-name>-<id>/
        │           ├── <name> - YYYY-MM-DD HH:MM.json           ← blueprint
        │           └── <name> - YYYY-MM-DD HH:MM.scenario.json  ← metadata
        └── _metadata/
            ├── hooks.json
            ├── connections.json
            ├── datastructures.json
            ├── functions.json
            ├── keys.json
            └── datastores/
                └── <name>-<id>/
                    ├── datastore.json
                    └── records.json
```

### `make-cli analyze` — Analyze Local Sync ⭐
```
make-cli analyze stats   [--dir DIR]   # counts: teams, folders, scenarios, active/inactive
make-cli analyze apps    [--dir DIR]   # which Make apps are used across all blueprints
make-cli analyze connections [--dir DIR]  # which connections are referenced
make-cli analyze errors  [--dir DIR]   # scenarios with isinvalid=true
make-cli analyze tree    [--dir DIR]   # org → team → folder → scenario hierarchy
make-cli analyze search <term> [--dir DIR] [--blueprint]  # search across names and blueprint JSON
```
`--dir` auto-detects from `sync/` if only one org is synced. Use `--dir sync/<name>-<id>` when multiple orgs exist.

### `make-cli config` — Configuration
```
make-cli config show
make-cli config set api_token YOUR_TOKEN
make-cli config set zone eu1
make-cli config set default_org_id 12345
make-cli config unset <key>
```

### `make-cli repl` — Interactive Shell
```
make-cli repl
```
Starts an interactive REPL with tab-completion and command history.

## Examples

```bash
# List all your orgs and find the ID
make-cli org list

# Sync your entire sandbox org
make-cli sync pull --org 725415 --output ~/make-backup

# Analyze what apps you use most
make-cli analyze apps --dir ~/make-backup

# Find all webhook scenarios
make-cli analyze search "webhook" --dir ~/make-backup --blueprint

# Show the full scenario tree
make-cli analyze tree --dir ~/make-backup

# Get a scenario blueprint as JSON and pipe to jq
make-cli --json scenario blueprint 4575008 | jq '.flow[].module'

# List active scenarios in a team
make-cli scenario list --team 741170 --active

# Run a scenario and wait for result
make-cli scenario run 4575008 --responsive
```

## MCP as a Workaround for Unavailable Endpoints

Some Make.com API endpoints are plan-restricted or not available via REST v2. The Make.com MCP server provides an alternative path for these:

- `credential-requests` (Enterprise-only REST endpoint) → use `mcp__make__credential-requests_list` etc.
- `incomplete-executions` (not available on all plans) → use `mcp__make__incomplete-executions_list`
- Admin-level user management beyond `user me`
- Any endpoint returning 404 or 403 via the CLI may be accessible via MCP

### Setting up the Make.com MCP server

**Header-based (recommended):**
```bash
# User scope — available across all projects
claude mcp add -t http -s user make "https://<ZONE>.make.com/mcp/stateless" \
  -H "Authorization: Bearer <MCP_TOKEN>"

# Local scope — only for current project
claude mcp add -t http -s local make-eu1 "https://<ZONE>.make.com/mcp/stateless" \
  -H "Authorization: Bearer <MCP_TOKEN>"
```

**Token in URL (simpler, less secure):**
```bash
claude mcp add -t http -s user make "https://<ZONE>.make.com/mcp/u/<MCP_TOKEN>/stateless"
```

### Zone matching is critical

The MCP URL zone must match the organization's zone (`eu1`, `eu2`, `us1`, `us2`). A zone mismatch causes "Access denied" even with a valid token. For multi-zone setups, add one server per zone:

```bash
claude mcp add -t http -s local make-eu1 "https://eu1.make.com/mcp/stateless" -H "Authorization: Bearer <TOKEN>"
claude mcp add -t http -s local make-us1 "https://us1.make.com/mcp/stateless" -H "Authorization: Bearer <TOKEN>"
```

MCP tool names follow the pattern `mcp__<server-name>__<action>`, e.g. `mcp__make-eu1__organizations_list`.

### MCP token

Create tokens in Make.com under **Profile > API access > Tokens** with the `mcp:use` scope.

### Config file locations

| Scope | File |
|-------|------|
| User/local | `~/.claude.json` |
| Project (versioned) | `.mcp.json` in project root |

Use `claude mcp add` CLI — never edit these files manually. Restart Claude Code after any MCP config change.

### Common MCP issues

| Problem | Cause | Fix |
|---------|-------|-----|
| "Access denied" on teams_list | Zone mismatch | Check org zone, add matching MCP server |
| MCP server not in /mcp list | Config in wrong file | Use `claude mcp add` CLI |
| Changes not taking effect | Session not restarted | Exit and relaunch Claude Code |
| Token expired | Rotated in Make.com | Remove and re-add with new token |
| Large response truncated | Blueprint too big | Read from persisted file path in error |

## Blueprint JSON Structure Reference

When working with synced blueprints (the `<name> - YYYY-MM-DD HH:MM.json` files, or via `scenario blueprint`), understanding the structure is essential.

```json
{
  "flow": [
    {
      "id": 15,
      "module": "hubspotcrm:getCompany",
      "metadata": {
        "expect": [...],
        "designer": { "name": "Get Company" }
      },
      "mapper": {
        "companyId": "{{3.id}}"
      }
    },
    {
      "id": 20,
      "module": "chargebee:createCustomer",
      "mapper": {
        "first_name": "{{15.properties.firstname}}",
        "custom_fields": [
          { "name": "cf_crid", "value": "{{15.properties.crid}}" }
        ]
      }
    }
  ]
}
```

Key distinctions:
- `mapper` = **active mappings** — values the module actually WRITES/SETS
- `metadata.expect` = input schema definitions — NOT active, just shape descriptions
- `metadata.designer` = UI layout info (display name/label shown in Make.com UI)
- Webhook sample data = test/mock data from past executions, NOT active mappings
- Module IDs (`"id": 15`) are referenced in expressions as `{{15.field}}`

## Searching for Properties Inside Blueprints

To find which scenarios use a specific field (e.g. a custom field `cf_crid`, a HubSpot property):

**Step 1 — Find all matching files:**
```bash
make-cli analyze search "cf_crid" --dir ~/make-backup --blueprint
# Or with grep across synced blueprint files:
grep -rl "cf_crid" ~/make-backup --include="*.json" --exclude="*.scenario.json"
```

**Step 2 — Distinguish active mappings from schema/sample data:**
- Only hits inside `"mapper": { ... }` blocks are actively setting that value
- Hits in `metadata.expect` or webhook sample data are just schema or test data

**Step 3 — Identify the operation:**
For each active mapper hit, check:
1. The parent module (`"module"` field) — e.g. `chargebee:createCustomer`
2. The source expression — e.g. `{{15.properties.crid}}` traces back to module ID 15
3. Whether it's a create, update, or raw API call (`makeAnAPICall`)

**Step 4 — Cross-reference with jq:**
```bash
# List all modules used in a blueprint
make-cli --json scenario blueprint 4575008 | jq '.flow[].module'

# Find all mapper keys containing a property name
cat ~/make-backup/teams/ai-testing-741170/folders/sow-123/scenario-456/blueprint.json \
  | jq '[.flow[] | select(.mapper != null) | {module, mapper}]'
```
