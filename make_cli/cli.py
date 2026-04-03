"""Make.com CLI — root entry point."""
import click
from make_cli.context import CliContext
from core.config import get_token, get_zone


@click.group(invoke_without_command=True)
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

try:
    from make_cli.commands.orgs import org
    main.add_command(org)
except ImportError:
    pass

try:
    from make_cli.commands.teams import team
    main.add_command(team)
except ImportError:
    pass

try:
    from make_cli.commands.folders import folder
    main.add_command(folder)
except ImportError:
    pass

try:
    from make_cli.commands.scenarios import scenario
    main.add_command(scenario)
except ImportError:
    pass

try:
    from make_cli.commands.sync import sync
    main.add_command(sync)
except ImportError:
    pass

try:
    from make_cli.commands.analyze import analyze
    main.add_command(analyze)
except ImportError:
    pass

try:
    from make_cli.commands.hooks import hook
    main.add_command(hook)
except ImportError:
    pass

try:
    from make_cli.commands.connections import connection
    main.add_command(connection)
except ImportError:
    pass

try:
    from make_cli.commands.executions import execution, incomplete
    main.add_command(execution)
    main.add_command(incomplete)
except ImportError:
    pass

try:
    from make_cli.commands.datastores import datastore
    main.add_command(datastore)
except ImportError:
    pass

try:
    from make_cli.commands.datastructures import datastructure
    main.add_command(datastructure)
except ImportError:
    pass

try:
    from make_cli.commands.functions import function
    main.add_command(function)
except ImportError:
    pass

try:
    from make_cli.commands.keys import key
    main.add_command(key)
except ImportError:
    pass

try:
    from make_cli.commands.credentials import credential
    main.add_command(credential)
except ImportError:
    pass

try:
    from make_cli.commands.apps import app
    main.add_command(app)
except ImportError:
    pass

try:
    from make_cli.commands.tools import tool
    main.add_command(tool)
except ImportError:
    pass

try:
    from make_cli.commands.validate import validate
    main.add_command(validate)
except ImportError:
    pass

try:
    from make_cli.commands.users import user
    main.add_command(user)
except ImportError:
    pass

try:
    from make_cli.commands.repl import repl
    main.add_command(repl)
except ImportError:
    pass


if __name__ == "__main__":
    main()
