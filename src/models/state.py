# ruff: noqa: ERA001
from enum import Enum

from msgspec import Struct


class STATUS(Enum):
    INITIAL = 0
    READY = 1
    ENTERING_POSITION = 2
    IN_POSITION = 3
    CLOSING_POSITION = 4
    SLEEPING = 5


class Position(Struct):
    price: float = 0.0
    position_time: int = 0
    amount: float = 0.0
    sl_price: float = 0.0
    tp_price: float = 0.0


# class Balance(Struct):
#     asset: str
#     free: float
#     locked: float


class State(Struct):
    status: STATUS = STATUS.INITIAL
    stream_ready: bool = False
    last_price: float = 0.0
    position: Position | None = None
    sleeping_at: float = 0.0

    # balances = [Balance]
    # orders: dict | None = None
    # orders_processing: dict | None = None  # for limit orders
