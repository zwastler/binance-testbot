import asyncio
import os
import signal
import sys
import time
from asyncio import Queue
from typing import Any

import msgspec
import structlog
from adapters.binance_wss import private_wss_client
from models import STATUS, Order, Position, State, Trade
from settings import settings

logger = structlog.get_logger(__name__)


class Trader:
    def __init__(self) -> None:
        self.state = State()

    def parse_message(self, message: dict[str, Any]) -> Trade | Order | None:
        if not (event_type := message.get("e", message.get("channel"))):
            return None

        match event_type:
            case "trade":
                return msgspec.convert(message, type=Trade)
            case "executionReport":
                return msgspec.convert(message, type=Order)
            case "outboundAccountPosition":
                self.update_balances(message["B"])

            case t if t.startswith("private_"):
                _, msg_type = event_type.split("_", 1)
                match msg_type:
                    case "trades_recent":
                        self.parse_recent_trades(message.get("result", {}))
                    case "order":
                        return msgspec.convert(message, type=Order)
                    case "exchangeinfo":
                        self.parse_exchange_info(message.get("result", {}))
                    case "account_status":
                        self.parse_and_update_balances(message.get("result", {}))

    def parse_recent_trades(self, data: dict[str, Any]) -> None:
        for trade in data:
            self.state.last_price = float(trade.get("price", 0))  # type: ignore
            break

    def parse_and_update_balances(self, data: dict[str, Any]) -> None:
        balances_data = data["balances"]
        for bal in balances_data:
            asset = bal["asset"]
            free = float(bal["free"])
            locked = float(bal["locked"])
            self.state.balances.update_balance(asset, free, locked)
        self.state.balance_ready = True
        logger.info(
            f"Balances updated: "
            f"{self.state.base_asset}: {getattr(self.state.balances, self.state.base_asset).free}, "
            f"{self.state.quote_asset}: {getattr(self.state.balances, self.state.quote_asset).free}",
            channel="trader",
        )

    def update_balances(self, data: dict[str, Any]) -> None:
        for bal in data:
            asset = bal["a"]  # type: ignore
            free = float(bal["f"])  # type: ignore
            locked = float(bal["l"])  # type: ignore
            self.state.balances.update_balance(asset, free, locked)
        logger.info(
            f"Balances updated: "
            f"{self.state.base_asset}: {getattr(self.state.balances, self.state.base_asset).free}, "
            f"{self.state.quote_asset}: {getattr(self.state.balances, self.state.quote_asset).free}",
            channel="trader",
        )

    def parse_exchange_info(self, data: dict[str, Any]) -> None:
        if info_symbol := data.get("symbols", [])[0].get("symbol"):
            if settings.SYMBOL == info_symbol:
                symbol_details = data.get("symbols", [])[0]
                filters = symbol_details.get("filters", [])

                self.state.base_asset = symbol_details.get("baseAsset")
                self.state.quote_asset = symbol_details.get("quoteAsset")

                if not symbol_details.get("status") == "TRADING":
                    logger.error(f"Symbol {settings.SYMBOL} is not in TRADING state", channel="trader")
                    self.exit_with_error()
                    return

                min_qtys = [f["minQty"] for f in filters if f["filterType"] == "LOT_SIZE"]
                self.state.min_qty = float(min_qtys[0]) if min_qtys else 0.0
                min_notional = [f["minNotional"] for f in filters if f["filterType"] == "NOTIONAL"]
                self.state.min_notional = float(min_notional[0]) if min_notional else 0.0

                if not self.state.min_qty or settings.POSITION_QUANTITY < self.state.min_qty:
                    logger.error(
                        f"Invalid position amount, min_qty for {settings.SYMBOL} is {self.state.min_qty}, "
                        f"but you try to trade {settings.POSITION_QUANTITY}",
                        channel="trader",
                    )
                    self.exit_with_error()
                    return

                self.state.symbols_ready = True
        logger.info("Symbols updated", channel="trader")

    async def events_processing(self, queue: Queue) -> None:
        while True:
            try:
                message = await queue.get()
                await self.check_event_messages(message)
                await self.check_state()

                if not (parsed_msg := self.parse_message(message)):
                    queue.task_done()
                    continue

                if isinstance(parsed_msg, Trade):
                    await self.process_trade(parsed_msg)
                elif isinstance(parsed_msg, Order):
                    await self.process_order(parsed_msg)

                match self.state.status:
                    case STATUS.IN_POSITION:
                        await self.check_position_actions()
                    case STATUS.READY:
                        await self.create_new_position()

                queue.task_done()

            except asyncio.CancelledError:
                await logger.ainfo("Task was cancelled: msg processing", channel="trader")
                break

    async def check_event_messages(self, message: dict[str, Any]) -> None:
        if not message.get("channel"):
            return

        if message.get("channel") == "user_stream" and message.get("event") == "connected":
            self.state.stream_ready = True
            await logger.adebug("User stream connected", channel="trader")

    async def process_trade(self, trade: Trade) -> None:
        self.state.last_price = float(trade.price)

    async def check_state(self) -> None:
        if self.state.last_price and self.state.status == STATUS.INITIAL:
            if all((self.state.stream_ready, self.state.balance_ready, self.state.symbols_ready)):
                self.state.status = STATUS.READY
                await logger.ainfo("TestBot is ready for trading..", channel="trader")

    async def process_order(self, order: Order) -> None:
        if not order.symbol == settings.SYMBOL:
            """Simple check for allow run multiple bot instances on same account and different symbols"""
            return
        if order.current_order_status == "FILLED":
            if self.state.status == STATUS.ENTERING_POSITION and self.state.position:
                await logger.ainfo(
                    f"Position entered at: {order.last_executed_price}, quantity: {order.last_executed_quantity}"
                    f" {self.state.base_asset}",
                    channel="trader",
                )
                price = order.last_executed_price
                self.state.position.price = price  # type: ignore
                self.state.position.position_time = order.transaction_time
                self.state.position.sl_price = price - (price * (settings.POSITION_SL_PERCENT / 100))  # type: ignore
                self.state.position.tp_price = price + (price * (settings.POSITION_SL_PERCENT / 100))  # type: ignore
                self.state.status = STATUS.IN_POSITION
            elif self.state.status == STATUS.CLOSING_POSITION:
                pnl = self.pnl_calculation(order)
                await logger.ainfo(
                    f"Position closed at: {order.last_executed_price}, quantity: {order.last_executed_quantity} "
                    f"{self.state.base_asset}, PnL: {pnl}",
                    channel="trader",
                    pnl=pnl,
                    total_trades=self.state.total_tp_trades + self.state.total_sl_trades,
                    total_pnl=self.state.total_pnl,
                )
                self.state.status = STATUS.SLEEPING
                self.state.sleeping_at = order.transaction_time + settings.POSITION_SLEEP_TIME * 1000
                self.state.position = None
                await logger.ainfo(f"Sleeping for {settings.POSITION_SLEEP_TIME} sec", channel="trader")
            else:
                await logger.aerror(
                    f"Unexpected filled order: {order.current_order_status}, state: {self.state.status}"
                    f"order: {order}",
                    channel="trader",
                )

    def pnl_calculation(self, order: Order) -> float:
        transaction_value = order.last_executed_price * order.quantity  # type: ignore
        position_value = self.state.position.price * self.state.position.amount  # type: ignore

        if order.commission_asset == self.state.base_asset:
            commission_value = order.commission_amount * order.last_executed_price  # type: ignore
        else:
            commission_value = order.commission_amount
        pnl = transaction_value - position_value - commission_value  # type: ignore
        self.state.total_pnl += pnl

        if pnl > 0:
            self.state.total_tp_trades += 1
        else:
            self.state.total_sl_trades += 1
        return round(pnl, 6)

    async def check_position_actions(self) -> None:
        """Check if position should be closed due to TP or SL limits"""

        if self.state.status == STATUS.IN_POSITION and self.state.position:
            if self.state.last_price >= self.state.position.tp_price:
                self.state.status = STATUS.CLOSING_POSITION
                await logger.ainfo(f"Closing position (take profit): {self.state.last_price}", channel="trader")
                await private_wss_client.order_place(side="SELL", quantity=self.state.position.amount)

            elif self.state.last_price <= self.state.position.sl_price:
                self.state.status = STATUS.CLOSING_POSITION
                await logger.ainfo(f"Closing position (stop loss): {self.state.last_price}", channel="trader")
                await private_wss_client.order_place(side="SELL", quantity=self.state.position.amount)

    async def create_new_position(self) -> None:
        if not self.state.status == STATUS.READY:
            return

        await self.check_position_limitations()

        await logger.ainfo(f"Entering new position: {self.state.last_price}", channel="trader")
        self.state.status = STATUS.ENTERING_POSITION
        self.state.position = Position(amount=settings.POSITION_QUANTITY)
        await private_wss_client.order_place(side="BUY", quantity=settings.POSITION_QUANTITY)

    async def check_position_limitations(self) -> None:
        quote_balance = getattr(self.state.balances, self.state.quote_asset).free
        requested_balance = settings.POSITION_QUANTITY * self.state.last_price
        if quote_balance < requested_balance:
            await logger.aerror(
                f"Not enough balance to enter new position. You balance: {quote_balance}, requested: "
                f"{requested_balance}",
                channel="trader",
            )
            self.exit_with_error()
            return

        if requested_balance < self.state.min_notional:
            await logger.aerror(
                f"Failed to create new position. "
                f"Requested value for order is {requested_balance} {self.state.quote_asset}, "
                f"minimal is {self.state.min_notional}",
                channel="trader",
            )
            self.exit_with_error()
            return

    async def time_watcher(self) -> None:
        """Check for position exists, and wait for POSITION_HOLD_TIME, after time elapsed, close position"""
        while True:
            timestamp = int(time.time() * 1000)
            try:
                if (
                    self.state.status == STATUS.SLEEPING
                    and self.state.sleeping_at
                    and timestamp >= self.state.sleeping_at
                ):
                    await logger.ainfo("sleeping complete, ready for entering new position.")
                    self.state.status = STATUS.READY
                    self.state.sleeping_at = 0

                elif self.state.status == STATUS.READY:  # force create new position without waiting new trades
                    await self.create_new_position()

                if not self.state.status == STATUS.IN_POSITION or not self.state.position:
                    await asyncio.sleep(1)
                    continue

                if timestamp >= self.state.position.position_time + settings.POSITION_HOLD_TIME * 1000:
                    """Close position if hold time exceeded"""
                    self.state.status = STATUS.CLOSING_POSITION
                    await logger.ainfo(
                        f"Closing position (hold time exceeded): {self.state.last_price}", channel="trader"
                    )
                    await private_wss_client.order_place(side="SELL", quantity=self.state.position.amount)

                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                await logger.ainfo("Task was cancelled: time watcher", channel="trader")
                break

    @staticmethod
    def exit_with_error() -> None:
        os.kill(os.getpid(), signal.SIGTERM)
        sys.exit(1)
