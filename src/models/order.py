# ruff: noqa: ERA001
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

    # UNUSED FIELDS
    # client_order_id: str | None = field(name="c")
    # order_creation_time: int = field(name="O")
    # cumulative_quote_asset_transacted_quantity: str = field(name="Z")
    # last_quote_asset_transacted_quantity: str = field(name="Y")
    # quote_order_quantity: str = field(name="Q")
    # working_time: int = field(name="W")
    # time_in_force: str = field(name="f")
    # stop_price: str = field(name="P")
    # iceberg_quantity: str = field(name="F")
    # order_list_id: int = field(name="g")
    # original_client_order_id: str | None = field(name="C")
    # current_execution_type: str = field(name="x")
    # order_reject_reason: str = field(name="r")
    # order_id: int = field(name="i")
    # cumulative_filled_quantity: str = field(name="z")
    # trade_id: int = field(name="t")
    # ignore: int = field(name="I")
    # is_order_on_the_book: bool = field(name="w")
    # is_trade_the_maker_side: bool = field(name="m")
    # ignore2: bool = field(name="M")

    def __post_init__(self) -> None:
        self.price = float(self.price)  # type: ignore
        self.quantity = float(self.quantity)  # type: ignore
        self.last_executed_price = float(self.last_executed_price)  # type: ignore
        self.last_executed_quantity = float(self.last_executed_quantity)  # type: ignore
        self.commission_amount = float(self.commission_amount)  # type: ignore
