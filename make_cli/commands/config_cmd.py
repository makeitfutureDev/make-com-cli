"""make-cli config commands."""
import shutil
from pathlib import Path
import click
from core.config import load_config, save_config
from core.output import print_kv, print_json, success, error


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
    display = f"{value[:4]}...{value[-4:]}" if "token" in key.lower() and len(value) > 12 else value
    success(f"Set {key} = {display}")


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


@config_cmd.command("install-skill")
@click.option("--scope", type=click.Choice(["user", "project"]), default="user",
              show_default=True, help="Install for all projects (user) or current project only")
def config_install_skill(scope: str):
    """Install SKILL.md so Claude Code can discover make-cli.

    \b
    Scopes:
      user     ~/.claude/skills/make-cli/SKILL.md  (all projects)
      project  .claude/skills/make-cli/SKILL.md    (current project)
    """
    # Find SKILL.md — check package dir first, then repo root
    pkg_dir = Path(__file__).resolve().parent.parent
    source = pkg_dir / "SKILL.md"
    if not source.exists():
        source = pkg_dir.parent / "SKILL.md"
    if not source.exists():
        error("SKILL.md not found. Is the package installed correctly?")
        raise SystemExit(1)

    if scope == "user":
        target_dir = Path.home() / ".claude" / "skills" / "make-cli"
    else:
        target_dir = Path(".claude") / "skills" / "make-cli"

    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "SKILL.md"
    shutil.copy2(source, target)
    success(f"Installed SKILL.md → {target}")
