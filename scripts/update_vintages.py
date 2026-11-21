#!/usr/bin/env python3
"""Pipeline schedulata di aggiornamento offerte e storico mercato per v.i.n.o."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.connectors.base import ConnectorError
from scripts.connectors.community import CommunityConnector
from scripts.connectors.ebay import EbayConnector
from scripts.connectors.marketplaces_eu import MarketplacesEuConnector
from scripts.market_tracker import NormalizedOffer, merge_offers, update_market_history


def run_update(
    vintages_path: Path,
    offers_path: Path,
    history_path: Path,
    run_date: str,
    dry_run: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    vintages_data = json.loads(vintages_path.read_text(encoding="utf-8"))
    vintages = vintages_data.get("vintages", [])
    if not vintages:
        raise ValueError("Dataset vintages.json vuoto o non valido")

    ledger = json.loads(offers_path.read_text(encoding="utf-8"))
    history = json.loads(history_path.read_text(encoding="utf-8"))

    incoming: list[NormalizedOffer] = []
    polled_sources: set[str] = set()

    ebay = EbayConnector()
    eu = MarketplacesEuConnector()
    community = CommunityConnector()

    for connector in (ebay, community):
        try:
            fetched = connector.fetch_offers(vintages)
            incoming.extend(fetched)
            if fetched or connector.name == "community":
                polled_sources.add(connector.name)
        except ConnectorError as exc:
            print(f"⚠️  Connettore {connector.name} saltato: {exc}", file=sys.stderr)

    try:
        incoming.extend(eu.fetch_offers(vintages))
        polled_sources.update(eu.polled_sources)
    except ConnectorError as exc:
        print(f"⚠️  Connettori EU saltati: {exc}", file=sys.stderr)

    updated_ledger = merge_offers(
        ledger=ledger,
        incoming=incoming,
        run_date=run_date,
        polled_sources=polled_sources if polled_sources else None,
    )
    updated_history = update_market_history(
        history=history,
        ledger=updated_ledger,
        run_date=run_date,
    )

    if not dry_run:
        offers_path.write_text(
            json.dumps(updated_ledger, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        history_path.write_text(
            json.dumps(updated_history, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return updated_ledger, updated_history


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggiorna offerte e storico mercato v.i.n.o.")
    parser.add_argument("--dry-run", action="store_true", help="Esegue senza scrivere su disco")
    parser.add_argument("--date", default=date.today().isoformat(), help="Data run YYYY-MM-DD")
    parser.add_argument("--vintages-path", type=Path, default=ROOT_DIR / "src/data/vintages.json")
    parser.add_argument("--offers-path", type=Path, default=ROOT_DIR / "src/data/offers.json")
    parser.add_argument("--history-path", type=Path, default=ROOT_DIR / "src/data/market-history.json")
    args = parser.parse_args()

    ledger, history = run_update(
        vintages_path=args.vintages_path,
        offers_path=args.offers_path,
        history_path=args.history_path,
        run_date=args.date,
        dry_run=args.dry_run,
    )
    mode = "DRY-RUN" if args.dry_run else "AGGIORNATO"
    print(f"✅ [{mode}] Offerte tracciate: {len(ledger['offers'])}, Annate in storico: {len(history['series'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
