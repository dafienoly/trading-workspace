from __future__ import annotations

from chixiao.core.interfaces import DataAdapter, Executor


def create_data_adapter(source: str, **kwargs) -> DataAdapter:
    if source == "akshare":
        from chixiao.data.akshare_adapter import AKShareAdapter
        return AKShareAdapter()
    elif source == "tushare":
        from chixiao.data.tushare_adapter import TuShareAdapter
        return TuShareAdapter(token=kwargs.get("token", ""))
    elif source == "wind":
        from chixiao.data.wind_adapter import WindAdapter
        return WindAdapter(**kwargs)
    else:
        from chixiao.data.akshare_adapter import AKShareAdapter
        return AKShareAdapter()


def create_executor(mode: str, **kwargs) -> Executor:
    if mode == "mode_a":
        from chixiao.execution.mode_a import ModeAExecutor
        return ModeAExecutor(csv_dir=kwargs.get("csv_dir", "data/positions"))
    elif mode == "mode_b":
        from chixiao.execution.mode_b import ModeBExecutor
        return ModeBExecutor(
            broker=kwargs.get("broker", "yh"),
            exe_path=kwargs.get("exe_path", ""),
        )
    elif mode == "mode_c":
        from chixiao.execution.mode_c import ModeCExecutor
        return ModeCExecutor(
            path=kwargs.get("path", ""),
            session_id=kwargs.get("session_id", 123456),
            account_id=kwargs.get("account_id", ""),
        )
    else:
        from chixiao.execution.mode_a import ModeAExecutor
        return ModeAExecutor(csv_dir=kwargs.get("csv_dir", "data/positions"))
