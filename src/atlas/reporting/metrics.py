def profit_factor(gross_profit: float, gross_loss: float) -> float | None:
    if gross_loss == 0:
        return None
    return gross_profit / abs(gross_loss)
