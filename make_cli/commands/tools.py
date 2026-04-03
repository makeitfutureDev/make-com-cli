"""make-cli tool commands — /tools endpoints (Make AI tools)."""
import click
from core.output import print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("tool")
def tool():
    """Manage Make.com AI tools."""
    pass


@tool.command("get")
@click.argument("tool_id", type=int)
@click.pass_obj
def tool_get(ctx, tool_id: int):
    """Get details of an AI tool."""
    try:
        data = ctx.client.get(f"/tools/{tool_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    t = data.get("tool", data)
    if ctx.json_mode:
        print_json(t)
    else:
        print_kv(t if isinstance(t, dict) else {"data": t}, title=f"Tool #{tool_id}")


@tool.command("create")
@click.option("--name", required=True, help="Tool name")
@click.option("--scenario-id", required=True, type=int, help="Scenario to expose as tool")
@click.option("--description", default=None, help="Tool description")
@click.pass_obj
def tool_create(ctx, name: str, scenario_id: int, description):
    """Create an AI tool from a scenario."""
    payload = {"name": name, "scenarioId": scenario_id}
    if description:
        payload["description"] = description
    try:
        data = ctx.client.post("/tools", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    t = data.get("tool", data)
    if ctx.json_mode:
        print_json(t)
    else:
        success(f"Created tool '{t.get('name')}' (ID: {t.get('id')})")
        print_kv(t if isinstance(t, dict) else {"data": t})


@tool.command("update")
@click.argument("tool_id", type=int)
@click.option("--name", default=None, help="New name")
@click.option("--description", default=None, help="New description")
@click.pass_obj
def tool_update(ctx, tool_id: int, name, description):
    """Update an AI tool."""
    payload = {}
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    if not payload:
        error("Provide at least one field to update.")
        raise SystemExit(1)
    try:
        data = ctx.client.patch(f"/tools/{tool_id}", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    t = data.get("tool", data)
    if ctx.json_mode:
        print_json(t)
    else:
        success(f"Updated tool #{tool_id}")
        print_kv(t if isinstance(t, dict) else {"data": t})
