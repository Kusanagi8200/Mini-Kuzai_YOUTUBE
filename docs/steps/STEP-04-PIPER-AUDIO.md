# `STEP-04 - Piper narration and audio`

Status --> **IN PROGRESS - V2 CORRECTION**

## `Objective`

Reuse the existing fhc2 Piper installation and canonical English voice, then produce a deterministic narration + music mix for the 60-second Short.

The narration must not invent scientific claims.

## `Known runtime`

Already detected during STEP-01:

- Piper binary --> `/opt/kuzai-tts/piper/venv/bin/piper`
- voice model --> `/opt/kuzai-tts/piper/models/en_US-lessac-high.onnx`
- canonical background music --> `assets/music/kuzai-dark-cyberpunk-background-60s.wav`

## `Current action`

Before implementing synthesis, probe the actual installed Piper CLI and voice runtime.

The probe must verify:
- Piper binary exists and executes
- model file exists
- matching model JSON configuration presence
- available CLI flags relevant to deterministic synthesis
- no assumption about unsupported flags

Probe tool:

`tools/audits/step04_piper_probe.py`

## `Planned audio contract`

After the probe is validated:

- narration --> Piper WAV
- background music --> canonical 60-second WAV
- music kept below narration
- final output --> AAC audio stream
- final media duration --> 60.000 seconds
- final mux --> STEP-03 H.264 video + STEP-04 AAC audio

Exact Piper invocation and mix parameters will be frozen only after real runtime verification.

## `Verified results`

GOGIT report `STEP-04-PIPER-PROBE-001` --> **PASS**

Verified runtime:
- Piper binary present
- voice model present
- model JSON present
- required synthesis flags present

GOGIT report `STEP-04-NARRATION-VERIFY-001` --> **PASS**

Verified narration:
- format --> WAV
- codec --> PCM 16-bit
- channels --> mono
- sample rate --> 22050 Hz
- duration --> 40.920 s

GOGIT report `STEP-04-FINAL-MEDIA-VERIFY-001` --> **PASS**

Verified final test media:
- video --> H.264
- resolution --> 1080 x 1920
- pixel format --> yuv420p
- audio --> AAC
- audio sample rate --> 48000 Hz
- audio channels --> stereo
- duration --> 60.000 s
- ffprobe --> PASS

## `V2 correction`

Operator-requested final presentation rules:
- dynamic text --> footer
- dynamic text --> centered
- text frame --> none
- background music --> 20%
- voice-over starts --> 10.000 s
- voice-over ends --> 50.000 s
- voice-over active window --> 40.000 s
- automatic narration timing correction --> maximum +/-10%

The source narration is normalized to the 40-second voice window using FFmpeg `atempo`. If the required speed correction exceeds +/-10%, rendering fails and the narration text must be revised.

STEP-04 remains open until the V2 media passes automated validation and operator visual/audio review.

## `Closure`

STEP-04 V2 --> **PENDING VERIFICATION**

STEP-05 --> **PAUSED UNTIL V2 ACCEPTANCE**

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
