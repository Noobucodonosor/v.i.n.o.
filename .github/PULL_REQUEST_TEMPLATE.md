## Contesto & Riferimenti
- **Task / Issue:** `closes #<NUMERO_ISSUE>` (oppure `TASK-<MODULO>-XX`)
- **ADR di riferimento:** `docs/adr/NNNN-...md` (se applicabile)
- **Modalità flusso:**
  - [ ] **Ask** (`P0-critical`, sicurezza, pagamenti, modifiche a `docs/adr/` o `AGENTS.md` — richiede review umana bloccante)
  - [ ] **Show** (`P1-high` / `P2-medium`, modifiche circoscritte e coperte da test automatici)

## Cosa cambia (in sintesi)
- 

## Verification Step & Quality Gate
- [ ] Ho ispezionato il diff della PR (`gh pr diff`) verificando che non ci siano duplicazioni o codice morto.
- [ ] I test verificano il **comportamento e gli edge case** sul diff (non solo la % di coverage).
- [ ] Nessun file > 50 MB, `.env`, database locale o segreto incluso nel commit.
- [ ] `pre_release_check.py` eseguito con esito positivo.

**Output / Comando di verifica eseguito:**
```bash
# es. pytest -q / npm test
```
