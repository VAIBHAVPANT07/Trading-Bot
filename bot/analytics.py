from typing import List, Dict


def calculate_portfolio_value(balances: List[Dict], prices: Dict[str, float]) -> float:
    """
    Calculate total portfolio value in USDT.
    """
    total = 0.0

    for asset in balances:
        free = float(asset.get("free", 0))
        locked = float(asset.get("locked", 0))
        qty = free + locked

        symbol = asset["asset"]

        if symbol == "USDT":
            total += qty
        elif f"{symbol}USDT" in prices:
            total += qty * prices[f"{symbol}USDT"]

    return total


def calculate_pnl(current_value: float, initial_value: float = 10000) -> float:
    """
    Calculate profit & loss.
    """
    return current_value - initial_value
