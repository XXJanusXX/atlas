from datetime import datetime, timezone
from decimal import Decimal

from atlas.config import AccountConfig, RiskConfig
from atlas.domain.models import Side, TradeProposal
from atlas.risk.engine import RiskEngine


def test_risk_engine_fails_closed_without_sizing_metadata() -> None:
    proposal = TradeProposal(
        instrument="EUR_USD", side=Side.BUY,
        entry_reference=Decimal("1.1000"), stop_loss=Decimal("1.0950"),
        rationale="Test proposal", strategy_id="test",
        created_at=datetime.now(timezone.utc),
    )
    result = RiskEngine(AccountConfig(), RiskConfig()).pre_trade_check(proposal)
    assert not result.approved
    assert "SIZING_METADATA_REQUIRED" in result.reason_codes
