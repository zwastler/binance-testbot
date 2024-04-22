from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    VERSION: str = "0.0.1"
    ENVIRONMENT: str = "development"

    LOGLEVEL: str = "INFO"
    JSON_LOGS: bool = False
    COLORED_LOGS: bool = not JSON_LOGS
    SAVE_LOG_FILE: bool = False
    LOG_FILE_PATH: str = "logs/test_bot.log"

    SYMBOL: str = "BTCUSDT"
    POSITION_QUANTITY: float = 0.001
    POSITION_TP_PERCENT: float = 0.25
    POSITION_SL_PERCENT: float = 0.25
    POSITION_HOLD_TIME: int = 60
    POSITION_SLEEP_TIME: int = 30

    API_KEY: str
    PRIVATE_KEY_BASE64: str


settings = Settings()
