"""make-cli key commands — /keys endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("key")
def key():
    """Manage Make.com API keys."""
    pass


@key.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.pass_obj
def key_list(ctx, team_id: int):
    """List all keys in a team."""
    try:
        items = ctx.client.paginate("/keys", "keys", params={"teamId": team_id})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Type", "Created"],
            [[k.get("id"), k.get("name"), k.get("type"), k.get("created")] for k in items],
            title=f"Keys in Team #{team_id}",
        )


@key.command("get")
@click.argument("key_id", type=int)
@click.pass_obj
def key_get(ctx, key_id: int):
    """Get details of a key."""
    try:
        data = ctx.client.get(f"/keys/{key_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    k = data.get("key", data)
    if ctx.json_mode:
        print_json(k)
    else:
        print_kv(k, title=f"Key #{key_id}")


@key.command("delete")
@click.argument("key_id", type=int)
@click.pass_obj
def key_delete(ctx, key_id: int):
    """Delete a key."""
    try:
        ctx.client.delete(f"/keys/{key_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": key_id})
    else:
        success(f"Deleted key #{key_id}")
