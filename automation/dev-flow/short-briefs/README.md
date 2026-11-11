# `DEV-FLOW Short briefs`

This directory contains canonical Short briefs for verified Mini-Kuzai FINAL-DEV-FLOW steps.

Rules:

- filename --> `Vxx-final.json`
- one brief per FINAL step
- brief must validate against `config/dev-flow-short-brief.schema.json`
- matching Mini-Kuzai FINAL receipt must already exist with `PUBLISHED` status
- matching FINAL request and immutable GOGIT report are validated before rendering
- the YouTube worker is independent from Mini-Kuzai and KUZ-DIN
- current worker mode --> `DRY_RUN_ONLY`
- current publication mode --> disabled
- duplicate or conflicting processing is blocked by local journal state

The local worker journal remains outside Git under:

`/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json`

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
