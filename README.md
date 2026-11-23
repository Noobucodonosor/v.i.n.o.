# v.i.n.o. — Annate Smartphone New Old Stock & Market Tracker

**Live su GitHub Pages:** [https://noobucodonosor.github.io/v.i.n.o./](https://noobucodonosor.github.io/v.i.n.o./)

**v.i.n.o.** parte da una tesi semplice: gli smartphone nuovi mai usati (*New Old Stock*) sono come il vino — esistono **buone annate** in cui il rapporto tra hardware di fascia alta, riparabilità, supporto software e prezzo di mercato reale raggiunge un punto di equilibrio irripetibile.

Applicazione statica **Astro + TypeScript + Zod** con persistenza **Git-backed** delle serie storiche di mercato e pipeline automatiche GitHub Actions, sviluppata con metodologia **ADR-Driven** (`3 ADR`, `8 Issue` completate).

## Funzionalità Principali
- **Calcolatore & Comparatore di Annate (`VintageCalculator.astro`, `src/lib/scoring.ts`):** valuta e confronta smartphone NOS su punteggi deterministici e trasparenti.
- **Market Tracker Git-Backed (`ADR-0003`):** persistenza strutturata in `src/data/offers.json`, `market-history.json` e `vintages.json` con deduplicazione, lifecycle offerte e connettori modulari (`scripts/connectors/`).
- **Validazione Rigida & Sicurezza (`ADR-0002`):** validazione schema **Zod** in TypeScript, sanitizzazione UI e workflow GitHub Actions a privilegi minimi.
- **Zero-Cost Hosting:** build statico **Astro SSG** pubblicato automaticamente su GitHub Pages.

## Stack Tecnologico
- **Frontend & SSG:** Astro 7, TypeScript 7, Zod 4
- **Automazione & Dati:** Python (market tracker & connettori), GitHub Actions (cron aggiornamento dati & deploy Pages)
- **Architettura & Governance:** 3 Architecture Decision Records in [`docs/adr/README.md`](./docs/adr/README.md)

## Avvio Locale e Test
```bash
npm install
npm test        # tsc --noEmit + node --test tests/*.test.ts
npm run dev     # server locale Astro
npm run build   # build statico produzione
```

## Licenza
Rilasciato sotto licenza [MIT](./LICENSE).
