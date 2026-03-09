import logging
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

from rainier_trader.config.settings import Settings
from rainier_trader.core.workflow import build_workflow

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)


def is_market_hours() -> bool:
    now = datetime.now(ET)
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE


class Orchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.app = build_workflow()
        self._running = False

    def run_cycle(self) -> None:
        if self.settings.schedule.market_hours_only and not is_market_hours():
            logger.debug("Outside market hours — skipping cycle")
            return

        for symbol in self.settings.watchlist:
            logger.info(f"Evaluating {symbol}")
            try:
                initial_state: dict = {
                    "symbol": symbol,
                    "timestamp": datetime.now(ET).isoformat(),
                }
                self.app.invoke(initial_state)
            except Exception:
                logger.exception(f"Unhandled error evaluating {symbol}")

    def run_once(self, symbol: str) -> None:
        initial_state: dict = {
            "symbol": symbol,
            "timestamp": datetime.now(ET).isoformat(),
        }
        self.app.invoke(initial_state)

    def start(self) -> None:
        self._running = True
        interval = self.settings.schedule.interval_minutes
        logger.info(f"Starting orchestrator — interval={interval}m, watchlist={self.settings.watchlist}")

        scheduler = BlockingScheduler()
        scheduler.add_job(self.run_cycle, "interval", minutes=interval)
        self.run_cycle()  # run immediately on start
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Orchestrator stopped")
