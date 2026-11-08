# `Mini-Kuzai - YOUTUBE`

Automated YouTube Shorts pipeline for **Mini-Kuzai / THE KUZ NETWORK**.

The project converts validated Mini-Kuzai development information into short vertical videos with a fixed visual identity, Piper narration, background music and controlled YouTube publication.

## `Target YouTube channel`

- Channel --> [THE KUZ NETWORK](https://www.youtube.com/channel/UC9MDfq5s-6j_twe4xJH_XXA)
- Channel ID --> `UC9MDfq5s-6j_twe4xJH_XXA`
- usage --> canonical publication target for Mini-Kuzai Shorts

## `Editorial order`

The first video is a channel introduction, not a DEV-FLOW step video.

VIDEO-001 presents:

- THE KUZ NETWORK
- Mini-Kuzai
- the `LLM From Scratch` objective
- the purpose of the channel
- the fact that future Shorts document validated development milestones

VIDEO-001 has no Vxx reference.

Only later videos use the DEV-FLOW format.

## `Canonical video format`

All generated videos use:

- resolution --> 1080 x 1920
- aspect ratio --> 9:16
- duration --> **60 seconds exactly**
- font --> Anta
- permanent top-right branding --> `THE KUZ NETWORK` + `KUZAI.ORG`
- permanent footer --> `GITHUB.COM/KUSANAGI8200`
- Piper narration --> sentence-chunked
- narration window --> 10 s to 50 s
- background music --> 20 percent
- H.264 video
- AAC stereo 48 kHz audio

## `YouTube metadata policy`

Descriptions for all Shorts follow these project constraints:

- no final colon character
- supplied colons are normalized to ` → `
- no `<` or `>`
- no `http://`
- no `https://`
- no `www.` URL
- descriptive text only

Permanent project addresses are displayed inside the rendered video instead of the description.

## `Current status`

**NEXT --> STEP-07 MINI-KUZAI FINAL-DEV-FLOW INTEGRATION**

Completed:

- STEP-00 repository bootstrap
- STEP-01 fhc2 environment audit
- STEP-02 assets
- STEP-03 renderer
- STEP-04 canonical V6 presentation/audio pipeline
- STEP-05 Google Cloud / YouTube Data API / OAuth
- first automated private upload
- authenticated channel verification
- actual private visibility verification
- VIDEO-001 operator review
- VIDEO-001 public publication
- public visibility verification through API
- publication journal
- media SHA256 idempotence

VIDEO-001 pilot:

- Video ID --> `lWo3DobOLqQ`
- title --> `THE KUZ NETWORK // MINI-KUZAI - LLM FROM SCRATCH`
- target channel --> verified
- private upload --> PASS
- operator visual/audio review --> PASS

VIDEO-001 final state:

- Video ID --> `lWo3DobOLqQ`
- visibility --> `public`
- public state verified through YouTube Data API --> PASS

Current action:

- prepare STEP-07 DEV-FLOW integration
- keep YouTube as an independent publication sink after verified Mini-Kuzai FINAL steps

## `Google Cloud / OAuth state`

Verified:

- Google Cloud project --> `Mini-Kuzai-YouTube`
- YouTube Data API v3 --> enabled
- OAuth client --> Desktop app
- audience --> External
- current publishing status --> Testing
- scopes --> `youtube.upload` + `youtube.readonly`
- OAuth files --> outside Git
- target Channel ID verification --> mandatory before upload

Known limitation:

Google documents that External OAuth applications in Testing issue refresh tokens that expire after seven days when non-basic identity scopes are used.

STEP-07 unattended automation therefore requires a production-state review before activation.

Complete setup procedure:

[Google Cloud and YouTube OAuth setup](docs/GOOGLE-YOUTUBE-OAUTH-PROCESS.md)

## `Target pipeline`

```text
validated Mini-Kuzai FINAL step
      |
      v
structured Short brief
      |
      +--> canonical 1080x1920 renderer
      +--> Anta overlays
      +--> Piper sentence-chunked narration
      +--> background music
      |
      v
60-second validated MP4
      |
      v
target-channel verification
      |
      v
controlled YouTube publication
      |
      v
journal + idempotence evidence
```

YouTube publication failure never invalidates the underlying Mini-Kuzai scientific result.

## `Navigation`

| Area | Link |
| --- | --- |
| Documentation index | [docs/README.md](docs/README.md) |
| Installation / development steps | [docs/steps/README.md](docs/steps/README.md) |
| Google Cloud / YouTube OAuth process | [docs/GOOGLE-YOUTUBE-OAUTH-PROCESS.md](docs/GOOGLE-YOUTUBE-OAUTH-PROCESS.md) |
| Project workflow policy | [docs/WORKFLOW.md](docs/WORKFLOW.md) |
| GOGIT documentation | [tools/GOGIT.md](tools/GOGIT.md) |
| Application code | [app/README.md](app/README.md) |
| Assistant reports | [reports/assistant-results/README.md](reports/assistant-results/README.md) |

## `Installation roadmap`

| Step | Scope | Status |
| --- | --- | --- |
| STEP-00 | Repository bootstrap and operating rules | **COMPLETED** |
| STEP-01 | fhc2 environment audit | **COMPLETED** |
| STEP-02 | Background, fonts and music assets | **COMPLETED** |
| STEP-03 | Python / FFmpeg renderer | **COMPLETED** |
| STEP-04 | Piper narration and audio mix | **COMPLETED - V6 CANONICAL** |
| STEP-05 | YouTube Data API and OAuth | **COMPLETED** |
| STEP-06 | Channel introduction pilot | **COMPLETED** |
| STEP-07 | Mini-Kuzai FINAL-DEV-FLOW integration | **NEXT** |

## `Operating principles`

- Work step by step and verify each change.
- Back up an existing file before modifying it.
- Never commit OAuth secrets, tokens, passwords, private keys or private account data.
- Keep OAuth and publication state outside Git.
- Verify the authenticated YouTube Channel ID before every upload.
- Block duplicate media through SHA256 journal checks.
- Publish sanitized command results through GOGIT.
- Update code and documentation after every completed project step.
- YouTube failure must never invalidate a Mini-Kuzai scientific result.

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
