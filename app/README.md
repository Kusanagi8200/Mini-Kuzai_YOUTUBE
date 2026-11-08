# `Application code`

## `Current implementation`

STEP-03 renderer --> **COMPLETED**:

`app/render_short.py`

The renderer:
- reads the canonical 1080 x 1920 background
- reads `config/overlay-layout.json`
- reads a structured timeline JSON
- resolves Ubuntu Sans Bold through fontconfig
- renders dynamic overlay states with Pillow
- assembles the states with FFmpeg
- produces a deterministic 60-second H.264 / yuv420p MP4
- intentionally produces no audio during STEP-03

Renderer test timeline:

`config/video001-intro-render-test.json`

Output validation:

`tools/audits/step03_renderer_check.py`

## `STEP-04 audio implementation`

Completed components:
- `app/generate_narration.py`
- `app/mix_audio.py`
- Piper narration generation
- background music mix
- final AAC mux
- final media validation

## `Current STEP-05 work`

- YouTube Data API v3 integration
- OAuth authorization outside Git
- authenticated channel verification
- PRIVATE first upload
- publication journal and idempotence

## `Planned modules`

- structured final Short brief builder
- final media validation
- YouTube uploader
- publication journal and idempotence

Generated media remains under `work/` and outside Git.

[Back to project README](../README.md)

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
