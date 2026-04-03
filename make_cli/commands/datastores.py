"""make-cli datastore commands — /data-stores and /data-store-records endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("datastore")
def datastore():
    """Manage Make.com data stores and their records."""
    pass


@datastore.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.pass_obj
def datastore_list(ctx, team_id: int):
    """List all data stores in a team."""
    try:
        items = ctx.client.paginate("/data-stores", "dataStores", params={"teamId": team_id})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Records", "Size (bytes)", "Max Size"],
            [[d.get("id"), d.get("name"), d.get("records"),
              d.get("size"), d.get("maxSize")] for d in items],
            title=f"Data Stores in Team #{team_id}",
        )


@datastore.command("get")
@click.argument("datastore_id", type=int)
@click.pass_obj
def datastore_get(ctx, datastore_id: int):
    """Get details of a data store."""
    try:
        data = ctx.client.get(f"/data-stores/{datastore_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    d = data.get("dataStore", data)
    if ctx.json_mode:
        print_json(d)
    else:
        print_kv(d, title=f"Data Store #{datastore_id}")


@datastore.command("create")
@click.option("--name", required=True, help="Data store name")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--max-size", default=None, type=int, help="Max size in bytes")
@click.option("--data-structure-id", default=None, type=int, help="Data structure ID")
@click.pass_obj
def datastore_create(ctx, name: str, team_id: int, max_size, data_structure_id):
    """Create a new data store."""
    payload = {"name": name, "teamId": team_id}
    if max_size:
        payload["maxSize"] = max_size
    if data_structure_id:
        payload["dataStructureId"] = data_structure_id
    try:
        data = ctx.client.post("/data-stores", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    d = data.get("dataStore", data)
    if ctx.json_mode:
        print_json(d)
    else:
        success(f"Created data store '{d.get('name')}' (ID: {d.get('id')})")
        print_kv(d)


@datastore.command("update")
@click.argument("datastore_id", type=int)
@click.option("--name", default=None, help="New name")
@click.option("--max-size", default=None, type=int, help="New max size in bytes")
@click.pass_obj
def datastore_update(ctx, datastore_id: int, name, max_size):
    """Update a data store."""
    payload = {}
    if name:
        payload["name"] = name
    if max_size:
        payload["maxSize"] = max_size
    if not payload:
        error("Provide at least one field to update.")
        raise SystemExit(1)
    try:
        data = ctx.client.patch(f"/data-stores/{datastore_id}", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    d = data.get("dataStore", data)
    if ctx.json_mode:
        print_json(d)
    else:
        success(f"Updated data store #{datastore_id}")
        print_kv(d)


@datastore.command("delete")
@click.argument("datastore_id", type=int)
@click.pass_obj
def datastore_delete(ctx, datastore_id: int):
    """Delete a data store."""
    try:
        ctx.client.delete(f"/data-stores/{datastore_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": datastore_id})
    else:
        success(f"Deleted data store #{datastore_id}")


# --- Records subgroup ---
@datastore.group("records")
def records():
    """Manage records within a data store."""
    pass


@records.command("list")
@click.argument("datastore_id", type=int)
@click.option("--limit", default=100, type=int, show_default=True)
@click.pass_obj
def records_list(ctx, datastore_id: int, limit: int):
    """List records in a data store."""
    try:
        items = ctx.client.paginate(
            f"/data-stores/{datastore_id}/data", "records",
            params={}, limit=limit
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        if not items:
            click.echo("No records found.")
            return
        # Dynamic columns from first record's keys
        keys = list(items[0].keys()) if items else ["key", "data"]
        print_table(
            keys,
            [[str(r.get(k, "")) for k in keys] for r in items],
            title=f"Records in Data Store #{datastore_id}",
        )


@records.command("create")
@click.argument("datastore_id", type=int)
@click.argument("key")
@click.argument("data")
@click.pass_obj
def records_create(ctx, datastore_id: int, key: str, data: str):
    """Create a record. DATA is a JSON string."""
    import json
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON for data: {e}")
        raise SystemExit(1)
    try:
        result = ctx.client.post(
            f"/data-stores/{datastore_id}/data",
            data={"key": key, "data": data_dict},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    r = result.get("record", result)
    if ctx.json_mode:
        print_json(r)
    else:
        success(f"Created record '{key}'")
        print_kv(r if isinstance(r, dict) else {"result": r})


@records.command("update")
@click.argument("datastore_id", type=int)
@click.argument("key")
@click.argument("data")
@click.pass_obj
def records_update(ctx, datastore_id: int, key: str, data: str):
    """Update a record. DATA is a JSON string."""
    import json
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON for data: {e}")
        raise SystemExit(1)
    try:
        result = ctx.client.patch(
            f"/data-stores/{datastore_id}/data/{key}",
            data={"data": data_dict},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    r = result.get("record", result)
    if ctx.json_mode:
        print_json(r)
    else:
        success(f"Updated record '{key}'")
        print_kv(r if isinstance(r, dict) else {"result": r})


@records.command("replace")
@click.argument("datastore_id", type=int)
@click.argument("key")
@click.argument("data")
@click.pass_obj
def records_replace(ctx, datastore_id: int, key: str, data: str):
    """Replace a record entirely. DATA is a JSON string."""
    import json
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON for data: {e}")
        raise SystemExit(1)
    try:
        result = ctx.client._request(
            "PUT", f"/data-stores/{datastore_id}/data/{key}",
            json={"data": data_dict},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    r = result.get("record", result)
    if ctx.json_mode:
        print_json(r)
    else:
        success(f"Replaced record '{key}'")


@records.command("delete")
@click.argument("datastore_id", type=int)
@click.argument("key")
@click.pass_obj
def records_delete(ctx, datastore_id: int, key: str):
    """Delete a record from a data store."""
    try:
        ctx.client.delete(f"/data-stores/{datastore_id}/data/{key}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "key": key})
    else:
        success(f"Deleted record '{key}'")
