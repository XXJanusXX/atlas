from atlas.config import AccountConfig, RiskConfig
from atlas.domain.models import RiskDecision, TradeProposal


class RiskEngine:
    def __init__(self, account: AccountConfig, limits: RiskConfig) -> None:
        self.account = account
        self.limits = limits

    def pre_trade_check(self, proposal: TradeProposal) -> RiskDecision:
        if proposal.entry_reference <= 0 or proposal.stop_loss <= 0:
            return RiskDecision(approved=False, reason_codes=["INVALID_PRICE"])
        if proposal.side.value == "buy" and proposal.stop_loss >= proposal.entry_reference:
            return RiskDecision(approved=False, reason_codes=["INVALID_STOP_DIRECTION"])
        if proposal.side.value == "sell" and proposal.stop_loss <= proposal.entry_reference:
            return RiskDecision(approved=False, reason_codes=["INVALID_STOP_DIRECTION"])
        # Contract metadata and account-currency conversion are required for correct sizing.
        # Fail closed rather than guessing pip value, contract size or permitted units.
        return RiskDecision(approved=False, reason_codes=["SIZING_METADATA_REQUIRED"])
