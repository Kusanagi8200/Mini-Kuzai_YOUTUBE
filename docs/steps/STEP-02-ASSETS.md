# `STEP-02 - Assets`

Status --> **COMPLETED**

## `Objective`

Install and validate the fixed Short assets and freeze the visual layout before renderer implementation.

## `Master background`

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

## `Fixed video duration`

All videos are exactly **60 seconds**.

This applies to:
- `VIDEO-001-CHANNEL-INTRO`
- all future Mini-Kuzai DEV-FLOW Shorts

Narration, overlays and audio mixing must fit inside this fixed 60-second timeline.

## `Video 001 overlays`

The first video is a **channel introduction** and does not display a Vxx reference.

Internal reference:

`VIDEO-001-CHANNEL-INTRO`

Its overlays will introduce:
- THE KUZ NETWORK
- Mini-Kuzai
- LLM FROM SCRATCH
- project/channel objective
- future development-flow video series

## `Later DEV-FLOW overlays`

Step-specific videos will add automatically:
- `Vxx`
- `FLOW Vxx OK`
- step title
- main metric or result
- short conclusion
- `DEV FLOW #xxx`

GOGIT report `STEP-02-OVERLAY-LAYOUT-VERIFY-001` --> **PASS**

Frozen layout:
- canvas --> 1080 x 1920
- primary dynamic panel --> x=310, y=100, width=570, height=240
- all dynamic child zones contained in primary panel --> PASS
- all zones inside canvas --> PASS
- primary panel clear of reserved logo, character, branding and conservative Shorts UI zones --> PASS

Canonical configuration --> `config/overlay-layout.json`

Documentation --> `docs/OVERLAY-LAYOUT.md`

## `Music`

Selected style:
- dark cyberpunk industrial ambient
- no drums or percussion
- heavy bass pads and sub-bass drones
- slow analog bass movement
- electrical / machine / server-room textures
- sparse enough to preserve spoken narration intelligibility

Canonical filename:

`assets/music/kuzai-dark-cyberpunk-background-60s.wav`

If only MP3 is available from the source, use:

`assets/music/kuzai-dark-cyberpunk-background-60s.mp3`

GOGIT report `STEP-02-MUSIC-WAV-VERIFY-001` --> **PASS**

Verified on fhc2:
- canonical file --> `assets/music/kuzai-dark-cyberpunk-background-60s.wav`
- format --> WAV
- codec --> `pcm_s32le`
- sample rate --> 48000 Hz
- channels --> 2
- bits per sample --> 32
- duration --> 60.000 s
- file size --> 23,040,378 bytes
- SHA-256 --> `e73c66f523290613cfe1ad513174803a1a6b07041a6211ddfbafe3a8e9d604bd`
- Git blob --> `a756651fdae861cda8aeb247a7f81cbf84fa697f`
- Git blob match --> PASS

Source --> track created by the project operator for THE KUZ NETWORK using Suno.

Usage --> **NON-COMMERCIAL**.

Usage policy --> `docs/SUNO-RIGHTS.md`.

If future monetization or another commercial use is enabled, rights must be reviewed again before publication.

Mixing requirement --> keep music below Piper narration.

## `Font`

GOGIT report `STEP-02-FONT-SELECTION-001` --> **PASS**

Selected renderer font:
- family --> `Ubuntu Sans`
- style --> `Bold`
- fontconfig pattern --> `Ubuntu Sans:style=Bold`
- path --> `/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf`

No additional font package is required.

## `Runtime prerequisite`

GOGIT report `STEP-02-FFMPEG-INSTALL-001` --> **PASS**

Verified:
- FFmpeg --> `/usr/bin/ffmpeg`
- ffprobe --> `/usr/bin/ffprobe`
- FFmpeg version --> `6.1.1-3ubuntu5`
- ffprobe version --> `6.1.1-3ubuntu5`

## `Exit criteria`

- master background present and verified --> **DONE**
- font selected and validated --> **DONE**
- music asset present and technically validated --> **DONE**
- music source recorded --> **DONE**
- non-commercial usage policy documented --> **DONE**
- safe zones / overlay coordinates frozen --> **DONE**
- fixed duration --> **60 seconds**
- FFmpeg and ffprobe available --> **DONE**

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
