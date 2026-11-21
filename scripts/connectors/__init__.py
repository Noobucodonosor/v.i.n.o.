"""Connettori modulari multi-fonte per v.i.n.o. (ADR-0003)."""

from scripts.connectors.base import BaseConnector
from scripts.connectors.community import CommunityConnector
from scripts.connectors.ebay import EbayConnector
from scripts.connectors.marketplaces_eu import MarketplacesEuConnector

__all__ = [
    "BaseConnector",
    "CommunityConnector",
    "EbayConnector",
    "MarketplacesEuConnector",
]
