---
name: make.com-manage-orgs
description: Manage Make.com organizations, teams, and scenarios via the MCP server. Use this skill whenever the user mentions Make.com MCP setup, listing Make.com organizations or teams, downloading or exporting Make.com scenario blueprints, backing up Make.com scenarios, or configuring the Make.com MCP connection in Claude Code. Also trigger when the user asks about connecting to Make.com from Claude, or when they encounter "Access denied" errors with Make.com MCP.
---

# Make.com Organization Management via MCP

This skill covers configuring the Make.com MCP server in Claude Code and working with organizations, teams, and scenario blueprints through the MCP tools.

## MCP Configuration

The Make.com MCP server uses HTTP transport with a bearer token for authentication. Getting the configuration right is the most common stumbling block, so pay close attention to these details.

### Adding the MCP server

There are two authentication approaches — header-based (recommended) and token-in-URL:

**Header-based (recommended):**
```bash
# User scope — available across all projects
claude mcp add -t http -s user make "https://<ZONE>.make.com/mcp/stateless" \
  -H "Authorization: Bearer <MCP_TOKEN>"

# Local scope — only for current project
claude mcp add -t http -s local make-eu1 "https://<ZONE>.make.com/mcp/stateless" \
  -H "Authorization: Bearer <MCP_TOKEN>"
```

**Token in URL (simpler but less secure):**
```bash
claude mcp add -t http -s user make "https://<ZONE>.make.com/mcp/u/<MCP_TOKEN>/stateless"
```

### Zone matching is critical

Each Make.com organization lives in a specific zone (e.g., `eu1.make.com`, `eu2.make.com`, `us1.make.com`). The MCP server URL zone must match the organization's zone, otherwise you get "Access denied" errors even with a valid token.

When working with orgs across multiple zones, add separate MCP servers for each zone:
```bash
claude mcp add -t http -s local make-eu1 "https://eu1.make.com/mcp/stateless" -H "Authorization: Bearer <TOKEN>"
claude mcp add -t http -s local make-us1 "https://us1.make.com/mcp/stateless" -H "Authorization: Bearer <TOKEN>"
```

The tool names follow the pattern `mcp__<server-name>__<action>`, so zone-specific servers become `mcp__make-eu1__organizations_list`, etc.

### Where configs are stored

- **User/local scope:** `~/.claude.json`
- **Project scope:** `.mcp.json` in project root
- **NOT** in `.claude/settings.json` — that file is only for permissions and other settings, not MCP server configs

After adding or modifying MCP config, the user must restart their Claude Code session for changes to take effect.

### JSON structure reference

This is what the MCP config looks like in the actual config files after running `claude mcp add`.

**In `~/.claude.json` (user scope):**
```json
{
  "mcpServers": {
    "make": {
      "type": "http",
      "url": "https://eu1.make.com/mcp/stateless",
      "headers": {
        "Authorization": "Bearer <MCP_TOKEN>"
      }
    }
  }
}
```

**In `~/.claude.json` (local/project-specific scope)** — nested under the project path:
```json
{
  "projects": {
    "/Users/username/my-project": {
      "mcpServers": {
        "make-eu1": {
          "type": "http",
          "url": "https://eu1.make.com/mcp/stateless",
          "headers": {
            "Authorization": "Bearer <MCP_TOKEN>"
          }
        }
      }
    }
  }
}
```

**In `.mcp.json` (project scope, checked into version control):**
```json
{
  "mcpServers": {
    "make": {
      "type": "http",
      "url": "https://eu1.make.com/mcp/stateless",
      "headers": {
        "Authorization": "Bearer <MCP_TOKEN>"
      }
    }
  }
}
```

**Multiple zones example:**
```json
{
  "mcpServers": {
    "make-eu1": {
      "type": "http",
      "url": "https://eu1.make.com/mcp/stateless",
      "headers": {
        "Authorization": "Bearer <MCP_TOKEN>"
      }
    },
    "make-us1": {
      "type": "http",
      "url": "https://us1.make.com/mcp/stateless",
      "headers": {
        "Authorization": "Bearer <MCP_TOKEN>"
      }
    }
  }
}
```

Always use `claude mcp add` CLI to add servers rather than editing these files manually — the CLI handles the correct nesting and structure automatically.

### Getting an MCP token

Tokens are created in Make.com under Profile > API access > Tokens. The token needs the `mcp:use` scope at minimum. Tokens are sensitive — treat them like passwords.

### Updating or removing

```bash
# Remove and re-add to update token
claude mcp remove make -s user
claude mcp add -t http -s user make "https://<ZONE>.make.com/mcp/stateless" -H "Authorization: Bearer <NEW_TOKEN>"

# Remove entirely
claude mcp remove make-eu1
```

## Working with Organizations, Teams, and Scenarios

### Listing organizations

Use `organizations_list` (no parameters needed). The response includes each org's `id`, `name`, `zone`, `productName`, and `license` details.

```
Tool: mcp__make__organizations_list (or mcp__make-eu1__organizations_list)
Params: none
```

The response can be very large if the token has access to many orgs. Extract just the `id` and `name` fields to find the target org, and note the `zone` field to ensure you're using the right MCP server.

### Listing teams

Use `teams_list` with the organization ID.

```
Tool: mcp__make-eu1__teams_list
Params: { "organizationId": 12345 }
```

Returns an array of teams with `id`, `name`, and `organizationId`.

### Listing scenarios

Use `scenarios_list` with a team ID.

```
Tool: mcp__make-eu1__scenarios_list
Params: { "teamId": 534539 }
```

Returns scenario `id`, `name`, `teamId`, scheduling info, status, used packages, creation/update metadata, and execution stats. List all teams in parallel to save time.

### Getting a scenario blueprint

Use `scenarios_get` with a scenario ID. The response includes the full scenario config plus the `blueprint` field containing the scenario's flow definition.

```
Tool: mcp__make-eu1__scenarios_get
Params: { "scenarioId": 3927238 }
```

The blueprint contains `flow` (modules and routing), `name`, `metadata` (designer positions), `scheduling`, and `interface` definitions.

## Bulk Export Workflow

When the user wants to export/backup all scenarios from an organization, follow this sequence:

### Step 1: Find the organization
List all organizations and search by name. Note the `zone` field — you'll need a matching MCP server.

### Step 2: List all teams
Call `teams_list` with the org ID. Save the team list for folder creation.

### Step 3: Create folder structure
Create a local folder for each team:
```
<export-dir>/
  Team A/
  Team B/
  Team C/
```

### Step 4: List scenarios per team
Call `scenarios_list` for each team. Do this in parallel — one call per team simultaneously. Extract scenario IDs and names from each response.

For large responses that get saved to disk (the MCP tool auto-saves results over ~10K tokens), use jq or Python to extract the `id` and `name` fields.

### Step 5: Download blueprints
For each scenario, call `scenarios_get` to fetch the blueprint. Save the `blueprint` field as pretty-printed JSON.

**File naming:** `{scenarioId}_{sanitized_name}.json`
- Sanitize by replacing `/\:*?"<>|` characters with `_`

**Parallelization:** For orgs with many scenarios (20+), use parallel agents — group scenarios by team and spawn one agent per team. Each agent fetches all scenarios for its team and saves the blueprints.

### Step 6: Handle large responses
Scenario blueprints can be large. When the MCP tool saves output to a file instead of returning it inline:
1. Read the persisted file
2. Parse the JSON to extract just the `blueprint` object
3. Write the blueprint as pretty-printed JSON to the target file

## Searching for Properties Inside Scenarios

When the user wants to find which scenarios use a specific field, property, or custom field (e.g., `cf_crid`, `properties.crid`, a Chargebee custom field, a HubSpot property), follow this approach.

### Prerequisites

Scenario blueprints must be exported locally as JSON files first (see Bulk Export Workflow above). Searching works on the local JSON files, not via MCP calls.

### Step 1: Find all files containing the property

Use `Grep` to search across all exported scenario folders:
```
Grep pattern: "cf_crid"  (or whatever field name)
Path: <project-root>
Output mode: files_with_matches
```

### Step 2: Distinguish active mappings from sample data

A property appearing in a scenario file does NOT mean the scenario writes/sets that property. It may only appear in:
- **Webhook sample data / metadata** — the property is being READ from an incoming event, not written
- **Module `metadata` or `expect` sections** — schema definitions or sample outputs, not active mappings
- **Search filters** — used to query/filter, not to set the value

**Active mappings** are found in module `mapper` objects — these are the fields that actually SET values on the target system. Look for the property inside `"mapper": { ... }` blocks.

### Step 3: Identify the operation type

For each file with an active mapping, determine:
1. **Target module** — the module whose `mapper` contains the property (e.g., `chargebee:createCustomer`, `chargebee:updateCustomer`, `hubspotcrm:updateCompany`)
2. **Operation type** — create vs. update vs. raw API call (`makeAnAPICall`)
3. **Source module** — trace the value expression (e.g., `{{15.properties.crid}}`) back to the module with that ID to find where the data comes from. Module IDs are in the `"id"` field of each module object in the blueprint's `flow` array.

### Step 4: Present results

Report findings as a table with columns:
| Team/Folder | Scenario ID | Scenario Name | Target Module (operation) | Source Module | Mapping Expression |

### Blueprint JSON structure reference

```json
{
  "flow": [
    {
      "id": 15,                          // Module ID — referenced in expressions as {{15.field}}
      "module": "hubspotcrm:getCompany", // Module type
      "metadata": {
        "expect": [...],                 // Input schema — NOT active mappings
        "designer": { "name": "Get Company" }  // Display label
      },
      "mapper": {                        // ACTIVE MAPPINGS — values being set
        "companyId": "{{3.id}}"
      }
    },
    {
      "id": 20,
      "module": "chargebee:createCustomer",
      "mapper": {
        "first_name": "{{15.properties.firstname}}",
        "custom_fields": [
          { "name": "cf_crid", "value": "{{15.properties.crid}}" }  // <-- This is an active mapping
        ]
      }
    }
  ]
}
```

Key distinction:
- `mapper` = active mappings (the module WRITES these values)
- `metadata.expect` = input schema definitions (NOT active)
- `metadata.designer` = UI layout info (contains module `name`/label)
- Sample data in webhook modules = test/mock data from past executions

## Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| "Access denied" on teams_list | Zone mismatch | Check org's zone, add matching MCP server |
| MCP server not in /mcp list | Config in wrong file | Use `claude mcp add` CLI, not manual JSON editing |
| Changes not taking effect | Session not restarted | Exit and relaunch Claude Code |
| Token expired | Token rotated in Make.com | Remove and re-add with new token |
| Large response truncated | Blueprint too big | Read from persisted file path in error message |
