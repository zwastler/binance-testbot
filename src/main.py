import asyncio
import signal

import structlog
from adapters.binance_wss import private_wss_client, public_wss_client
from core.trader import Trader
from settings import settings

logger = structlog.get_logger(__name__)
shutdown_event = asyncio.Event()


async def close_tasks(tasks: list) -> None:
    for task in tasks:
        task.cancel()


async def main() -> None:
    structlog.contextvars.bind_contextvars(
        symbol=settings.SYMBOL, version=settings.VERSION, environment=settings.ENVIRONMENT
    )

    trader = Trader()
    queue: asyncio.Queue = asyncio.Queue()
    tasks = [
        asyncio.create_task(public_wss_client.wss_connect(queue)),
        asyncio.create_task(private_wss_client.wss_connect(queue)),
        asyncio.create_task(trader.events_processing(queue)),
        asyncio.create_task(trader.time_watcher()),  # Watcher for position hold time
    ]

    for sig in (signal.SIGTERM, signal.SIGINT):
        asyncio.get_running_loop().add_signal_handler(sig, lambda: asyncio.create_task(close_tasks(tasks)))

    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
