# `Overlay layout`

## `Purpose`

Freeze the text layout rules for Mini-Kuzai YouTube Shorts.

These rules now apply to:
- VIDEO-001 channel introduction
- all future Mini-Kuzai DEV-FLOW videos

## `Global style constraints`

- all text blocks are horizontally centered
- all text blocks use square-corner backgrounds
- title block --> black text on white background
- dynamic text blocks --> white text on black background
- GitHub footer --> white text on black background
- padding --> 2 px horizontal on each side
- typography --> prefer `ANTA` when available
- fallback typography --> `Ubuntu Sans Bold`

## `Text blocks order`

From top to bottom in the footer zone:
- static title --> `THE KUZ NETWORK`
- optional badge --> usually `Vxx` or status
- dynamic headline
- dynamic body
- static GitHub footer --> `GITHUB.COM/KUSANAGI8200`

## `Permanent top-right branding`

Mandatory for VIDEO-001 and all future Mini-Kuzai videos:

- `THE KUZ NETWORK` --> white text on black square-corner background
- `KUZAI.ORG` --> white text on black square-corner background
- `KUZAI.ORG` is displayed directly below `THE KUZ NETWORK`
- both blocks are right-aligned in the top-right corner
- background width follows text width with 1 px horizontal padding on each side
- branding must remain outside the central step-information area
- central space is reserved for current and future development-step information
- font preference --> `Anta`
- fallback --> `Ubuntu Sans Bold`

## `Canonical configuration`

Renderer configuration:
- `config/overlay-layout.json`

Renderer code:
- `app/render_short.py`

If `assets/fonts/Anta-Regular.ttf` exists, it is used first.
If not, the renderer tries system fontconfig match for `Anta`.
If `Anta` is unavailable, the renderer falls back to `Ubuntu Sans Bold`.

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
