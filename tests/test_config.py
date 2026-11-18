from decimal import Decimal

import pytest

from atlas.config import AccountConfig, RuntimeConfig


def test_initial_equity_is_one_hundred_usd() -> None:
    assert AccountConfig().initial_equity == Decimal("100.00")


def test_only_paper_mode_is_accepted() -> None:
    RuntimeConfig(execution_mode="paper").validate_safety_boundary()
    with pytest.raises(ValueError):
        RuntimeConfig(execution_mode="live").validate_safety_boundary()
