"""make-cli org commands — /organizations endpoints."""
import click
from core.output import print_table, print_kv, print_json, error, success
from utils.make_backend import MakeAPIError


@click.group("org")
def org():
    """Manage Make.com organizations."""
    pass


@org.command("list")
@click.pass_obj
def org_list(ctx):
    """List all organizations accessible with your token."""
    try:
        data = ctx.client.get("/organizations")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    orgs = data.get("organizations", [])
    if ctx.json_mode:
        print_json(orgs)
    else:
        print_table(
            ["ID", "Name", "Zone", "Active Scenarios", "Paused"],
            [[o.get("id"), o.get("name"), o.get("zone"), o.get("activeScenarios"), o.get("isPaused")] for o in orgs],
            title="Organizations",
        )


@org.command("get")
@click.argument("org_id", type=int)
@click.pass_obj
def org_get(ctx, org_id: int):
    """Get details of an organization."""
    ctx.use_org_zone(org_id)
    try:
        data = ctx.client.get(f"/organizations/{org_id}")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    o = data.get("organization", data)
    if ctx.json_mode:
        print_json(o)
    else:
        print_kv(o, title=f"Organization #{org_id}")


@org.command("create")
@click.option("--name", required=True, help="Organization name")
@click.option("--region-id", required=True, type=int, help="Region ID (see: make-cli org regions)")
@click.option("--timezone-id", required=True, type=int, help="Timezone ID (see: make-cli org timezones)")
@click.option("--country-id", required=True, type=int, help="Country ID (see: make-cli org countries)")
@click.pass_obj
def org_create(ctx, name: str, region_id: int, timezone_id: int, country_id: int):
    """Create a new organization."""
    try:
        data = ctx.client.post("/organizations", data={
            "name": name,
            "regionId": region_id,
            "timezoneId": timezone_id,
            "countryId": country_id,
        })
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    o = data.get("organization", data)
    if ctx.json_mode:
        print_json(o)
    else:
        success(f"Created organization '{o.get('name')}' (ID: {o.get('id')})")
        print_kv(o)


@org.command("update")
@click.argument("org_id", type=int)
@click.option("--name", default=None, help="New name")
@click.option("--country-id", default=None, type=int, help="New country ID")
@click.option("--timezone-id", default=None, type=int, help="New timezone ID")
@click.pass_obj
def org_update(ctx, org_id: int, name, country_id, timezone_id):
    """Update an organization."""
    ctx.use_org_zone(org_id)
    payload = {}
    if name:
        payload["name"] = name
    if country_id:
        payload["countryId"] = country_id
    if timezone_id:
        payload["timezoneId"] = timezone_id
    if not payload:
        error("Provide at least one field to update (--name, --country-id, --timezone-id)")
        raise SystemExit(1)
    try:
        data = ctx.client.patch(f"/organizations/{org_id}", data=payload)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    o = data.get("organization", data)
    if ctx.json_mode:
        print_json(o)
    else:
        success(f"Updated organization #{org_id}")
        print_kv(o)


@org.command("delete")
@click.argument("org_id", type=int)
@click.option("--confirmed", is_flag=True, default=False, help="Confirm deletion (required if org has scenarios)")
@click.pass_obj
def org_delete(ctx, org_id: int, confirmed: bool):
    """Delete an organization."""
    ctx.use_org_zone(org_id)
    try:
        params = {"confirmed": "true"} if confirmed else {}
        ctx.client.delete(f"/organizations/{org_id}", params=params)
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json({"deleted": True, "id": org_id})
    else:
        success(f"Deleted organization #{org_id}")


@org.command("usage")
@click.argument("org_id", type=int)
@click.pass_obj
def org_usage(ctx, org_id: int):
    """Show usage statistics for an organization."""
    ctx.use_org_zone(org_id)
    try:
        data = ctx.client.get(f"/organizations/{org_id}/usage")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    usage = data.get("usage", data)
    if ctx.json_mode:
        print_json(usage)
    else:
        if isinstance(usage, dict):
            print_kv(usage, title=f"Organization #{org_id} Usage")
        else:
            print_json(usage)


@org.command("regions")
@click.pass_obj
def org_regions(ctx):
    """List available regions (for --region-id when creating orgs)."""
    try:
        data = ctx.client.get("/enums/imt-regions")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    regions = data.get("imtRegions", data.get("regions", []))
    if ctx.json_mode:
        print_json(regions)
    else:
        if regions and isinstance(regions[0], dict):
            print_table(["ID", "Name"], [[r.get("id"), r.get("name")] for r in regions], title="Regions")
        else:
            print_json(regions)


@org.command("timezones")
@click.pass_obj
def org_timezones(ctx):
    """List available timezones (for --timezone-id when creating orgs)."""
    try:
        data = ctx.client.get("/enums/timezones")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    tzs = data.get("timezones", [])
    if ctx.json_mode:
        print_json(tzs)
    else:
        if tzs and isinstance(tzs[0], dict):
            print_table(["ID", "Name"], [[t.get("id"), t.get("name")] for t in tzs], title="Timezones")
        else:
            print_json(tzs)


@org.command("countries")
@click.pass_obj
def org_countries(ctx):
    """List available countries (for --country-id when creating orgs)."""
    try:
        data = ctx.client.get("/enums/countries")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    countries = data.get("countries", [])
    if ctx.json_mode:
        print_json(countries)
    else:
        if countries and isinstance(countries[0], dict):
            print_table(["ID", "Name"], [[c.get("id"), c.get("name")] for c in countries], title="Countries")
        else:
            print_json(countries)
