"""make-cli hook commands — /hooks endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("hook")
def hook():
    """Manage Make.com webhooks and mailhooks."""
    pass


@hook.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--type", "hook_type", default=None, help="Filter by type (web/mail)")
@click.pass_obj
def hook_list(ctx, team_id: int, hook_type):
    """List all webhooks/mailhooks in a team."""
    params = {"teamId": team_id}
    if hook_type:
        params["type"] = hook_type
    try:
        items = ctx.client.paginate("/hooks", "hooks", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Type", "Scenario ID", "Enabled", "URL"],
            [[h.get("id"), h.get("name"), h.get("type"), h.get("scenarioId"),
              h.get("enabled"), h.get("url", "")[:60]] for h in items],
            title=f"Hooks in Team #{team_id}",
        )


@hook.command("get")
@click.argument("hook_id", type=int)
@click.pass_obj
def hook_get(ctx, hook_id: int):
    """Get details of a webhook."""
    try:
        data = ctx.client.get(f"/hooks/{hook_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    h = data.get("hook", data)
    if ctx.json_mode:
        print_json(h)
    else:
        print_kv(h, title=f"Hook #{hook_id}")


@hook.command("create")
@click.option("--name", required=True, help="Hook name")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--type", "hook_type", default="web", show_default=True,
              type=click.Choice(["web", "mail"]), help="Hook type")
@click.pass_obj
def hook_create(ctx, name: str, team_id: int, hook_type: str):
    """Create a new webhook."""
    try:
        data = ctx.client.post("/hooks", data={"name": name, "teamId": team_id, "type": hook_type})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    h = data.get("hook", data)
    if ctx.json_mode:
        print_json(h)
    else:
        success(f"Created hook '{h.get('name')}' (ID: {h.get('id')})")
        print_kv(h)


@hook.command("update")
@click.argument("hook_id", type=int)
@click.option("--name", default=None, help="New name")
@click.pass_obj
def hook_update(ctx, hook_id: int, name):
    """Update a webhook."""
    payload = {}
    if name:
        payload["name"] = name
    if not payload:
        error("Provide at least one field to update.")
        raise SystemExit(1)
    try:
        data = ctx.client.patch(f"/hooks/{hook_id}", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    h = data.get("hook", data)
    if ctx.json_mode:
        print_json(h)
    else:
        success(f"Updated hook #{hook_id}")
        print_kv(h)


@hook.command("delete")
@click.argument("hook_id", type=int)
@click.pass_obj
def hook_delete(ctx, hook_id: int):
    """Delete a webhook."""
    try:
        ctx.client.delete(f"/hooks/{hook_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": hook_id})
    else:
        success(f"Deleted hook #{hook_id}")


@hook.command("config")
@click.argument("hook_id", type=int)
@click.pass_obj
def hook_config(ctx, hook_id: int):
    """Get the configuration of a webhook."""
    try:
        data = ctx.client.get(f"/hooks/{hook_id}/config")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    cfg = data.get("hookConfig", data)
    if ctx.json_mode:
        print_json(cfg)
    else:
        print_kv(cfg if isinstance(cfg, dict) else {"config": cfg},
                 title=f"Hook #{hook_id} Config")
