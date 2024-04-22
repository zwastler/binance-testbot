
import pytest

from adapters.binance_wss import BinancePrivateWSS


@pytest.mark.asyncio
@pytest.mark.xfail
async def test_invalid_private_key_loading():
    pkey = "invalid_base64=="
    client = BinancePrivateWSS("BTCUSD", "api_key", pkey)
    client.load_private_key(pkey)


@pytest.mark.asyncio
async def test_valid_private_key_loading(pkey):
    client = BinancePrivateWSS("BTCUSD", "api_key", pkey)
    client.load_private_key(pkey)
    assert client.private_key
