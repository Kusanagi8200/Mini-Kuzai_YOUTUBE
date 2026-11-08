# `Mini-Kuzai - YOUTUBE`

Automated YouTube Shorts pipeline for **Mini-Kuzai / THE KUZ NETWORK**.

The project converts Mini-Kuzai development information into short vertical videos with a fixed visual identity, Piper narration, background music and controlled YouTube publication.

## `Target YouTube channel`

- Channel --> [THE KUZ NETWORK](https://www.youtube.com/channel/UC9MDfq5s-6j_twe4xJH_XXA)
- Channel ID --> `UC9MDfq5s-6j_twe4xJH_XXA`
- Usage --> canonical publication target for Mini-Kuzai Shorts

## `Editorial order`

The **first video is a channel introduction**, not a DEV-FLOW step video.

Video 001 will present:
- THE KUZ NETWORK
- Mini-Kuzai
- the "LLM From Scratch" objective
- the purpose of the channel
- the fact that future videos will document validated development steps

Video 001 has **no Vxx reference**.

Only later videos use the automatic DEV-FLOW format with `Vxx`, step title, metric/result and `DEV FLOW #xxx`.

The currently active Mini-Kuzai V80 work is therefore **not** the first YouTube video.

## `Video format`

All generated videos use the same fixed format:
- resolution --> 1080 x 1920
- aspect ratio --> 9:16
- duration --> **60 seconds exactly**
- narration and overlays must fit inside this fixed duration
- background music is trimmed or looped/faded to the same 60-second timeline

## `Current status`

**IN PROGRESS --> STEP-04 PIPER + AUDIO**

Completed:
- STEP-00 repository bootstrap
- STEP-01 fhc2 environment audit
- Python 3.12.3 detected
- Pillow detected
- Piper detected at `/opt/kuzai-tts/piper/venv/bin/piper`
- Piper voice detected at `/opt/kuzai-tts/piper/models/en_US-lessac-high.onnx`
- Git and GitHub CLI verified
- FFmpeg installed and verified --> `/usr/bin/ffmpeg`
- ffprobe installed and verified --> `/usr/bin/ffprobe`
- FFmpeg/ffprobe version --> `6.1.1-3ubuntu5`
- renderer font selected --> `Ubuntu Sans Bold`
- master background stored at `assets/backgrounds/mini-kuzai-short-master.png`
- canonical YouTube channel registered
- target 1080 x 1920 Short format frozen
- fixed duration --> 60 seconds
- canonical background music validated --> 60.000-second WAV, 48 kHz stereo
- overlay layout frozen and verified --> PASS
- STEP-02 assets --> COMPLETED
- background music usage --> NON-COMMERCIAL
- STEP-03 renderer --> PASS (1080x1920, H.264, 30 fps, 60.000 s)

Current:
- probe the existing Piper runtime and voice CLI
- implement narration generation and final audio mix after probe validation

No YouTube API credentials, OAuth tokens or publication automation are configured yet.

## `Target pipeline`

```text
VIDEO 001
channel introduction
      |
      v
fixed background + intro overlays
+ Piper narration + music
      |
      v
60-second validated MP4
      |
      v
PRIVATE YouTube pilot

THEN

validated Mini-Kuzai FINAL step
      |
      v
structured short brief
      |
      +--> fixed 1080x1920 background
      +--> dynamic Vxx / title / metric overlays
      +--> Piper narration
      +--> background music
      |
      v
60-second validated MP4
      |
      v
controlled YouTube publication
```

## `Navigation`

| Area | Link |
| --- | --- |
| Documentation index | [docs/README.md](docs/README.md) |
| Installation / development steps | [docs/steps/README.md](docs/steps/README.md) |
| Project workflow policy | [docs/WORKFLOW.md](docs/WORKFLOW.md) |
| GOGIT documentation | [tools/GOGIT.md](tools/GOGIT.md) |
| GOGIT implementation | [tools/gogit_publish.py](tools/gogit_publish.py) |
| Application code | [app/README.md](app/README.md) |
| Assistant reports | [reports/assistant-results/README.md](reports/assistant-results/README.md) |

## `Installation roadmap`

| Step | Scope | Status |
| --- | --- | --- |
| STEP-00 | Repository bootstrap and operating rules | **COMPLETED** |
| STEP-01 | fhc2 read-only environment audit | **COMPLETED** |
| STEP-02 | Background, fonts and music assets | **COMPLETED** |
| STEP-03 | Python / FFmpeg renderer | **COMPLETED** |
| STEP-04 | Piper narration and audio mix | **IN PROGRESS** |
| STEP-05 | YouTube Data API and OAuth | Planned |
| STEP-06 | Channel introduction private pilot | Planned |
| STEP-07 | Mini-Kuzai FINAL-DEV-FLOW integration | Planned |

## `Operating principles`

- Work step by step and verify each change.
- Back up an existing file before modifying it.
- Prefer autonomous bounded sequences when intermediate manual validation is not required.
- Publish sanitized command results through GOGIT instead of manually copying successful terminal output.
- Update code and documentation after every completed installation step.
- Never commit OAuth secrets, tokens, passwords, private keys or private data.
- YouTube failure must never invalidate a Mini-Kuzai scientific result.
- Generated videos and temporary render files stay outside Git.

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
