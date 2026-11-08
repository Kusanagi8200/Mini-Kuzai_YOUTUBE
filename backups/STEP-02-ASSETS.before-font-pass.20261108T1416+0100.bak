# STEP-02 - Assets

Status --> **IN PROGRESS**

## Objective

Install and validate the fixed Short assets and freeze the visual layout before renderer implementation.

## Master background

Validated source asset supplied in the ChatGPT project discussion:
- format --> PNG
- resolution --> 1080 x 1920
- aspect ratio --> 9:16
- mode --> RGBA
- SHA-256 --> `1e4fca73ca61d9c1de9908ffe1046e6c2e02de1e2e94a18af0c6b06563078316`
- fixed THE KUZ NETWORK logo
- fixed Mini-Kuzai character
- fixed Mini-KuzAI From Scratch branding
- no embedded Vxx number
- no embedded step-specific metric or conclusion

Target repository path:

`assets/backgrounds/mini-kuzai-short-master.png`

The validated image still needs to be copied into the repository/fhc2 storage under this canonical filename.

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

GOGIT report `STEP-02-FFMPEG-INSTALL-001` --> **PASS**

Verified:
- FFmpeg --> `/usr/bin/ffmpeg`
- ffprobe --> `/usr/bin/ffprobe`
- FFmpeg version --> `6.1.1-3ubuntu5`
- ffprobe version --> `6.1.1-3ubuntu5`

The rendering prerequisite is satisfied.

## Exit criteria

- master background present under the canonical filename and checksum reverified
- font selected and validated
- music asset selected and license/source recorded
- safe zones / overlay coordinates frozen
- FFmpeg and ffprobe available --> **DONE**
