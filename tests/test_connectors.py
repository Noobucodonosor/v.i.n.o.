import json
from pathlib import Path
import tempfile
import unittest

from scripts.connectors.community import CommunityConnector
from scripts.connectors.ebay import EbayConnector
from scripts.connectors.marketplaces_eu import MarketplacesEuConnector
from scripts.update_vintages import run_update


class TestConnectorsAndPipeline(unittest.TestCase):
    def test_ebay_connector_graceful_without_token(self) -> None:
        conn = EbayConnector(token="", client_id="", client_secret="")
        self.assertEqual(conn.fetch_offers([{"id": "apple-iphone-13-mini-2021", "brand": "Apple", "model": "iPhone 13 mini"}]), [])

    def test_ebay_connector_exchanges_client_credentials(self) -> None:
        seen_headers: list[dict[str, str]] = []

        def fake_fetch(_url: str, headers: dict[str, str]) -> dict:
            seen_headers.append(headers)
            return {"itemSummaries": []}

        conn = EbayConnector(
            token="",
            client_id="cid",
            client_secret="csec",
            fetcher=fake_fetch,
            token_exchanger=lambda cid, csec: f"fresh-{cid}-{csec}",
        )
        conn.fetch_offers([{"id": "apple-iphone-13-mini-2021", "brand": "Apple", "model": "iPhone 13 mini"}])
        self.assertEqual(seen_headers[0]["Authorization"], "Bearer fresh-cid-csec")

    def test_ebay_connector_normalizes_mock_payload(self) -> None:
        mock_payload = {
            "itemSummaries": [
                {
                    "itemId": "v1|123456|0",
                    "title": "iPhone 13 mini 128GB Nuovo Sigillato",
                    "price": {"value": "610.00", "currency": "EUR"},
                    "itemWebUrl": "https://www.ebay.it/itm/123456",
                },
                {
                    "itemId": "v1|999|0",
                    "title": "Ignored USD listing",
                    "price": {"value": "500.00", "currency": "USD"},
                    "itemWebUrl": "https://www.ebay.com/itm/999",
                },
            ]
        }
        conn = EbayConnector(token="dummy-token", fetcher=lambda _u, _h: mock_payload)
        offers = conn.fetch_offers([{"id": "apple-iphone-13-mini-2021", "brand": "Apple", "model": "iPhone 13 mini"}])
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].offer_id, "ebay:v1_123456_0")
        self.assertEqual(offers[0].price, 610.0)

    def test_eu_connector_disabled_by_default(self) -> None:
        conn = MarketplacesEuConnector(enabled=False)
        self.assertEqual(conn.fetch_offers([]), [])

    def test_community_connector_reads_submissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sub_path = Path(tmp) / "community.json"
            sub_path.write_text(
                json.dumps(
                    {
                        "submissions": [
                            {
                                "external_id": "comm-1",
                                "vintage_id": "google-pixel-5-2020",
                                "url": "https://example.com/pixel5",
                                "title": "Pixel 5 Sigillato",
                                "price": 340,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            conn = CommunityConnector(submissions_path=sub_path)
            offers = conn.fetch_offers([{"id": "google-pixel-5-2020"}])
            self.assertEqual(len(offers), 1)
            self.assertEqual(offers[0].offer_id, "community:comm-1")

    def test_update_vintages_dry_run(self) -> None:
        root = Path(__file__).resolve().parent.parent
        ledger, history = run_update(
            vintages_path=root / "src/data/vintages.json",
            offers_path=root / "src/data/offers.json",
            history_path=root / "src/data/market-history.json",
            run_date="2026-11-22",
            dry_run=True,
        )
        self.assertGreaterEqual(len(ledger["offers"]), 1)
        self.assertIn("apple-iphone-13-mini-2021", history["series"])


if __name__ == "__main__":
    unittest.main()
