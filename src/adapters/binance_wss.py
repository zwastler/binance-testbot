import asyncio
import base64
import time
from typing import Any
from urllib.parse import urlencode

import structlog
from aiohttp import ClientSession, ClientWebSocketResponse, WSMsgType, client_exceptions
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from msgspec import json

from settings import settings

logger = structlog.get_logger(__name__)
decoder = json.Decoder()
encoder = json.Encoder()


class SingletonMeta(type):
    _instances: dict = {}

    def __call__(cls, *args: list[Any], **kwargs: dict[str, Any]) -> Any:
        if cls not in cls._instances:
            instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class BinanceWSS(metaclass=SingletonMeta):
    wss_client: ClientWebSocketResponse = None
    queue: asyncio.Queue = None  # type: ignore

    def __init__(self, symbol: str, channel: str, url: str) -> None:
        self.symbol = symbol
        self.wss_url = url
        self.channel = channel

    def create_ws_message(self, method: str) -> dict[str, Any]:
        timestamp = int(time.time() * 1000)
        payload = {
            "id": f"{method}_{timestamp}".replace(".", "_").lower(),
            "method": method,
            "params": {},
        }
        match method:
            case "SUBSCRIBE":
                payload.update(
                    {
                        "id": f"subscribe_{self.symbol}_{timestamp}".lower(),
                        "params": [f"{self.symbol.lower()}@trade"],
                    }
                )
        return payload

    async def after_connect(self) -> None:
        if self.wss_client:
            await self.send_json(self.create_ws_message("SUBSCRIBE"))

    async def after_cancel(self) -> None: ...

    async def send_json(self, message: dict[str, Any]) -> None:
        await logger.adebug(message, channel=self.channel)
        if self.wss_client:
            try:
                await self.wss_client.send_str(encoder.encode(message).decode(), compress=False)
            except client_exceptions.ClientError:
                await logger.awarning("Failed to send message", message=message, channel=self.channel, exc_info=True)
        else:
            await logger.awarning("WebSocket connection not established", channel=self.channel)

    async def wss_connect(self, queue: asyncio.Queue) -> None:
        self.queue = queue
        while True:
            try:
                async with ClientSession() as session:
                    await logger.ainfo(f"Connecting to {self.channel} wss channel", channel=self.channel)
                    async with session.ws_connect(self.wss_url, autoclose=False) as wss:
                        self.wss_client = wss
                        await self.after_connect()
                        await self.receive_messages(queue)
            except asyncio.CancelledError:
                logger.info(f"Task was cancelled: {self.__class__.__name__}")
                if self.wss_client:
                    await self.wss_client.close()
                await self.after_cancel()
                break
            except Exception as err:
                await logger.awarning(
                    "WebSocket connection failed, attempting to reconnect...", channel=self.channel, exception=err
                )
                await asyncio.sleep(0.25)  # wait before attempting to reconnect

    async def receive_messages(self, queue: asyncio.Queue) -> None:
        while True:
            if not self.wss_client:
                await logger.awarning("WebSocket connection not established", channel=self.channel)
                await asyncio.sleep(0.25)
                continue
            async for msg in self.wss_client:  # type: ignore
                if msg.type == WSMsgType.TEXT:
                    message = decoder.decode(msg.data)
                    try:
                        await self.process_message(message, queue)
                    except Exception:
                        await logger.awarning(
                            "Failed process message", message=message, channel=self.channel, exc_info=True
                        )

                elif msg.type in (WSMsgType.ERROR, WSMsgType.CLOSED):
                    await logger.awarning("WebSocket closed", channel=self.channel)
                    break
                else:
                    await logger.awarning(f"Unknown MsgType: {msg.type}", channel=self.channel)

    async def process_message(self, message: dict[str, Any], queue: asyncio.Queue) -> None:
        message_id, message_ts = self.parse_message_metadata(message)
        message["channel"] = self.channel

        if message.get("e", ""):
            queue.put_nowait(message)

        if latency := self.calc_latency(message_ts):
            await logger.adebug(message, channel=self.channel, latency=latency)
        else:
            await logger.adebug(message, channel=self.channel)

    def parse_message_metadata(self, message: dict[str, Any]) -> tuple[str, int]:
        if "_" in message.get("id", ""):
            message_id, message_ts = message.get("id", "").rsplit("_", 1)
        else:
            message_id, message_ts = "public", message.get("id", 0)
        if message.get("e") and message.get("E"):
            message_ts = int(message["E"])
        return message_id, int(message_ts)

    def calc_latency(self, message_ts: int | str) -> int:
        if isinstance(message_ts, str):
            message_ts = int(message_ts) if message_ts.isdigit() else 0
        elif not isinstance(message_ts, int):
            return 0
        return int(time.time() * 1000) - message_ts


class BinancePrivateWSS(BinanceWSS):
    extra_tasks: list[asyncio.Task] = []

    def __init__(self, symbol: str, channel: str, url: str, api_key: str, private_key_base64: str) -> None:
        super().__init__(symbol, channel, url)
        self.listen_key = None
        if not hasattr(self, "api_initialized"):
            self.api_key = api_key
            self.private_key = self.load_private_key(private_key_base64)
            self.api_initialized = True

    @staticmethod
    def load_private_key(private_key_base64: str) -> Any:
        try:
            private_key = load_pem_private_key(data=base64.b64decode(private_key_base64), password=None)
            logger.debug("Private key successfully loaded")
            return private_key
        except Exception as err:
            logger.error("failed to load private key", exc_info=True)
            raise Exception from err

    def generate_signature(self, data: str) -> str:
        return base64.b64encode(self.private_key.sign(data.encode())).decode()

    def create_ws_message(self, method: str) -> dict[str, Any]:
        timestamp = int(time.time() * 1000)
        payload = {
            "id": f"{method}_{timestamp}".replace(".", "_").lower(),
            "method": method,
            "params": {"apiKey": self.api_key, "timestamp": timestamp},
        }

        match method:
            case "session.logon" | "account.status":
                pre_signature = {"apiKey": self.api_key, "timestamp": timestamp}
                payload["params"]["signature"] = self.generate_signature(urlencode(pre_signature))  # type: ignore
            case "exchangeInfo":
                payload["params"] = {"symbols": [self.symbol.upper()]}  # type: ignore
            case "trades.recent":
                payload["params"] = {"symbol": self.symbol.upper(), "limit": 1}  # type: ignore
            case "userDataStream.start":
                payload["params"] = {"apiKey": self.api_key}  # type: ignore
            case "userDataStream.ping":
                payload["params"] = {"apiKey": self.api_key, "listenKey": self.listen_key}

        return payload

    async def user_data_stream_connect(self) -> None:
        if self.queue and self.listen_key:
            await UserStreamWSS(
                symbol=self.symbol,
                channel="user_stream",
                url="wss://testnet.binance.vision/ws",
                listen_key=self.listen_key,
            ).wss_connect(self.queue)

    async def user_data_stream_ping_worker(self) -> None:
        while True:
            await asyncio.sleep(60 * 30)  # send ping every 30 minutes
            await logger.ainfo("Sending UserStream listenKey update.", channel=self.channel)
            await self.send_json(self.create_ws_message("userDataStream.ping"))  # type: ignore

    async def after_cancel(self) -> None:
        if self.extra_tasks:
            for task in self.extra_tasks:
                task.cancel()

    async def after_connect(self) -> None:
        if self.wss_client:
            for method in (
                "session.logon",
                "trades.recent",
                "exchangeInfo",
                "account.status",
                "userDataStream.start",
            ):
                await self.send_json(self.create_ws_message(method))
        else:
            await logger.awarning("WebSocket connection not established", channel=self.channel)

    async def process_message(self, message: dict[str, Any], queue: asyncio.Queue) -> None:
        await super().process_message(message, queue)

        message_id, message_ts = message.get("id", "").rsplit("_", 1)
        latency = int(time.time() * 1000) - int(message_ts) if message_ts.isdigit() else -1

        match message_id:
            case "session_logon":
                await logger.ainfo(f"Auth Done ({message_id}) for {latency}ms", channel=self.channel)
                self.auth_complete = True
            case "account_status" | "exchangeinfo" | "trades_recent":
                queue.put_nowait({**message, **{"channel": f"{self.channel}_{message_id}"}})
            case "userdatastream_start":
                if listen_key := message.get("result", {}).get("listenKey"):
                    self.listen_key = listen_key
                    self.extra_tasks = [
                        asyncio.create_task(self.user_data_stream_connect()),
                        asyncio.create_task(self.user_data_stream_ping_worker()),
                    ]

    async def order_place(self, side: str, quantity: float) -> None:
        if side not in ("BUY", "SELL"):
            await logger.awarning(f"Invalid side: {side}", channel=self.channel)
            return

        if not self.wss_client or not self.auth_complete:
            await logger.awarning("WebSocket connection not established or not authenticated", channel=self.channel)
            return
        await self.send_json(
            {
                "id": f"{side}_market_{int(time.time() * 1000)}".lower(),
                "method": "order.place",
                "params": {
                    "symbol": self.symbol.upper(),
                    "quantity": f"{quantity:.9f}".rstrip("0") + "0",
                    "side": side,
                    "type": "MARKET",
                    "timestamp": int(time.time() * 1000),
                },
            }
        )


class UserStreamWSS(BinanceWSS):
    def __init__(self, symbol: str, channel: str, url: str, listen_key: str) -> None:
        super().__init__(symbol, channel, url)
        self.wss_url = f"{url}/{listen_key}"

    async def after_connect(self) -> None:
        self.queue.put_nowait({"channel": self.channel, "event": "connected"})  # type: ignore
        pass

    async def process_message(self, message: dict[str, Any], queue: asyncio.Queue) -> None:
        await super().process_message(message, queue)
        await logger.adebug(message, channel=self.channel)


public_wss_client = BinanceWSS(symbol=settings.SYMBOL, channel="public", url="wss://testnet.binance.vision/ws")

private_wss_client = BinancePrivateWSS(
    symbol=settings.SYMBOL,
    channel="private",
    url="wss://testnet.binance.vision/ws-api/v3",
    api_key=settings.API_KEY,
    private_key_base64=settings.PRIVATE_KEY_BASE64,
)
