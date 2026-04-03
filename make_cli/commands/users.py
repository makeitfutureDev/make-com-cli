"""make-cli user commands — /users endpoints."""
import click
from core.output import print_kv, print_json, error
from utils.make_backend import MakeAPIError


@click.group("user")
def user():
    """Manage Make.com user information."""
    pass


@user.command("me")
@click.pass_obj
def user_me(ctx):
    """Show details of the currently authenticated user."""
    try:
        data = ctx.client.get("/users/me")
    except MakeAPIError as e:
        error(str(e))
        raise SystemExit(1)
    u = data.get("user", data)
    if ctx.json_mode:
        print_json(u)
    else:
        print_kv(u, title="Current User")
