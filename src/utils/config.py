import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    provider: str = "openai"
    api_base: str = "https://api.openai.com/v1"
    api_key: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000


class TushareConfig(BaseSettings):
    token: str


class MongoDBConfig(BaseSettings):
    uri: str = "mongodb://localhost:27017"
    db_name: str = "quant_trading"


class SQLiteConfig(BaseSettings):
    path: str = "data/sqlite/trading.db"


class DatabaseConfig(BaseSettings):
    mongodb: MongoDBConfig
    sqlite: SQLiteConfig


class LoggingConfig(BaseSettings):
    level: str = "INFO"
    file: str = "logs/app.log"


class Config(BaseSettings):
    llm: LLMConfig
    tushare: TushareConfig
    database: DatabaseConfig
    logging: LoggingConfig

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        config_path = Path(config_path).resolve()
        env_path = config_path.parent.parent / ".env"
        load_dotenv(env_path, override=False)

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        resolved_data = _expand_env_placeholders(data)
        return cls(**resolved_data)


_config: Optional[Config] = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.load()
    return _config


_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::-(.*?))?\}")


def _expand_env_placeholders(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env_placeholders(item) for key, item in value.items()}

    if isinstance(value, list):
        return [_expand_env_placeholders(item) for item in value]

    if isinstance(value, str):
        return _ENV_PATTERN.sub(_resolve_env_placeholder, value)

    return value


def _resolve_env_placeholder(match: re.Match[str]) -> str:
    env_name = match.group(1)
    default_value = match.group(2)
    env_value = os.getenv(env_name)

    if env_value is not None:
        return env_value

    if default_value is not None:
        return default_value

    raise ValueError(f"缺少必需的环境变量: {env_name}")
