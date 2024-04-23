from msgspec import Struct, field


class Trade(Struct):
    event_type: str = field(name="e")
    event_time: int = field(name="E")
    symbol: str = field(name="s")
    price: str = field(name="p")
    trade_time: int = field(name="T")
    quantity: str = field(name="q")

    def __post_init__(self) -> None:
        self.price = float(self.price)  # type: ignore
        self.quantity = float(self.quantity)  # type: ignore
