"""Make.com CLI — root entry point."""
import importlib
import click
from make_cli.context import CliContext
from core.config import get_token, get_zone
from core.output import set_json_mode

__version__ = "0.1.0"


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="make-cli")
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output as JSON")
@click.option("--zone", default=None, help="Make.com zone (eu1, eu2, us1, us2)")
@click.option(
    "--token",
    default=None,
    envvar="MAKE_API_TOKEN",
    help="Make.com API token (overrides config/env)",
)
@click.pass_context
def main(ctx: click.Context, json_mode: bool, zone: str, token: str):
    """Make.com CLI — manage scenarios, teams, folders and sync your org."""
    ctx.ensure_object(dict)
    set_json_mode(json_mode)

    resolved_token = get_token(token)
    resolved_zone = get_zone(zone)

    ctx.obj = CliContext(
        json_mode=json_mode,
        _token=resolved_token,
        _zone=resolved_zone,
    )

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# --- Register command groups ---
from make_cli.commands.config_cmd import config_cmd
main.add_command(config_cmd)

_COMMAND_IMPORTS = [
    ("make_cli.commands.orgs", "org"),
    ("make_cli.commands.teams", "team"),
    ("make_cli.commands.folders", "folder"),
    ("make_cli.commands.scenarios", "scenario"),
    ("make_cli.commands.sync", "sync"),
    ("make_cli.commands.analyze", "analyze"),
    ("make_cli.commands.hooks", "hook"),
    ("make_cli.commands.connections", "connection"),
    ("make_cli.commands.executions", "execution"),
    ("make_cli.commands.executions", "incomplete"),
    ("make_cli.commands.datastores", "datastore"),
    ("make_cli.commands.datastructures", "datastructure"),
    ("make_cli.commands.functions", "function"),
    ("make_cli.commands.keys", "key"),
    ("make_cli.commands.credentials", "credential"),
    ("make_cli.commands.apps", "app"),
    ("make_cli.commands.tools", "tool"),
    ("make_cli.commands.validate", "validate"),
    ("make_cli.commands.users", "user"),
    ("make_cli.commands.repl", "repl"),
]

for module_path, attr_name in _COMMAND_IMPORTS:
    try:
        mod = importlib.import_module(module_path)
        main.add_command(getattr(mod, attr_name))
    except (ImportError, AttributeError):
        pass


if __name__ == "__main__":
    main()
