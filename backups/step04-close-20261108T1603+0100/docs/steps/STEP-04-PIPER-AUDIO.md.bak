# `STEP-04 - Piper narration and audio`

Status --> **IN PROGRESS**

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

## `Exit criteria`

A deterministic narration and music mix passes automated ffprobe validation and is muxed with the verified STEP-03 visual stream.

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
