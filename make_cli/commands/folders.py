"""make-cli folder commands — /scenarios-folders endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("folder")
def folder():
    """Manage Make.com scenario folders."""
    pass


@folder.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.pass_obj
def folder_list(ctx, team_id: int):
    """List all scenario folders in a team."""
    try:
        data = ctx.client.get("/scenarios-folders", params={"teamId": team_id})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    folders = data.get("scenariosFolders", [])
    if ctx.json_mode:
        print_json(folders)
    else:
        print_table(
            ["ID", "Name", "Scenarios"],
            [[f.get("id"), f.get("name"), f.get("scenariosTotal")] for f in folders],
            title=f"Folders in Team #{team_id}",
        )


@folder.command("create")
@click.option("--name", required=True, help="Folder name (max 100 chars)")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.pass_obj
def folder_create(ctx, name: str, team_id: int):
    """Create a new scenario folder."""
    try:
        data = ctx.client.post("/scenarios-folders", data={"name": name, "teamId": team_id})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    f = data.get("scenarioFolder", data)
    if ctx.json_mode:
        print_json(f)
    else:
        success(f"Created folder '{f.get('name')}' (ID: {f.get('id')})")
        print_kv(f)


@folder.command("update")
@click.argument("folder_id", type=int)
@click.option("--name", required=True, help="New folder name (max 100 chars)")
@click.pass_obj
def folder_update(ctx, folder_id: int, name: str):
    """Rename a scenario folder."""
    try:
        data = ctx.client.patch(f"/scenarios-folders/{folder_id}", data={"name": name})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    f = data.get("scenarioFolder", data)
    if ctx.json_mode:
        print_json(f)
    else:
        success(f"Renamed folder #{folder_id} to '{name}'")


@folder.command("delete")
@click.argument("folder_id", type=int)
@click.pass_obj
def folder_delete(ctx, folder_id: int):
    """Delete a scenario folder."""
    try:
        ctx.client.delete(f"/scenarios-folders/{folder_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": folder_id})
    else:
        success(f"Deleted folder #{folder_id}")
