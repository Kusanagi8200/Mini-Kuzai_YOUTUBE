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


## `Current orchestration state`

Automatic brief generation is active for V81+.

The worker derives `Vxx-final.json` only from a genuine committed FINAL receipt plus immutable scientific GOGIT evidence, validates the generated brief, commits it, and stops before the next bounded media transaction.

V81 verified this path in production. Its brief was generated automatically, validated, rendered into a 60-second Short, published to YouTube, handed to LinkedIn as native video, referenced from the canonical GitHub Discussion, and closed with a committed cross-channel receipt.

A failed automatic brief commit must restore the repository to the pre-generation commit so the polling timer cannot remain wedged on a staged file.

`FLOW-PRESENTATION-001` remains a historical non-scientific integration test and is not DEV-FLOW scientific evidence.
