"""make-cli repl — interactive shell with tab-completion and history."""
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

    import subprocess
    import sys
    import shlex
    from pathlib import Path

    # Build completions from all registered commands
    main_cmd = ctx.find_root().command
    top_commands = list(main_cmd.commands.keys())

    # Gather all subcommands for completion
    completions = list(top_commands)
    for cmd_name, cmd_obj in main_cmd.commands.items():
        if hasattr(cmd_obj, "commands"):
            for sub in cmd_obj.commands.keys():
                completions.append(f"{cmd_name} {sub}")

    completer = WordCompleter(completions, sentence=True)

    style = Style.from_dict({
        "prompt": "ansigreen bold",
    })

    history_dir = Path.home() / ".make-cli"
    history_dir.mkdir(exist_ok=True)
    history_file = history_dir / "repl_history"

    session = PromptSession(
        history=FileHistory(str(history_file)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
        style=style,
    )

    console.print("[bold green]make-cli REPL[/bold green] — type commands, [dim]exit[/dim] or [dim]Ctrl+D[/dim] to quit, [dim]Tab[/dim] to complete\n")

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

        # Run as subprocess so Click context is fresh each time
        result = subprocess.run(
            [sys.executable, "-m", "make_cli.cli"] + args,
            capture_output=False,
        )
