# `DEV-FLOW Short briefs`

This directory contains canonical Short briefs for verified Mini-Kuzai FINAL-DEV-FLOW steps.

Rules:

- filename --> `Vxx-final.json`
- one brief per FINAL step
- brief must validate against `config/dev-flow-short-brief.schema.json`
- matching Mini-Kuzai FINAL receipt must already exist with `PUBLISHED` status
- matching FINAL request and immutable GOGIT report are validated before rendering
- the YouTube worker is independent from Mini-Kuzai and KUZ-DIN
- current worker mode --> `PUBLIC_UPLOAD`
- current publication mode --> public
- duplicate or conflicting processing is blocked by local journal state
- exactly one public upload is allowed per immutable brief/media SHA256
- YouTube failure never invalidates the Mini-Kuzai scientific FINAL

The local worker journal remains outside Git under:

`/root/.local/state/mini-kuzai-youtube/dev-flow-short-worker.json`

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**


## `Current orchestration gap`

The renderer, audit and YouTube publication path are validated.

For V81+, the remaining automation task is to create the canonical `Vxx-final.json` brief automatically from a genuine committed FINAL receipt + immutable scientific GOGIT evidence. Until that orchestration exists, brief authoring remains an explicit preparation step.

`FLOW-PRESENTATION-001` validated downstream media publication but is not a DEV-FLOW scientific brief.
