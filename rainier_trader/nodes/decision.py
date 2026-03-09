import logging

from rainier_trader.core.state import TradingState

logger = logging.getLogger(__name__)


async def llm_decision(state: TradingState) -> dict:
    from rainier_trader.clients.llm_client import ClaudeClient
    from rainier_trader.clients.alpaca_client import AlpacaClient
    from rainier_trader.config.settings import load_settings
    from rainier_trader.models.portfolio import Portfolio

    settings = load_settings()
    broker = AlpacaClient(settings.alpaca_api_key, settings.alpaca_secret_key, paper=settings.is_paper)
    llm = ClaudeClient(
        settings.anthropic_api_key,
        settings.llm.model,
        settings.llm.temperature,
        settings.llm.max_tokens,
    )

    try:
        account = await broker.get_account()
        positions = await broker.get_positions()
        portfolio = Portfolio(account=account, positions=positions)

        decision = await llm.analyze_and_decide(
            symbol=state["symbol"],
            indicators=state["indicators"],
            portfolio=portfolio,
            timestamp=state["timestamp"],
        )
        logger.info(
            f"{state['symbol']}: decision={decision.action} confidence={decision.confidence:.2f}"
        )
        return {
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
        }
    except Exception:
        logger.exception(f"{state['symbol']}: LLM decision failed — defaulting to hold")
        return {"action": "hold", "confidence": 0.0, "reasoning": "LLM unavailable"}
