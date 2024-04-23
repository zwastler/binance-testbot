from msgspec import Struct, field


class Order(Struct):
    event_type: str = field(name="e")
    event_time: int = field(name="E")
    symbol: str = field(name="s")
    side: str = field(name="S")
    order_type: str = field(name="o")
    quantity: str = field(name="q")
    price: str = field(name="p")
    current_order_status: str = field(name="X")
    last_executed_quantity: str = field(name="l")
    last_executed_price: str = field(name="L")
    commission_amount: str = field(name="n")
    commission_asset: str | None = field(name="N")
    transaction_time: int = field(name="T")

    def __post_init__(self) -> None:
        self.price = float(self.price)  # type: ignore
        self.quantity = float(self.quantity)  # type: ignore
        self.last_executed_price = float(self.last_executed_price)  # type: ignore
        self.last_executed_quantity = float(self.last_executed_quantity)  # type: ignore
        self.commission_amount = float(self.commission_amount)  # type: ignore
