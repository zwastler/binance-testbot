from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from adapters.binance_wss import public_wss_client, private_wss_client
from freezegun import freeze_time


@pytest.fixture
def mock_private_order_place():
    with patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock) as mock_order_place:
        yield mock_order_place @ pytest.fixture


@pytest.fixture
def mock_private_wss_client():
    wss_client = MagicMock()
    async_methods = ['send_json']
    for method_name in async_methods:
        setattr(wss_client, method_name, AsyncMock())
    with patch('adapters.binance_wss.private_wss_client.wss_client', new_callable=lambda: wss_client):
        yield wss_client


@pytest.fixture
def mock_async_logger():
    logger = MagicMock()
    async_methods = ['info', 'warning', 'error', 'debug', 'ainfo', 'asuccess']
    for method_name in async_methods:
        setattr(logger, method_name, AsyncMock())

    with patch('adapters.binance_wss.logger', new_callable=lambda: logger):
        yield logger


@freeze_time("2024-04-22T16:47:01Z")
def test_create_ws_message():
    symbol = "BTCUSD"
    message = public_wss_client.create_ws_message("SUBSCRIBE")
    assert message == {"method": "SUBSCRIBE", "params": [f"{symbol.lower()}@trade"],
                       "id": f"subscribe_{symbol.lower()}_1713804421000", }


@freeze_time("2024-04-22T16:47:01Z")
def test_create_ws_message_logon():
    symbol = "BTCUSD"
    message = private_wss_client.create_ws_message("session.logon")
    assert message['id'] == "session_logon_1713804421000"
    assert message['method'] == "session.logon"
    assert message['params']['timestamp'] == 1713804421000
    assert message['params']['apiKey'] == 'test_key'
    assert message['params']['signature']


@freeze_time("2024-04-22T16:47:01Z")
def test_create_ws_message_exchange_info():
    symbol = "BTCUSD"
    method = "exchangeInfo"
    message = private_wss_client.create_ws_message(method)
    assert message['id'] == f"{method.replace('.', '_').lower()}_1713804421000"
    assert message['method'] == method
    assert message['params']['symbols'] == [symbol]


@freeze_time("2024-04-22T16:47:01Z")
def test_create_ws_message_userdatastream_start():
    symbol = "BTCUSD"
    method = "userDataStream.start"
    message = private_wss_client.create_ws_message(method)
    assert message['id'] == f"{method.replace('.', '_').lower()}_1713804421000"
    assert message['method'] == method
    assert message['params']['apiKey'] == 'test_key'


@freeze_time("2024-04-22T16:47:01Z")
def test_create_ws_message_userdatastream_ping():
    symbol = "BTCUSD"
    method = "userDataStream.ping"
    private_wss_client.listen_key = 'test_listenkey'
    message = private_wss_client.create_ws_message(method)

    assert message['id'] == f"{method.replace('.', '_').lower()}_1713804421000"
    assert message['method'] == method
    assert message['params']['apiKey'] == 'test_key'
    assert message['params']['listenKey'] == 'test_listenkey'
