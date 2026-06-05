import typer
from typing import Optional
from dotenv import load_dotenv
from api.order_service import OrderService
from api.models import OrderRequest, OrderSide, OrderType
from api.exceptions import TradingBotException
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.theme import Theme
import sys

# Load environment variables
load_dotenv()

# Setup rich console
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "highlight": "magenta bold"
})
console = Console(theme=custom_theme)

app = typer.Typer(
    help="Binance Futures Testnet Trading CLI",
    rich_markup_mode="rich"
)

def display_order_summary(order_type: OrderType, symbol: str, side: OrderSide, quantity: float, price: Optional[float] = None, stop_price: Optional[float] = None):
    """Displays a beautiful order summary using Rich panel and table."""
    table = Table(show_header=False, box=None)
    table.add_row("[cyan]Order Type:[/cyan]", f"[highlight]{order_type.value}[/highlight]")
    table.add_row("[cyan]Symbol:[/cyan]", f"[white]{symbol.upper()}[/white]")
    
    # Live price with 5% deviation limit
    try:
        from api.binance_client import BinanceClient
        live_price = BinanceClient().get_symbol_price(symbol.upper())
    except Exception:
        live_price = 0.0

    if live_price > 0:
        deviation = live_price * 0.05
        table.add_row("[cyan]Live Price:[/cyan]", f"[white]${live_price:,.2f} ± {int(deviation):,}[/white]")
        
    side_color = "green" if side == OrderSide.BUY else "red"
    table.add_row("[cyan]Side:[/cyan]", f"[{side_color} bold]{side.value}[/{side_color} bold]")
    table.add_row("[cyan]Quantity:[/cyan]", f"[white]{quantity}[/white]")
    
    if price is not None:
        table.add_row("[cyan]Price:[/cyan]", f"[white]${price}[/white]")
    if stop_price is not None:
        table.add_row("[cyan]Stop Price:[/cyan]", f"[white]${stop_price}[/white]")
        
    # Virtual wallet info
    try:
        from api.wallet import get_wallet_summary
        w = get_wallet_summary(symbol)
        balance = w.get("balance", 10000.0)
        position = w.get("position", 0.0)
        position_value = w.get("position_value", 0.0)
        total_value = w.get("total_value", 10000.0)
        sandbox = w.get("mock_mode", False)
        
        sandbox_text = "[bold green]ENABLED (Local Mock Mode)[/bold green]" if sandbox else "[bold red]DISABLED (Real Binance API)[/bold red]"
        table.add_row("[cyan]Sandbox Mode:[/cyan]", sandbox_text)
        table.add_row("[cyan]Wallet USD Balance:[/cyan]", f"[white]${balance:,.2f}[/white]")
        table.add_row("[cyan]Open Position Qty:[/cyan]", f"[white]{position:,.4f} contracts[/white]")
        table.add_row("[cyan]Holding Value ($):[/cyan]", f"[white]${position_value:,.2f}[/white]")
        table.add_row("[cyan]Total Net Worth ($):[/cyan]", f"[bold yellow]${total_value:,.2f}[/bold yellow]")
    except Exception:
        pass
        
    console.print(Panel(
        table,
        title="[bold yellow]Order Confirmation Summary[/bold yellow]",
        border_style="yellow",
        expand=False
    ))

def execute_order(request: OrderRequest):
    """Executes the order through OrderService and displays the result."""
    service = OrderService()
    
    console.print("\n[info]Communicating with Binance Futures Testnet...[/info]")
    try:
        response = service.place_order(request)
        
        # Display response in a nice table
        table = Table(title="[bold green]Order Execution Result[/bold green]", border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Status", "[success]SUCCESS[/success]" if response.success else "[error]FAILED[/error]")
        table.add_row("Symbol", response.symbol)
        table.add_row("Side", response.side)
        table.add_row("Order Type", response.order_type)
        table.add_row("Order ID", str(response.order_id))
        table.add_row("Binance Status", response.status)
        table.add_row("Executed Qty", response.executed_qty)
        table.add_row("Avg Execution Price", f"${response.avg_price}")
        
        console.print(table)
        console.print("\n[success]Order processed successfully and logged.[/success]\n")

        
    except TradingBotException as e:
        console.print(Panel(
            f"[error]Error placing order:[/error]\n[white]{e}[/white]",
            title="[bold red]Execution Failed[/bold red]",
            border_style="red"
        ))
        sys.exit(1)
    except Exception as e:
        console.print(Panel(
            f"[error]Unexpected critical error:[/error]\n[white]{e}[/white]",
            title="[bold red]System Error[/bold red]",
            border_style="red"
        ))
        sys.exit(1)

@app.command()
def health():
    """Checks connection to Binance Futures Testnet."""
    console.print("[info]Checking connectivity to Binance Futures Testnet...[/info]")
    service = OrderService()
    result = service.health_check()
    
    if result.get("status") == "ok":
        console.print(Panel(
            f"[success]Status: Connected[/success]\n[white]Exchange: {result.get('exchange')}[/white]",
            title="[bold green]System Health Check[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[error]Status: Disconnected[/error]\n[red]Message: {result.get('message')}[/red]",
            title="[bold red]System Health Check[/bold red]",
            border_style="red"
        ))
        sys.exit(1)

@app.command()
def market(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair symbol (e.g. BTCUSDT)"),
    side: OrderSide = typer.Option(..., "--side", "-d", help="Order side (BUY/SELL)"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity")
):
    """Places a MARKET order on Binance Futures Testnet."""
    display_order_summary(OrderType.MARKET, symbol, side, quantity)
    
    confirm = typer.confirm("Confirm placement of this MARKET order?")
    if not confirm:
        console.print("[warning]Order cancelled by user.[/warning]")
        raise typer.Abort()
        
    request = OrderRequest(
        symbol=symbol.upper(),
        side=side,
        order_type=OrderType.MARKET,
        quantity=quantity
    )
    execute_order(request)

@app.command()
def limit(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair symbol (e.g. BTCUSDT)"),
    side: OrderSide = typer.Option(..., "--side", "-d", help="Order side (BUY/SELL)"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: float = typer.Option(..., "--price", "-p", help="Limit execution price")
):
    """Places a LIMIT order on Binance Futures Testnet."""
    display_order_summary(OrderType.LIMIT, symbol, side, quantity, price=price)
    
    confirm = typer.confirm("Confirm placement of this LIMIT order?")
    if not confirm:
        console.print("[warning]Order cancelled by user.[/warning]")
        raise typer.Abort()
        
    request = OrderRequest(
        symbol=symbol.upper(),
        side=side,
        order_type=OrderType.LIMIT,
        quantity=quantity,
        price=price
    )
    execute_order(request)

@app.command()
def stop_limit(
    symbol: str = typer.Option(..., "--symbol", "-s", help="Trading pair symbol (e.g. BTCUSDT)"),
    side: OrderSide = typer.Option(..., "--side", "-d", help="Order side (BUY/SELL)"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="Order quantity"),
    price: float = typer.Option(..., "--price", "-p", help="Limit execution price"),
    stop_price: float = typer.Option(..., "--stop-price", "-t", help="Trigger stop price")
):
    """Places a STOP_LIMIT order on Binance Futures Testnet."""
    display_order_summary(OrderType.STOP_LIMIT, symbol, side, quantity, price=price, stop_price=stop_price)
    
    confirm = typer.confirm("Confirm placement of this STOP_LIMIT order?")
    if not confirm:
        console.print("[warning]Order cancelled by user.[/warning]")
        raise typer.Abort()
        
    request = OrderRequest(
        symbol=symbol.upper(),
        side=side,
        order_type=OrderType.STOP_LIMIT,
        quantity=quantity,
        price=price,
        stop_price=stop_price
    )
    execute_order(request)

@app.command()
def wallet(
    symbol: str = typer.Option("BTCUSDT", "--symbol", "-s", help="Symbol to price open position value")
):
    """Displays simulated local virtual wallet state (balance, positions, net worth)."""
    try:
        from api.wallet import get_wallet_summary
        w = get_wallet_summary(symbol)
        balance = w.get("balance", 10000.0)
        position = w.get("position", 0.0)
        position_value = w.get("position_value", 0.0)
        total_value = w.get("total_value", 10000.0)
        price = w.get("price", 0.0)
        
        table = Table(title=f"[bold yellow]Virtual Wallet Status (Priced at {symbol.upper()} @ ${price:,.2f})[/bold yellow]", border_style="yellow")
        table.add_column("Asset/Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Virtual USD Balance (Margin)", f"${balance:,.2f}")
        table.add_row("Open Contract Position", f"{position:,.4f} contracts")
        table.add_row("Holding Position Value ($)", f"${position_value:,.2f}")
        table.add_row("Total Account Net Worth ($)", f"[bold yellow]${total_value:,.2f}[/bold yellow]")
        console.print(table)
    except Exception as e:
        console.print(f"[error]Error fetching wallet status: {e}[/error]")

@app.command()
def load_funds(
    amount: float = typer.Option(10000.0, "--amount", "-a", help="Amount of virtual funds to load")
):
    """Loads simulated virtual funds into the virtual wallet."""
    try:
        from api.wallet import load_funds
        new_balance = load_funds(amount)
        console.print(f"[success]Successfully loaded ${amount:,.2f} virtual funds![/success]")
        console.print(f"[info]New Wallet Balance: ${new_balance:,.2f}[/info]")
    except Exception as e:
        console.print(f"[error]Error loading virtual funds: {e}[/error]")

@app.command()
def sandbox(
    enable: Optional[bool] = typer.Option(None, "--enable/--disable", help="Enable or disable sandbox mode (local simulated execution)")
):
    """View or toggle local Sandbox/Mock Exchange Mode."""
    from api.wallet import is_mock_mode, set_mock_mode
    if enable is None:
        current = is_mock_mode()
        status_text = "[success]ENABLED (Local Simulated Trades)[/success]" if current else "[error]DISABLED (Real Binance Testnet API)[/error]"
        console.print(f"Current Sandbox Mode: {status_text}")
    else:
        res = set_mock_mode(enable)
        status_text = "[success]ENABLED[/success]" if res else "[error]DISABLED[/error]"
        console.print(f"[info]Sandbox Mode updated to:[/info] {status_text}")

if __name__ == "__main__":
    app()


