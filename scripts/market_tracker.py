"""Motore di persistenza offerte e aggregazione storico mercato (ADR-0003)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from statistics import median
from typing import Any

ALLOWED_SOURCES = {"ebay", "subito", "wallapop", "vinted", "community"}
ALLOWED_CONDITIONS = {"sealed", "nos_open_box"}
HTML_OR_SCRIPT_RE = re.compile(r"<[^>]*>|javascript:", re.IGNORECASE)
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
ID_RE = re.compile(r"^[a-z]+:[a-zA-Z0-9._-]+$")


@dataclass(frozen=True)
class NormalizedOffer:
    """Offerta normalizzata restituita da un connettore."""

    source: str
    external_id: str
    vintage_id: str
    url: str
    title: str
    condition: str
    price: float
    currency: str = "EUR"
    is_sold: bool = False

    @property
    def offer_id(self) -> str:
        return f"{self.source}:{self.external_id}"


def _validate_normalized_offer(offer: NormalizedOffer) -> None:
    if offer.source not in ALLOWED_SOURCES:
        raise ValueError(f"Fonte non valida: {offer.source}")
    if offer.condition not in ALLOWED_CONDITIONS:
        raise ValueError(f"Condizione non valida: {offer.condition}")
    if offer.currency != "EUR":
        raise ValueError(f"Valuta non supportata: {offer.currency}")
    if offer.price <= 0:
        raise ValueError(f"Prezzo deve essere positivo: {offer.price}")
    if not SLUG_RE.match(offer.vintage_id):
        raise ValueError(f"vintage_id non valido: {offer.vintage_id}")
    if not ID_RE.match(offer.offer_id):
        raise ValueError(f"offer_id non valido: {offer.offer_id}")
    if not (offer.url.startswith("https://") or offer.url.startswith("http://")):
        raise ValueError(f"URL non sicuro: {offer.url}")
    if HTML_OR_SCRIPT_RE.search(offer.title):
        raise ValueError("Titolo contiene markup HTML o schema javascript:")


def merge_offers(
    ledger: dict[str, Any],
    incoming: list[NormalizedOffer],
    run_date: str,
    missing_threshold: int = 3,
    polled_sources: set[str] | None = None,
) -> dict[str, Any]:
    """Esegue merge idempotente delle offerte con deduplicazione e lifecycle."""
    existing_by_id: dict[str, dict[str, Any]] = {
        item["id"]: dict(item) for item in ledger.get("offers", [])
    }
    seen_ids: set[str] = set()

    for raw in incoming:
        _validate_normalized_offer(raw)
        oid = raw.offer_id
        seen_ids.add(oid)
        rounded_price = round(float(raw.price), 2)

        if oid in existing_by_id:
            entry = existing_by_id[oid]
            entry["title"] = raw.title.strip()
            entry["url"] = raw.url
            entry["last_seen"] = run_date
            entry["missed_runs"] = 0

            history = list(entry.get("price_history", []))
            if not history or history[-1]["price"] != rounded_price:
                history.append({"date": run_date, "price": rounded_price})
            entry["price_history"] = history

            if raw.is_sold:
                entry["status"] = "sold"
                entry["closed_at"] = entry.get("closed_at") or run_date
            elif entry["status"] == "expired":
                entry["status"] = "active"
                entry["closed_at"] = None
        else:
            status = "sold" if raw.is_sold else "active"
            existing_by_id[oid] = {
                "id": oid,
                "vintage_id": raw.vintage_id,
                "source": raw.source,
                "url": raw.url,
                "title": raw.title.strip(),
                "condition": raw.condition,
                "currency": raw.currency,
                "status": status,
                "first_seen": run_date,
                "last_seen": run_date,
                "closed_at": run_date if raw.is_sold else None,
                "missed_runs": 0,
                "price_history": [{"date": run_date, "price": rounded_price}],
            }

    for oid, entry in existing_by_id.items():
        if oid in seen_ids or entry["status"] != "active":
            continue
        if polled_sources is not None and entry["source"] not in polled_sources:
            continue
        missed = int(entry.get("missed_runs", 0)) + 1
        entry["missed_runs"] = missed
        if missed >= missing_threshold:
            entry["status"] = "expired"
            entry["closed_at"] = run_date

    sorted_offers = sorted(existing_by_id.values(), key=lambda x: x["id"])
    return {
        "version": ledger.get("version", "1.0.0"),
        "updated_at": run_date,
        "offers": sorted_offers,
    }


def update_market_history(
    history: dict[str, Any],
    ledger: dict[str, Any],
    run_date: str,
) -> dict[str, Any]:
    """Aggiorna la serie storica aggregata per ciascuna annata."""
    by_vintage: dict[str, list[dict[str, Any]]] = {}
    for offer in ledger.get("offers", []):
        by_vintage.setdefault(offer["vintage_id"], []).append(offer)

    series = {k: list(v) for k, v in history.get("series", {}).items()}

    for vintage_id, offers in sorted(by_vintage.items()):
        active_prices = [
            o["price_history"][-1]["price"]
            for o in offers
            if o["status"] == "active" and o.get("price_history")
        ]
        sold_prices = [
            o["price_history"][-1]["price"]
            for o in offers
            if o["status"] == "sold" and o.get("price_history")
        ]
        expired_count = sum(1 for o in offers if o["status"] == "expired")

        snapshot = {
            "date": run_date,
            "median_asking_eur": round(median(active_prices), 2) if active_prices else None,
            "median_sold_eur": round(median(sold_prices), 2) if sold_prices else None,
            "active_count": len(active_prices),
            "sold_count": len(sold_prices),
            "expired_count": expired_count,
        }

        vintage_series = series.get(vintage_id, [])
        if vintage_series and vintage_series[-1]["date"] == run_date:
            vintage_series[-1] = snapshot
        else:
            vintage_series.append(snapshot)
        series[vintage_id] = vintage_series

    return {
        "version": history.get("version", "1.0.0"),
        "updated_at": run_date,
        "series": series,
    }
