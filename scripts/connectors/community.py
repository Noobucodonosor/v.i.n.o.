"""Connettore per segnalazioni curate dalla community nel repository."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.connectors.base import BaseConnector
from scripts.market_tracker import NormalizedOffer

DEFAULT_SUBMISSIONS_PATH = Path("src/data/community-submissions.json")


class CommunityConnector(BaseConnector):
    name = "community"

    def __init__(self, submissions_path: Path | None = None) -> None:
        self.submissions_path = submissions_path or DEFAULT_SUBMISSIONS_PATH

    def fetch_offers(self, vintages: list[dict[str, Any]]) -> list[NormalizedOffer]:
        if not self.submissions_path.exists():
            return []

        raw = json.loads(self.submissions_path.read_text(encoding="utf-8"))
        valid_ids = {v["id"] for v in vintages}
        results: list[NormalizedOffer] = []

        for item in raw.get("submissions", []):
            if item.get("vintage_id") not in valid_ids:
                continue
            results.append(
                NormalizedOffer(
                    source=self.name,
                    external_id=str(item["external_id"]),
                    vintage_id=item["vintage_id"],
                    url=item["url"],
                    title=item["title"],
                    condition=item.get("condition", "sealed"),
                    price=float(item["price"]),
                    currency="EUR",
                    is_sold=bool(item.get("is_sold", False)),
                )
            )
        return results
