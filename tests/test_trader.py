import asyncio
import os
import signal

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from core.trader import Trader
from models import Trade, Order, STATUS, Position
from settings import settings
import logging

logging.getLogger('asyncio').setLevel(logging.WARNING)


@pytest.fixture
def mock_async_logger():
    logger = MagicMock()
    async_methods = [
        'debug', 'info', 'warning', 'error',
        'adebug', 'ainfo', 'awarning', 'aerror',
    ]
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
def test_exchangeinfo_json():
    return {'id': 'exchangeinfo_1713887583205', 'status': 200, "channel": "private_exchangeinfo",
            'result': {'timezone': 'UTC', 'serverTime': 1713887583500, 'rateLimits': [
                {'rateLimitType': 'REQUEST_WEIGHT', 'interval': 'MINUTE', 'intervalNum': 1, 'limit': 6000},
                {'rateLimitType': 'ORDERS', 'interval': 'SECOND', 'intervalNum': 10, 'limit': 50},
                {'rateLimitType': 'ORDERS', 'interval': 'DAY', 'intervalNum': 1, 'limit': 160000},
                {'rateLimitType': 'CONNECTIONS', 'interval': 'MINUTE', 'intervalNum': 5, 'limit': 300}],
                       'exchangeFilters': [], 'symbols': [
                    {'symbol': 'BTCUSDT', 'status': 'TRADING', 'baseAsset': 'BTC', 'baseAssetPrecision': 8,
                     'quoteAsset': 'USDT', 'quotePrecision': 8, 'quoteAssetPrecision': 8, 'baseCommissionPrecision': 8,
                     'quoteCommissionPrecision': 8,
                     'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
                     'icebergAllowed': True, 'ocoAllowed': True, 'otoAllowed': False,
                     'quoteOrderQtyMarketAllowed': True, 'allowTrailingStop': True, 'cancelReplaceAllowed': True,
                     'isSpotTradingAllowed': True, 'isMarginTradingAllowed': False, 'filters': [
                        {'filterType': 'PRICE_FILTER', 'minPrice': '0.01000000', 'maxPrice': '1000000.00000000',
                         'tickSize': '0.01000000'},
                        {'filterType': 'LOT_SIZE', 'minQty': '0.00001000', 'maxQty': '9000.00000000',
                         'stepSize': '0.00001000'}, {'filterType': 'ICEBERG_PARTS', 'limit': 10},
                        {'filterType': 'MARKET_LOT_SIZE', 'minQty': '0.00000000', 'maxQty': '96.17023316',
                         'stepSize': '0.00000000'},
                        {'filterType': 'TRAILING_DELTA', 'minTrailingAboveDelta': 10, 'maxTrailingAboveDelta': 2000,
                         'minTrailingBelowDelta': 10, 'maxTrailingBelowDelta': 2000},
                        {'filterType': 'PERCENT_PRICE_BY_SIDE', 'bidMultiplierUp': '5', 'bidMultiplierDown': '0.2',
                         'askMultiplierUp': '5', 'askMultiplierDown': '0.2', 'avgPriceMins': 5},
                        {'filterType': 'NOTIONAL', 'minNotional': '5.00000000', 'applyMinToMarket': True,
                         'maxNotional': '9000000.00000000', 'applyMaxToMarket': False, 'avgPriceMins': 5},
                        {'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200},
                        {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}], 'permissions': [],
                     'permissionSets': [['SPOT']], 'defaultSelfTradePreventionMode': 'EXPIRE_MAKER',
                     'allowedSelfTradePreventionModes': ['NONE', 'EXPIRE_TAKER', 'EXPIRE_MAKER', 'EXPIRE_BOTH']}]},
            'rateLimits': [{'rateLimitType': 'REQUEST_WEIGHT', 'interval': 'MINUTE', 'intervalNum': 1, 'limit': 6000,
                            'count': 24}]}


@pytest.fixture
def test_balances_json():
    return {'id': 'account_status_1713887583205', 'status': 200,  # "channel": "private_account_status",
            'result': {'makerCommission': 0, 'takerCommission': 0, 'buyerCommission': 0, 'sellerCommission': 0,
                       'commissionRates': {'maker': '0.00000000', 'taker': '0.00000000', 'buyer': '0.00000000',
                                           'seller': '0.00000000'}, 'canTrade': True, 'canWithdraw': True,
                       'canDeposit': True, 'brokered': False, 'requireSelfTradePrevention': False, 'preventSor': False,
                       'updateTime': 1713887581213, 'accountType': 'SPOT',
                       'balances': [{'asset': 'BTC', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'USDT', 'free': '10000.00000000', 'locked': '0.00000000'}],
                       'permissions': ['SPOT'], 'uid': 1713356096419702488}, 'rateLimits': [
            {'rateLimitType': 'REQUEST_WEIGHT', 'interval': 'MINUTE', 'intervalNum': 1, 'limit': 6000, 'count': 46}]}


@pytest.fixture
def test_outbound_position_json():
    return {'e': 'outboundAccountPosition', 'E': 1713930281749, 'u': 1713930281749,
            'B': [{'a': 'BTC', 'f': '1.00010000', 'l': '0.00000000'},
                  {'a': 'USDT', 'f': '9910.22740230', 'l': '0.00000000'}], 'channel': 'user_stream'}


@pytest.fixture
def test_trader(test_balances_json, test_exchangeinfo_json, mock_async_logger):
    test_trader = Trader()
    test_trader.parse_exchange_info(test_exchangeinfo_json["result"])
    test_trader.parse_and_update_balances(test_balances_json["result"])
    test_trader.state.last_price = 10000
    return test_trader


@pytest.fixture
def filled_queue(test_trade_json, test_execution_report_json):
    queue = asyncio.Queue()
    queue.put_nowait(test_trade_json)
    queue.put_nowait(test_execution_report_json)
    return queue


def test_parse_message_trade(test_trader, test_trade_json):
    parsed_message = test_trader.parse_message(test_trade_json)
    assert isinstance(parsed_message, Trade)


#
def test_parse_message_order(test_trader, test_execution_report_json):
    parsed_message = test_trader.parse_message(test_execution_report_json)
    assert isinstance(parsed_message, Order)


@pytest.mark.parametrize(
    "message,expected",
    [
        ({"e": "unknownType"}, None),
        ({"random": "message"}, None),
    ],
)
def test_parse_message_unknown(test_trader, message, expected):
    result = test_trader.parse_message(message)
    assert result == expected


def test_parse_message_exchange_info(test_exchangeinfo_json, mock_async_logger):
    test_trader = Trader()
    test_trader.parse_message(test_exchangeinfo_json)
    assert test_trader.state.base_asset
    assert test_trader.state.quote_asset


def test_parse_message_exchange_info_error_trading(test_exchangeinfo_json, monkeypatch, mock_async_logger):
    exit_mock = Mock(side_effect=SystemExit(1))
    kill_mock = Mock()
    monkeypatch.setattr('sys.exit', exit_mock)
    monkeypatch.setattr('os.kill', kill_mock)

    test_trader = Trader()
    test_exchangeinfo_json["result"]["symbols"][0]["status"] = "NOT_TRADING"
    with pytest.raises(SystemExit):
        test_trader.parse_message(test_exchangeinfo_json)
    assert test_trader.state.base_asset
    assert test_trader.state.quote_asset


def test_parse_message_parse_balance(test_balances_json, mock_async_logger):
    test_trader = Trader()
    test_trader.parse_message(test_balances_json)
    assert test_trader.state.balances.USDT.free > 0
    assert test_trader.state.balances.BTC.free > 0


def test_parse_message_update_balance(test_exchangeinfo_json, test_outbound_position_json, mock_async_logger):
    test_trader = Trader()
    test_trader.parse_message(test_exchangeinfo_json)
    test_trader.parse_message(test_outbound_position_json)
    assert test_trader.state.balances.USDT.free > 0
    assert test_trader.state.balances.BTC.free > 0


def test_exit_with_error(monkeypatch, test_trader):
    exit_mock = Mock(side_effect=SystemExit(1))
    kill_mock = Mock()
    monkeypatch.setattr('sys.exit', exit_mock)
    monkeypatch.setattr('os.kill', kill_mock)

    with pytest.raises(SystemExit) as e:
        test_trader.exit_with_error()
    assert e.type == SystemExit
    assert e.value.code == 1
    kill_mock.assert_called_once_with(os.getpid(), signal.SIGTERM)
    exit_mock.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_process_trade(test_trader, test_trade_json):
    parsed_trade = test_trader.parse_message(test_trade_json)
    assert isinstance(parsed_trade, Trade)
    await test_trader.process_trade(parsed_trade)
    assert test_trader.state.last_price == float(parsed_trade.price)


@pytest.fixture
def event_message_connected():
    return {'channel': 'user_stream', 'event': 'connected'}


@pytest.mark.asyncio
@patch('core.trader.Trader.process_trade', new_callable=AsyncMock)
@patch('core.trader.Trader.process_order', new_callable=AsyncMock)
@patch('core.trader.Trader.check_position_actions', new_callable=AsyncMock)
@patch('core.trader.Trader.create_new_position', new_callable=AsyncMock)
@patch('core.trader.Trader.check_event_messages', new_callable=AsyncMock)
async def test_events_processing(mock_check_event_messages, mock_create_new_position,
                                 mock_check_position_actions, mock_process_order, mock_process_trade, test_trader,
                                 filled_queue, mock_async_logger):
    task = asyncio.create_task(test_trader.events_processing(filled_queue))
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
async def test_check_event_messages_skip(test_trader):
    await test_trader.check_event_messages({})
    assert not test_trader.state.stream_ready


@pytest.mark.asyncio
async def test_check_event_messages(test_trader, event_message_connected, mock_async_logger):
    await test_trader.check_event_messages(event_message_connected)
    assert test_trader.state.stream_ready


@pytest.mark.asyncio
async def test_process_order_entering_position(test_trader, test_execution_report_json, mock_async_logger):
    test_trader.state.status = STATUS.ENTERING_POSITION
    test_trader.state.position = Position(price=0, amount=0, position_time=0, sl_price=0, tp_price=0)
    order = test_trader.parse_message(test_execution_report_json)
    await test_trader.process_order(order)
    assert test_trader.state.status == STATUS.IN_POSITION
    mock_async_logger.ainfo.assert_awaited_once_with(
        f"Position entered at: {order.last_executed_price}, quantity: {order.last_executed_quantity} "
        f"{test_trader.state.base_asset}", channel="trader"
    )


@pytest.mark.asyncio
async def test_process_order_closing_position_and_sleep(test_trader, test_execution_report_json, mock_async_logger):
    test_trader.state.status = STATUS.CLOSING_POSITION
    test_trader.state.position = Position(price=1000, amount=1, position_time=1713797483678, sl_price=950,
                                          tp_price=1050)
    order = test_trader.parse_message(test_execution_report_json)
    pnl = test_trader.pnl_calculation(order)
    await test_trader.process_order(order)
    assert test_trader.state.status == STATUS.SLEEPING
    assert test_trader.state.sleeping_at == order.transaction_time + settings.POSITION_SLEEP_TIME * 1000


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_check_position_actions_take_profit(mock_order_place, test_trader, mock_async_logger):
    test_trader.state.status = STATUS.IN_POSITION
    test_trader.state.position = Position(price=1000, amount=1, position_time=1713797483678, sl_price=950,
                                          tp_price=1050)
    test_trader.state.last_price = 1060
    await test_trader.check_position_actions()
    mock_order_place.assert_awaited_once_with(side="SELL", quantity=1)
    mock_async_logger.ainfo.assert_awaited_once_with(f"Closing position (take profit): {test_trader.state.last_price}",
                                                     channel="trader")


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_check_state(mock_order_place, mock_async_logger, test_trader):
    test_trader.state.stream_ready = True
    test_trader.state.balance_ready = True
    test_trader.state.symbols_ready = True
    test_trader.state.status = STATUS.INITIAL
    test_trader.state.last_price = 940
    await test_trader.check_state()
    assert test_trader.state.status == STATUS.READY


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_check_position_actions_stop_loss(mock_order_place, mock_async_logger, test_trader):
    test_trader.state.status = STATUS.IN_POSITION
    test_trader.state.position = Position(price=1000, amount=1, position_time=1713797483678, sl_price=950,
                                          tp_price=1050)
    test_trader.state.last_price = 940
    await test_trader.check_position_actions()
    mock_order_place.assert_awaited_once_with(side="SELL", quantity=1)
    mock_async_logger.ainfo.assert_awaited_once_with(f"Closing position (stop loss): {test_trader.state.last_price}",
                                                     channel="trader")


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_create_new_position_not_ready(mock_order_place, test_trader):
    test_trader.state.status = STATUS.SLEEPING
    await test_trader.create_new_position()
    mock_order_place.assert_not_awaited()


@pytest.mark.asyncio
@patch('adapters.binance_wss.private_wss_client.order_place', new_callable=AsyncMock)
async def test_create_new_position_ready(mock_order_place, mock_async_logger, test_trader):
    test_trader.state.status = STATUS.READY
    test_trader.state.last_price = 1000
    test_trader.state.min_notional = 0.1
    await test_trader.create_new_position()
    mock_order_place.assert_awaited_once_with(side="BUY", quantity=settings.POSITION_QUANTITY)
