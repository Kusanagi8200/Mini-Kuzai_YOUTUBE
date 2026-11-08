# `STEP-03 - Renderer`

Status --> **COMPLETED**

## `Objective`

Implement and validate the deterministic Python + FFmpeg vertical video renderer.

The renderer handles the visual stream only. Piper narration and final music/voice mixing remain STEP-04 responsibilities.

## `Implemented components`

- renderer --> `app/render_short.py`
- frozen overlay layout --> `config/overlay-layout.json`
- VIDEO-001 renderer test timeline --> `config/video001-intro-render-test.json`
- ffprobe output validator --> `tools/audits/step03_renderer_check.py`

## `Renderer contract`

- canvas --> 1080 x 1920
- aspect ratio --> 9:16
- duration --> exactly 60 seconds
- frame rate --> 30 fps
- video codec --> H.264
- pixel format --> yuv420p
- fixed background --> `assets/backgrounds/mini-kuzai-short-master.png`
- font --> Ubuntu Sans Bold resolved through fontconfig
- dynamic overlays --> frozen upper-right panel
- generated render files --> `work/`
- generated render files --> outside Git
- STEP-03 output --> video only, no audio stream

## `VIDEO-001 renderer test`

The renderer test uses five sequential 12-second visual states:

1. THE KUZ NETWORK
2. MINI-KUZAI
3. BUILT FROM ZERO
4. OPEN DEVELOPMENT
5. FOLLOW THE BUILD

This is a technical renderer test, not the final VIDEO-001 editorial script.

## `Validation`

The STEP-03 audit checks:

- output file exists
- codec --> H.264
- width --> 1080
- height --> 1920
- pixel format --> yuv420p
- duration --> 60,000 ms with maximum 100 ms tolerance
- audio streams --> 0

## `Verified result`

GOGIT report `STEP-03-RENDERER-VERIFY-001` --> **PASS**

Verified on fhc2:
- codec --> H.264
- width --> 1080
- height --> 1920
- pixel format --> yuv420p
- frame rate --> 30 fps
- duration --> 60.000 s
- audio streams --> 0
- ffprobe --> PASS

## `Closure`

STEP-03 --> **COMPLETED**

Next --> [STEP-04 - Piper narration and audio](STEP-04-PIPER-AUDIO.md)

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
