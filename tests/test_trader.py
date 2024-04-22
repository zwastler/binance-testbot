import asyncio

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.trader import Trader
from models import Trade, Order, STATUS, Position
from settings import settings


@pytest.fixture
def mock_async_logger():
    logger = MagicMock()
    async_methods = ['info', 'warning', 'error', 'debug', 'ainfo', 'asuccess']
    for method_name in async_methods:
        setattr(logger, method_name, AsyncMock())

    with patch('core.trader.logger', new_callable=lambda: logger):
        yield logger


@pytest.fixture
def test_execution_report_json():
    return {'e': 'executionReport', 'E': 1713797483678, 's': 'BTCUSDT', 'c': 'LdXdY6Kopqz8rTdGfVREYG', 'S': 'BUY',
            'o': 'MARKET', 'f': 'GTC', 'q': '0.00100000', 'p': '0.00000000', 'P': '0.00000000', 'F': '0.00000000',
            'g': -1, 'C': '', 'x': 'TRADE', 'X': 'FILLED', 'r': 'NONE', 'i': 4245657, 'l': '0.00100000',
            'z': '0.00100000', 'L': '66250.98000000', 'n': '0.00000000', 'N': 'BTC', 'T': 1713797483678, 't': 1414697,
            'I': 9896267, 'w': False, 'm': False, 'M': True, 'O': 1713797483678, 'Z': '66.25098000', 'Y': '66.25098000',
            'Q': '0.00000000', 'W': 1713797483678, 'V': 'EXPIRE_MAKER', 'channel': 'user_stream'}


@pytest.fixture
def test_trade_json():
    return {'e': 'trade', 'E': 1713797829314, 's': 'BTCUSDT', 't': 1415300, 'p': '66197.57000000', 'q': '0.00100000',
            'b': 4247688, 'a': 4247669, 'T': 1713797829314, 'm': False, 'M': True, 'channel': 'public'}


@pytest.fixture
def test_order_json():
    return {'id': 'sell_market_1713797911505', 'status': 200,
            'result': {'symbol': 'BTCUSDT', 'orderId': 4248177, 'orderListId': -1,
                       'clientOrderId': 'F7WkDMY0Jw8a6lKyCT3tGv', 'transactTime': 1713797911508, 'price': '0.00000000',
                       'origQty': '0.00100000', 'executedQty': '0.00100000', 'cummulativeQuoteQty': '66.11912000',
                       'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'SELL',
                       'workingTime': 1713797911508, 'fills': [
                    {'price': '66119.12000000', 'qty': '0.00100000', 'commission': '0.00000000',
                     'commissionAsset': 'USDT', 'tradeId': 1415420}], 'selfTradePreventionMode': 'EXPIRE_MAKER'},
            'rateLimits': [
                {'rateLimitType': 'ORDERS', 'interval': 'SECOND', 'intervalNum': 10, 'limit': 50, 'count': 1},
                {'rateLimitType': 'ORDERS', 'interval': 'DAY', 'intervalNum': 1, 'limit': 160000, 'count': 898},
                {'rateLimitType': 'REQUEST_WEIGHT', 'interval': 'MINUTE', 'intervalNum': 1, 'limit': 6000, 'count': 1}]}


@pytest.fixture
def trader():
    return Trader()


@pytest.fixture
def filled_queue(test_trade_json, test_execution_report_json):
    queue = asyncio.Queue()
    queue.put_nowait(test_trade_json)
    queue.put_nowait(test_execution_report_json)
    return queue


def test_parse_message_trade(trader, test_trade_json):
    parsed_message = trader.parse_message(test_trade_json)
    assert isinstance(parsed_message, Trade)


#
def test_parse_message_order(trader, test_execution_report_json):
    parsed_message = trader.parse_message(test_execution_report_json)
    assert isinstance(parsed_message, Order)


@pytest.mark.parametrize(
    "message,expected",
    [
        ({"e": "unknownType"}, None),
        ({"random": "message"}, None),
    ],
)
def test_parse_message_unknown(trader, message, expected):
    result = trader.parse_message(message)
    assert result == expected


@pytest.mark.asyncio
async def test_process_trade(trader, test_trade_json):
    parsed_trade = trader.parse_message(test_trade_json)
    assert isinstance(parsed_trade, Trade)
    await trader.process_trade(parsed_trade)

    # Verifying that state.last_price is updated
    assert trader.state.last_price == float(parsed_trade.price)


@pytest.fixture
def account_position_message():
    return {'e': 'outboundAccountPosition'}


@pytest.fixture
def event_message_connected():
    return {'channel': 'user_stream', 'event': 'connected'}


@pytest.mark.asyncio
async def test_parse_message_account_position(trader, account_position_message):
    assert trader.parse_message(account_position_message) is None


@pytest.mark.asyncio
@patch('core.trader.Trader.process_trade', new_callable=AsyncMock)
@patch('core.trader.Trader.process_order', new_callable=AsyncMock)
@patch('core.trader.Trader.check_position_actions', new_callable=AsyncMock)
@patch('core.trader.Trader.create_new_position', new_callable=AsyncMock)
@patch('core.trader.Trader.check_event_messages', new_callable=AsyncMock)
async def test_events_processing(mock_check_event_messages, mock_create_new_position,
                                 mock_check_position_actions, mock_process_order, mock_process_trade, trader,
                                 filled_queue, mock_async_logger):
    task = asyncio.create_task(trader.events_processing(filled_queue))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    mock_process_trade.assert_awaited_once()
    mock_process_order.assert_awaited_once()
    mock_check_position_actions.assert_not_called()
    mock_create_new_position.assert_not_called()
    assert filled_queue.empty()


@pytest.mark.asyncio
async def test_check_event_messages_skip(trader):
    await trader.check_event_messages({})
    assert not trader.state.stream_ready


@pytest.mark.asyncio
async def test_check_event_messages(trader, event_message_connected):
    await trader.check_event_messages(event_message_connected)
    assert trader.state.stream_ready


@pytest.mark.asyncio
async def test_process_order_entering_position(trader, test_execution_report_json, mock_async_logger):
    trader.state.status = STATUS.ENTERING_POSITION
    trader.state.position = Position(price=0, amount=0, position_time=0, sl_price=0, tp_price=0)
    order = trader.parse_message(test_execution_report_json)
    await trader.process_order(order)
    assert trader.state.status == STATUS.IN_POSITION
    mock_async_logger.ainfo.assert_awaited_once_with(
        f"Position entered: {order.last_executed_price}", channel="trader"
    )


@pytest.mark.asyncio
async def test_process_order_closing_position_and_sleep(trader, test_execution_report_json, mock_async_logger):
    trader.state.status = STATUS.CLOSING_POSITION
    trader.state.position = Position(price=1000, amount=1, position_time=1713797483678, sl_price=950, tp_price=1050)
    order = trader.parse_message(test_execution_report_json)
    pnl = order.last_executed_price - trader.state.position.price  # type: ignore
    await trader.process_order(order)
    assert trader.state.status == STATUS.SLEEPING
    assert trader.state.sleeping_at == order.transaction_time + settings.POSITION_SLEEP_TIME * 1000
    mock_async_logger.ainfo.assert_awaited_once_with(
        f"Position closed: {order.last_executed_price} PnL {pnl}, sleeping for {settings.POSITION_SLEEP_TIME}s",
        channel="trader"
    )


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_check_position_actions_take_profit(mock_order_place, trader, mock_async_logger):
    trader.state.status = STATUS.IN_POSITION
    trader.state.position = Position(price=1000, amount=1, position_time=1713797483678, sl_price=950, tp_price=1050)
    trader.state.last_price = 1060
    await trader.check_position_actions()
    mock_order_place.assert_awaited_once_with(side="SELL", quantity=1)
    mock_async_logger.ainfo.assert_awaited_once_with(f"Closing position (take profit): {trader.state.last_price}",
                                                     channel="trader")


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_check_state(mock_order_place, mock_async_logger, trader):
    trader.state.stream_ready = True
    trader.state.status = STATUS.INITIAL
    trader.state.last_price = 940
    await trader.check_state()
    assert trader.state.status == STATUS.READY


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_check_position_actions_stop_loss(mock_order_place, mock_async_logger, trader):
    trader.state.status = STATUS.IN_POSITION
    trader.state.position = Position(price=1000, amount=1, position_time=1713797483678, sl_price=950, tp_price=1050)
    trader.state.last_price = 940
    await trader.check_position_actions()
    mock_order_place.assert_awaited_once_with(side="SELL", quantity=1)
    mock_async_logger.ainfo.assert_awaited_once_with(f"Closing position (stop loss): {trader.state.last_price}",
                                                     channel="trader")


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_create_new_position_not_ready(mock_order_place, trader):
    trader.state.status = STATUS.SLEEPING
    await trader.create_new_position()
    mock_order_place.assert_not_awaited()


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_create_new_position_ready(mock_order_place, mock_async_logger, trader):
    trader.state.status = STATUS.READY
    trader.state.last_price = 1000
    await trader.create_new_position()
    mock_order_place.assert_awaited_once_with(side="BUY", quantity=settings.POSITION_QUANTITY)
    mock_async_logger.ainfo.assert_awaited_once_with(f"Entering new position: {trader.state.last_price}",
                                                     channel="trader")
