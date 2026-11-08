# STEP-02 - Assets

Status --> **IN PROGRESS**

## Objective

Install and validate the fixed Short assets and freeze the visual layout before renderer implementation.

## Master background

Validated design:
- resolution --> 1080 x 1920
- aspect ratio --> 9:16
- fixed THE KUZ NETWORK logo
- fixed Mini-Kuzai character
- fixed Mini-KuzAI From Scratch branding
- no embedded Vxx number
- no embedded step-specific metric or conclusion

Target repository path:

`assets/backgrounds/mini-kuzai-short-master.png`

The master image itself still needs to be copied to fhc2/repository storage.

## Dynamic overlays

The renderer will add these values automatically:
- `Vxx`
- `FLOW Vxx OK`
- step title
- main metric or result
- short conclusion
- `DEV FLOW #xxx`

Coordinates and safe zones will be frozen after the master image is present locally.

## Music

Background music is not selected yet.

Requirements:
- YouTube-compatible usage rights
- source/license documented
- suitable for low-volume mixing below Piper narration

Target repository path:

`assets/music/`

## Font

STEP-01 detected 496 fontconfig entries. The final renderer font will be selected from installed fonts rather than installing one unnecessarily.

## Runtime prerequisite

STEP-01 found FFmpeg and ffprobe absent. They must be installed and verified before STEP-03 rendering begins.

## Exit criteria

- master background present and checksum recorded
- font selected and validated
- music asset selected and license/source recorded
- safe zones / overlay coordinates frozen
- FFmpeg and ffprobe available for the next renderer step
