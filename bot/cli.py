"""
╔══════════════════════════════════════════════════╗
║        Binance Spot Testnet Trading Bot CLI      ║
╚══════════════════════════════════════════════════╝
"""

from __future__ import annotations

import os
from typing import Optional

import typer
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import get_logger, get_log_file_path
from bot.orders import place_order
from bot.validators import ValidationError

# ─────────────────────────────────────────────────

logger = get_logger(__name__)
console = Console()

app = typer.Typer(
    name="trading-bot",
    help="⚡ Binance Spot Testnet Trading Bot",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# ─────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────

def _banner() -> None:
    banner = Text()
    banner.append("  ◈ ", style="cyan")
    banner.append("BINANCE SPOT", style="bold white")
    banner.append("  ·  ", style="dim white")
    banner.append("TESTNET", style="bold yellow")
    banner.append("  ·  ", style="dim white")
    banner.append("TRADING BOT", style="bold cyan")
    banner.append("  ◈", style="cyan")

    console.print()
    console.print(Panel(
        Align.center(banner),
        border_style="cyan",
        padding=(0, 4),
    ))

    console.print(
        Align.center(Text(f"Log → {get_log_file_path()}", style="dim")),
    )
    console.print()


# ─────────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────────

def _get_client() -> BinanceClient:
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        console.print("[red]Missing API credentials[/]")
        raise typer.Exit(1)

    return BinanceClient(api_key, api_secret)


# ─────────────────────────────────────────────────
# Order UI
# ─────────────────────────────────────────────────

def _print_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str],
):
    side_color = "green" if side == "BUY" else "red"

    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Field", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Symbol", symbol)
    table.add_row("Side", f"[{side_color}]{side}[/]")
    table.add_row("Type", order_type)
    table.add_row("Quantity", quantity)

    if price:
        table.add_row("Price", price)

    console.print(Panel(table, title="Order Request", border_style="cyan"))


def _print_order_response(result):
    if not result.success:
        console.print(Panel(
            f"[red]{result.error}[/]",
            title="Order Failed",
            border_style="red",
        ))
        raise typer.Exit(1)

    data = result.data

    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Field", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Order ID", str(data.get("orderId")))
    table.add_row("Symbol", data.get("symbol"))
    table.add_row("Side", data.get("side"))
    table.add_row("Status", data.get("status"))
    table.add_row("Executed Qty", data.get("executedQty"))

    console.print(Panel(
        table,
        title="[green]✓ Order Placed[/]",
        border_style="green",
    ))


# ─────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────

@app.command()
def order(
    symbol: str,
    side: str = typer.Option(..., "--side"),
    order_type: str = typer.Option(..., "--type"),
    qty: str = typer.Option(..., "--qty"),
    price: Optional[str] = typer.Option(None, "--price"),
):
    """Place order"""

    _banner()

    _print_order_request(symbol, side, order_type, qty, price)

    client = _get_client()

    with console.status("[cyan]Placing order..."):
        result = place_order(
            client=client,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=price,
        )

    _print_order_response(result)


# ─────────────────────────────────────────────────
# Account (FIXED FOR SPOT)
# ─────────────────────────────────────────────────

@app.command()
def account():
    """Show account balances"""

    _banner()
    client = _get_client()

    with console.status("[cyan]Fetching account..."):
        try:
            account = client.get_account()
        except BinanceAPIError as e:
            console.print(f"[red]{e}[/]")
            raise typer.Exit(1)

    balances = account.get("balances", [])

    rows = []
    for b in balances:
        free = float(b["free"])
        locked = float(b["locked"])
        total = free + locked

        if total > 0:
            rows.append((b["asset"], free, locked, total))

    table = Table(
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
        border_style="cyan",
    )

    table.add_column("Asset")
    table.add_column("Free", justify="right")
    table.add_column("Locked", justify="right")
    table.add_column("Total", justify="right")

    for asset, free, locked, total in rows:
        table.add_row(
            asset,
            f"{free:.6f}",
            f"{locked:.6f}",
            f"[bold]{total:.6f}[/]",
        )

    console.print(Panel(
        table,
        title="Spot Account Balances",
        border_style="cyan",
    ))


# ─────────────────────────────────────────────────
# Cancel
# ─────────────────────────────────────────────────

@app.command()
def cancel(symbol: str, order_id: int):
    """Cancel order"""

    _banner()
    client = _get_client()

    with console.status("[cyan]Cancelling..."):
        try:
            resp = client.cancel_order(symbol, order_id)
        except BinanceAPIError as e:
            console.print(f"[red]{e}[/]")
            raise typer.Exit(1)

    console.print(Panel(
        f"[green]Order {order_id} cancelled[/]",
        border_style="green",
    ))


# ─────────────────────────────────────────────────
# Open Orders
# ─────────────────────────────────────────────────

@app.command("open-orders")
def open_orders(symbol: Optional[str] = None):
    """List open orders"""

    _banner()
    client = _get_client()

    with console.status("[cyan]Fetching open orders..."):
        orders = client.get_open_orders(symbol)

    if not orders:
        console.print("No open orders.")
        return

    table = Table(box=box.SIMPLE_HEAD, header_style="bold cyan")

    table.add_column("Order ID")
    table.add_column("Symbol")
    table.add_column("Side")
    table.add_column("Price")
    table.add_column("Qty")
    table.add_column("Status")

    for o in orders:
        table.add_row(
            str(o["orderId"]),
            o["symbol"],
            o["side"],
            o["price"],
            o["origQty"],
            o["status"],
        )

    console.print(Panel(table, border_style="cyan"))


# ─────────────────────────────────────────────────
# Ping
# ─────────────────────────────────────────────────

@app.command()
def ping():
    """Check connectivity"""

    _banner()
    client = _get_client()

    with console.status("[cyan]Pinging..."):
        ok = client.ping()

    if ok:
        console.print("[green]✓ Binance reachable[/]")
    else:
        console.print("[red]Connection failed[/]")


# ─────────────────────────────────────────────────

if __name__ == "__main__":
    app()
