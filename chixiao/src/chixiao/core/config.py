from __future__ import annotations

from pathlib import Path

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_source: str = "akshare"
    execution_mode: str = "mode_a"
    risk_max_position_pct: float = 0.25
    risk_max_single_loss_pct: float = 0.02
    risk_max_portfolio_drawdown_pct: float = 0.10
    data_cache_dir: str = "data/cache"
    data_cache_expiry_hours: int = 4
    csv_dir: str = "data/positions"
    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"

    model_config = {"env_prefix": "CHIXIAO_"}


def load_config(config_path: str | Path | None = None) -> Settings:
    if config_path is None:
        return Settings()

    path = Path(config_path)
    if not path.exists():
        return Settings()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return Settings(**raw)
