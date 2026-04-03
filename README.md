# make-com-cli

> Open-source CLI for the [Make.com](https://make.com) automation platform — built by [Makeitfuture](https://www.makeitfuture.com), Make.com's **#1 Platinum Partner** and **AI Partner of the Year 2025**.

`make-com-cli` gives developers and AI agents full programmatic access to Make.com via the official [Make.com API v2](https://developers.make.com/api-documentation). Sync entire organizations to disk, analyze blueprints, manage scenarios, and automate everything from the terminal or from within an AI agent workflow.

Inspired by and built following the patterns of [CLI-Anything](https://github.com/HKUDS/CLI-Anything) — a framework for building AI-agent-friendly command-line interfaces.

---

## Why this CLI?

Make.com is one of the most powerful automation platforms available, but working with it programmatically — especially from AI agents — requires navigating a rich REST API. This CLI wraps the full Make.com API v2 surface into a consistent, scriptable interface:

- **AI agents** can call `make-cli` commands directly to manage automations
- **Developers** get a fast way to inspect, sync, and control Make.com from the terminal
- **Teams** can version-control their scenario blueprints by syncing to a local folder
- **Admins** managing multiple organizations across zones (eu1, eu2, us1, us2) get automatic zone-switching per org

---

## About Makeitfuture

[Makeitfuture](https://www.makeitfuture.com) is Europe's leading AI automation agency and **Make.com Platinum Partner** — the highest tier in Make.com's partner program. Recognized as:

- 🏆 **No. 1 No-Code Company in EMEA Region 2024** — awarded by Make.com
- 🤖 **AI Partner of the Year 2025** — awarded by Make.com at Waves '25
- 🥇 **Airtable Gold Partner** · **Zapier Certified Expert**

Specializing in AI-powered workflow automation, custom integrations, and end-to-end business process optimization across Make.com, Zapier, n8n, Workato, and Airtable.

---

## Install

**Recommended — install globally via uv:**
```bash
uv tool install git+https://github.com/makeitfutureDev/make-com-cli
```

**Or clone and install locally:**
```bash
git clone https://github.com/makeitfutureDev/make-com-cli
cd make-com-cli
uv venv .venv && source .venv/bin/activate
uv pip install -e .
```

**Update to latest:**
```bash
uv tool upgrade make-cli
```

---

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

Get your API token: **Make.com → Profile → API Tokens**

> Zone is auto-detected per org — if you work across multiple zones, just set any valid zone as default and the CLI switches automatically.

**Install the Claude Code skill** (makes the CLI discoverable by AI agents):
```bash
make-cli config install-skill
```
This copies `SKILL.md` to `~/.claude/skills/make-cli/` so Claude Code automatically knows how to use the CLI. Use `--scope project` to install for the current project only.

---

## Quick Start

```bash
# List all organizations your token has access to
make-cli org list

# Sync an entire org (auto-creates sync/<org-name>-<org-id>/)
make-cli sync pull --org <org-id>

# Explore synced data offline — no API calls needed
make-cli analyze tree --dir sync/<org-name>-<org-id>
make-cli analyze apps --dir sync/<org-name>-<org-id>
make-cli analyze search "webhook" --blueprint --dir sync/<org-name>-<org-id>

# Interactive shell with tab completion
make-cli repl
```

---

## Commands

| Group | Description |
|---|---|
| `org` | Organizations — list, get, create, update, delete, usage |
| `team` | Teams — list, get, create, delete, usage |
| `folder` | Scenario folders — list, create, update, delete |
| `scenario` | Scenarios — full CRUD, activate/deactivate, run, blueprint, clone, logs |
| `hook` | Webhooks & mailhooks — list, get, create, update, delete, config |
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
| `user` | Current user — `me` |
| `sync` | **Sync entire org to local folder** |
| `analyze` | **Analyze local synced data** (no API calls) |
| `config` | CLI configuration |
| `repl` | Interactive shell with tab completion |

All commands support `--json` for machine-readable output, making them easy to pipe into `jq` or consume from AI agents.

---

## Sync

Downloads the full org hierarchy to disk — scenarios, blueprints, hooks, connections, datastores, functions, keys, and data structures:

```
sync/<org-name>-<org-id>/
├── manifest.json               ← scenario index + last sync timestamps
├── org.json
└── teams/
    └── <team-name>-<id>/
        ├── team.json
        ├── folders/
        │   ├── No Folder/      ← scenarios not assigned to a folder
        │   │   └── <scenario-name>-<id>/
        │   │       ├── <name> - YYYY-MM-DD HH:MM.json           ← blueprint
        │   │       └── <name> - YYYY-MM-DD HH:MM.scenario.json  ← metadata
        │   └── <folder-name>-<id>/
        │       └── <scenario-name>-<id>/
        │           ├── <name> - YYYY-MM-DD HH:MM.json           ← blueprint
        │           └── <name> - YYYY-MM-DD HH:MM.scenario.json  ← metadata
        └── _metadata/          ← hooks, connections, datastores, functions, keys
            ├── hooks.json
            ├── connections.json
            ├── datastructures.json
            ├── functions.json
            ├── keys.json
            └── datastores/<name>-<id>/
                ├── datastore.json
                └── records.json
```

**Incremental sync** — only re-downloads scenarios that changed since last sync:
```bash
make-cli sync pull --org <id> --incremental
```

**Filter to a single team:**
```bash
make-cli sync pull --org <id> --team <team-id>
```

---

## Analyze

All `analyze` commands work on local synced files — no API calls, no token required:

```bash
make-cli analyze stats --dir ./make-backup          # scenario counts, active/inactive
make-cli analyze tree --dir ./make-backup           # org → team → folder → scenario tree
make-cli analyze apps --top 20 --dir ./make-backup  # most-used Make apps across all blueprints
make-cli analyze connections --dir ./make-backup    # connection references across blueprints
make-cli analyze errors --dir ./make-backup         # invalid/broken scenarios
make-cli analyze search "notion" --blueprint --dir ./make-backup  # search inside blueprints
```

---

## JSON Output & Scripting

Every command supports `--json` for piping into other tools:

```bash
# List all scenario names in a team
make-cli --json scenario list --team 741170 | jq '.[].name'

# Get all module types used in a blueprint
make-cli --json scenario blueprint 4575008 | jq '.flow[].module'

# Export all org IDs
make-cli --json org list | jq '.[].id'

# Find all active scenarios
make-cli --json scenario list --team 741170 | jq '[.[] | select(.isActive)]'
```

---

## For AI Agents

This CLI was designed with AI agent usability in mind, following [CLI-Anything](https://github.com/HKUDS/CLI-Anything) conventions:

- Every command has a clear, predictable interface
- `--json` flag on all commands returns structured data
- `SKILL.md` in the repo root provides a machine-readable skill definition for AI agents (Claude, GPT, etc.) to understand the CLI's capabilities
- The `repl` command provides an interactive session suitable for agent-driven exploration

Example agent workflow:
```bash
# Agent discovers available orgs
make-cli --json org list

# Agent syncs the target org (auto-creates sync/3--sandbox-makeitfuture-725415/)
make-cli sync pull --org 725415

# Agent searches blueprints for a specific integration
make-cli --json analyze search "hubspot" --blueprint --dir sync/3--sandbox-makeitfuture-725415
```

---

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- A Make.com API token with appropriate scopes

---

## License

MIT — built with ❤️ by [Makeitfuture](https://www.makeitfuture.com) · Make.com Platinum Partner · AI Partner of the Year 2025
