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
- narration window --> 5 s to 55 s for V81+ / cross-channel media flow
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

**STEP-07 --> COMPLETED / V81+ AUTOMATIC CROSS-CHANNEL MEDIA ORCHESTRATION ACTIVE**

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

- STEP-07 production runtime is active
- OAuth production readiness is validated
- FINAL-only public upload is enabled
- V80 is the first verified live FINAL Short - YouTube video ID `y-YnlPLbT9Q`
- FLOW-PRESENTATION-001 validated the 5-55 s media contract and tri-channel publication
- presentation YouTube video ID --> `vhQmddUuMcg`
- LinkedIn native-video post URN --> `urn:li:ugcPost:7526340708715327488`
- GitHub media publication --> Mini-Kuzai Discussion #12
- automatic V81+ orchestration --> INSTALLED AND ACTIVE
- runtime wrapper --> `tools/dev_flow_media_worker.py`
- FINAL receipt --> deterministic brief --> audited Short --> YouTube --> LinkedIn native video --> GitHub fallback --> committed media receipt
- V81 genuine FINAL media flow --> VERIFIED / CLOSED
- V81 YouTube --> PUBLIC / `EAMRSevA2zk`
- V81 LinkedIn native video --> PUBLISHED / `urn:li:ugcPost:7527349657677594624`
- V81 GitHub media publication --> Discussion #13 comment #19612381
- V81 cross-channel receipt --> `automation/publication-receipts/V81-final.json`
- current runtime state --> IDLE / ready for the next eligible FINAL receipt
- next project action --> wait for the next scientifically valid FINAL receipt; V82 scientific preparation belongs to Mini-Kuzai
- keep media publication independent from scientific validity
- never let a media failure invalidate the scientific FINAL

## `Pre-V81 cross-channel publication validation`

`FLOW-PRESENTATION-001` is the completed non-scientific validation of the media path before V81.

Target flow:

```text
validated media package
      |
      +--> YouTube public Short
      +--> LinkedIn native video post
      +--> GitHub media publication / public YouTube fallback
      |
      v
publication receipts
      |
      v
documentation update
```

The presentation does not represent V81 scientific evidence and cannot authorize training, BLIND access or checkpoint changes.

Current implementation:

- canonical voice window --> 5 s to 55 s
- presentation config --> `config/flow-presentation-001.json`
- audited local builder --> `tools/build_flow_presentation.py`
- builder performs no external publication
- FLOW-PRESENTATION-001 tri-channel publication --> VERIFIED
- YouTube public video --> `vhQmddUuMcg`
- LinkedIn native video post --> `urn:li:ugcPost:7526340708715327488`
- GitHub media publication --> Discussion #12 using the verified public YouTube link fallback
- GitHub Discussions accepts MP4 attachments, but automated native Discussion attachment publication remains a separate integration gate

## `Google Cloud / OAuth state`

Verified:

- Google Cloud project --> `Mini-Kuzai-YouTube`
- YouTube Data API v3 --> enabled
- OAuth client --> Desktop app
- audience --> External
- current publishing status --> In production
- scopes --> `youtube.upload` + `youtube.readonly`
- OAuth files --> outside Git
- target Channel ID verification --> mandatory before upload

Production OAuth state:

- Google Auth Platform --> External / In production
- public application home page --> KUZAI.ORG
- public OAuth privacy policy --> KUZAI.ORG
- authorized domain --> kuzai.org
- production OAuth reauthorization --> PASS
- refresh credential --> present
- target channel verification --> PASS
- production upload preflight --> PASS
- real STEP-07 upload --> public FINAL-only mode enabled

The application remains operator-controlled. A real DEV-FLOW Short is uploaded only after an eligible FINAL-DEV-FLOW has a committed PUBLISHED receipt and passes the independent media/provenance gates.

Complete setup procedure:

[Google Cloud and YouTube OAuth setup](docs/GOOGLE-YOUTUBE-OAUTH-PROCESS.md)

## `Target pipeline`

```text
validated Mini-Kuzai FINAL receipt
      |
      v
deterministic committed Short brief
      |
      v
canonical 60-second audited MP4
      |
      v
YouTube public publication
      |
      v
LinkedIn native video through KUZ-DIN
      |
      v
GitHub media fallback on canonical FINAL Discussion
      |
      v
committed cross-channel media receipt
```

The production worker performs one bounded transaction per invocation. Brief generation, YouTube publication and downstream cross-channel publication are therefore isolated and independently auditable.

YouTube publication failure never invalidates the underlying Mini-Kuzai scientific result.

## `V81 production result`

V81 is the first genuine V81+ FINAL to complete the full automatic cross-channel transaction.

- YouTube --> PUBLIC / `EAMRSevA2zk`
- LinkedIn native video --> PUBLISHED / `urn:li:ugcPost:7527349657677594624`
- GitHub media fallback --> Discussion #13 comment #19612381
- media duration --> 60 seconds
- cross-channel receipt --> `automation/publication-receipts/V81-final.json`
- scientific boundary --> training authorization false, BLIND access false
- repository state after publication --> clean and ready for the next eligible FINAL

## `THE KUZ NETWORK maintenance`

The ChatGPT operator command `MAJ-THEKUZNETWORK` audits and synchronizes the five canonical THE KUZ NETWORK repositories. See [MAJ-THEKUZNETWORK.md](MAJ-THEKUZNETWORK.md).

## `Navigation`

| Area | Link |
| --- | --- |
| Documentation index | [docs/README.md](docs/README.md) |
| Installation / development steps | [docs/steps/README.md](docs/steps/README.md) |
| Google Cloud / YouTube OAuth process | [docs/GOOGLE-YOUTUBE-OAUTH-PROCESS.md](docs/GOOGLE-YOUTUBE-OAUTH-PROCESS.md) |
| Project workflow policy | [docs/WORKFLOW.md](docs/WORKFLOW.md) |
| Cross-channel flow validation | [docs/FLOW-PRESENTATION-001.md](docs/FLOW-PRESENTATION-001.md) |
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
| STEP-07 | Mini-Kuzai FINAL-DEV-FLOW integration | **COMPLETED - V81+ AUTOMATIC CROSS-CHANNEL ORCHESTRATION ACTIVE** |

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
