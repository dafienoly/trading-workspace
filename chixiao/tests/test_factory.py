from chixiao.core.factory import create_data_adapter, create_executor
from chixiao.data.akshare_adapter import AKShareAdapter
from chixiao.data.tushare_adapter import TuShareAdapter
from chixiao.execution.mode_a import ModeAExecutor
from chixiao.core.interfaces import DataAdapter, Executor


class TestFactory:
    def test_create_akshare_adapter(self):
        adapter = create_data_adapter("akshare")
        assert isinstance(adapter, AKShareAdapter)
        assert isinstance(adapter, DataAdapter)

    def test_create_tushare_adapter(self):
        adapter = create_data_adapter("tushare", token="test")
        assert isinstance(adapter, TuShareAdapter)
        assert isinstance(adapter, DataAdapter)

    def test_create_unknown_adapter_fallback(self):
        adapter = create_data_adapter("unknown")
        assert isinstance(adapter, AKShareAdapter)

    def test_create_mode_a_executor(self):
        executor = create_executor("mode_a")
        assert isinstance(executor, ModeAExecutor)
        assert isinstance(executor, Executor)

    def test_create_unknown_executor_fallback(self):
        executor = create_executor("unknown")
        assert isinstance(executor, ModeAExecutor)
