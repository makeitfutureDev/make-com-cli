"""make-cli credential-request commands — /credential-requests endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("credential")
def credential():
    """Manage Make.com credential requests."""
    pass


@credential.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.pass_obj
def credential_list(ctx, team_id: int):
    """List all credential requests for a team."""
    try:
        items = ctx.client.paginate(
            "/credential-requests", "credentialRequests", params={"teamId": team_id}
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Type", "Status", "Created"],
            [[c.get("id"), c.get("name"), c.get("type"),
              c.get("status"), c.get("created")] for c in items],
            title=f"Credential Requests in Team #{team_id}",
        )


@credential.command("get")
@click.argument("request_id", type=int)
@click.pass_obj
def credential_get(ctx, request_id: int):
    """Get details of a credential request."""
    try:
        data = ctx.client.get(f"/credential-requests/{request_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    c = data.get("credentialRequest", data)
    if ctx.json_mode:
        print_json(c)
    else:
        print_kv(c, title=f"Credential Request #{request_id}")


@credential.command("create")
@click.option("--name", required=True, help="Request name")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--type", "conn_type", required=True, help="Connection type")
@click.pass_obj
def credential_create(ctx, name: str, team_id: int, conn_type: str):
    """Create a new credential request."""
    try:
        data = ctx.client.post(
            "/credential-requests",
            data={"name": name, "teamId": team_id, "type": conn_type},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    c = data.get("credentialRequest", data)
    if ctx.json_mode:
        print_json(c)
    else:
        success(f"Created credential request '{c.get('name')}' (ID: {c.get('id')})")
        print_kv(c)


@credential.command("delete")
@click.argument("request_id", type=int)
@click.pass_obj
def credential_delete(ctx, request_id: int):
    """Delete a credential request."""
    try:
        ctx.client.delete(f"/credential-requests/{request_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": request_id})
    else:
        success(f"Deleted credential request #{request_id}")


@credential.command("decline")
@click.argument("request_id", type=int)
@click.pass_obj
def credential_decline(ctx, request_id: int):
    """Decline a credential request."""
    try:
        data = ctx.client.post(f"/credential-requests/{request_id}/decline")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(data)
    else:
        success(f"Declined credential request #{request_id}")


@credential.command("extend")
@click.argument("request_id", type=int)
@click.argument("connection_id", type=int)
@click.pass_obj
def credential_extend(ctx, request_id: int, connection_id: int):
    """Extend a credential request with an existing connection."""
    try:
        data = ctx.client.post(
            f"/credential-requests/{request_id}/extend-connection",
            data={"connectionId": connection_id},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(data)
    else:
        success(f"Extended credential request #{request_id} with connection #{connection_id}")
