"""make-cli datastructure commands — /data-structures endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("datastructure")
def datastructure():
    """Manage Make.com data structures (JSON schemas)."""
    pass


@datastructure.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.pass_obj
def datastructure_list(ctx, team_id: int):
    """List all data structures in a team."""
    try:
        items = ctx.client.paginate(
            "/data-structures", "dataStructures", params={"teamId": team_id}
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Strict", "Fields"],
            [[d.get("id"), d.get("name"), d.get("strict"),
              len(d.get("spec", []))] for d in items],
            title=f"Data Structures in Team #{team_id}",
        )


@datastructure.command("get")
@click.argument("datastructure_id", type=int)
@click.pass_obj
def datastructure_get(ctx, datastructure_id: int):
    """Get details of a data structure."""
    try:
        data = ctx.client.get(f"/data-structures/{datastructure_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    d = data.get("dataStructure", data)
    if ctx.json_mode:
        print_json(d)
    else:
        print_kv({k: v for k, v in d.items() if k != "spec"},
                 title=f"Data Structure #{datastructure_id}")
        spec = d.get("spec", [])
        if spec:
            print_table(
                ["Name", "Type", "Required", "Label"],
                [[f.get("name"), f.get("type"), f.get("required"), f.get("label")] for f in spec],
                title="Fields",
            )


@datastructure.command("create")
@click.option("--name", required=True, help="Data structure name")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--spec", default=None, help="JSON array of field specs")
@click.option("--strict", is_flag=True, default=False, help="Strict mode")
@click.pass_obj
def datastructure_create(ctx, name: str, team_id: int, spec, strict: bool):
    """Create a new data structure."""
    import json
    payload = {"name": name, "teamId": team_id, "strict": strict}
    if spec:
        try:
            payload["spec"] = json.loads(spec)
        except json.JSONDecodeError as e:
            error(f"Invalid JSON for --spec: {e}")
            raise SystemExit(1)
    try:
        data = ctx.client.post("/data-structures", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    d = data.get("dataStructure", data)
    if ctx.json_mode:
        print_json(d)
    else:
        success(f"Created data structure '{d.get('name')}' (ID: {d.get('id')})")
        print_kv(d)


@datastructure.command("update")
@click.argument("datastructure_id", type=int)
@click.option("--name", default=None, help="New name")
@click.option("--spec", default=None, help="New JSON array of field specs")
@click.pass_obj
def datastructure_update(ctx, datastructure_id: int, name, spec):
    """Update a data structure."""
    import json
    payload = {}
    if name:
        payload["name"] = name
    if spec:
        try:
            payload["spec"] = json.loads(spec)
        except json.JSONDecodeError as e:
            error(f"Invalid JSON for --spec: {e}")
            raise SystemExit(1)
    if not payload:
        error("Provide at least one field to update.")
        raise SystemExit(1)
    try:
        data = ctx.client.patch(f"/data-structures/{datastructure_id}", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    d = data.get("dataStructure", data)
    if ctx.json_mode:
        print_json(d)
    else:
        success(f"Updated data structure #{datastructure_id}")
        print_kv(d)


@datastructure.command("delete")
@click.argument("datastructure_id", type=int)
@click.pass_obj
def datastructure_delete(ctx, datastructure_id: int):
    """Delete a data structure."""
    try:
        ctx.client.delete(f"/data-structures/{datastructure_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": datastructure_id})
    else:
        success(f"Deleted data structure #{datastructure_id}")


@datastructure.command("generate")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--sample", required=True, help="Sample JSON data to infer structure from")
@click.option("--name", default=None, help="Name for the generated structure")
@click.pass_obj
def datastructure_generate(ctx, team_id: int, sample: str, name):
    """Generate a data structure from sample JSON data."""
    import json
    try:
        sample_data = json.loads(sample)
    except json.JSONDecodeError as e:
        error(f"Invalid JSON for --sample: {e}")
        raise SystemExit(1)
    payload = {"teamId": team_id, "data": sample_data}
    if name:
        payload["name"] = name
    try:
        data = ctx.client.post("/data-structures/generate", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    d = data.get("dataStructure", data)
    if ctx.json_mode:
        print_json(d)
    else:
        success(f"Generated data structure (ID: {d.get('id')})")
        print_kv(d)
