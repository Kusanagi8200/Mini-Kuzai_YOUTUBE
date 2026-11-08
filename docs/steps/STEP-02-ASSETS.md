# STEP-02 - Assets

Status --> **IN PROGRESS**

## Objective

Install and validate the fixed Short assets and freeze the visual layout before renderer implementation.

## Master background

Canonical repository asset:

`assets/backgrounds/mini-kuzai-short-master.png`

GOGIT report `STEP-02-BACKGROUND-VERIFY-001` --> **PASS**

Verified on fhc2:
- format --> PNG
- resolution --> 1080 x 1920
- aspect ratio --> 9:16
- mode --> RGB
- file size --> 2,445,180 bytes
- SHA-256 --> `05ad423e88d17d4ff655d61dd7659594242546b2280ebcdf7a172a86ccc6f13d`
- Git blob --> `6b40e546b3d0d68840c23c8f30d0faf9fba04076`
- Git blob match --> PASS

Visual specification:
- fixed THE KUZ NETWORK logo
- fixed Mini-Kuzai character
- fixed Mini-KuzAI From Scratch branding
- no embedded Vxx number
- no embedded step-specific metric or conclusion

## Video 001 overlays

The first video is a **channel introduction** and does not display a Vxx reference.

Internal reference:

`VIDEO-001-CHANNEL-INTRO`

Its overlays will introduce:
- THE KUZ NETWORK
- Mini-Kuzai
- LLM FROM SCRATCH
- project/channel objective
- future development-flow video series

## Later DEV-FLOW overlays

Step-specific videos will add automatically:
- `Vxx`
- `FLOW Vxx OK`
- step title
- main metric or result
- short conclusion
- `DEV FLOW #xxx`

Coordinates and safe zones still need to be frozen.

## Music

Background music is not selected yet.

Requirements:
- YouTube-compatible usage rights
- source/license documented
- suitable for low-volume mixing below Piper narration

Target repository path:

`assets/music/`

## Font

GOGIT report `STEP-02-FONT-SELECTION-001` --> **PASS**

Selected renderer font:
- family --> `Ubuntu Sans`
- style --> `Bold`
- fontconfig pattern --> `Ubuntu Sans:style=Bold`
- path --> `/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf`

No additional font package is required.

## Runtime prerequisite

GOGIT report `STEP-02-FFMPEG-INSTALL-001` --> **PASS**

Verified:
- FFmpeg --> `/usr/bin/ffmpeg`
- ffprobe --> `/usr/bin/ffprobe`
- FFmpeg version --> `6.1.1-3ubuntu5`
- ffprobe version --> `6.1.1-3ubuntu5`

## Exit criteria

- master background present and verified --> **DONE**
- font selected and validated --> **DONE**
- music asset selected and license/source recorded
- safe zones / overlay coordinates frozen
- FFmpeg and ffprobe available --> **DONE**
