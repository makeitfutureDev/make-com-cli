"""make-cli connection commands — /connections endpoints."""
import click
from core.output import print_table, print_kv, print_json, error
from utils.make_backend import MakeAPIError


@click.group("connection")
def connection():
    """List and inspect Make.com connections."""
    pass


@connection.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--type", "conn_type", default=None, multiple=True,
              help="Filter by connection type (repeatable)")
@click.pass_obj
def connection_list(ctx, team_id: int, conn_type):
    """List all connections in a team."""
    params = {"teamId": team_id}
    if conn_type:
        # API uses type[] array param
        params["type[]"] = list(conn_type)
    try:
        items = ctx.client.paginate("/connections", "connections", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Type", "Account Name", "Valid", "Scoped"],
            [[c.get("id"), c.get("name"), c.get("type"),
              c.get("accountName"), c.get("isValid"), c.get("scoped")] for c in items],
            title=f"Connections in Team #{team_id}",
        )


@connection.command("get")
@click.argument("connection_id", type=int)
@click.pass_obj
def connection_get(ctx, connection_id: int):
    """Get details of a connection."""
    try:
        data = ctx.client.get(f"/connections/{connection_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    c = data.get("connection", data)
    if ctx.json_mode:
        print_json(c)
    else:
        print_kv(c, title=f"Connection #{connection_id}")
