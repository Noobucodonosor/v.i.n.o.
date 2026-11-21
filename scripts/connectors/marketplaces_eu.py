"""Connettori modulari per marketplace IT/EU (Subito, Wallapop, Vinted) con graceful degradation."""

from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote_plus

from scripts.connectors.base import BaseConnector, ConnectorError, fetch_json
from scripts.market_tracker import NormalizedOffer

DEFAULT_ENDPOINTS: dict[str, str] = {
    "subito": "https://www.subito.it/hades/v1/search/items?q={query}&c=12&lim=10",
    "wallapop": "https://api.wallapop.com/api/v3/general/search?keywords={query}&category_ids=16000",
}


class MarketplacesEuConnector(BaseConnector):
    """Adapter isolati e disattivabili per marketplace EU/IT (nessun bypass anti-bot)."""

    name = "eu_marketplaces"

    def __init__(
        self,
        enabled: bool | None = None,
        delay_s: float = 0.5,
    ) -> None:
        env_flag = os.environ.get("ENABLE_EU_CONNECTORS", "false").lower() == "true"
        self.enabled = enabled if enabled is not None else env_flag
        self.delay_s = delay_s
        self.polled_sources: set[str] = set()

    def fetch_offers(self, vintages: list[dict[str, Any]]) -> list[NormalizedOffer]:
        self.polled_sources = set()
        if not self.enabled:
            return []

        offers: list[NormalizedOffer] = []
        for source, template in DEFAULT_ENDPOINTS.items():
            try:
                source_offers = self._poll_source(source, template, vintages)
                offers.extend(source_offers)
                self.polled_sources.add(source)
            except ConnectorError:
                # Graceful degradation: una fonte bloccata non invalida le altre
                continue
        return offers

    def _poll_source(
        self,
        source: str,
        template: str,
        vintages: list[dict[str, Any]],
    ) -> list[NormalizedOffer]:
        collected: list[NormalizedOffer] = []
        for vintage in vintages:
            query = quote_plus(f"{vintage['brand']} {vintage['model']} nuovo sigillato")
            url = template.format(query=query)
            payload = fetch_json(url)
            items = payload.get("ads") or payload.get("search_objects") or []
            for item in items[:5]:
                ext_id = str(item.get("urn") or item.get("id") or "").strip()
                item_url = str(item.get("urls", {}).get("default") or item.get("web_slug") or "")
                price_raw = item.get("price") or item.get("features", {}).get("/price", {}).get("values", [{}])[0].get("key")
                if not ext_id or not item_url.startswith("http") or not price_raw:
                    continue
                try:
                    price = float(str(price_raw).replace("€", "").strip())
                except ValueError:
                    continue
                if price <= 0:
                    continue
                collected.append(
                    NormalizedOffer(
                        source=source,
                        external_id=ext_id.replace(":", "_"),
                        vintage_id=vintage["id"],
                        url=item_url,
                        title=str(item.get("subject") or item.get("title") or vintage["model"])[:180],
                        condition="sealed",
                        price=price,
                        currency="EUR",
                        is_sold=False,
                    )
                )
            if self.delay_s > 0:
                time.sleep(self.delay_s)
        return collected
