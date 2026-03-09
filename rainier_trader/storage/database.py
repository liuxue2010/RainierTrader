import sqlite3
from pathlib import Path

DB_PATH = Path("rainier.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    signal TEXT,
    confidence REAL,
    reasoning TEXT,
    risk_approved INTEGER,
    risk_note TEXT,
    order_id TEXT,
    quantity REAL,
    price REAL,
    total_value REAL,
    status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    starting_equity REAL,
    ending_equity REAL,
    daily_pnl REAL,
    daily_return_pct REAL,
    trades_executed INTEGER,
    trades_skipped INTEGER,
    win_count INTEGER,
    loss_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    config_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def insert_trade(self, entry: dict) -> None:
        sql = """
        INSERT INTO trades
            (timestamp, symbol, action, signal, confidence, reasoning,
             risk_approved, risk_note, order_id, quantity, price, total_value, status)
        VALUES
            (:timestamp, :symbol, :action, :signal, :confidence, :reasoning,
             :risk_approved, :risk_note, :order_id, :quantity, :price, :total_value, :status)
        """
        with self._conn() as conn:
            conn.execute(sql, entry)

    def get_trades(self, date: str | None = None, symbol: str | None = None) -> list[dict]:
        conditions = []
        params: list = []
        if date:
            conditions.append("DATE(timestamp) = ?")
            params.append(date)
        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM trades {where} ORDER BY timestamp DESC"
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def upsert_daily_summary(self, summary: dict) -> None:
        sql = """
        INSERT INTO daily_summary
            (date, starting_equity, ending_equity, daily_pnl, daily_return_pct,
             trades_executed, trades_skipped, win_count, loss_count)
        VALUES
            (:date, :starting_equity, :ending_equity, :daily_pnl, :daily_return_pct,
             :trades_executed, :trades_skipped, :win_count, :loss_count)
        ON CONFLICT(date) DO UPDATE SET
            ending_equity=excluded.ending_equity,
            daily_pnl=excluded.daily_pnl,
            daily_return_pct=excluded.daily_return_pct,
            trades_executed=excluded.trades_executed,
            trades_skipped=excluded.trades_skipped,
            win_count=excluded.win_count,
            loss_count=excluded.loss_count
        """
        with self._conn() as conn:
            conn.execute(sql, summary)
