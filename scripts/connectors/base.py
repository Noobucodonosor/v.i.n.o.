"""Interfaccia base e helper HTTP condivisi per i connettori di mercato."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scripts.market_tracker import NormalizedOffer

USER_AGENT = "v.i.n.o.-market-tracker/1.0 (+https://github.com/Noobucodonosor/v.i.n.o.)"


class ConnectorError(RuntimeError):
    """Errore controllato durante il fetch da una fonte esterna."""


class BaseConnector(ABC):
    """Contratto comune per tutti i connettori di offerte."""

    name: str

    @abstractmethod
    def fetch_offers(self, vintages: list[dict[str, Any]]) -> list[NormalizedOffer]:
        """Recupera e normalizza le offerte per le annate configurate."""


def fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
    timeout_s: float = 8.0,
) -> dict[str, Any]:
    """Esegue una GET JSON con timeout e User-Agent trasparente."""
    req_headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = Request(url, headers=req_headers, method="GET")
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ConnectorError(f"Errore fetch {url}: {exc}") from exc
