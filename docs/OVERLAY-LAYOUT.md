# `Overlay layout`

## `Purpose`

Freeze the dynamic text geometry for the 1080 x 1920 Mini-Kuzai YouTube master background before renderer implementation.

This is a **project-defined conservative layout**, not a claim that YouTube guarantees fixed UI pixel positions.

## `Design principle`

Dynamic information is displayed sequentially in one compact panel in the upper-right area.

This intentionally avoids:
- the fixed THE KUZ NETWORK logo in the upper-left
- the Mini-Kuzai character in the center
- the fixed "Mini-KuzAI From Scratch" branding
- the conservative right-side Shorts interaction strip
- the conservative bottom Shorts metadata / navigation strip

The renderer must not scatter essential text across the frame.

## `Canvas`

- width --> 1080 px
- height --> 1920 px
- origin --> top-left
- coordinates --> pixels

## `Reserved zones`

| Zone | X | Y | Width | Height |
| --- | ---: | ---: | ---: | ---: |
| Fixed logo | 40 | 60 | 260 | 280 |
| Character protection | 220 | 340 | 620 | 900 |
| Fixed branding | 120 | 1260 | 840 | 240 |
| Conservative Shorts right UI | 900 | 300 | 180 | 1200 |
| Conservative Shorts bottom UI | 0 | 1500 | 1080 | 420 |

## `Dynamic zones`

| Zone | X | Y | Width | Height |
| --- | ---: | ---: | ---: | ---: |
| Primary panel | 310 | 100 | 570 | 240 |
| Vxx / status badge | 740 | 110 | 130 | 60 |
| Headline | 330 | 170 | 520 | 80 |
| Body / metric | 330 | 250 | 520 | 80 |

All essential dynamic overlays reuse this same upper-right region over time.

## `Typography`

- family --> `Ubuntu Sans`
- style --> `Bold`
- badge --> 42 px
- headline --> 54 px
- body --> 38 px
- alignment --> right
- headline --> maximum 2 lines
- body --> maximum 2 lines

## `Panel style`

- background --> black at 58% opacity
- border --> neutral light gray at 55% opacity
- text --> `#F2F2F2`
- internal padding --> 20 px

The panel is intentionally neutral and monochrome so that the fixed background remains the visual identity.

## `VIDEO-001 use`

The introduction video has no Vxx badge.

The same panel is reused sequentially for:
- THE KUZ NETWORK
- Mini-Kuzai
- LLM FROM SCRATCH
- channel objective
- future validated development milestones

## `DEV-FLOW use`

Later videos reuse the same geometry sequentially for:
- Vxx / FLOW Vxx OK
- step title
- main metric or result
- short conclusion
- DEV FLOW reference

## `Canonical configuration`

Renderer-readable coordinates are stored in:

`config/overlay-layout.json`

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
