"""make-cli app commands — app modules and documentation."""
import click
from core.output import print_table, print_kv, print_json, error
from utils.make_backend import MakeAPIError


@click.group("app")
def app():
    """Browse Make.com apps and modules."""
    pass


@app.command("modules")
@click.argument("app_name")
@click.option("--team", "team_id", default=None, type=int, help="Team ID (for custom apps)")
@click.pass_obj
def app_modules(ctx, app_name: str, team_id):
    """List all modules for an app."""
    params = {"name": app_name}
    if team_id:
        params["teamId"] = team_id
    try:
        data = ctx.client.get(f"/apps/{app_name}/modules", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    modules = data.get("appModules", data.get("modules", []))
    if ctx.json_mode:
        print_json(modules)
    else:
        if modules and isinstance(modules[0], dict):
            print_table(
                ["Name", "Label", "Type", "Description"],
                [[m.get("name"), m.get("label"), m.get("type"),
                  str(m.get("description", ""))[:60]] for m in modules],
                title=f"Modules for app '{app_name}'",
            )
        else:
            print_json(modules)


@app.command("module")
@click.argument("app_name")
@click.argument("module_name")
@click.pass_obj
def app_module(ctx, app_name: str, module_name: str):
    """Get details of a specific module."""
    try:
        data = ctx.client.get(f"/apps/{app_name}/modules/{module_name}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    m = data.get("appModule", data)
    if ctx.json_mode:
        print_json(m)
    else:
        print_kv(m if isinstance(m, dict) else {"data": m},
                 title=f"{app_name}:{module_name}")


@app.command("docs")
@click.argument("app_name")
@click.pass_obj
def app_docs(ctx, app_name: str):
    """Get documentation for an app."""
    try:
        data = ctx.client.get(f"/apps/{app_name}/documentation")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    docs = data.get("documentation", data)
    if ctx.json_mode:
        print_json(docs)
    else:
        if isinstance(docs, str):
            from core.output import console
            console.print(docs)
        else:
            print_kv(docs if isinstance(docs, dict) else {"docs": docs})


@app.command("recommend")
@click.option("--query", required=True, help="Natural language description of what you need")
@click.option("--team", "team_id", default=None, type=int, help="Team ID")
@click.pass_obj
def app_recommend(ctx, query: str, team_id):
    """Get app recommendations for a given use case."""
    params = {"query": query}
    if team_id:
        params["teamId"] = team_id
    try:
        data = ctx.client.get("/apps/recommend", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    apps = data.get("apps", data.get("recommendations", []))
    if ctx.json_mode:
        print_json(apps)
    else:
        if apps and isinstance(apps[0], dict):
            print_table(
                ["Name", "Label", "Score"],
                [[a.get("name"), a.get("label"), a.get("score")] for a in apps],
                title=f"Recommended apps for: '{query}'",
            )
        else:
            print_json(apps)
