import asyncio
import base64
import time
from typing import Any
from urllib.parse import urlencode

import structlog
from aiohttp import ClientSession, WSMsgType
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from msgspec.json import Decoder
from settings import settings

logger = structlog.get_logger(__name__)
decoder = Decoder()


class SingletonMeta(type):
    _instances: dict = {}

    def __call__(cls, *args: list[Any], **kwargs: dict[str, Any]) -> Any:
        if cls not in cls._instances:
            instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class BinanceWSS(metaclass=SingletonMeta):
    wss_client: ClientSession | None = None
    wss_url = "wss://testnet.binance.vision/ws"
    channel = "public"
    queue: asyncio.Queue | None = None

    def __init__(self, symbol: str) -> None:
        self.queue = None
        self.symbol = symbol

    def create_ws_message(self, method: str) -> dict[str, Any] | None:
        timestamp = int(time.time() * 1000)
        match method:
            case "SUBSCRIBE":
                return {
                    "id": f"subscribe_" f"{self.symbol}_{timestamp}".lower(),
                    "method": f"{method}",
                    "params": [f"{self.symbol.lower()}@trade"],
                }

    async def after_connect(self) -> None:
        if self.wss_client:
            await self.wss_client.send_json(self.create_ws_message("SUBSCRIBE"))

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
                await asyncio.sleep(0.25)  # wait before attempting to reconnect
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
        # TODO: Refactor this
        if "_" in message.get("id", ""):
            message_id, message_ts = message.get("id", "").rsplit("_", 1)
        else:
            message_id, message_ts = "public", message.get("id", 0)
            message["channel"] = self.channel

        if message.get("e", ""):
            queue.put_nowait(message)
            message_ts = int(message.get("E", 0)) or int(message_ts)

        if isinstance(message_ts, str):
            latency = int(time.time() * 1000) - int(message_ts) if message_ts.isdigit() else -1
        elif isinstance(message_ts, int):
            latency = int(time.time() * 1000) - message_ts
        else:
            latency = -1

        if latency:
            await logger.adebug(message, channel=self.channel, latency=latency)
        else:
            await logger.adebug(message, channel=self.channel)


class BinancePrivateWSS(BinanceWSS):
    wss_url = "wss://testnet.binance.vision/ws-api/v3"
    channel = "private"

    def __init__(self, symbol: str, api_key: str, private_key_base64: str) -> None:
        super().__init__(symbol)
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

    def create_ws_message(self, method: str) -> dict[str, Any] | None:
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

            case "userDataStream.start":
                payload["params"] = {"apiKey": self.api_key}  # type: ignore

            case "userDataStream.ping":
                payload["params"] = {"apiKey": self.api_key, "listenKey": self.listen_key}

        return payload

    async def user_data_stream_connect(self) -> None:
        if self.queue:
            await UserStreamWSS(self.symbol, self.listen_key).wss_connect(self.queue)

    async def user_data_stream_ping_worker(self) -> None:
        while True:
            await asyncio.sleep(60 * 30)  # send ping every 30 minutes
            await logger.ainfo("Sending UserStream listenKey update.", channel=self.channel)
            await self.wss_client.send_json(self.create_ws_message("userDataStream.ping"))  # type: ignore

    async def after_connect(self) -> None:
        if self.wss_client:
            await self.wss_client.send_json(self.create_ws_message("session.logon"))
            await self.wss_client.send_json(self.create_ws_message("exchangeInfo"))
            await self.wss_client.send_json(self.create_ws_message("account.status"))
            await self.wss_client.send_json(self.create_ws_message("userDataStream.start"))
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
            case "account_status" | "exchangeInfo":
                queue.put_nowait({**message, **{"channel": f"{self.channel}_{message_id}"}})
            case "userdatastream_start":
                if listen_key := message.get("result", {}).get("listenKey"):
                    self.listen_key = listen_key
                    asyncio.create_task(self.user_data_stream_connect())
                    asyncio.create_task(self.user_data_stream_ping_worker())

    async def order_place(self, side: str, quantity: float) -> None:
        if side not in ("BUY", "SELL"):
            await logger.awarning(f"Invalid side: {side}", channel=self.channel)
            return

        if not self.wss_client or not self.auth_complete:
            await logger.awarning("WebSocket connection not established or not authenticated", channel=self.channel)
            return
        await self.wss_client.send_json(
            {
                "id": f"{side}_market_{int(time.time() * 1000)}".lower(),
                "method": "order.place",
                "params": {
                    "symbol": self.symbol.upper(),
                    "quantity": quantity,
                    "side": side,
                    "type": "MARKET",
                    "timestamp": int(time.time() * 1000),
                },
            }
        )


class UserStreamWSS(BinanceWSS):
    base_wss_url = "wss://testnet.binance.vision/ws"
    channel = "user_stream"

    def __init__(self, symbol: str, listen_key: str) -> None:
        super().__init__(symbol)
        self.wss_url = f"{self.base_wss_url}/{listen_key}"

    async def after_connect(self) -> None:
        self.queue.put_nowait({"channel": self.channel, "event": "connected"})  # type: ignore
        pass

    async def process_message(self, message: dict[str, Any], queue: asyncio.Queue) -> None:
        await super().process_message(message, queue)
        await logger.adebug(message, channel=self.channel)


public_wss_client = BinanceWSS(symbol=settings.SYMBOL)

private_wss_client = BinancePrivateWSS(
    symbol=settings.SYMBOL,
    api_key=settings.API_KEY,
    private_key_base64=settings.PRIVATE_KEY_BASE64,
)
