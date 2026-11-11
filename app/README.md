# `Application code`

## `Renderer`

`app/render_short.py`

Verified canonical presentation:

- 1080 x 1920
- 9:16
- 60 seconds exactly
- Anta font embedded in the repository
- top-right permanent branding
- dynamic step information in the central/lower information area
- permanent `GITHUB.COM/KUSANAGI8200` footer

## `Narration and audio`

Components:

- `app/generate_narration.py`
- `app/mix_audio.py`

Verified rules:

- Piper narration generated sentence by sentence
- short fades between chunks prevent scratch artifacts
- voice window --> 5.000 s to 55.000 s for V81+
- background music --> 20 percent
- final audio --> AAC stereo 48 kHz

The V80 production Short remains a historical 10-50 s artifact. The 5-55 s contract applies to new media generated after the 2026-11-11 timing revision.

## `YouTube uploader`

`app/youtube_upload.py`

STEP-05 implementation --> **COMPLETED**

Controls:

- OAuth credentials stored outside Git
- target Channel ID verification
- required scopes --> `youtube.upload` + `youtube.readonly`
- MP4 validation
- media SHA256
- local upload journal
- duplicate-media blocking
- preflight by default
- explicit `--execute` requirement
- pilot upload forced to `private`

Description policy:

- no final colon character
- colons supplied to the uploader are converted to ` → `
- no angle brackets
- no `http://`
- no `https://`
- no `www.` URL

Complete Google setup procedure:

[Google Cloud and YouTube OAuth setup](../docs/GOOGLE-YOUTUBE-OAUTH-PROCESS.md)

## `Runtime state`

Generated media remains under `work/` and outside Git.

OAuth material remains outside Git under:

`/root/.config/mini-kuzai-youtube/`

The local upload journal remains outside Git under:

`/root/.local/state/mini-kuzai-youtube/`

[Back to project README](../README.md)

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
