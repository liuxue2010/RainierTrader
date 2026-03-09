from langgraph.graph import StateGraph, END

from rainier_trader.core.state import TradingState
from rainier_trader.nodes.market_data import fetch_market_data
from rainier_trader.nodes.analysis import analyze_indicators
from rainier_trader.nodes.decision import llm_decision
from rainier_trader.nodes.risk import risk_check
from rainier_trader.nodes.execution import execute_order
from rainier_trader.nodes.logger import log_trade, log_skip


def build_workflow() -> StateGraph:
    workflow = StateGraph(TradingState)

    workflow.add_node("fetch_market_data", fetch_market_data)
    workflow.add_node("analyze", analyze_indicators)
    workflow.add_node("decide", llm_decision)
    workflow.add_node("risk_check", risk_check)
    workflow.add_node("execute", execute_order)
    workflow.add_node("log_skip", log_skip)
    workflow.add_node("log_trade", log_trade)

    workflow.set_entry_point("fetch_market_data")
    workflow.add_edge("fetch_market_data", "analyze")
    workflow.add_edge("analyze", "decide")

    workflow.add_conditional_edges(
        "decide",
        lambda state: "risk_check" if state["action"] != "hold" else "log_skip",
    )
    workflow.add_conditional_edges(
        "risk_check",
        lambda state: "execute" if state["risk_approved"] else "log_skip",
    )

    workflow.add_edge("execute", "log_trade")
    workflow.add_edge("log_skip", END)
    workflow.add_edge("log_trade", END)

    return workflow.compile()
