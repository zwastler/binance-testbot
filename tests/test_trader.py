import asyncio

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
def test_exchangeinfo():
    return {'id': 'exchangeinfo_1713887583205', 'status': 200,
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
def test_balances():
    return {'id': 'account_status_1713887583205', 'status': 200,
            'result': {'makerCommission': 0, 'takerCommission': 0, 'buyerCommission': 0, 'sellerCommission': 0,
                       'commissionRates': {'maker': '0.00000000', 'taker': '0.00000000', 'buyer': '0.00000000',
                                           'seller': '0.00000000'}, 'canTrade': True, 'canWithdraw': True,
                       'canDeposit': True, 'brokered': False, 'requireSelfTradePrevention': False, 'preventSor': False,
                       'updateTime': 1713887581213, 'accountType': 'SPOT',
                       'balances': [{'asset': 'ETH', 'free': '1.04000000', 'locked': '0.00000000'},
                                    {'asset': 'BTC', 'free': '1.13010000', 'locked': '0.00000000'},
                                    {'asset': 'LTC', 'free': '5.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BNB', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'USDT', 'free': '1246.79804230', 'locked': '0.00000000'},
                                    {'asset': 'TRX', 'free': '4131.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XRP', 'free': '818.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NEO', 'free': '25.00000000', 'locked': '0.00000000'},
                                    {'asset': 'QTUM', 'free': '99.00000000', 'locked': '0.00000000'},
                                    {'asset': 'EOS', 'free': '475.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SNT', 'free': '10735.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BNT', 'free': '584.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GAS', 'free': '77.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LRC', 'free': '1493.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ZRX', 'free': '762.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KNC', 'free': '658.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IOTA', 'free': '1673.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LINK', 'free': '28.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XVG', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MTL', 'free': '239.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ETC', 'free': '15.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ZEC', 'free': '18.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AST', 'free': '3051.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DASH', 'free': '13.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OAX', 'free': '1823.00000000', 'locked': '0.00000000'},
                                    {'asset': 'REQ', 'free': '3156.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VIB', 'free': '4119.00000000', 'locked': '0.00000000'},
                                    {'asset': 'POWR', 'free': '1316.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ENJ', 'free': '1130.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STORJ', 'free': '726.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KMD', 'free': '1055.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NULS', 'free': '580.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AMB', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BAT', 'free': '1613.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LSK', 'free': '268.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MANA', 'free': '835.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ADX', 'free': '1795.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ADA', 'free': '863.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XLM', 'free': '3870.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WAVES', 'free': '161.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ICX', 'free': '1585.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ELF', 'free': '806.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RLC', 'free': '147.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PIVX', 'free': '1044.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IOST', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STEEM', 'free': '1582.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BLZ', 'free': '1183.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ZIL', 'free': '15291.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ONT', 'free': '1445.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WAN', 'free': '1365.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SYS', 'free': '1862.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LOOM', 'free': '4851.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TUSD', 'free': '10000.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ZEN', 'free': '43.00000000', 'locked': '0.00000000'},
                                    {'asset': 'THETA', 'free': '179.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IOTX', 'free': '6608.00000000', 'locked': '0.00000000'},
                                    {'asset': 'QKC', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DATA', 'free': '6659.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SC', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DENT', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ARDR', 'free': '4004.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HOT', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VET', 'free': '11179.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DOCK', 'free': '11617.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RVN', 'free': '12535.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DCR', 'free': '19.00000000', 'locked': '0.00000000'},
                                    {'asset': 'REN', 'free': '5157.00000000', 'locked': '0.00000000'},
                                    {'asset': 'USDC', 'free': '10000.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ONG', 'free': '1234.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FET', 'free': '197.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CELR', 'free': '14912.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OMG', 'free': '522.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MATIC', 'free': '566.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ATOM', 'free': '46.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PHB', 'free': '223.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TFUEL', 'free': '4740.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ONE', 'free': '18255.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FTM', 'free': '508.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ALGO', 'free': '2206.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DOGE', 'free': '2659.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DUSK', 'free': '1104.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ANKR', 'free': '8517.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WIN', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'COS', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KEY', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FUN', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CVC', 'free': '2552.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CHZ', 'free': '3465.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BAND', 'free': '235.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XTZ', 'free': '399.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HBAR', 'free': '4895.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NKN', 'free': '2808.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STX', 'free': '160.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KAVA', 'free': '540.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ARPA', 'free': '4910.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CTXC', 'free': '1256.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BCH', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TROY', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VITE', 'free': '14452.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FTT', 'free': '309.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TRY', 'free': '18466.00000000', 'locked': '0.00000000'},
                                    {'asset': 'EUR', 'free': '460.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OGN', 'free': '2263.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WRX', 'free': '1706.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LTO', 'free': '2023.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MBL', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'COTI', 'free': '3182.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STPT', 'free': '7372.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ZAR', 'free': '18466.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SOL', 'free': '2.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IDRT', 'free': '18466.00', 'locked': '0.00'},
                                    {'asset': 'CTSI', 'free': '1839.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HIVE', 'free': '1271.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CHR', 'free': '1290.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MDT', 'free': '4810.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STMX', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DGB', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'UAH', 'free': '18466.00000000', 'locked': '0.00000000'},
                                    {'asset': 'COMP', 'free': '7.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BIDR', 'free': '158.00', 'locked': '0.00'},
                                    {'asset': 'SXP', 'free': '1107.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SNX', 'free': '129.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VTHO', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IRIS', 'free': '13153.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MKR', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RUNE', 'free': '68.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FIO', 'free': '10781.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AVA', 'free': '579.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BAL', 'free': '104.00000000', 'locked': '0.00000000'},
                                    {'asset': 'YFI', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DAI', 'free': '10000.00000000', 'locked': '0.00000000'},
                                    {'asset': 'JST', 'free': '12731.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CRV', 'free': '818.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SAND', 'free': '823.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OCEAN', 'free': '464.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NMR', 'free': '15.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DOT', 'free': '59.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LUNA', 'free': '583.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IDEX', 'free': '5780.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RSR', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PAXG', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WNXM', 'free': '7.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TRB', 'free': '5.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WBTC', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SUSHI', 'free': '324.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KSM', 'free': '12.00000000', 'locked': '0.00000000'},
                                    {'asset': 'EGLD', 'free': '9.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DIA', 'free': '813.00000000', 'locked': '0.00000000'},
                                    {'asset': 'UMA', 'free': '137.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BEL', 'free': '235.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WING', 'free': '61.00000000', 'locked': '0.00000000'},
                                    {'asset': 'UNI', 'free': '45.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OXT', 'free': '3495.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SUN', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AVAX', 'free': '10.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BAKE', 'free': '1345.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FLM', 'free': '3695.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SCRT', 'free': '855.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CAKE', 'free': '130.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ORN', 'free': '232.00000000', 'locked': '0.00000000'},
                                    {'asset': 'UTK', 'free': '4081.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XVS', 'free': '34.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ALPHA', 'free': '2865.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VIDT', 'free': '10269.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AAVE', 'free': '3.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BRL', 'free': '97.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NEAR', 'free': '72.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FIL', 'free': '59.00000000', 'locked': '0.00000000'},
                                    {'asset': 'INJ', 'free': '15.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AUDIO', 'free': '1875.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CTK', 'free': '549.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AKRO', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AXS', 'free': '51.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HARD', 'free': '2012.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SLP', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STRAX', 'free': '4498.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FOR', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'UNFI', 'free': '91.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ROSE', 'free': '4022.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XEM', 'free': '10520.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SKL', 'free': '4353.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GLM', 'free': '940.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GRT', 'free': '1534.00000000', 'locked': '0.00000000'},
                                    {'asset': 'JUV', 'free': '164.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PSG', 'free': '93.00000000', 'locked': '0.00000000'},
                                    {'asset': '1INCH', 'free': '881.00000000', 'locked': '0.00000000'},
                                    {'asset': 'REEF', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OG', 'free': '80.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ATM', 'free': '133.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ASR', 'free': '96.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CELO', 'free': '473.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RIF', 'free': '1976.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TRU', 'free': '3698.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CKB', 'free': '14226.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TWT', 'free': '413.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FIRO', 'free': '245.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LIT', 'free': '353.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SFP', 'free': '575.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FXS', 'free': '74.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DODO', 'free': '2204.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FRONT', 'free': '417.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ACM', 'free': '172.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AUCTION', 'free': '22.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PHA', 'free': '2004.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BADGER', 'free': '84.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FIS', 'free': '683.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OM', 'free': '600.00000000', 'locked': '0.00000000'},
                                    {'asset': 'POND', 'free': '16200.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DEGO', 'free': '169.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ALICE', 'free': '278.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LINA', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PERP', 'free': '336.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SUPER', 'free': '446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CFX', 'free': '1527.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TKO', 'free': '819.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PUNDIX', 'free': '624.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TLM', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BAR', 'free': '134.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FORTH', 'free': '86.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BURGER', 'free': '631.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SHIB', 'free': '18446.00', 'locked': '0.00'},
                                    {'asset': 'ICP', 'free': '31.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AR', 'free': '16.00000000', 'locked': '0.00000000'},
                                    {'asset': 'POLS', 'free': '460.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MDX', 'free': '6775.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MASK', 'free': '105.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LPT', 'free': '31.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AGIX', 'free': '486.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ATA', 'free': '2217.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GTC', 'free': '279.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ERN', 'free': '80.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KLAY', 'free': '2084.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BOND', 'free': '119.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MLN', 'free': '18.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DEXE', 'free': '32.00000000', 'locked': '0.00000000'},
                                    {'asset': 'QUICK', 'free': '6260.00000000', 'locked': '0.00000000'},
                                    {'asset': 'C98', 'free': '1198.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CLV', 'free': '4893.00000000', 'locked': '0.00000000'},
                                    {'asset': 'QNT', 'free': '4.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FLOW', 'free': '412.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MINA', 'free': '483.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RAY', 'free': '258.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FARM', 'free': '4.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ALPACA', 'free': '2080.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MBOX', 'free': '1196.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GHST', 'free': '197.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WAXP', 'free': '5827.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GNO', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PROM', 'free': '34.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XEC', 'free': '18446.00', 'locked': '0.00'},
                                    {'asset': 'DYDX', 'free': '164.00000000', 'locked': '0.00000000'},
                                    {'asset': 'USDP', 'free': '499.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GALA', 'free': '8526.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ILV', 'free': '4.00000000', 'locked': '0.00000000'},
                                    {'asset': 'YGG', 'free': '392.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DF', 'free': '8153.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FIDA', 'free': '1102.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CVP', 'free': '872.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AGLD', 'free': '334.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RAD', 'free': '191.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BETA', 'free': '5292.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RARE', 'free': '2919.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SSV', 'free': '10.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LAZIO', 'free': '139.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CHESS', 'free': '1880.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DAR', 'free': '2153.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BNX', 'free': '772.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MOVR', 'free': '27.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CITY', 'free': '127.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ENS', 'free': '24.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KP3R', 'free': '4.00000000', 'locked': '0.00000000'},
                                    {'asset': 'QI', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PORTO', 'free': '159.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VGX', 'free': '4814.00000000', 'locked': '0.00000000'},
                                    {'asset': 'JASMY', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AMP', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PYR', 'free': '78.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RNDR', 'free': '54.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ALCX', 'free': '12.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SANTOS', 'free': '69.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BICO', 'free': '668.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FLUX', 'free': '472.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VOXEL', 'free': '1565.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HIGH', 'free': '150.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CVX', 'free': '137.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PEOPLE', 'free': '14007.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OOKI', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SPELL', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'JOE', 'free': '638.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ACH', 'free': '14981.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IMX', 'free': '191.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GLMR', 'free': '1148.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LOKA', 'free': '1362.00000000', 'locked': '0.00000000'},
                                    {'asset': 'API3', 'free': '156.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BTTC', 'free': '18446.0', 'locked': '0.0'},
                                    {'asset': 'ACA', 'free': '3234.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XNO', 'free': '346.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WOO', 'free': '1227.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ALPINE', 'free': '193.00000000', 'locked': '0.00000000'},
                                    {'asset': 'T', 'free': '10504.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ASTR', 'free': '3568.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GMT', 'free': '1715.00000000', 'locked': '0.00000000'},
                                    {'asset': 'KDA', 'free': '408.00000000', 'locked': '0.00000000'},
                                    {'asset': 'APE', 'free': '302.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BSW', 'free': '4309.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BIFI', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NEXO', 'free': '365.00000000', 'locked': '0.00000000'},
                                    {'asset': 'REI', 'free': '4421.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GAL', 'free': '114.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LDO', 'free': '189.00000000', 'locked': '0.00000000'},
                                    {'asset': 'EPX', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OP', 'free': '166.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LEVER', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STG', 'free': '676.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LUNC', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GMX', 'free': '13.00000000', 'locked': '0.00000000'},
                                    {'asset': 'POLYX', 'free': '988.00000000', 'locked': '0.00000000'},
                                    {'asset': 'APT', 'free': '41.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PLN', 'free': '18466.00000000', 'locked': '0.00000000'},
                                    {'asset': 'OSMO', 'free': '396.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HFT', 'free': '1179.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HOOK', 'free': '386.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MAGIC', 'free': '501.00000000', 'locked': '0.00000000'},
                                    {'asset': 'HIFI', 'free': '431.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RPL', 'free': '18.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PROS', 'free': '971.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RON', 'free': '18466.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GNS', 'free': '109.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SYN', 'free': '383.00000000', 'locked': '0.00000000'},
                                    {'asset': 'LQTY', 'free': '328.00000000', 'locked': '0.00000000'},
                                    {'asset': 'USTC', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'UFT', 'free': '939.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ID', 'free': '574.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ARB', 'free': '340.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RDNT', 'free': '1657.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ARS', 'free': '18466.00000000', 'locked': '0.00000000'},
                                    {'asset': 'EDU', 'free': '586.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SUI', 'free': '322.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AERGO', 'free': '3060.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PEPE', 'free': '18446.00', 'locked': '0.00'},
                                    {'asset': 'FLOKI', 'free': '18446.00', 'locked': '0.00'},
                                    {'asset': 'WBETH', 'free': '1.00000000', 'locked': '0.00000000'},
                                    {'asset': 'COMBO', 'free': '517.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MAV', 'free': '834.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PENDLE', 'free': '80.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ARKM', 'free': '263.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WLD', 'free': '76.00000000', 'locked': '0.00000000'},
                                    {'asset': 'FDUSD', 'free': '10000.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SEI', 'free': '745.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CYBER', 'free': '36.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ARK', 'free': '534.00000000', 'locked': '0.00000000'},
                                    {'asset': 'CREAM', 'free': '10.00000000', 'locked': '0.00000000'},
                                    {'asset': 'GFT', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'IQ', 'free': '18446.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NTRN', 'free': '474.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TIA', 'free': '44.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MEME', 'free': '13494.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ORDI', 'free': '7.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BEAMX', 'free': '16367.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VIC', 'free': '517.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BLUR', 'free': '964.00000000', 'locked': '0.00000000'},
                                    {'asset': 'VANRY', 'free': '2290.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AEUR', 'free': '460.00000000', 'locked': '0.00000000'},
                                    {'asset': 'JTO', 'free': '133.00000000', 'locked': '0.00000000'},
                                    {'asset': '1000SATS', 'free': '18446.00', 'locked': '0.00'},
                                    {'asset': 'BONK', 'free': '18446.00', 'locked': '0.00'},
                                    {'asset': 'ACE', 'free': '59.00000000', 'locked': '0.00000000'},
                                    {'asset': 'NFP', 'free': '774.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AI', 'free': '348.00000000', 'locked': '0.00000000'},
                                    {'asset': 'XAI', 'free': '489.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MANTA', 'free': '184.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ALT', 'free': '888.00000000', 'locked': '0.00000000'},
                                    {'asset': 'JUP', 'free': '383.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PYTH', 'free': '665.00000000', 'locked': '0.00000000'},
                                    {'asset': 'RONIN', 'free': '134.00000000', 'locked': '0.00000000'},
                                    {'asset': 'DYM', 'free': '101.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PIXEL', 'free': '816.00000000', 'locked': '0.00000000'},
                                    {'asset': 'STRK', 'free': '272.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PORTAL', 'free': '334.00000000', 'locked': '0.00000000'},
                                    {'asset': 'PDA', 'free': '4014.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AXL', 'free': '359.00000000', 'locked': '0.00000000'},
                                    {'asset': 'WIF', 'free': '144.00000000', 'locked': '0.00000000'},
                                    {'asset': 'METIS', 'free': '5.00000000', 'locked': '0.00000000'},
                                    {'asset': 'JPY', 'free': '18466.00000000', 'locked': '0.00000000'},
                                    {'asset': 'AEVO', 'free': '191.00000000', 'locked': '0.00000000'},
                                    {'asset': 'BOME', 'free': '18446.00', 'locked': '0.00'},
                                    {'asset': 'ETHFI', 'free': '87.00000000', 'locked': '0.00000000'},
                                    {'asset': 'ENA', 'free': '355.00000000', 'locked': '0.00000000'},
                                    {'asset': 'W', 'free': '593.00000000', 'locked': '0.00000000'},
                                    {'asset': 'TNSR', 'free': '301.00000000', 'locked': '0.00000000'},
                                    {'asset': 'SAGA', 'free': '80.00000000', 'locked': '0.00000000'},
                                    {'asset': 'MXN', 'free': '18466.00000000', 'locked': '0.00000000'}],
                       'permissions': ['SPOT'], 'uid': 1713356096419702488}, 'rateLimits': [
            {'rateLimitType': 'REQUEST_WEIGHT', 'interval': 'MINUTE', 'intervalNum': 1, 'limit': 6000, 'count': 46}]}


@pytest.fixture
def test_trader(test_balances, test_exchangeinfo, mock_async_logger):
    test_trader = Trader()
    test_trader.parse_exchangeinfo(test_exchangeinfo["result"])
    test_trader.parse_and_update_balances(test_balances["result"])
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


@pytest.mark.asyncio
async def test_process_trade(test_trader, test_trade_json):
    parsed_trade = test_trader.parse_message(test_trade_json)
    assert isinstance(parsed_trade, Trade)
    await test_trader.process_trade(parsed_trade)
    assert test_trader.state.last_price == float(parsed_trade.price)


@pytest.fixture
def account_position_message():
    return {'e': 'outboundAccountPosition'}


@pytest.fixture
def event_message_connected():
    return {'channel': 'user_stream', 'event': 'connected'}


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_parse_message_account_position(test_trader, account_position_message):
    assert test_trader.parse_message(account_position_message) is None


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
        f"Position entered at: {order.last_executed_price}", channel="trader"
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
