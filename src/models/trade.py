# ruff: noqa: ERA001
from msgspec import Struct, field


class Trade(Struct):
    event_type: str = field(name="e")
    event_time: int = field(name="E")
    symbol: str = field(name="s")
    price: str = field(name="p")
    trade_time: int = field(name="T")

    # UNUSED FIELDS
    # trade_id: int = field(name="t")
    # quantity: str = field(name="q")
    # buyer_order_id: int = field(name="b")
    # seller_order_id: int = field(name="a")
    # is_buyer_market_maker: bool = field(name="m")

    def __post_init__(self) -> None:
        self.price = float(self.price)  # type: ignore
        self.quantity = float(self.quantity)  # type: ignore
