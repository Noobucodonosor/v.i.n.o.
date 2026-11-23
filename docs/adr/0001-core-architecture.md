# ADR-0001: Architettura Core, Stack Tecnologico e Modello Dati/Business (`v.i.n.o.`)

- **Stato:** Proposto (`Proposed`)
- **Priorità:** P1 — Alta (Baseline)
- **Data:** 2026-11-21
- **Autori:** Dany
- **Fonti:** Requisiti iniziali utente ("smartphone nuovi ma mai usati come il vino: esistono buone annate"), scelte stack (Astro + GitHub Pages + GitHub Actions)

---

## 1. Contesto e Problema

Il progetto **v.i.n.o.** nasce dall'intuizione che gli smartphone **nuovi ma mai usati** (*New Old Stock / sigillati*) si comportino come il vino: non tutti gli anni o i modelli invecchiano allo stesso modo, ed esistono "buone annate" con valore collezionistico, tecnico o di usabilità ancora rilevante (es. supporto software, riparabilità, iconografia design, stato chimico atteso della batteria, rarità).

Vincoli tecnici e operativi:
- Il servizio deve girare su **GitHub Pages** (hosting statico gratuito, zero server backend sempre accesi).
- Deve offrire una **web app interattiva** con comparatore e calcolatore del valore "annata" degli smartphone.
- I dati di catalogo e valutazione devono essere **aggiornabili periodicamente in modo automatico** tramite GitHub Actions (scraping/API esterne), mantenendo il sito veloce e deterministico al build time.

---

## 2. Decisione Architetturale

1. **Frontend Statico + Isole Interattive (`Astro` + `TypeScript`):**
   - Utilizzo di **Astro** come generatore di siti statici (SSG) con deploy diretto su **GitHub Pages**.
   - Pagine editoriali/schede "annata" pre-renderizzate a build time (SEO-friendly, zero JS superfluo).
   - Componenti interattivi client-side (Islands) per:
     - **Calcolatore "Annata"**: stima punteggio/indice di valore in base a modello, anno di uscita, stato sigillo/confezione, batteria/degrado atteso e rarità.
     - **Comparatore**: confronto affiancato tra 2 o più smartphone/annate (specifiche chiave, indice "annata", pro/contro di conservazione).
2. **Modello Dati Statico (`src/data/vintages.json`):**
   - Dataset strutturato in JSON versionato nel repository (es. `brand`, `model`, `release_year`, `vintage_score`, `tasting_notes`, `collectibility`, `repairability`, `battery_risk`, `estimated_value_range`, `last_updated`).
   - Validazione rigorosa dello schema (es. Zod) sia in fase di aggiornamento dati che di build Astro.
3. **Aggiornamento Periodico Dati (`GitHub Actions`):**
   - Workflow schedulato (cron) che esegue uno script di raccolta/aggiornamento (da API/fonti pubbliche autorizzate), valida il JSON risultante e committa/apre PR solo se ci sono variazioni valide.
   - Rebuild e deploy automatico su GitHub Pages ad ogni push su `main` o aggiornamento del dataset.

---

## 3. Conseguenze

- **Positive:**
  - Costi di hosting nulli (GitHub Pages + GitHub Actions su repo pubblico/standard).
  - Prestazioni elevate e sicurezza intrinseca (nessun database esposto o server da mantenere).
  - Architettura modulare: logica di calcolo del punteggio "annata" testabile in isolamento con unit test.
- **Trade-off / Vincoli:**
  - Nessuna persistenza lato server per dati utente (eventuali preferiti/confronti restano in `localStorage` o URL query params).
  - Gli script di aggiornamento dati in GitHub Actions devono gestire rate limit, errori di rete e fallback senza corrompere il dataset esistente.

---

## 4. Task Operativi Collegati (con Definition of Done)

- [x] **TASK-CORE-01**: **Inizializzazione progetto Astro + TypeScript e deploy GitHub Pages**
  - *File coinvolti*: `package.json`, `astro.config.mjs`, `tsconfig.json`, `.github/workflows/deploy-pages.yml`
  - *Acceptance Criteria*: Il progetto Astro si avvia in locale e genera la build statica in `dist/`; il workflow GitHub Actions pubblica correttamente su GitHub Pages.
  - *Verification Step*: `npm run build`
- [x] **TASK-CORE-02**: **Definizione schema dati "Annate" (`vintages.json`) e dataset iniziale**
  - *File coinvolti*: `src/schemas/vintage.ts`, `src/data/vintages.json`
  - *Acceptance Criteria*: Schema validato con Zod (o equivalente) con almeno 5-10 modelli rappresentativi di diverse annate e campi per note di "degustazione" e fattori di rischio/valore.
  - *Verification Step*: `npm test` (validazione schema sul dataset)
- [x] **TASK-CORE-03**: **Sviluppo Calcolatore e Comparatore di "Annate" interattivo**
  - *File coinvolti*: `src/components/VintageCalculator.astro` (o Island TS/React/Preact), `src/components/VintageComparator.astro`, `src/lib/scoring.ts`
  - *Acceptance Criteria*: L'utente può calcolare il punteggio di un'annata selezionando modello/condizioni e confrontare almeno 2 smartphone fianco a fianco; la funzione di scoring è coperta da unit test.
  - *Verification Step*: `npm test && npm run build`
- [x] **TASK-DATA-01**: **Pipeline GitHub Actions per aggiornamento periodico dati statici**
  - *File coinvolti*: `scripts/update_vintages.py` (o `.ts`), `.github/workflows/update-data.yml`
  - *Acceptance Criteria*: Lo script aggiorna o arricchisce i dati in modo idempotente, valida lo schema prima di salvare e non sovrascrive con dati vuoti/corrotti in caso di errore API.
  - *Verification Step*: `python3 scripts/update_vintages.py --dry-run` (o equivalente comando di test)
