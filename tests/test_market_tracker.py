import unittest

from scripts.market_tracker import NormalizedOffer, merge_offers, update_market_history


class TestMarketTracker(unittest.TestCase):
    def setUp(self) -> None:
        self.empty_ledger = {"version": "1.0.0", "updated_at": "2026-11-20", "offers": []}
        self.empty_history = {"version": "1.0.0", "updated_at": "2026-11-20", "series": {}}

    def test_deduplication_and_price_history_append_only_on_change(self) -> None:
        offer_v1 = NormalizedOffer(
            source="ebay",
            external_id="12345",
            vintage_id="apple-iphone-13-mini-2021",
            url="https://www.ebay.it/itm/12345",
            title="iPhone 13 mini sigillato",
            condition="sealed",
            price=600.0,
        )
        ledger = merge_offers(self.empty_ledger, [offer_v1], "2026-11-21", polled_sources={"ebay"})
        self.assertEqual(len(ledger["offers"]), 1)

        # Same price on next run -> price_history stays length 1
        ledger = merge_offers(ledger, [offer_v1], "2026-11-22", polled_sources={"ebay"})
        self.assertEqual(len(ledger["offers"][0]["price_history"]), 1)

        # Changed price -> appends new point
        offer_v2 = NormalizedOffer(
            source="ebay",
            external_id="12345",
            vintage_id="apple-iphone-13-mini-2021",
            url="https://www.ebay.it/itm/12345",
            title="iPhone 13 mini sigillato",
            condition="sealed",
            price=575.0,
        )
        ledger = merge_offers(ledger, [offer_v2], "2026-11-23", polled_sources={"ebay"})
        self.assertEqual(len(ledger["offers"][0]["price_history"]), 2)
        self.assertEqual(ledger["offers"][0]["price_history"][-1]["price"], 575.0)

    def test_lifecycle_active_to_expired_and_sold(self) -> None:
        offer = NormalizedOffer(
            source="subito",
            external_id="abc99",
            vintage_id="google-pixel-5-2020",
            url="https://www.subito.it/telefonia/pixel-5-abc99.htm",
            title="Google Pixel 5 nuovo sigillato",
            condition="sealed",
            price=350.0,
        )
        ledger = merge_offers(self.empty_ledger, [offer], "2026-11-20", missing_threshold=2, polled_sources={"subito"})

        # Miss 1 -> still active
        ledger = merge_offers(ledger, [], "2026-11-21", missing_threshold=2, polled_sources={"subito"})
        self.assertEqual(ledger["offers"][0]["status"], "active")

        # Miss 2 -> expired
        ledger = merge_offers(ledger, [], "2026-11-22", missing_threshold=2, polled_sources={"subito"})
        self.assertEqual(ledger["offers"][0]["status"], "expired")
        self.assertEqual(ledger["offers"][0]["closed_at"], "2026-11-22")

        # Marked sold explicitly
        sold_offer = NormalizedOffer(
            source="ebay",
            external_id="s1",
            vintage_id="google-pixel-5-2020",
            url="https://www.ebay.it/itm/s1",
            title="Pixel 5 venduto",
            condition="sealed",
            price=380.0,
            is_sold=True,
        )
        ledger = merge_offers(ledger, [sold_offer], "2026-11-22", polled_sources={"ebay"})
        sold_entry = [o for o in ledger["offers"] if o["id"] == "ebay:s1"][0]
        self.assertEqual(sold_entry["status"], "sold")

    def test_market_history_aggregation(self) -> None:
        offers = [
            NormalizedOffer("ebay", "1", "apple-iphone-13-mini-2021", "https://www.ebay.it/itm/1", "Offerta 1", "sealed", 500.0),
            NormalizedOffer("subito", "2", "apple-iphone-13-mini-2021", "https://www.subito.it/2", "Offerta 2", "sealed", 600.0),
            NormalizedOffer("ebay", "3", "apple-iphone-13-mini-2021", "https://www.ebay.it/itm/3", "Venduto 3", "sealed", 550.0, is_sold=True),
        ]
        ledger = merge_offers(self.empty_ledger, offers, "2026-11-22")
        history = update_market_history(self.empty_history, ledger, "2026-11-22")
        snap = history["series"]["apple-iphone-13-mini-2021"][-1]
        self.assertEqual(snap["median_asking_eur"], 550.0)
        self.assertEqual(snap["median_sold_eur"], 550.0)
        self.assertEqual(snap["active_count"], 2)
        self.assertEqual(snap["sold_count"], 1)


if __name__ == "__main__":
    unittest.main()
