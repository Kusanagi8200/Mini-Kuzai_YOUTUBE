# `STEP-04 - Piper narration and audio`

Status --> **COMPLETED - V6 CANONICAL**

## `Objective`

Reuse the existing fhc2 Piper installation and canonical English voice, then produce a deterministic narration + music mix for the 60-second Short.

The narration must not invent scientific claims.

## `Verified runtime`

- Piper binary --> `/opt/kuzai-tts/piper/venv/bin/piper`
- voice model --> `/opt/kuzai-tts/piper/models/en_US-lessac-high.onnx`
- model JSON --> present
- background music --> `assets/music/kuzai-dark-cyberpunk-background-60s.wav`
- font --> `assets/fonts/Anta-Regular.ttf`
- FFmpeg / ffprobe --> verified

## `Canonical narration implementation`

The initial long Piper synthesis produced two audible scratch artifacts.

The final implementation therefore synthesizes narration sentence by sentence.

`app/generate_narration.py` now:

- splits narration into sentences
- generates each sentence independently with Piper
- applies a short 12 ms fade at chunk boundaries
- inserts controlled inter-sentence silence
- concatenates chunks into one PCM WAV
- prevents the scratch artifacts observed in the long single-pass synthesis

Operator listening verification --> PASS.

## `Canonical audio contract`

- total video duration --> 60.000 s
- voice start --> 10.000 s
- voice end --> 50.000 s
- voice window --> 40.000 s
- background music volume --> 20 percent
- narration timing normalization --> FFmpeg `atempo`
- maximum accepted narration speed correction --> plus/minus 10 percent
- final audio --> AAC stereo 48 kHz
- final video --> H.264 1080 x 1920 yuv420p

If narration would require more than the allowed timing correction, the mix fails instead of excessively distorting speech.

## `Canonical V6 presentation`

Verified presentation:

- Anta font
- top-right `THE KUZ NETWORK`
- `KUZAI.ORG` directly below
- white text on black square-corner backgrounds
- central area reserved for current/future step information
- dynamic text centered
- `GITHUB.COM/KUSANAGI8200` permanent footer
- exact 60-second duration

Operator visual acceptance --> PASS.

## `Verified evidence`

GOGIT:

- `STEP-04-PIPER-PROBE-001` --> PASS
- `STEP-04-NARRATION-VERIFY-001` --> PASS
- `STEP-04-FINAL-MEDIA-VERIFY-001` --> PASS
- `STEP-04-V3-SCRATCH-FIX-VERIFY-001` --> PASS
- `STEP-04-V6-CANONICAL-VERIFY-001` --> PASS

Final canonical report confirms:

- `CANONICAL_LAYOUT=V6`
- `OPERATOR_VISUAL_ACCEPTANCE=PASS`
- `DURATION_MS=60000`
- `VOICE_START_MS=10000`
- `VOICE_END_MS=50000`
- `VOICE_WINDOW_MS=40000`
- `MUSIC_VOLUME_PERCENT=20`
- `FONT_FAMILY=ANTA`
- `SCRATCH_AUDIO_FIXED=1`
- `FUTURE_VIDEO_CONSTRAINTS=FROZEN`

## `Closure`

STEP-04 --> **COMPLETED**

The V6 presentation/audio rules are frozen for VIDEO-001 and future Mini-Kuzai Shorts.

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
