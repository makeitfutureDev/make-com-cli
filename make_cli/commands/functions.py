"""make-cli function commands — /functions endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("function")
def function():
    """Manage Make.com custom functions."""
    pass


@function.command("list")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.pass_obj
def function_list(ctx, team_id: int):
    """List all custom functions in a team."""
    try:
        items = ctx.client.paginate("/functions", "functions", params={"teamId": team_id})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(items)
    else:
        print_table(
            ["ID", "Name", "Language", "Description"],
            [[f.get("id"), f.get("name"), f.get("language"), f.get("description", "")[:60]]
             for f in items],
            title=f"Functions in Team #{team_id}",
        )


@function.command("get")
@click.argument("function_id", type=int)
@click.pass_obj
def function_get(ctx, function_id: int):
    """Get details and code of a custom function."""
    try:
        data = ctx.client.get(f"/functions/{function_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    f = data.get("function", data)
    if ctx.json_mode:
        print_json(f)
    else:
        meta = {k: v for k, v in f.items() if k != "code"}
        print_kv(meta, title=f"Function #{function_id}")
        code = f.get("code", "")
        if code:
            from rich.syntax import Syntax
            from core.output import console
            console.print("\n[bold cyan]Code:[/bold cyan]")
            console.print(Syntax(code, "javascript", theme="monokai", line_numbers=True))


@function.command("create")
@click.option("--name", required=True, help="Function name")
@click.option("--team", "team_id", required=True, type=int, help="Team ID")
@click.option("--code", required=True, help="JavaScript code or @file path")
@click.option("--description", default=None, help="Description")
@click.pass_obj
def function_create(ctx, name: str, team_id: int, code: str, description):
    """Create a new custom function."""
    if code.startswith("@"):
        with open(code[1:]) as f:
            code = f.read()
    payload = {"name": name, "teamId": team_id, "code": code}
    if description:
        payload["description"] = description
    try:
        data = ctx.client.post("/functions", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    fn = data.get("function", data)
    if ctx.json_mode:
        print_json(fn)
    else:
        success(f"Created function '{fn.get('name')}' (ID: {fn.get('id')})")


@function.command("update")
@click.argument("function_id", type=int)
@click.option("--name", default=None, help="New name")
@click.option("--code", default=None, help="New JavaScript code or @file path")
@click.option("--description", default=None, help="New description")
@click.pass_obj
def function_update(ctx, function_id: int, name, code, description):
    """Update a custom function."""
    payload = {}
    if name:
        payload["name"] = name
    if code:
        if code.startswith("@"):
            with open(code[1:]) as f:
                code = f.read()
        payload["code"] = code
    if description:
        payload["description"] = description
    if not payload:
        error("Provide at least one field to update.")
        raise SystemExit(1)
    try:
        data = ctx.client.patch(f"/functions/{function_id}", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    fn = data.get("function", data)
    if ctx.json_mode:
        print_json(fn)
    else:
        success(f"Updated function #{function_id}")


@function.command("delete")
@click.argument("function_id", type=int)
@click.pass_obj
def function_delete(ctx, function_id: int):
    """Delete a custom function."""
    try:
        ctx.client.delete(f"/functions/{function_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": function_id})
    else:
        success(f"Deleted function #{function_id}")


@function.command("check")
@click.argument("function_id", type=int)
@click.pass_obj
def function_check(ctx, function_id: int):
    """Check/validate a custom function for syntax errors."""
    try:
        data = ctx.client.post(f"/functions/{function_id}/check")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(data)
    else:
        valid = data.get("valid", data.get("success", True))
        if valid:
            success("Function is valid.")
        else:
            error(f"Function has errors: {data}")
