"""make-cli sync commands — pull entire org to local filesystem."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.tree import Tree

from core.output import error, success, console
from utils.make_backend import MakeAPIError

MANIFEST_FILE = "manifest.json"


def _slugify(name: str) -> str:
    """Convert a name to a safe directory slug."""
    return re.sub(r"[^\w\-]", "-", name.strip()).strip("-").lower()[:60]


def _dir_name(name: str, id_: int) -> str:
    return f"{_slugify(name)}-{id_}"


def _parse_timestamp(last_edit: str) -> str:
    """Return 'YYYY-MM-DD HH:MM' from an ISO timestamp string, or now if unparseable."""
    if last_edit:
        try:
            dt = datetime.fromisoformat(last_edit.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def _load_manifest(output_dir: Path) -> dict:
    manifest_path = output_dir / MANIFEST_FILE
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return {"scenarios": {}}


def _save_manifest(output_dir: Path, manifest: dict):
    with open(output_dir / MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2, default=str)


def _write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


@click.group("sync")
def sync():
    """Sync Make.com org data to a local folder."""
    pass


@sync.command("pull")
@click.option("--org", "org_id", required=True, type=int, help="Organization ID to sync")
@click.option("--output", "output_dir", default="./make-sync", show_default=True,
              help="Local output directory")
@click.option("--incremental", is_flag=True, default=False,
              help="Skip scenarios unchanged since last sync")
@click.option("--team", "team_filter", default=None, type=int,
              help="Sync only a specific team ID")
@click.pass_obj
def sync_pull(ctx, org_id: int, output_dir: str, incremental: bool, team_filter):
    """Pull all scenarios from an org to a local folder.

    Downloads org → teams → folders → scenarios → blueprints.
    Preserves the full hierarchy on disk for offline analysis.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest(out) if incremental else {"scenarios": {}}

    stats = {"teams": 0, "folders": 0, "scenarios": 0, "blueprints": 0,
             "skipped": 0, "hooks": 0, "connections": 0, "datastores": 0,
             "functions": 0, "keys": 0, "datastructures": 0}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        transient=False,
    ) as progress:

        # --- Step 1: Org ---
        task = progress.add_task("Fetching organization...", total=None)
        try:
            org_data = ctx.client.get(f"/organizations/{org_id}")
        except MakeAPIError as e:
            error(str(e))
            raise SystemExit(1)
        org = org_data.get("organization", org_data)
        _write_json(out / "org.json", org)

        # Switch client zone to match the org's actual zone
        org_zone = org.get("zone", "")
        if org_zone:
            ctx.client.switch_zone(org_zone)

        manifest["org_id"] = org_id
        manifest["zone"] = ctx.client.zone
        progress.update(task, description=f"Org: [bold]{org.get('name')}[/bold] [dim]({ctx.client.zone})[/dim]", completed=1, total=1)

        # --- Step 2: Teams ---
        progress.update(task, description="Fetching teams...")
        try:
            teams = ctx.client.paginate("/teams", "teams", params={"organizationId": org_id})
        except MakeAPIError as e:
            error(str(e))
            raise SystemExit(1)

        if team_filter:
            teams = [t for t in teams if t["id"] == team_filter]

        teams_dir = out / "teams"
        teams_dir.mkdir(exist_ok=True)
        progress.update(task, description=f"Found {len(teams)} team(s)", completed=1, total=1)

        team_task = progress.add_task("Processing teams...", total=len(teams))

        for team in teams:
            team_id = team["id"]
            team_name = team["name"]
            team_dir = teams_dir / _dir_name(team_name, team_id)
            team_dir.mkdir(parents=True, exist_ok=True)
            _write_json(team_dir / "team.json", team)
            stats["teams"] += 1

            progress.update(team_task, description=f"Team: [cyan]{team_name}[/cyan]")

            # --- Step 3: Folders for this team ---
            try:
                folder_data = ctx.client.get("/scenarios-folders", params={"teamId": team_id})
            except MakeAPIError as e:
                error(f"Could not fetch folders for team {team_id}: {e}")
                folder_data = {}

            folders = folder_data.get("scenariosFolders", [])
            folders_by_id = {}
            folders_dir = team_dir / "folders"

            for folder in folders:
                fid = folder["id"]
                fname = folder["name"]
                folder_dir = folders_dir / _dir_name(fname, fid)
                folder_dir.mkdir(parents=True, exist_ok=True)
                _write_json(folder_dir / "folder.json", folder)
                folders_by_id[fid] = folder_dir
                stats["folders"] += 1

            unfiled_dir = folders_dir / "No Folder"
            meta_dir = team_dir / "_metadata"

            # --- Step 4: Scenarios for this team ---
            try:
                scenarios = ctx.client.paginate(
                    "/scenarios", "scenarios", params={"teamId": team_id}
                )
            except MakeAPIError as e:
                error(f"Could not fetch scenarios for team {team_id}: {e}")
                scenarios = []

            scen_task = progress.add_task(
                f"  Scenarios in {team_name}...", total=len(scenarios)
            )

            for scenario in scenarios:
                sid = scenario["id"]
                sname = scenario.get("name", f"scenario-{sid}")
                last_edit = scenario.get("lastEdit", "")

                # Incremental: skip if unchanged
                if incremental and str(sid) in manifest.get("scenarios", {}):
                    stored = manifest["scenarios"][str(sid)]
                    if stored.get("last_edit") == last_edit:
                        stats["skipped"] += 1
                        progress.advance(scen_task)
                        continue

                # Determine target directory
                folder_id = scenario.get("folderId")
                if folder_id and folder_id in folders_by_id:
                    scenario_dir = folders_by_id[folder_id] / _dir_name(sname, sid)
                else:
                    unfiled_dir.mkdir(parents=True, exist_ok=True)
                    scenario_dir = unfiled_dir / _dir_name(sname, sid)

                scenario_dir.mkdir(parents=True, exist_ok=True)

                # Build timestamp suffix from lastEdit (fall back to now)
                ts = _parse_timestamp(last_edit)
                file_stem = f"{sname} - {ts}"
                _write_json(scenario_dir / f"{file_stem}.scenario.json", scenario)

                # --- Step 5: Blueprint ---
                try:
                    bp_data = ctx.client.get(f"/scenarios/{sid}/blueprint")
                    blueprint = bp_data.get("response", {}).get("blueprint", bp_data)
                    _write_json(scenario_dir / f"{file_stem}.json", blueprint)
                    stats["blueprints"] += 1
                except MakeAPIError as e:
                    # Blueprint may not be available for all scenarios
                    _write_json(scenario_dir / f"{file_stem}.json", {"error": str(e)})

                stats["scenarios"] += 1

                # Update manifest entry
                manifest.setdefault("scenarios", {})[str(sid)] = {
                    "path": str(scenario_dir.relative_to(out)),
                    "last_edit": last_edit,
                    "name": sname,
                    "team_id": team_id,
                    "folder_id": folder_id,
                }

                progress.advance(scen_task)

            progress.update(scen_task, visible=False)

            # --- Step 6: Metadata (hooks, connections, datastores, structures, functions, keys) ---
            meta_dir.mkdir(exist_ok=True)

            progress.update(team_task, description=f"  Metadata in {team_name}...")

            try:
                hooks = ctx.client.paginate("/hooks", "hooks", params={"teamId": team_id})
                _write_json(meta_dir / "hooks.json", hooks)
                stats["hooks"] += len(hooks)
            except MakeAPIError:
                pass

            try:
                connections = ctx.client.paginate(
                    "/connections", "connections", params={"teamId": team_id}
                )
                _write_json(meta_dir / "connections.json", connections)
                stats["connections"] += len(connections)
            except MakeAPIError:
                pass

            try:
                struct_list = ctx.client.paginate(
                    "/data-structures", "dataStructures", params={"teamId": team_id}
                )
                _write_json(meta_dir / "datastructures.json", struct_list)
                stats["datastructures"] += len(struct_list)
            except MakeAPIError:
                pass

            try:
                fn_list = ctx.client.paginate(
                    "/functions", "functions", params={"teamId": team_id}
                )
                _write_json(meta_dir / "functions.json", fn_list)
                stats["functions"] += len(fn_list)
            except MakeAPIError:
                pass

            try:
                key_list = ctx.client.paginate("/keys", "keys", params={"teamId": team_id})
                _write_json(meta_dir / "keys.json", key_list)
                stats["keys"] += len(key_list)
            except MakeAPIError:
                pass

            try:
                ds_list = ctx.client.paginate(
                    "/data-stores", "dataStores", params={"teamId": team_id}
                )
                ds_dir = meta_dir / "datastores"
                ds_dir.mkdir(exist_ok=True)
                for ds in ds_list:
                    ds_id = ds["id"]
                    ds_name = ds.get("name", f"ds-{ds_id}")
                    ds_item_dir = ds_dir / _dir_name(ds_name, ds_id)
                    ds_item_dir.mkdir(exist_ok=True)
                    _write_json(ds_item_dir / "datastore.json", ds)
                    try:
                        records_data = ctx.client.get(f"/data-stores/{ds_id}/data")
                        _write_json(ds_item_dir / "records.json", records_data.get("records", []))
                    except MakeAPIError:
                        pass
                stats["datastores"] += len(ds_list)
            except MakeAPIError:
                pass

            progress.advance(team_task)

        progress.update(team_task, visible=False)

    # Write final manifest
    manifest["last_sync"] = datetime.now(timezone.utc).isoformat()
    _save_manifest(out, manifest)

    # Summary
    stats["output_directory"] = str(out.resolve())
    if ctx.json_mode:
        from core.output import print_json
        print_json(stats)
    else:
        summary = Table(title="Sync Complete", show_header=True, header_style="bold green")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Count", justify="right")
        summary.add_row("Teams synced", str(stats["teams"]))
        summary.add_row("Folders synced", str(stats["folders"]))
        summary.add_row("Scenarios synced", str(stats["scenarios"]))
        summary.add_row("Blueprints downloaded", str(stats["blueprints"]))
        if stats["skipped"]:
            summary.add_row("Scenarios skipped (unchanged)", str(stats["skipped"]))
        summary.add_row("Webhooks synced", str(stats["hooks"]))
        summary.add_row("Connections synced", str(stats["connections"]))
        summary.add_row("Data stores synced", str(stats["datastores"]))
        summary.add_row("Data structures synced", str(stats["datastructures"]))
        summary.add_row("Functions synced", str(stats["functions"]))
        summary.add_row("Keys synced", str(stats["keys"]))
        summary.add_row("Output directory", stats["output_directory"])
        console.print(summary)
