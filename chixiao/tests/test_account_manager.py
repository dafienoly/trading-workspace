from datetime import datetime, date
from decimal import Decimal
from chixiao.account.account_manager import AccountManager, AccountInfo
from chixiao.core.models import Position, Portfolio, AccountSnapshot


class TestAccountManager:
    def test_register_account(self):
        mgr = AccountManager()
        mgr.register_account("manual_001", "手动同步", "mode_a")
        accounts = mgr.list_accounts()
        assert len(accounts) == 1
        assert accounts[0].account_id == "manual_001"

    def test_register_multiple_accounts(self):
        mgr = AccountManager()
        mgr.register_account("manual_001", "手动同步", "mode_a")
        mgr.register_account("broker_001", "国泰海通", "mode_b")
        accounts = mgr.list_accounts()
        assert len(accounts) == 2

    def test_get_aggregated_portfolio(self):
        mgr = AccountManager()
        mgr.register_account("acc_1", "券商A", "mode_a")
        mgr.register_account("acc_2", "券商B", "mode_a")

        snapshot_1 = AccountSnapshot(
            account_id="acc_1",
            broker="券商A",
            portfolio=Portfolio(
                positions=[Position(symbol="000001", name="平安银行", quantity=1000, avg_cost=Decimal("10.00"), current_price=Decimal("11.00"))],
                cash=Decimal("50000"),
                timestamp=datetime.now(),
            ),
            date=date.today(),
        )
        snapshot_2 = AccountSnapshot(
            account_id="acc_2",
            broker="券商B",
            portfolio=Portfolio(
                positions=[Position(symbol="000001", name="平安银行", quantity=500, avg_cost=Decimal("10.50"), current_price=Decimal("11.00"))],
                cash=Decimal("30000"),
                timestamp=datetime.now(),
            ),
            date=date.today(),
        )

        mgr.update_snapshot("acc_1", snapshot_1)
        mgr.update_snapshot("acc_2", snapshot_2)

        agg = mgr.get_aggregated_portfolio()
        assert agg is not None
        assert agg.cash == Decimal("80000")
        pos_000001 = next(p for p in agg.positions if p.symbol == "000001")
        assert pos_000001.quantity == 1500

    def test_get_account_snapshot(self):
        mgr = AccountManager()
        mgr.register_account("acc_1", "券商A", "mode_a")
        snapshot = AccountSnapshot(
            account_id="acc_1",
            broker="券商A",
            portfolio=Portfolio(
                positions=[], cash=Decimal("100000"), timestamp=datetime.now()
            ),
            date=date.today(),
        )
        mgr.update_snapshot("acc_1", snapshot)
        result = mgr.get_snapshot("acc_1")
        assert result is not None
        assert result.total_assets == Decimal("100000")

    def test_get_nonexistent_snapshot(self):
        mgr = AccountManager()
        result = mgr.get_snapshot("nonexistent")
        assert result is None
