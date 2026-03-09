# Phase 3: OpenClaw Skill adapter
# Thin wrapper around core orchestrator for OpenClaw messaging interface.
# See openclaw/skill.json for the manifest.

import asyncio
import threading

from rainier_trader.config.settings import load_settings
from rainier_trader.core.orchestrator import Orchestrator

_orchestrator: Orchestrator | None = None
_thread: threading.Thread | None = None


def handle_command(command: str, args: list[str] | None = None) -> str:
    """Entry point called by OpenClaw gateway."""
    if command == "start":
        return _start()
    elif command == "stop":
        return _stop()
    elif command == "status":
        return _status()
    elif command == "portfolio":
        return asyncio.run(_portfolio())
    elif command == "trades":
        return _trades()
    elif command == "performance":
        return "Performance reporting coming soon."
    return f"Unknown command: {command}"


def _start() -> str:
    global _orchestrator, _thread
    if _thread and _thread.is_alive():
        return "RainierTrader is already running."
    settings = load_settings()
    _orchestrator = Orchestrator(settings)
    _thread = threading.Thread(target=_orchestrator.start, daemon=True)
    _thread.start()
    return f"RainierTrader started in {settings.mode} mode. Watching: {', '.join(settings.watchlist)}"


def _stop() -> str:
    return "Stop signal sent. (Graceful shutdown coming in a future release.)"


def _status() -> str:
    running = _thread and _thread.is_alive()
    return f"Status: {'RUNNING' if running else 'STOPPED'}"


async def _portfolio() -> str:
    from rainier_trader.clients.alpaca_client import AlpacaClient
    from rainier_trader.utils.formatting import format_portfolio

    settings = load_settings()
    broker = AlpacaClient(settings.alpaca_api_key, settings.alpaca_secret_key, paper=settings.is_paper)
    account = await broker.get_account()
    positions = await broker.get_positions()
    return format_portfolio(account.__dict__, [p.__dict__ for p in positions])


def _trades() -> str:
    from datetime import date
    from rainier_trader.storage.database import Database
    from rainier_trader.utils.formatting import format_trades_table

    db = Database()
    results = db.get_trades(date=str(date.today()))
    return format_trades_table(results)
