# `Overlay layout`

## `Purpose`

Freeze the dynamic text geometry for the 1080 x 1920 Mini-Kuzai YouTube master background.

## `Design principle V2`

Dynamic text is displayed sequentially in the **footer area**, horizontally centered.

The renderer uses:
- no surrounding frame
- no panel background
- white text
- black text stroke for contrast
- centered alignment

This rule applies to:
- VIDEO-001 channel introduction
- all future Mini-Kuzai DEV-FLOW videos

## `Canvas`

- width --> 1080 px
- height --> 1920 px
- origin --> top-left
- coordinates --> pixels

## `Dynamic footer zones`

| Zone | X | Y | Width | Height |
| --- | ---: | ---: | ---: | ---: |
| Footer working area | 70 | 1510 | 940 | 270 |
| Badge / Vxx | 120 | 1515 | 840 | 45 |
| Headline | 80 | 1570 | 920 | 90 |
| Body / metric | 80 | 1665 | 920 | 80 |

## `Typography`

- family --> `Ubuntu Sans`
- style --> `Bold`
- badge --> 34 px
- headline --> 58 px
- body --> 40 px
- alignment --> center
- stroke --> 4 px black
- frame --> none

## `Canonical configuration`

`config/overlay-layout.json`

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
