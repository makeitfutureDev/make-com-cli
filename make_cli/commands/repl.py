"""make-cli repl — interactive shell with tab-completion and history."""
import shlex
import click
from core.output import console


@click.command("repl")
@click.pass_context
def repl(ctx):
    """Start an interactive REPL shell for make-cli."""
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.completion import WordCompleter
        from prompt_toolkit.styles import Style
    except ImportError:
        console.print("[red]prompt-toolkit is required for REPL mode.[/red]")
        raise SystemExit(1)

    from pathlib import Path

    # Build completions from all registered commands
    root_cmd = ctx.find_root().command
    completions = list(root_cmd.commands.keys())
    for cmd_name, cmd_obj in root_cmd.commands.items():
        if hasattr(cmd_obj, "commands"):
            for sub in cmd_obj.commands.keys():
                completions.append(f"{cmd_name} {sub}")

    completer = WordCompleter(completions, sentence=True)

    style = Style.from_dict({
        "prompt": "ansigreen bold",
    })

    history_dir = Path.home() / ".make-cli"
    history_dir.mkdir(exist_ok=True)

    session = PromptSession(
        history=FileHistory(str(history_dir / "repl_history")),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        style=style,
    )

    # Banner with SKILL.md path for AI agent discoverability
    from make_cli.cli import __version__
    skill_path = Path(__file__).resolve().parent.parent.parent / "SKILL.md"
    console.print(f"[bold green]make-cli REPL[/bold green] v{__version__}")
    console.print(f"[dim]SKILL.md: {skill_path}[/dim]")
    console.print("[dim]Type commands, [bold]Tab[/bold] to complete, [bold]exit[/bold] or [bold]Ctrl+D[/bold] to quit[/dim]\n")

    while True:
        try:
            raw = session.prompt("make-cli> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye![/dim]")
            break

        raw = raw.strip()
        if not raw:
            continue
        if raw in ("exit", "quit", "q"):
            console.print("[dim]Bye![/dim]")
            break
        if raw in ("help", "?"):
            raw = "--help"

        try:
            args = shlex.split(raw)
        except ValueError as e:
            console.print(f"[red]Parse error:[/red] {e}")
            continue

        # Run in-process via Click's invoke — no subprocess overhead
        try:
            root_cmd.main(args, ctx=ctx.find_root(), standalone_mode=False)
        except SystemExit:
            pass
        except click.exceptions.UsageError as e:
            console.print(f"[yellow]Usage error:[/yellow] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
        finally:
            # Reset json_mode so --json in one command doesn't leak to the next
            from core.output import set_json_mode
            set_json_mode(False)
