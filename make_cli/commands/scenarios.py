"""make-cli scenario commands — /scenarios endpoints."""
import json
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("scenario")
def scenario():
    """Manage Make.com scenarios."""
    pass


@scenario.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--folder", "folder_id", default=None, type=int, help="Filter by folder ID")
@click.option("--active", is_flag=True, default=False, help="Show only active scenarios")
@click.pass_obj
def scenario_list(ctx, team_id: int, folder_id, active: bool):
    """List scenarios in a team."""
    params = {"teamId": team_id}
    if folder_id:
        params["folderId"] = folder_id
    if active:
        params["isActive"] = "true"
    try:
        items = ctx.client.paginate("/scenarios", "scenarios", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Active", "Folder", "Last Edit"],
            [[s.get("id"), s.get("name"), s.get("isActive"), s.get("folderId"), s.get("lastEdit")] for s in items],
            title=f"Scenarios in Team #{team_id}",
        )


@scenario.command("get")
@click.argument("scenario_id", type=int)
@click.pass_obj
def scenario_get(ctx, scenario_id: int):
    """Get details of a scenario."""
    try:
        data = ctx.client.get(f"/scenarios/{scenario_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    s = data.get("scenario", data)
    if ctx.json_mode:
        print_json(s)
    else:
        print_kv(s, title=f"Scenario #{scenario_id}")


@scenario.command("create")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--blueprint", required=True, help="Blueprint JSON string or @file path")
@click.option("--scheduling", default='{"type":"indefinitely","interval":900}', help="Scheduling JSON string")
@click.option("--folder", "folder_id", default=None, type=int, help="Folder ID")
@click.option("--name", default=None, help="Scenario name")
@click.pass_obj
def scenario_create(ctx, team_id: int, blueprint: str, scheduling: str, folder_id, name):
    """Create a new scenario. Blueprint can be a JSON string or @filename."""
    if blueprint.startswith("@"):
        with open(blueprint[1:]) as f:
            blueprint_str = f.read()
        try:
            json.loads(blueprint_str)
        except json.JSONDecodeError as e:
            error(f"Invalid blueprint JSON: {e}")
            raise SystemExit(1)
    else:
        blueprint_str = blueprint

    payload = {
        "teamId": team_id,
        "blueprint": blueprint_str,
        "scheduling": scheduling,
    }
    if folder_id:
        payload["folderId"] = folder_id

    try:
        data = ctx.client.post("/scenarios", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    s = data.get("scenario", data)
    if ctx.json_mode:
        print_json(s)
    else:
        success(f"Created scenario '{s.get('name')}' (ID: {s.get('id')})")
        print_kv(s)


@scenario.command("update")
@click.argument("scenario_id", type=int)
@click.option("--name", default=None, help="New name")
@click.option("--blueprint", default=None, help="New blueprint JSON string or @file path")
@click.option("--scheduling", default=None, help="New scheduling JSON string")
@click.option("--folder", "folder_id", default=None, type=int, help="Move to folder ID")
@click.pass_obj
def scenario_update(ctx, scenario_id: int, name, blueprint, scheduling, folder_id):
    """Update a scenario."""
    payload = {}
    if name:
        payload["name"] = name
    if blueprint:
        if blueprint.startswith("@"):
            with open(blueprint[1:]) as f:
                payload["blueprint"] = f.read()
        else:
            payload["blueprint"] = blueprint
    if scheduling:
        payload["scheduling"] = scheduling
    if folder_id is not None:
        payload["folderId"] = folder_id
    if not payload:
        error("Provide at least one field to update.")
        raise SystemExit(1)
    try:
        data = ctx.client.patch(f"/scenarios/{scenario_id}", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    s = data.get("scenario", data)
    if ctx.json_mode:
        print_json(s)
    else:
        success(f"Updated scenario #{scenario_id}")
        print_kv(s)


@scenario.command("delete")
@click.argument("scenario_id", type=int)
@click.pass_obj
def scenario_delete(ctx, scenario_id: int):
    """Delete a scenario."""
    try:
        ctx.client.delete(f"/scenarios/{scenario_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": scenario_id})
    else:
        success(f"Deleted scenario #{scenario_id}")


@scenario.command("activate")
@click.argument("scenario_id", type=int)
@click.pass_obj
def scenario_activate(ctx, scenario_id: int):
    """Activate (enable) a scenario."""
    try:
        data = ctx.client.post(f"/scenarios/{scenario_id}/start")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    s = data.get("scenario", data)
    if ctx.json_mode:
        print_json(s)
    else:
        success(f"Activated scenario #{scenario_id}")


@scenario.command("deactivate")
@click.argument("scenario_id", type=int)
@click.pass_obj
def scenario_deactivate(ctx, scenario_id: int):
    """Deactivate (disable) a scenario."""
    try:
        data = ctx.client.post(f"/scenarios/{scenario_id}/stop")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    s = data.get("scenario", data)
    if ctx.json_mode:
        print_json(s)
    else:
        success(f"Deactivated scenario #{scenario_id}")


@scenario.command("run")
@click.argument("scenario_id", type=int)
@click.option("--data", "input_data", default=None, help="Input data as JSON string")
@click.option("--responsive", is_flag=True, default=False, help="Wait up to 40s for result")
@click.option("--callback", default=None, help="Callback URL for async completion")
@click.pass_obj
def scenario_run(ctx, scenario_id: int, input_data, responsive: bool, callback):
    """Run a scenario."""
    payload = {}
    if input_data:
        try:
            payload["data"] = json.loads(input_data)
        except json.JSONDecodeError as e:
            error(f"Invalid JSON for --data: {e}")
            raise SystemExit(1)
    if responsive:
        payload["responsive"] = True
    if callback:
        payload["callbackUrl"] = callback
    try:
        data = ctx.client.post(f"/scenarios/{scenario_id}/run", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(data)
    else:
        exec_id = data.get("executionId", "n/a")
        status = data.get("status", "n/a")
        success(f"Scenario #{scenario_id} triggered. Execution ID: {exec_id}, Status: {status}")


@scenario.command("blueprint")
@click.argument("scenario_id", type=int)
@click.option("--version", "blueprint_id", default=None, type=int, help="Specific blueprint version ID")
@click.option("--draft", is_flag=True, default=False, help="Get draft blueprint")
@click.option("--out", default=None, help="Save to file (default: print to stdout)")
@click.pass_obj
def scenario_blueprint(ctx, scenario_id: int, blueprint_id, draft: bool, out):
    """Get a scenario's blueprint (automation graph JSON)."""
    params = {}
    if blueprint_id:
        params["blueprintId"] = blueprint_id
    if draft:
        params["draft"] = "true"
    try:
        data = ctx.client.get(f"/scenarios/{scenario_id}/blueprint", params=params or None)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    bp = data.get("response", {}).get("blueprint", data)
    bp_str = json.dumps(bp, indent=2)
    if out:
        with open(out, "w") as f:
            f.write(bp_str)
        success(f"Blueprint saved to {out}")
    else:
        print(bp_str)


@scenario.command("versions")
@click.argument("scenario_id", type=int)
@click.pass_obj
def scenario_versions(ctx, scenario_id: int):
    """List blueprint versions of a scenario."""
    try:
        data = ctx.client.get(f"/scenarios/{scenario_id}/blueprints")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    versions = data.get("blueprints", data.get("scenarioBlueprints", []))
    if ctx.json_mode:
        print_json(versions)
    else:
        if versions and isinstance(versions[0], dict):
            print_table(
                ["ID", "Created", "Author"],
                [[v.get("id"), v.get("created"), v.get("createdByUser", {}).get("name")] for v in versions],
                title=f"Blueprint Versions — Scenario #{scenario_id}",
            )
        else:
            print_json(versions)


@scenario.command("clone")
@click.argument("scenario_id", type=int)
@click.option("--team", "team_id", default=None, type=int, help="Target team ID (default: same team)")
@click.option("--folder", "folder_id", default=None, type=int, help="Target folder ID")
@click.pass_obj
def scenario_clone(ctx, scenario_id: int, team_id, folder_id):
    """Clone a scenario."""
    payload = {}
    if team_id:
        payload["teamId"] = team_id
    if folder_id:
        payload["folderId"] = folder_id
    try:
        data = ctx.client.post(f"/scenarios/{scenario_id}/clone", data=payload or None)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    s = data.get("scenario", data)
    if ctx.json_mode:
        print_json(s)
    else:
        success(f"Cloned scenario #{scenario_id} → new ID: {s.get('id')}")
        print_kv(s)


@scenario.command("logs")
@click.argument("scenario_id", type=int)
@click.option("--limit", default=20, type=int, help="Max number of log entries")
@click.pass_obj
def scenario_logs(ctx, scenario_id: int, limit: int):
    """List recent execution logs for a scenario."""
    try:
        data = ctx.client.get(
            f"/scenarios/{scenario_id}/logs",
            params={"pg[limit]": limit, "pg[sortDir]": "desc"},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    logs = data.get("scenarioLogs", data.get("logs", []))
    if ctx.json_mode:
        print_json(logs)
    else:
        print_table(
            ["Execution ID", "Status", "Started", "Duration (ms)", "Operations"],
            [
                [
                    lg.get("executionId"),
                    lg.get("status"),
                    lg.get("timestamp"),
                    lg.get("duration"),
                    lg.get("operations"),
                ]
                for lg in logs
            ],
            title=f"Logs — Scenario #{scenario_id}",
        )
