import asyncio
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_trader_class():
    with patch('core.trader.Trader', autospec=True) as mock_trader_class:
        mock_trader_class_instance = mock_trader_class.return_value
        mock_trader_class_instance.events_processing.return_value = asyncio.Future()
        mock_trader_class_instance.time_watcher.return_value = asyncio.Future()
        yield mock_trader_class_instance


@pytest.fixture
def mock_public_wss_client():
    with patch('adapters.binance_wss.public_wss_client.wss_connect', new_callable=AsyncMock) as mock_wss:
        yield mock_wss


@pytest.fixture
def mock_private_wss_client():
    with patch('adapters.binance_wss.private_wss_client.wss_connect', new_callable=AsyncMock) as mock_wss:
        yield mock_wss


@pytest.mark.asyncio
async def test_main_creates_tasks(mock_public_wss_client, mock_private_wss_client, mock_trader_class):
    with patch('asyncio.Queue') as mock_queue_class:
        mock_queue = mock_queue_class.return_value

        from main import main

        asyncio.create_task(main())
        await asyncio.sleep(0.01)

        mock_public_wss_client.assert_called_with(mock_queue)
        mock_private_wss_client.assert_called_with(mock_queue)
        mock_trader_class.events_processing.assert_called_with(mock_queue)
        mock_trader_class.time_watcher.assert_called_with()
