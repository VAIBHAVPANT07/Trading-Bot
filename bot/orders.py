"""
High-level order placement logic.

Bridges validated user input to the BinanceClient, formats responses
for CLI display, and keeps business logic decoupled from the transport layer.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from bot.client import BinanceClient, BinanceAPIError
from bot.validators import validate_all, ValidationError
from bot.logging_config import get_logger

logger = get_logger(__name__)


class OrderResult:
    """Structured result from an order placement attempt."""

    def __init__(self, success: bool, data: Dict[str, Any], error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

    @property
    def order_id(self) -> Optional[int]:
        return self.data.get("orderId")

    @property
    def status(self) -> Optional[str]:
        return self.data.get("status")

    @property
    def executed_qty(self) -> str:
        return self.data.get("executedQty", "0")

    @property
    def avg_price(self) -> str:
        return self.data.get("avgPrice", "N/A")

    @property
    def client_order_id(self) -> Optional[str]:
        return self.data.get("clientOrderId")


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
    reduce_only: bool = False,
) -> OrderResult:
    """
    Validate input, place an order, and return a structured OrderResult.

    Args:
        client:       Initialized BinanceClient
        symbol:       Trading pair (e.g. BTCUSDT)
        side:         BUY or SELL
        order_type:   MARKET, LIMIT, STOP_MARKET, or STOP_LIMIT
        quantity:     Order quantity as string
        price:        Limit price (required for LIMIT/STOP_LIMIT)
        stop_price:   Stop trigger price (required for STOP_MARKET/STOP_LIMIT)
        reduce_only:  Whether to reduce position only

    Returns:
        OrderResult with success flag, raw data, and optional error message.
    """
    # 1. Validate
    try:
        params = validate_all(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        return OrderResult(success=False, data={}, error=str(exc))

    # 2. Place order
    try:
        response = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
            stop_price=params["stop_price"],
            reduce_only=reduce_only,
        )
        return OrderResult(success=True, data=response)

    except ValidationError as exc:
        logger.error("Validation error: %s", exc)
        return OrderResult(success=False, data={}, error=str(exc))

    except BinanceAPIError as exc:
        logger.error("Binance API error [%s]: %s", exc.code, exc.msg)
        return OrderResult(success=False, data={}, error=f"Binance API Error [{exc.code}]: {exc.msg}")

    except (ConnectionError, TimeoutError) as exc:
        logger.error("Network error: %s", exc)
        return OrderResult(success=False, data={}, error=f"Network Error: {exc}")

    except Exception as exc:
        logger.exception("Unexpected error during order placement")
        return OrderResult(success=False, data={}, error=f"Unexpected error: {exc}")


def get_account_summary(client: BinanceClient) -> Optional[Dict[str, Any]]:
    """Return simplified account info (USDT balance + unrealized PnL)."""
    try:
        account = client.get_account()
        assets = {a["asset"]: a for a in account.get("assets", [])}
        usdt = assets.get("USDT", {})
        return {
            "totalWalletBalance": account.get("totalWalletBalance", "N/A"),
            "totalUnrealizedProfit": account.get("totalUnrealizedProfit", "N/A"),
            "availableBalance": account.get("availableBalance", "N/A"),
            "canTrade": account.get("canTrade", False),
            "canDeposit": account.get("canDeposit", False),
        }
    except BinanceAPIError as exc:
        logger.error("Failed to fetch account: %s", exc)
        return None
    except Exception:
        logger.exception("Unexpected error fetching account")
        return None
