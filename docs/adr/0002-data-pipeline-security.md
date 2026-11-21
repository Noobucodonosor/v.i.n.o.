# ADR-0002: Sicurezza Pipeline Dati, Validazione Input e Hardening GitHub Pages

- **Stato:** Proposto (`Proposed`)
- **Priorità:** P0 — Critica
- **Data:** 2026-11-21
- **Autori:** Dany
- **Fonti:** Requisiti di sicurezza metodologia ADR + pipeline GitHub Actions per dati esterni

---

## 1. Contesto e Problema

Il progetto **v.i.n.o.** combina una web app statica su GitHub Pages con una pipeline GitHub Actions che recupera/aggiorna dati da fonti esterne (API o scraping). I principali rischi `P0-critical` sono:
1. **Esposizione di segreti** (eventuali API key nei workflow o nel bundle client Astro).
2. **Data poisoning / corruzione del build**: dati malformati o inattesi provenienti da fonti esterne potrebbero rompere la build o iniettare markup/HTML non sanitizzato nella UI.
3. **Permessi eccessivi nei workflow GitHub Actions** (`GITHUB_TOKEN` con permessi troppo ampi).

---

## 2. Decisione Architetturale

1. **Separazione netta Build vs Segreti:**
   - Nessuna chiave API privata deve mai finire in variabili `PUBLIC_*` di Astro o nel bundle client.
   - Eventuali chiavi per script di raccolta dati vivono esclusivamente nei **GitHub Repository Secrets** e vengono usate solo dal workflow `update-data.yml`.
2. **Validazione Schema & Sanitizzazione Dati:**
   - Ogni aggiornamento automatico in `src/data/vintages.json` deve superare la validazione dello schema (tipi, range numerici, lunghezze stringhe, assenza di HTML raw) prima del commit/PR.
   - Rendering sicuro in Astro (niente `set:html` su dati provenienti da fonti esterne).
3. **Principio del Minimo Privilegio su GitHub Actions:**
   - Ogni workflow dichiara esplicitamente `permissions:` minime (`contents: read` per build, `contents: write` / `pull-requests: write` solo dove strettamente necessario).
   - Controllo automatico tramite `.github/workflows/adr-pre-release.yml` e `pre_release_check.py`.

---

## 3. Conseguenze

- **Positive:**
  - Prevenzione di leak di credenziali lato client e su Git.
  - Resilienza del sito statico anche se una fonte dati esterna diventa temporaneamente non disponibile o restituisce payload anomali.
- **Trade-off / Vincoli:**
  - Ogni modifica a workflow GitHub Actions, schema di validazione o regole di sicurezza richiede review umana (`Ask`).

---

## 4. Task Operativi Collegati (con Definition of Done)

- [ ] **TASK-SEC-01**: **Hardening validazione dati esterni, sanitizzazione UI e permessi GitHub Actions**
  - *File coinvolti*: `.github/workflows/update-data.yml`, `.github/workflows/deploy-pages.yml`, `src/schemas/vintage.ts`
  - *Acceptance Criteria*: Tutti i workflow hanno `permissions` minime esplicite; lo schema rifiuta payload malformati o stringhe con HTML/script; nessun segreto è esposto nel bundle `dist/`.
  - *Verification Step*: `python3 ~/.gemini/config/skills/adr-github-methodology/scripts/pre_release_check.py && npm run build`
