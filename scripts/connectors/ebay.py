"""Connettore ufficiale eBay Browse API (credenziali via GitHub Secrets / env)."""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen

from scripts.connectors.base import BaseConnector, ConnectorError, USER_AGENT, fetch_json
from scripts.market_tracker import NormalizedOffer

EBAY_BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"


def exchange_client_credentials(
    client_id: str,
    client_secret: str,
    timeout_s: float = 8.0,
) -> str:
    """Scambia Client ID + Client Secret per un Application Token eBay (valido 2h)."""
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("ascii")
    body = urlencode({"grant_type": "client_credentials", "scope": EBAY_SCOPE}).encode("utf-8")
    req = Request(
        EBAY_TOKEN_URL,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            token = payload.get("access_token", "")
            if not token:
                raise ConnectorError("Risposta OAuth eBay priva di access_token")
            return str(token)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ConnectorError(f"Errore OAuth eBay: {exc}") from exc


class EbayConnector(BaseConnector):
    name = "ebay"

    def __init__(
        self,
        token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        fetcher: Callable[[str, dict[str, str]], dict[str, Any]] | None = None,
        token_exchanger: Callable[[str, str], str] | None = None,
    ) -> None:
        self._token = token if token is not None else os.environ.get("EBAY_OAUTH_TOKEN", "")
        self._client_id = (
            client_id if client_id is not None else os.environ.get("EBAY_CLIENT_ID", "")
        )
        self._client_secret = (
            client_secret if client_secret is not None else os.environ.get("EBAY_CLIENT_SECRET", "")
        )
        self._fetcher = fetcher or (lambda url, hdrs: fetch_json(url, headers=hdrs))
        self._token_exchanger = token_exchanger or exchange_client_credentials

    def _resolve_token(self) -> str:
        if self._token:
            return self._token
        if self._client_id and self._client_secret:
            return self._token_exchanger(self._client_id, self._client_secret)
        return ""

    def fetch_offers(self, vintages: list[dict[str, Any]]) -> list[NormalizedOffer]:
        token = self._resolve_token()
        if not token:
            return []

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_IT",
        }
        results: list[NormalizedOffer] = []

        for vintage in vintages:
            query = quote_plus(f"{vintage['brand']} {vintage['model']} sigillato")
            url = f"{EBAY_BROWSE_URL}?q={query}&filter=conditionIds:{{1000}}&limit=10"
            payload = self._fetcher(url, headers)
            for item in payload.get("itemSummaries", []):
                price_info = item.get("price", {})
                if price_info.get("currency") != "EUR":
                    continue
                try:
                    price_val = float(price_info["value"])
                except (KeyError, TypeError, ValueError):
                    continue
                if price_val <= 0 or not item.get("itemWebUrl") or not item.get("itemId"):
                    continue

                results.append(
                    NormalizedOffer(
                        source=self.name,
                        external_id=str(item["itemId"]).replace("|", "_"),
                        vintage_id=vintage["id"],
                        url=item["itemWebUrl"],
                        title=str(item.get("title", f"{vintage['brand']} {vintage['model']}"))[:180],
                        condition="sealed",
                        price=price_val,
                        currency="EUR",
                        is_sold=False,
                    )
                )

        return results
