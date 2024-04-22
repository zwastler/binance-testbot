import asyncio
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
        self.state = State(status=STATUS.INITIAL)

    @staticmethod
    def parse_message(message: dict[str, Any]) -> Trade | Order | None:
        if not (event_type := message.get("e", message.get("channel"))):
            return None

        match event_type:
            case "trade":
                return msgspec.convert(message, type=Trade)
            case "executionReport":
                return msgspec.convert(message, type=Order)
            case "outboundAccountPosition":
                # TODO: processing of account position
                pass

            case t if t.startswith("private_"):
                _, msg_type = event_type.split("_", 1)
                match msg_type:
                    case "order":
                        return msgspec.convert(message, type=Order)
                        pass
                    case "exchangeInfo":
                        pass
                    case "account_status":
                        pass

    async def events_processing(self, queue: Queue) -> None:
        while True:
            try:
                message = await queue.get()
                await self.check_event_messages(message)

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

    async def process_trade(self, trade: Trade) -> None:
        self.state.last_price = float(trade.price)

    async def check_state(self) -> None:
        if self.state.last_price and self.state.status == STATUS.INITIAL and self.state.stream_ready:
            self.state.status = STATUS.READY
            await logger.ainfo("TestBot is ready for trading..", channel="trader")

    async def process_order(self, order: Order) -> None:
        if order.current_order_status == "FILLED":
            if self.state.status == STATUS.ENTERING_POSITION and self.state.position:
                await logger.ainfo(f"Position entered: {order.last_executed_price}", channel="trader")
                price = order.last_executed_price
                self.state.position.price = price  # type: ignore
                self.state.position.position_time = order.transaction_time
                self.state.position.sl_price = price - (price * (settings.POSITION_SL_PERCENT / 100))  # type: ignore
                self.state.position.tp_price = price + (price * (settings.POSITION_SL_PERCENT / 100))  # type: ignore
                self.state.status = STATUS.IN_POSITION
            elif self.state.status == STATUS.CLOSING_POSITION:
                # TODO: Implement PnL calculation with commissions
                pnl = order.last_executed_price - self.state.position.price  # type: ignore
                await logger.ainfo(
                    f"Position closed: {order.last_executed_price} PnL {pnl}, sleeping for "
                    f"{settings.POSITION_SLEEP_TIME}s",
                    channel="trader",
                )
                self.state.status = STATUS.SLEEPING
                self.state.sleeping_at = order.transaction_time + settings.POSITION_SLEEP_TIME * 1000
                self.state.position = None

    async def check_position_actions(self) -> None:
        """Check if position should be closed due to TP or SL limits, or open new"""

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

        await logger.ainfo(f"Entering new position: {self.state.last_price}", channel="trader")
        self.state.status = STATUS.ENTERING_POSITION
        self.state.position = Position(amount=settings.POSITION_QUANTITY)
        await private_wss_client.order_place(side="BUY", quantity=settings.POSITION_QUANTITY)

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
