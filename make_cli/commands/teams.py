"""make-cli team commands — /teams endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("team")
def team():
    """Manage Make.com teams."""
    pass


@team.command("list")
@click.option("--org", "org_id", required=True, type=int, help="Organization ID")
@click.pass_obj
def team_list(ctx, org_id: int):
    """List all teams in an organization."""
    ctx.use_org_zone(org_id)
    try:
        items = ctx.client.paginate("/teams", "teams", params={"organizationId": org_id})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Org ID", "Ops Limit"],
            [[t.get("id"), t.get("name"), t.get("organizationId"), t.get("operationsLimit")] for t in items],
            title=f"Teams in Org #{org_id}",
        )


@team.command("get")
@click.argument("team_id", type=int)
@click.pass_obj
def team_get(ctx, team_id: int):
    """Get details of a team."""
    try:
        data = ctx.client.get(f"/teams/{team_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    t = data.get("team", data)
    if ctx.json_mode:
        print_json(t)
    else:
        print_kv(t, title=f"Team #{team_id}")


@team.command("create")
@click.option("--name", required=True, help="Team name")
@click.option("--org", "org_id", required=True, type=int, help="Organization ID")
@click.option("--ops-limit", default=None, type=int, help="Operations limit")
@click.pass_obj
def team_create(ctx, name: str, org_id: int, ops_limit):
    """Create a new team."""
    ctx.use_org_zone(org_id)
    payload = {"name": name, "organizationId": org_id}
    if ops_limit is not None:
        payload["operationsLimit"] = ops_limit
    try:
        data = ctx.client.post("/teams", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    t = data.get("team", data)
    if ctx.json_mode:
        print_json(t)
    else:
        success(f"Created team '{t.get('name')}' (ID: {t.get('id')})")
        print_kv(t)


@team.command("delete")
@click.argument("team_id", type=int)
@click.option("--confirmed", is_flag=True, default=False, help="Confirm deletion")
@click.pass_obj
def team_delete(ctx, team_id: int, confirmed: bool):
    """Delete a team."""
    try:
        params = {"confirmed": "true"} if confirmed else {}
        ctx.client.delete(f"/teams/{team_id}", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": team_id})
    else:
        success(f"Deleted team #{team_id}")


@team.command("usage")
@click.argument("team_id", type=int)
@click.pass_obj
def team_usage(ctx, team_id: int):
    """Show usage statistics for a team."""
    try:
        data = ctx.client.get(f"/teams/{team_id}/usage")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    usage = data.get("usage", data)
    if ctx.json_mode:
        print_json(usage)
    else:
        if isinstance(usage, dict):
            print_kv(usage, title=f"Team #{team_id} Usage")
        else:
            print_json(usage)
