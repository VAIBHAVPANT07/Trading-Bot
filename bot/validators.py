"""
Input validation for CLI parameters.
Raises descriptive errors for any invalid input before hitting the API.
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Optional
import re


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET", "STOP_LIMIT"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{3,20}$")


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    """Ensure the symbol is a non-empty uppercase alphanumeric string."""
    s = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(s):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected uppercase alphanumeric (e.g. BTCUSDT)."
        )
    return s


def validate_side(side: str) -> str:
    """Ensure side is BUY or SELL."""
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return s


def validate_order_type(order_type: str) -> str:
    """Ensure order type is one of the supported types."""
    ot = order_type.strip().upper()
    if ot not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return ot


def validate_quantity(quantity: str) -> Decimal:
    """Parse and validate quantity — must be a positive number."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than zero, got: {qty}.")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[Decimal]:
    """Parse and validate price. Required for LIMIT and STOP_LIMIT orders."""
    ot = order_type.strip().upper()
    needs_price = ot in {"LIMIT", "STOP_LIMIT"}

    if needs_price and (price is None or str(price).strip() == ""):
        raise ValidationError(
            f"Price is required for {ot} orders."
        )
    if price is None or str(price).strip() == "":
        return None

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValidationError(f"Price must be greater than zero, got: {p}.")
    return p


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[Decimal]:
    """Parse and validate stop price. Required for STOP_MARKET and STOP_LIMIT orders."""
    ot = order_type.strip().upper()
    needs_stop = ot in {"STOP_MARKET", "STOP_LIMIT"}

    if needs_stop and (stop_price is None or str(stop_price).strip() == ""):
        raise ValidationError(
            f"Stop price (--stop-price) is required for {ot} orders."
        )
    if stop_price is None or str(stop_price).strip() == "":
        return None

    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValidationError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValidationError(f"Stop price must be greater than zero, got: {sp}.")
    return sp


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> dict:
    """Run all validations and return a clean, typed parameter dict."""
    return {
        "symbol":     validate_symbol(symbol),
        "side":       validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity":   validate_quantity(quantity),
        "price":      validate_price(price, order_type),
        "stop_price": validate_stop_price(stop_price, order_type),
    }
