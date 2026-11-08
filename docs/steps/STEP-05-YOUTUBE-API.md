# `STEP-05 - YouTube Data API`

Status --> **COMPLETED**

## `Objective`

Configure THE KUZ NETWORK YouTube channel for controlled API upload with explicit channel verification, private pilot publication and local idempotence.

## `Canonical target`

- Channel URL --> https://www.youtube.com/channel/UC9MDfq5s-6j_twe4xJH_XXA
- Channel ID --> `UC9MDfq5s-6j_twe4xJH_XXA`
- Channel title --> `THE KUZ NETWORK`
- first automated upload --> PRIVATE only

## `Verified Google configuration`

- dedicated Google Cloud project --> `Mini-Kuzai-YouTube`
- YouTube Data API v3 --> ENABLED
- Google Auth Platform audience --> External
- publishing status during pilot --> Testing
- OAuth client type --> Desktop app
- OAuth scopes --> `youtube.upload` + `youtube.readonly`
- OAuth client and token files --> stored outside Git
- credential file mode --> `600`
- refresh token --> present
- authenticated channel verification --> PASS

The additional `youtube.readonly` scope is required by the implemented `channels.list(mine=true)` identity verification.

## `Verified uploader controls`

`app/youtube_upload.py` enforces:

- target Channel ID match before upload
- MP4 input
- private credential file permissions
- required OAuth scopes
- media SHA256
- duplicate-media blocking
- local publication journal
- default preflight without upload
- explicit `--execute` requirement
- `PRIVATE_ONLY` upload policy for the pilot
- YouTube Short metadata policy

## `Description policy`

For all future Shorts:

- no colon character in the final description
- supplied colons are normalized to ` → `
- no `<` or `>`
- no `http://`
- no `https://`
- no `www.` URL
- descriptive text only

Permanent project references stay in the rendered video:

- `KUZAI.ORG`
- `GITHUB.COM/KUSANAGI8200`

## `Private pilot result`

VIDEO-001:

- title --> `THE KUZ NETWORK // MINI-KUZAI - LLM FROM SCRATCH`
- Video ID --> `pexXCUznWRk`
- target channel --> PASS
- API upload --> PASS
- actual YouTube visibility --> `private`
- journal match --> PASS
- idempotence --> PASS

GOGIT evidence:

- `STEP-05-PRIVATE-UPLOAD-001` --> PASS
- `STEP-05-PRIVATE-VERIFY-001` --> PASS

## `Google process documentation`

Complete setup and recovery procedure:

[Google Cloud and YouTube OAuth setup](../GOOGLE-YOUTUBE-OAUTH-PROCESS.md)

## `Known limitation`

The OAuth application is currently External with publishing status `Testing`.

Google documents that refresh tokens issued in this state expire after seven days when the requested scopes exceed basic identity scopes.

This does not invalidate STEP-05, but unattended long-term STEP-07 automation requires a separate production-state review.

## `Exit criteria`

Satisfied:

- private test video uploaded
- expected channel verified
- actual private visibility verified through API
- credentials remain outside Git
- journal and idempotence verified

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
