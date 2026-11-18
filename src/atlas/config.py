from decimal import Decimal

from pydantic import BaseModel, Field


class AccountConfig(BaseModel):
    base_currency: str = "USD"
    initial_equity: Decimal = Field(default=Decimal("100.00"), gt=0)
    leverage_enabled: bool = False


class RiskConfig(BaseModel):
    risk_per_trade_pct: Decimal = Field(default=Decimal("0.25"), gt=0, le=1)
    max_total_open_risk_pct: Decimal = Field(default=Decimal("0.75"), gt=0, le=5)
    max_daily_loss_pct: Decimal = Field(default=Decimal("1.00"), gt=0, le=10)
    max_weekly_loss_pct: Decimal = Field(default=Decimal("2.00"), gt=0, le=20)
    max_open_positions: int = Field(default=3, ge=1, le=10)


class RuntimeConfig(BaseModel):
    execution_mode: str = "paper"

    def validate_safety_boundary(self) -> None:
        if self.execution_mode != "paper":
            raise ValueError("This release supports paper mode only.")
