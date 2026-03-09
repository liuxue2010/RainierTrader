from datetime import date


def format_trades_table(trades: list[dict]) -> str:
    if not trades:
        return "No trades found."

    header = f"{'Time':<20} {'Symbol':<8} {'Action':<6} {'Price':>8} {'Qty':>8} {'Status':<10} Reasoning"
    sep = "-" * 90
    rows = [header, sep]
    for t in trades:
        ts = t.get("timestamp", "")[:19]
        rows.append(
            f"{ts:<20} {t['symbol']:<8} {t['action']:<6} "
            f"{_money(t.get('price')):>8} {_num(t.get('quantity')):>8} "
            f"{t.get('status', ''):<10} {(t.get('reasoning') or '')[:50]}"
        )
    return "\n".join(rows)


def format_portfolio(account: dict, positions: list[dict]) -> str:
    lines = [
        f"Equity:        ${account['equity']:>12,.2f}",
        f"Cash:          ${account['cash']:>12,.2f}",
        f"Buying Power:  ${account['buying_power']:>12,.2f}",
        f"Daily P&L:     ${account['daily_pl']:>+12,.2f} ({account['daily_pl_pct']:+.2f}%)",
        "",
        "Positions:",
    ]
    if not positions:
        lines.append("  (none)")
    for p in positions:
        lines.append(
            f"  {p['symbol']:<8} qty={p['qty']:.2f}  "
            f"avg=${p['avg_entry_price']:.2f}  "
            f"current=${p['current_price']:.2f}  "
            f"P&L=${p['unrealized_pl']:+.2f} ({float(p['unrealized_plpc'])*100:+.2f}%)"
        )
    return "\n".join(lines)


def _money(v) -> str:
    return f"${v:.2f}" if v is not None else "N/A"


def _num(v) -> str:
    return f"{v:.2f}" if v is not None else "N/A"
