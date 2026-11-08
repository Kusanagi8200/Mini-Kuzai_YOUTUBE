# `Overlay layout`

## `Purpose`

Freeze the canonical text layout rules for Mini-Kuzai YouTube Shorts.

These rules apply to:

- VIDEO-001 channel introduction
- all future Mini-Kuzai DEV-FLOW videos

## `Canonical version`

Current canonical layout --> **V8**

V8 was introduced after real YouTube Shorts player validation showed that the lower player title/handle overlays could hide project text.

## `Global style constraints`

- font --> `Anta`
- fallback --> `Ubuntu Sans Bold`
- square-corner backgrounds
- dynamic text --> white on black
- GitHub footer --> white on black
- dynamic information remains centered horizontally
- permanent branding remains outside the central step-information area

## `Permanent top-right branding`

Mandatory:

- `THE KUZ NETWORK`
- `KUZAI.ORG` directly below
- white text on black background
- right-aligned
- positioned in the top-right corner

## `Dynamic information area`

Canonical V8 positions:

- badge top --> `1510 px`
- headline top --> `1555 px`
- body top --> `1630 px`

The dynamic information block is intentionally raised compared with V6 so the YouTube player overlays do not cover the step information.

These positions are frozen for future videos unless real YouTube UI validation requires another safe-zone correction.

## `GitHub footer safe zone`

Permanent text:

`GITHUB.COM/KUSANAGI8200`

Canonical V8 placement:

- right aligned
- right coordinate --> `1077 px`
- top coordinate --> `1748 px`
- text --> white
- background --> black
- font --> Anta
- font size --> `28 px`

The footer is intentionally placed approximately at the vertical level of the YouTube channel-handle overlay.

It must not be placed against the physical bottom edge of the 1080 x 1920 frame because YouTube overlays the Short title and player information in that area.

This safe-zone rule applies to all future videos.

## `Canonical configuration`

Renderer configuration:

- `config/overlay-layout.json`

Renderer:

- `app/render_short.py`

Font:

- `assets/fonts/Anta-Regular.ttf`

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
