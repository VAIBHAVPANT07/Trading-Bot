"""
Binance Spot Testnet REST client.

Wraps authenticated HMAC-SHA256 requests with structured logging,
automatic timestamp sync, and graceful error handling.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://testnet.binance.vision"
RECV_WINDOW = 5000


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, msg: str, status_code: int = 0):
        self.code = code
        self.msg = msg
        self.status_code = status_code
        super().__init__(f"[{code}] {msg}")


class BinanceClient:
    """Thread-safe Binance Spot Testnet REST client."""

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "TradingBot/1.0",
            }
        )

        logger.debug("BinanceClient initialized | base_url=%s", self.base_url)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> str:
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _request(
        self,
        method: str,
        endpoint: str,
        signed: bool = False,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        url = f"{self.base_url}{endpoint}"
        params = params or {}
        data = data or {}

        if signed:
            payload = {
                **params,
                **data,
                "timestamp": self._timestamp(),
                "recvWindow": RECV_WINDOW,
            }

            payload["signature"] = self._sign(payload)

            if method.upper() in ("GET", "DELETE"):
                params = payload
                data = {}
            else:
                data = payload
                params = {}

        logger.debug(
            "→ %s %s | params=%s | body_keys=%s",
            method.upper(),
            endpoint,
            list(params.keys()) if params else [],
            list(data.keys()) if data else [],
        )

        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params if params else None,
                data=urlencode(data) if data else None,
                timeout=10,
            )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error reaching %s: %s", url, exc)
            raise ConnectionError(
                f"Cannot connect to Binance Testnet ({url}). Check your internet."
            ) from exc

        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise TimeoutError("Request to Binance timed out.") from exc

        logger.debug("← HTTP %s | endpoint=%s", resp.status_code, endpoint)

        try:
            body = resp.json()
        except ValueError:
            logger.error("Non-JSON response: %s", resp.text[:200])
            resp.raise_for_status()
            raise

        if isinstance(body, dict) and "code" in body and body["code"] < 0:
            err = BinanceAPIError(
                body["code"],
                body.get("msg", "Unknown error"),
                resp.status_code,
            )
            logger.error("Binance API error: %s", err)
            raise err

        if resp.status_code >= 400:
            if isinstance(body, dict):
                raise BinanceAPIError(
                    body.get("code", resp.status_code),
                    body.get("msg", resp.text),
                    resp.status_code,
                )
            resp.raise_for_status()

        return body

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ping(self) -> bool:
        """Check connectivity."""
        try:
            self._request("GET", "/api/v3/ping")
            logger.info("Ping successful — Binance Spot Testnet reachable.")
            return True
        except Exception as exc:
            logger.warning("Ping failed: %s", exc)
            return False

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/api/v3/exchangeInfo", params=params)

    def get_account(self) -> Dict[str, Any]:
        return self._request("GET", "/api/v3/account", signed=True)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:

        data: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            data["timeInForce"] = time_in_force
            if price is not None:
                data["price"] = str(price)

        if stop_price is not None:
            data["stopPrice"] = str(stop_price)

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s stopPrice=%s",
            side,
            order_type,
            symbol,
            quantity,
            price,
            stop_price,
        )

        response = self._request(
            "POST",
            "/api/v3/order",
            signed=True,
            data=data,
        )

        logger.info(
            "Order placed ✓ | orderId=%s status=%s executedQty=%s",
            response.get("orderId"),
            response.get("status"),
            response.get("executedQty"),
        )

        return response

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        data = {"symbol": symbol, "orderId": order_id}
        logger.info("Cancelling order | symbol=%s orderId=%s", symbol, order_id)
        return self._request("DELETE", "/api/v3/order", signed=True, data=data)

    def get_open_orders(self, symbol: Optional[str] = None) -> Any:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/api/v3/openOrders", signed=True, params=params)
