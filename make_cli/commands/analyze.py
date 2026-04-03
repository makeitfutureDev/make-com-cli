"""make-cli analyze commands — work on local synced data, no API calls."""
import json
from collections import Counter
from pathlib import Path

import click
from rich.table import Table
from rich.tree import Tree

from core.output import print_json, print_table, error, console


def _find_sync_dir(path: str) -> Path:
    d = Path(path)
    if not d.exists():
        error(f"Sync directory not found: {d}. Run: make-cli sync pull --org <id> --output {d}")
        raise SystemExit(1)
    if not (d / "manifest.json").exists():
        error(f"No manifest.json found in {d}. Is this a valid sync directory?")
        raise SystemExit(1)
    return d


def _load_json(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _load_scenario_json(scenario_dir: Path) -> dict:
    """Load the scenario metadata file (*.scenario.json) from a scenario directory."""
    for f in scenario_dir.glob("*.scenario.json"):
        return _load_json(f)
    # Fallback for old-style sync directories
    legacy = scenario_dir / "scenario.json"
    return _load_json(legacy) if legacy.exists() else {}


def _iter_scenarios(sync_dir: Path):
    """Yield (scenario_path, scenario_data, blueprint_data) for all synced scenarios."""
    for scenario_json in sync_dir.rglob("*.scenario.json"):
        # Skip anything inside _metadata directories
        if "_metadata" in scenario_json.parts:
            continue
        scenario = _load_json(scenario_json)
        # Blueprint has the same stem without .scenario suffix
        stem = scenario_json.name[: -len(".scenario.json")]
        blueprint_path = scenario_json.parent / f"{stem}.json"
        blueprint = _load_json(blueprint_path) if blueprint_path.exists() else {}
        yield scenario_json.parent, scenario, blueprint


def _extract_modules(blueprint: dict) -> list:
    """Recursively extract all module IDs from a blueprint's flow."""
    modules = []
    flow = blueprint.get("flow", [])
    for node in flow:
        module = node.get("module")
        if module:
            modules.append(module)
        # recurse into nested routes/filters
        for key in ("routes", "filter", "subflow"):
            sub = node.get(key)
            if isinstance(sub, list):
                for item in sub:
                    if isinstance(item, dict):
                        modules.extend(_extract_modules(item))
    return modules


@click.group("analyze")
def analyze():
    """Analyze locally synced Make.com data (no API calls)."""
    pass


@analyze.command("stats")
@click.option("--dir", "sync_dir", default="./make-sync", show_default=True,
              help="Sync directory to analyze")
@click.pass_obj
def analyze_stats(ctx, sync_dir: str):
    """Show statistics: teams, folders, scenarios, active/inactive."""
    d = _find_sync_dir(sync_dir)
    manifest = _load_json(d / "manifest.json")

    teams = [t for t in (d / "teams").iterdir() if t.is_dir() and not t.name.startswith("_")] if (d / "teams").exists() else []
    # Count folder directories under teams/*/folders/
    total_folders = sum(
        1 for folders_dir in d.glob("teams/*/folders")
        for f in folders_dir.iterdir() if f.is_dir()
    )
    scenarios = list(_iter_scenarios(d))
    active = sum(1 for _, s, _ in scenarios if s.get("isActive"))
    inactive = len(scenarios) - active
    invalid = sum(1 for _, s, _ in scenarios if s.get("isinvalid"))
    blueprints = sum(1 for _, _, bp in scenarios if bp and "flow" in bp)

    data = {
        "org_id": manifest.get("org_id"),
        "zone": manifest.get("zone"),
        "last_sync": manifest.get("last_sync"),
        "teams": len(teams),
        "folders": total_folders,
        "scenarios_total": len(scenarios),
        "scenarios_active": active,
        "scenarios_inactive": inactive,
        "scenarios_invalid": invalid,
        "blueprints_available": blueprints,
    }

    if ctx and ctx.json_mode:
        print_json(data)
    else:
        table = Table(title=f"Sync Stats — {d.resolve()}", show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        for k, v in data.items():
            table.add_row(k.replace("_", " ").title(), str(v) if v is not None else "")
        console.print(table)


@analyze.command("apps")
@click.option("--dir", "sync_dir", default="./make-sync", show_default=True,
              help="Sync directory to analyze")
@click.option("--top", default=30, type=int, show_default=True, help="Show top N apps")
@click.pass_obj
def analyze_apps(ctx, sync_dir: str, top: int):
    """List all Make apps/modules used across all scenario blueprints."""
    d = _find_sync_dir(sync_dir)
    module_counter: Counter = Counter()
    app_counter: Counter = Counter()

    for _, _, blueprint in _iter_scenarios(d):
        modules = _extract_modules(blueprint)
        module_counter.update(modules)
        # App name = everything before the first colon in module ID
        for m in modules:
            app = m.split(":")[0] if ":" in m else m
            app_counter[app] += 1

    if ctx and ctx.json_mode:
        print_json({
            "apps": dict(app_counter.most_common(top)),
            "modules": dict(module_counter.most_common(top)),
        })
    else:
        # Apps table
        table = Table(title=f"Top {top} Apps Used", header_style="bold cyan")
        table.add_column("App", style="cyan")
        table.add_column("Uses", justify="right")
        for app, count in app_counter.most_common(top):
            table.add_row(app, str(count))
        console.print(table)

        # Modules table
        mod_table = Table(title=f"Top {top} Modules Used", header_style="bold cyan")
        mod_table.add_column("Module ID", style="dim cyan")
        mod_table.add_column("Uses", justify="right")
        for mod, count in module_counter.most_common(top):
            mod_table.add_row(mod, str(count))
        console.print(mod_table)


@analyze.command("connections")
@click.option("--dir", "sync_dir", default="./make-sync", show_default=True,
              help="Sync directory to analyze")
@click.pass_obj
def analyze_connections(ctx, sync_dir: str):
    """List all connection references found across blueprints."""
    d = _find_sync_dir(sync_dir)
    # connection references appear inside module parameters as {"connection": {...}}
    connections: dict = {}  # connection_id -> {name, type, scenarios}

    def _find_connections(obj, scenario_name):
        if isinstance(obj, dict):
            if "connection" in obj and isinstance(obj["connection"], dict):
                conn = obj["connection"]
                cid = str(conn.get("id", "unknown"))
                if cid not in connections:
                    connections[cid] = {
                        "id": cid,
                        "name": conn.get("name", ""),
                        "type": conn.get("type", ""),
                        "scenarios": [],
                    }
                if scenario_name not in connections[cid]["scenarios"]:
                    connections[cid]["scenarios"].append(scenario_name)
            for v in obj.values():
                _find_connections(v, scenario_name)
        elif isinstance(obj, list):
            for item in obj:
                _find_connections(item, scenario_name)

    for _, scenario, blueprint in _iter_scenarios(d):
        sname = scenario.get("name", "unknown")
        _find_connections(blueprint, sname)

    result = sorted(connections.values(), key=lambda x: len(x["scenarios"]), reverse=True)

    if ctx and ctx.json_mode:
        print_json(result)
    else:
        table = Table(title="Connection References", header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("Used in # Scenarios", justify="right")
        for conn in result:
            table.add_row(
                conn["id"], conn["name"], conn["type"], str(len(conn["scenarios"]))
            )
        console.print(table)


@analyze.command("errors")
@click.option("--dir", "sync_dir", default="./make-sync", show_default=True,
              help="Sync directory to analyze")
@click.pass_obj
def analyze_errors(ctx, sync_dir: str):
    """List all invalid scenarios (isinvalid=true)."""
    d = _find_sync_dir(sync_dir)
    invalid = []

    for path, scenario, _ in _iter_scenarios(d):
        if scenario.get("isinvalid"):
            invalid.append({
                "id": scenario.get("id"),
                "name": scenario.get("name"),
                "team_id": scenario.get("teamId"),
                "folder_id": scenario.get("folderId"),
                "last_edit": scenario.get("lastEdit"),
                "path": str(path),
            })

    if ctx and ctx.json_mode:
        print_json(invalid)
    else:
        if not invalid:
            console.print("[green]No invalid scenarios found.[/green]")
        else:
            table = Table(title=f"Invalid Scenarios ({len(invalid)})", header_style="bold red")
            table.add_column("ID", style="dim")
            table.add_column("Name", style="red")
            table.add_column("Team ID")
            table.add_column("Last Edit")
            for s in invalid:
                table.add_row(str(s["id"]), s["name"], str(s["team_id"]), s["last_edit"] or "")
            console.print(table)


@analyze.command("tree")
@click.option("--dir", "sync_dir", default="./make-sync", show_default=True,
              help="Sync directory to analyze")
@click.pass_obj
def analyze_tree(ctx, sync_dir: str):
    """Display the org → team → folder → scenario hierarchy."""
    d = _find_sync_dir(sync_dir)
    manifest = _load_json(d / "manifest.json")
    org = _load_json(d / "org.json")

    org_name = org.get("name", f"Org #{manifest.get('org_id')}")
    root = Tree(f"[bold yellow]🏢 {org_name}[/bold yellow]")

    teams_dir = d / "teams"
    if not teams_dir.exists():
        console.print(root)
        return

    for team_dir in sorted(teams_dir.iterdir()):
        if not team_dir.is_dir() or team_dir.name.startswith("_"):
            continue
        team = _load_json(team_dir / "team.json")
        team_name = team.get("name", team_dir.name)
        team_node = root.add(f"[bold cyan]👥 {team_name}[/bold cyan]")

        # Folders (including "No Folder" for unfiled scenarios)
        folders_dir = team_dir / "folders"
        if folders_dir.exists():
            for folder_dir in sorted(folders_dir.iterdir()):
                if not folder_dir.is_dir():
                    continue
                if folder_dir.name == "No Folder":
                    fname = "No Folder"
                    folder_node = team_node.add(f"[dim]📁 {fname}[/dim]")
                else:
                    folder = _load_json(folder_dir / "folder.json")
                    fname = folder.get("name", folder_dir.name)
                    folder_node = team_node.add(f"[yellow]📁 {fname}[/yellow]")
                for scenario_dir in sorted(folder_dir.iterdir()):
                    if not scenario_dir.is_dir():
                        continue
                    s = _load_scenario_json(scenario_dir)
                    sname = s.get("name", scenario_dir.name)
                    active = s.get("isActive", False)
                    icon = "🟢" if active else "⚫"
                    folder_node.add(f"{icon} {sname} [dim](#{s.get('id')})[/dim]")

    console.print(root)


@analyze.command("search")
@click.argument("term")
@click.option("--dir", "sync_dir", default="./make-sync", show_default=True,
              help="Sync directory to analyze")
@click.option("--blueprint", "search_blueprint", is_flag=True, default=False,
              help="Also search inside blueprint JSON content")
@click.pass_obj
def analyze_search(ctx, term: str, sync_dir: str, search_blueprint: bool):
    """Search for a term across scenario names and optionally blueprint content."""
    d = _find_sync_dir(sync_dir)
    term_lower = term.lower()
    results = []

    for path, scenario, blueprint in _iter_scenarios(d):
        sname = scenario.get("name", "")
        matched_in = []

        if term_lower in sname.lower():
            matched_in.append("name")

        if search_blueprint:
            bp_str = json.dumps(blueprint).lower()
            if term_lower in bp_str:
                matched_in.append("blueprint")

        if matched_in:
            results.append({
                "id": scenario.get("id"),
                "name": sname,
                "active": scenario.get("isActive"),
                "team_id": scenario.get("teamId"),
                "matched_in": ", ".join(matched_in),
                "path": str(path.relative_to(d)),
            })

    if ctx and ctx.json_mode:
        print_json(results)
    else:
        if not results:
            console.print(f"[yellow]No results for '{term}'[/yellow]")
        else:
            table = Table(
                title=f"Search: '{term}' — {len(results)} result(s)",
                header_style="bold cyan",
            )
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Active")
            table.add_column("Matched In")
            table.add_column("Path", style="dim")
            for r in results:
                table.add_row(
                    str(r["id"]),
                    r["name"],
                    "🟢" if r["active"] else "⚫",
                    r["matched_in"],
                    r["path"],
                )
            console.print(table)
