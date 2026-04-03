"""Output helpers: rich tables vs JSON."""
import json
from typing import Any
from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def print_json(data: Any):
    print(json.dumps(data, indent=2, default=str))


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
    err_console.print(f"[bold red]Error:[/bold red] {msg}")


def success(msg: str):
    console.print(f"[bold green]✓[/bold green] {msg}")
