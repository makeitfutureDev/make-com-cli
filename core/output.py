"""Output helpers: rich tables vs JSON."""
import json
import sys
import functools
from typing import Any
from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)

# Module-level flag set by the CLI root group
_json_mode = False


def set_json_mode(enabled: bool):
    global _json_mode
    _json_mode = enabled


def print_json(data: Any):
    print(json.dumps(data, indent=2, default=str))


def print_error_json(msg: str, error_type: str = "api_error"):
    """Output a structured JSON error to stdout (for agent consumption)."""
    print(json.dumps({"error": msg, "type": error_type}))


def print_table(headers: list, rows: list, title: str = None):
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for h in headers:
        table.add_column(str(h))
    for row in rows:
        table.add_row(*[str(v) if v is not None else "" for v in row])
    console.print(table)


def print_kv(data: dict, title: str = None):
    """Print a single object as key-value pairs."""
    table = Table(title=title, show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold cyan", no_wrap=True)
    table.add_column("Value")
    for k, v in data.items():
        table.add_row(str(k), str(v) if v is not None else "")
    console.print(table)


def error(msg: str):
    if _json_mode:
        print_error_json(msg)
    else:
        err_console.print(f"[bold red]Error:[/bold red] {msg}")


def success(msg: str):
    if _json_mode:
        return  # success messages are noise in JSON mode
    console.print(f"[bold green]✓[/bold green] {msg}")
