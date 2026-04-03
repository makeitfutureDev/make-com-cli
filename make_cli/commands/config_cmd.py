"""make-cli config commands."""
import click
from core.config import load_config, save_config
from core.output import print_kv, print_json, success


@click.group("config")
def config_cmd():
    """Manage make-cli configuration."""
    pass


@config_cmd.command("show")
@click.pass_obj
def config_show(ctx):
    """Show current configuration."""
    cfg = load_config()
    if ctx and ctx.json_mode:
        print_json(cfg)
    else:
        if not cfg:
            click.echo("No configuration found. Use: make-cli config set api_token <token>")
        else:
            print_kv(cfg, title="make-cli Configuration")


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value.

    \b
    Keys:
      api_token       Your Make.com API token
      zone            API zone: eu1, eu2, us1, us2 (default: eu1)
      default_org_id  Default organization ID
    """
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    success(f"Set {key} = {value}")


@config_cmd.command("unset")
@click.argument("key")
def config_unset(key: str):
    """Remove a configuration value."""
    cfg = load_config()
    if key in cfg:
        del cfg[key]
        save_config(cfg)
        success(f"Removed {key}")
    else:
        click.echo(f"Key '{key}' not found in config.")
