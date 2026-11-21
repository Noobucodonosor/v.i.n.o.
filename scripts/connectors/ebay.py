"""Connettore ufficiale eBay Browse API (credenziali via GitHub Secrets / env)."""

from __future__ import annotations

import os
from typing import Any, Callable
from urllib.parse import quote_plus

from scripts.connectors.base import BaseConnector, fetch_json
from scripts.market_tracker import NormalizedOffer

EBAY_BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"


class EbayConnector(BaseConnector):
    name = "ebay"

    def __init__(
        self,
        token: str | None = None,
        fetcher: Callable[[str, dict[str, str]], dict[str, Any]] | None = None,
    ) -> None:
        self._token = token if token is not None else os.environ.get("EBAY_OAUTH_TOKEN", "")
        self._fetcher = fetcher or (lambda url, hdrs: fetch_json(url, headers=hdrs))

    def fetch_offers(self, vintages: list[dict[str, Any]]) -> list[NormalizedOffer]:
        if not self._token:
            return []

        headers = {
            "Authorization": f"Bearer {self._token}",
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
