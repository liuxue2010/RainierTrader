import asyncio
import logging
import sys
from datetime import date
from pathlib import Path

import typer

from rainier_trader.config.settings import load_settings, validate_settings

app = typer.Typer(name="rainier", help="RainierTrader — Autonomous AI trading agent")


def _setup_logging(level: str, log_file: str) -> None:
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ],
    )


@app.command()
def run(
    config: str = typer.Option("config/config.yaml", help="Path to config file"),
    paper: bool = typer.Option(False, "--paper", help="Force paper trading mode"),
) -> None:
    """Start the trading agent."""
    settings = load_settings(config)
    if paper:
        settings.mode = "paper"

    errors = validate_settings(settings)
    if errors:
        for e in errors:
            typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)

    _setup_logging(settings.logging.level, settings.logging.file)

    from rainier_trader.core.orchestrator import Orchestrator
    typer.echo(f"Starting RainierTrader in {settings.mode.upper()} mode...")
    Orchestrator(settings).start()


@app.command(name="run-once")
def run_once(
    symbol: str = typer.Argument(..., help="Stock symbol to evaluate"),
    config: str = typer.Option("config/config.yaml", help="Path to config file"),
) -> None:
    """Run a single evaluation cycle for one symbol (useful for testing)."""
    settings = load_settings(config)
    errors = validate_settings(settings)
    if errors:
        for e in errors:
            typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)

    _setup_logging(settings.logging.level, settings.logging.file)

    from rainier_trader.core.orchestrator import Orchestrator
    typer.echo(f"Running single cycle for {symbol}...")
    asyncio.run(Orchestrator(settings).run_once(symbol))
    typer.echo("Done.")


@app.command()
def status(
    config: str = typer.Option("config/config.yaml", help="Path to config file"),
) -> None:
    """Show current portfolio and agent status."""
    async def _run():
        settings = load_settings(config)
        from rainier_trader.clients.alpaca_client import AlpacaClient
        from rainier_trader.utils.formatting import format_portfolio

        broker = AlpacaClient(settings.alpaca_api_key, settings.alpaca_secret_key, paper=settings.is_paper)
        account = await broker.get_account()
        positions = await broker.get_positions()
        typer.echo(format_portfolio(
            account.__dict__,
            [p.__dict__ for p in positions],
        ))

    asyncio.run(_run())


@app.command()
def trades(
    config: str = typer.Option("config/config.yaml", help="Path to config file"),
    today_only: bool = typer.Option(True, "--today/--all", help="Show today's trades or all"),
) -> None:
    """Show trade history."""
    from rainier_trader.storage.database import Database
    from rainier_trader.utils.formatting import format_trades_table

    db = Database()
    filter_date = str(date.today()) if today_only else None
    results = db.get_trades(date=filter_date)
    typer.echo(format_trades_table(results))


@app.command()
def report(
    period: str = typer.Option("day", help="Reporting period: day | week | month"),
) -> None:
    """Show performance report."""
    typer.echo(f"Performance report ({period}) — coming soon.")


@app.command(name="check-config")
def check_config(
    config: str = typer.Option("config/config.yaml", help="Path to config file"),
) -> None:
    """Validate configuration and API key setup."""
    try:
        settings = load_settings(config)
    except FileNotFoundError as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(1)

    errors = validate_settings(settings)
    if errors:
        for e in errors:
            typer.echo(f"[FAIL] {e}")
        raise typer.Exit(1)

    typer.echo("[OK] Configuration is valid.")
    typer.echo(f"     Mode:      {settings.mode}")
    typer.echo(f"     Watchlist: {', '.join(settings.watchlist)}")
    typer.echo(f"     Interval:  {settings.schedule.interval_minutes} min")
    typer.echo(f"     Model:     {settings.llm.model}")
