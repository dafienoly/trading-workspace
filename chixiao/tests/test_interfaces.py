from abc import ABC
from chixiao.core.interfaces import DataAdapter, Executor, FactorProvider


class TestInterfaces:
    def test_data_adapter_is_abstract(self):
        assert issubclass(DataAdapter, ABC)
        assert hasattr(DataAdapter, "get_bars")
        assert hasattr(DataAdapter, "get_latest_price")

    def test_executor_is_abstract(self):
        assert issubclass(Executor, ABC)
        assert hasattr(Executor, "submit_order")
        assert hasattr(Executor, "cancel_order")
        assert hasattr(Executor, "sync_positions")

    def test_factor_provider_is_abstract(self):
        assert issubclass(FactorProvider, ABC)
        assert hasattr(FactorProvider, "compute_factors")
