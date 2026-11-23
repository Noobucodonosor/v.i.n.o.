# ADR-0003: Persistenza Offerte e Market Tracking Git-Backed

- **Stato:** Proposto (`Proposed`)
- **Priorità:** P1 — Alta
- **Data:** 2026-11-21
- **Autori:** Dany
- **Fonti:** Requisito utente ("accedendo a internet riesce a mantenere persistenti le offerte e a tracciare un mercato"), scelta persistenza Git-backed + multi-fonte (eBay API, marketplace IT/EU, segnalazioni community)

---

## 1. Contesto e Problema

Le inserzioni online di smartphone nuovi mai usati (*New Old Stock / sigillati*) sono effimere: una volta vendute o scadute spariscono dai marketplace. Per trattare gli smartphone come un vero mercato di "annate" (stile vino) e alimentarvi il calcolatore/comparatore, **v.i.n.o.** deve:
1. **Mantenere persistenti le offerte** nel tempo (conservando storico prezzi, stato e durata sul mercato anche dopo la rimozione dell'annuncio).
2. **Tracciare l'andamento del mercato** per ciascuna annata/modello (prezzo mediano, volume, scarsità, delta tra prezzo richiesto e venduto).
3. Operare a **costo zero e senza server dedicati**, restando compatibile con **GitHub Actions + Astro SSG + GitHub Pages**.

---

## 2. Decisione Architetturale

1. **Persistenza Git-Backed nel Repository:**
   - **`src/data/offers.json`**: registro persistente delle singole offerte tracciate. Ogni record è identificato in modo univoco da `id` deterministico (`<source>:<external_id>` o hash URL canonico) e traccia:
     - Metadati annuncio: `vintage_id`, `source` (`ebay` | `subito` | `wallapop` | `vinted` | `community`), `url`, `title`, `condition` (`sealed` | `nos_open_box`), `currency`.
     - Lifecycle: `status` (`active` | `sold` | `expired` | `unverified`), `first_seen`, `last_seen`, `closed_at`.
     - Storico prezzo dell'offerta: `price_history: Array<{ date: string; price: number }>`.
   - **`src/data/market-history.json`**: serie storica aggregata per `vintage_id` (es. snapshot settimanali/giornalieri con `median_asking_price`, `median_sold_price`, `active_count`, `sold_count`, `vintage_market_index`), consumata direttamente da **Astro** a build time.
   - **Nota sui volumi:** finché il dataset resta nell'ordine di qualche migliaio di offerte (<10 MB), Git + JSON garantiscono semplicità e zero costi (rispettando il limite <50 MB del gate CI). Oltre tale soglia, si potrà archiviare lo storico freddo per anno (`src/data/archive/YYYY.json`) o migrare su DB serverless esterno con un ADR successivo.

2. **Architettura a Connettori Modulari (`scripts/connectors/`):**
   - Ogni fonte implementa un'interfaccia comune (`fetch_offers(query_config) -> list[NormalizedOffer]`):
     - **Connettore API ufficiali** (`ebay.py`): usa eBay Browse API (credenziali in GitHub Secrets) per annunci attivi e riferimenti di mercato.
     - **Connettori Marketplace IT/EU** (`subito.py`, `wallapop.py`, `vinted.py`): adapter isolati e disattivabili via config, con rate limiting, timeout brevi e *graceful degradation* (se una fonte blocca o cambia struttura, logga un warning e non blocca le altre né corrompe i dati). Nessun bypass di CAPTCHA o protezioni anti-bot.
     - **Connettore Community** (`community.py`): legge segnalazioni validate (es. da file curati o GitHub Issues approvate) e le arricchisce/normalizza nello stesso formato.

3. **Motore di Lifecycle, Deduplicazione & Aggregazione (`scripts/update_vintages.py`):**
   - Eseguito periodicamente via GitHub Actions (`cron`).
   - Esegue il merge idempotente in `offers.json`: aggiorna `last_seen`, appende un nuovo punto in `price_history` solo se il prezzo è cambiato, marca `expired` le offerte assenti da >N run consecutivi (o `sold` se confermato dalla fonte).
   - Ricalcola `market-history.json` e aggiorna gli indicatori di mercato in `vintages.json`.
   - Valida tutto contro lo schema prima di committare/aprire PR.

---

## 3. Conseguenze

- **Positive:**
  - Storico completo e immutabile (tracciato in Git) dell'evoluzione dei prezzi e della rarità delle annate.
  - Zero costi infrastrutturali (nessun DB esterno da pagare o mantenere).
  - Isolamento dei guasti: se un connettore fallisce, gli altri continuano e i dati storici restano intatti.
- **Trade-off / Vincoli:**
  - Frequenza di aggiornamento legata al cron di GitHub Actions (es. 1–2 volte al giorno, non real-time al secondo).
  - Alcuni marketplace EU possono limitare lo scraping automatizzato; il sistema deve tollerare fonti parziali e valorizzare le API ufficiali + segnalazioni community.

---

## 4. Task Operativi Collegati (con Definition of Done)

- [x] **TASK-MKT-01**: **Schema persistenza offerte (`offers.json`), serie storica (`market-history.json`) e motore di lifecycle/deduplicazione**
  - *File coinvolti*: `src/schemas/offer.ts`, `src/data/offers.json`, `src/data/market-history.json`, `scripts/market_tracker.py`
  - *Acceptance Criteria*: Deduplicazione idempotente per `source:external_id`, aggiornamento `price_history` solo su variazione prezzo, transizione stato `active -> expired/sold` e calcolo aggregati in `market-history.json`.
  - *Verification Step*: `pytest tests/test_market_tracker.py` (o equivalente test unitario su fixture mock)
- [x] **TASK-MKT-02**: **Connettori modulari multi-fonte (eBay API, marketplace IT/EU, community)**
  - *File coinvolti*: `scripts/connectors/base.py`, `scripts/connectors/ebay.py`, `scripts/connectors/marketplaces_eu.py`, `scripts/connectors/community.py`
  - *Acceptance Criteria*: Ogni connettore normalizza l'output nello schema comune, gestisce errori di rete/rate-limit con graceful degradation e rispetta la separazione dei segreti.
  - *Verification Step*: `python3 scripts/update_vintages.py --dry-run`
- [x] **TASK-MKT-03**: **UI Astro per andamento mercato e offerte persistenti per annata**
  - *File coinvolti*: `src/components/MarketChart.astro`, `src/components/OffersLedger.astro`, `src/pages/vintage/[slug].astro`
  - *Acceptance Criteria*: Ogni scheda annata mostra lo storico prezzi aggregato e l'elenco delle offerte tracciate (attive e storiche/chiuse) senza esporre HTML non sanitizzato.
  - *Verification Step*: `npm run build`
