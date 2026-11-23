# DESIGN.md — Contratto UI & Architettura di Sottrazione (`v.i.n.o.`)

> Per ogni intervento UI, rispetta questo contratto e compila il Registro delle Esclusioni prima di scrivere codice.

## 1. Banned Tokens (Lista Piatta)
- Nessun gradient su testo o bottoni primari.
- Nessuna card annidata dentro un'altra card ("cardocalypse").
- Nessuna etichetta `ALL CAPS` puramente decorativa.
- Nessun nome interno di file, schema o score grezzo non contestualizzato visibile a riposo.
- Nessun puntino pulsante o animazione decorativa continua.
- Nessuna azione secondaria con lo stesso peso visivo della CTA primaria.
- Nessuna navigazione primaria nascosta dietro menu hamburger su desktop (>840 px).
- Nessun bottom sheet impilato sopra un altro bottom sheet su mobile.

## 2. Palette e Contrasto
- **Mandato**: Usa esclusivamente i token esadecimali definiti in `:root` (`--bg: #faf7f2`, `--surface: #ffffff`, `--ink: #1e1915`, `--muted: #6b5f55`, `--accent: #722f37`, `--border: #e5ddd3`, più `--alert` solo per rischi batteria/errori), garantendo contrasto >= 4,5:1 per testo normale e >= 3:1 per testo grande e componenti UI (WCAG 2.2 AA).
- **Confine**: Vietati colori hardcoded fuori token e informazioni affidate al solo colore senza testo o forma.

## 3. Scala Tipografica
- **Mandato**: Adotta al massimo due famiglie tipografiche coerenti con il dominio editoriale/enologico (`system-ui` o coppia serif/sans intenzionale), assegnando ruoli netti a valore primario, intestazioni, corpo e metadati per una scansione immediata.
- **Confine**: Vietati font di fallback generici non intenzionali (es. Inter/Space Grotesk usati per inerzia) e titoli con una sola parola in corsivo serif usata come accento decorativo.

## 4. Spaziatura, Ritmo e Target Touch
- **Mandato**: Costruisci padding e gap sulla griglia da `8 px` (mezzi passi da `4 px` solo in componenti densi), riducendo la distanza dentro le coppie etichetta-valore e aumentandola tra sezioni distinte; imposta target mobile (`<select>`, link, bottoni) a `>= 44×44 px` con `@media (pointer: coarse)`.
- **Confine**: Vietata spaziatura uniforme monotona e target interattivi `< 24×24 CSS px` (SC 2.5.8).

## 5. Pattern Componenti, Above-the-Fold e Progressive Disclosure
- **Mandato**: Mostra a riposo esattamente `1` vista protagonista (Calcolatore Annata), al massimo `3` metriche primarie leggibili in 2 secondi (Punteggio + Grado, Valore Stimato, Rischio Batteria), `1` azione/controllo primario e `1` segnale sobrio di freschezza dati; colloca Comparatore esteso, Catalogo completo, Storico Mercato e Registro Offerte in viste dedicate o progressive disclosure (`< 3` livelli) dietro trigger ad alto *information scent*.
- **Confine**: Vietati pannelli secondari o tabelle dense che spingono il risultato del calcolatore sotto il fold su `1366×768` o `360×800`.

## 6. Voce, Copy e Sintesi Dati
- **Mandato**: Usa forma attiva dal punto di vista dell'utente e sintetizza i campi correlati in frasi verbali-numeriche compatte (es. `"Gran Riserva 94/100 · €480–€690 · Rischio batteria medio"`), promuovendo automaticamente avvisi critici (scarica profonda batteria o dati non aggiornati).
- **Confine**: Vietata la mappatura 1:1 di payload JSON in badge separati, i claim promozionali generici e i messaggi di errore vaghi.

---

## 7. Registro Obbligatorio delle Esclusioni (Pre-Codice)

| Dato / Funzionalità | Decisione UI | Motivazione UX (modello mentale / budget) | Destinazione & Trigger (Information Scent) | Eccezione di sicurezza (promozione automatica) |
| :--- | :--- | :--- | :--- | :--- |
| Metriche secondarie (`collectibility`, `repairability`, `software_longevity`) | Escluso a riposo → Progressive Disclosure | Sforerebbe il budget above-the-fold (`<= 3` metriche). | Scheda annata `/vintage/[slug]/` + sezione `"Confronta due annate"` | Nessuna |
| Campi `price_history`, `first_seen`, `last_seen`, `missed_runs` | Accorpato / Nascosto | Evita mappatura 1:1 del JSON `offers.json`. | Tabella `"Registro Offerte Persistenti"` in `/vintage/[slug]/` | Segnala se `updated_at` è obsoleto |
| Formula moltiplicatori interni (`seal.priceFactor`, `multiplier`) | Eliminato dalla vista utente | Gergo di implementazione privo di valore decisionale diretto. | Solo codice `src/lib/scoring.ts` e test | Nessuna |
| Avviso scarica profonda batteria su annate vecchie/calde | Promosso a riposo | Rischio fisico/economico su dispositivi sigillati New Old Stock. | Riga avviso dentro il risultato del Calcolatore | Sempre visibile quando `battery_risk === "Alto"` o `storageEnv === "warm"` |
