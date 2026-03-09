import os
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

from rainier_trader.config.defaults import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class ScheduleConfig:
    interval_minutes: int
    market_hours_only: bool


@dataclass
class IndicatorConfig:
    sma_fast: int
    sma_slow: int
    sma_trend: int
    rsi_period: int
    rsi_overbought: int
    rsi_oversold: int
    macd_fast: int
    macd_slow: int
    macd_signal: int
    bb_period: int
    bb_std: float


@dataclass
class StrategyConfig:
    indicators: IndicatorConfig
    min_confidence: float


@dataclass
class RiskConfig:
    max_position_pct: float
    max_positions: int
    stop_loss_pct: float
    take_profit_pct: float
    daily_loss_limit_pct: float
    min_cash_reserve_pct: float


@dataclass
class OrderConfig:
    type: str
    time_in_force: str


@dataclass
class LLMConfig:
    model: str
    temperature: float
    max_tokens: int


@dataclass
class LoggingConfig:
    level: str
    file: str


@dataclass
class Settings:
    mode: str
    watchlist: list[str]
    schedule: ScheduleConfig
    strategy: StrategyConfig
    risk: RiskConfig
    orders: OrderConfig
    llm: LLMConfig
    logging: LoggingConfig

    # Secrets (from .env)
    alpaca_api_key: str = field(default="", repr=False)
    alpaca_secret_key: str = field(default="", repr=False)
    anthropic_api_key: str = field(default="", repr=False)

    @property
    def is_paper(self) -> bool:
        return self.mode == "paper"


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_settings(config_path: str | Path = "config/config.yaml") -> Settings:
    load_dotenv()

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path) as f:
        user_config = yaml.safe_load(f) or {}

    cfg = _deep_merge(DEFAULT_CONFIG, user_config)
    ind = cfg["strategy"]["indicators"]

    return Settings(
        mode=cfg["mode"],
        watchlist=cfg["watchlist"],
        schedule=ScheduleConfig(**cfg["schedule"]),
        strategy=StrategyConfig(
            indicators=IndicatorConfig(**ind),
            min_confidence=cfg["strategy"]["min_confidence"],
        ),
        risk=RiskConfig(**cfg["risk"]),
        orders=OrderConfig(**cfg["orders"]),
        llm=LLMConfig(**cfg["llm"]),
        logging=LoggingConfig(**cfg["logging"]),
        alpaca_api_key=os.getenv("ALPACA_API_KEY", ""),
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )


def validate_settings(settings: Settings) -> list[str]:
    errors = []
    if not settings.alpaca_api_key:
        errors.append("ALPACA_API_KEY is not set")
    if not settings.alpaca_secret_key:
        errors.append("ALPACA_SECRET_KEY is not set")
    if not settings.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY is not set")
    if not settings.watchlist:
        errors.append("watchlist is empty")
    if settings.mode not in ("paper", "live"):
        errors.append(f"mode must be 'paper' or 'live', got '{settings.mode}'")
    return errors
