# ruff: noqa: ERA001
from enum import Enum
from typing import Any

from msgspec import Struct


class STATUS(Enum):
    INITIAL = 0
    READY = 1
    ENTERING_POSITION = 2
    IN_POSITION = 3
    CLOSING_POSITION = 4
    SLEEPING = 5
    ERROR = 9


class Position(Struct):
    price: float = 0.0
    position_time: int = 0
    amount: float = 0.0
    sl_price: float = 0.0
    tp_price: float = 0.0


class Balance:
    def __init__(self, asset: str, free: float, locked: float) -> None:
        self.asset = asset
        self.free = free
        self.locked = locked


class Balances:
    def __init__(self) -> None:
        self._balances: Any = {}

    def update_balance(self, asset: str, free: float, locked: float) -> None:
        self._balances[asset] = Balance(asset, free, locked)

    def __getattr__(self, item: str) -> Any:
        return self._balances.get(item, None)


class State(Struct):
    balances: Balances = Balances()

    stream_ready: bool = False
    balance_ready: bool = False
    symbols_ready: bool = False

    base_asset: str = ""
    quote_asset: str = ""
    min_qty: float = 0.0
    min_notional: float = 0.0

    status: STATUS = STATUS.INITIAL
    last_price: float = 0.0
    position: Position | None = None
    sleeping_at: float = 0.0

    total_tp_trades: int = 0
    total_sl_trades: int = 0
    total_pnl: float = 0.0

    # orders: dict | None = None
    # orders_processing: dict | None = None  # for limit orders
