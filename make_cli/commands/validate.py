"""make-cli validate commands — schema validation helpers."""
import json
import click
from core.output import print_json, error, success, console
from utils.make_backend import MakeAPIError


@click.group("validate")
def validate():
    """Validate Make.com schemas and configurations."""
    pass


def _load_input(value: str) -> dict:
    """Load JSON from a string or @file path."""
    if value.startswith("@"):
        with open(value[1:]) as f:
            return json.load(f)
    return json.loads(value)


@validate.command("blueprint")
@click.argument("blueprint")
@click.pass_obj
def validate_blueprint(ctx, blueprint: str):
    """Validate a scenario blueprint JSON. Pass JSON string or @file."""
    try:
        data = _load_input(blueprint)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        error(f"Could not parse blueprint: {e}")
        raise SystemExit(1)
    try:
        result = ctx.client.post("/scenarios/validate-blueprint",
                                 data={"blueprint": json.dumps(data)})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(result)
    else:
        valid = result.get("valid", result.get("success", True))
        errors = result.get("errors", [])
        if valid and not errors:
            success("Blueprint is valid.")
        else:
            error(f"Blueprint has {len(errors)} error(s):")
            for e_ in errors:
                console.print(f"  • {e_}")


@validate.command("scheduling")
@click.argument("scheduling")
@click.pass_obj
def validate_scheduling(ctx, scheduling: str):
    """Validate a scheduling JSON string. Pass JSON string or @file."""
    try:
        data = _load_input(scheduling)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        error(f"Could not parse scheduling: {e}")
        raise SystemExit(1)
    try:
        result = ctx.client.post("/scenarios/validate-scheduling",
                                 data={"scheduling": json.dumps(data)})
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(result)
    else:
        valid = result.get("valid", result.get("success", True))
        if valid:
            success("Scheduling is valid.")
        else:
            error(f"Scheduling is invalid: {result}")


@validate.command("hook-config")
@click.argument("hook_id", type=int)
@click.argument("config")
@click.pass_obj
def validate_hook_config(ctx, hook_id: int, config: str):
    """Validate a webhook configuration. CONFIG is JSON string or @file."""
    try:
        data = _load_input(config)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        error(f"Could not parse config: {e}")
        raise SystemExit(1)
    try:
        result = ctx.client.post(
            f"/hooks/{hook_id}/validate-config", data={"config": data}
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(result)
    else:
        valid = result.get("valid", result.get("success", True))
        if valid:
            success("Hook config is valid.")
        else:
            error(f"Hook config is invalid: {result}")


@validate.command("module-config")
@click.argument("app_name")
@click.argument("module_name")
@click.argument("config")
@click.pass_obj
def validate_module_config(ctx, app_name: str, module_name: str, config: str):
    """Validate a module configuration. CONFIG is JSON string or @file."""
    try:
        data = _load_input(config)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        error(f"Could not parse config: {e}")
        raise SystemExit(1)
    try:
        result = ctx.client.post(
            f"/apps/{app_name}/modules/{module_name}/validate",
            data={"config": data},
        )
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    if ctx.json_mode:
        print_json(result)
    else:
        valid = result.get("valid", result.get("success", True))
        if valid:
            success(f"Module config for {app_name}:{module_name} is valid.")
        else:
            error(f"Module config is invalid: {result}")
