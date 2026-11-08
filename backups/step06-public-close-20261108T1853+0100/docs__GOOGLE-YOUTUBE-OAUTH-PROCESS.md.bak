# `Google Cloud and YouTube OAuth setup`

This page documents the complete Google Cloud, Google Auth Platform and YouTube Data API setup used by the Mini-Kuzai YouTube pipeline.

It records the verified procedure without storing any client secret, access token, refresh token, private email address or other credential in Git.

## `Canonical target`

- Google Cloud project --> `Mini-Kuzai-YouTube`
- OAuth application --> `Mini-Kuzai YouTube Uploader`
- OAuth desktop client --> `Mini-Kuzai YouTube Uploader - fhc2`
- YouTube channel --> `THE KUZ NETWORK`
- Channel ID --> `UC9MDfq5s-6j_twe4xJH_XXA`
- Runtime host --> `fhc2`
- OAuth client file --> `/root/.config/mini-kuzai-youtube/oauth-client.json`
- OAuth token file --> `/root/.config/mini-kuzai-youtube/token.json`
- Upload journal --> `/root/.local/state/mini-kuzai-youtube/upload-journal.json`

## `1 - Create the Google Cloud project`

Create a dedicated Google Cloud project.

Project name used for this deployment:

`Mini-Kuzai-YouTube`

Do not enable unrelated paid Google Cloud services.

Official reference:

https://docs.cloud.google.com/resource-manager/docs/creating-managing-projects

## `2 - Enable YouTube Data API v3`

In Google Cloud Console:

`APIs & Services → Library → YouTube Data API v3 → Enable`

The API must show status `Enabled`.

Official reference:

https://developers.google.com/youtube/v3/getting-started

## `3 - Configure Google Auth Platform`

Open:

`Google Auth Platform → Overview → Get started`

Configure:

- App name --> `Mini-Kuzai YouTube Uploader`
- User support email --> monitored Google account
- Audience --> `External`
- Contact information --> monitored Google account
- Publishing status during initial setup --> `Testing`

Do not store the support/contact email address in this public repository.

## `4 - Add the test user`

Open:

`Google Auth Platform → Audience`

Under `Test users`, add the Google account that owns or administers the target YouTube channel.

Only authorized test users can complete the OAuth flow while the application remains in Testing status.

## `5 - Configure OAuth scopes`

Open:

`Google Auth Platform → Data Access → Add or remove scopes`

Required scopes:

`https://www.googleapis.com/auth/youtube.upload`

Purpose --> upload a video to the authenticated YouTube channel.

`https://www.googleapis.com/auth/youtube.readonly`

Purpose --> resolve the authenticated YouTube channel with `channels.list(mine=true)` and verify the Channel ID before upload.

The deployment initially used only `youtube.upload`. The channel identity check returned HTTP 403 `insufficientPermissions`. Adding `youtube.readonly` and reauthorizing resolved the issue.

Do not request broader scopes unless a future feature explicitly requires them.

Official references:

https://developers.google.com/youtube/data/reference/rest/v3/videos/insert

https://developers.google.com/youtube/data/reference/rest/v3/channels/list

## `6 - Create the OAuth Desktop client`

Open:

`Google Auth Platform → Clients → Create client`

Configure:

- Application type --> `Desktop app`
- Name --> `Mini-Kuzai YouTube Uploader - fhc2`

Download the OAuth client JSON.

Never commit the downloaded JSON to Git.

The repository `.gitignore` rejects common OAuth credential filenames.

Official reference:

https://developers.google.com/identity/protocols/oauth2/native-app

## `7 - Store the OAuth client outside Git`

Canonical directory on `fhc2`:

`/root/.config/mini-kuzai-youtube`

Required permissions:

- directory --> `700`
- OAuth client JSON --> `600`
- token JSON --> `600`

Canonical OAuth client path:

`/root/.config/mini-kuzai-youtube/oauth-client.json`

The file must contain a Desktop/Installed application configuration with a loopback redirect URI.

Never print or publish:

- client secret
- access token
- refresh token
- authorization URL containing temporary authorization parameters

## `8 - Python environment`

The project uses a repository-local virtual environment excluded from Git:

`.venv/`

Required packages:

- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth`

The validated runtime uses Python 3.12 on `fhc2`.

## `9 - Complete the OAuth authorization`

The Desktop OAuth flow uses a loopback callback.

The verified callback port is:

`127.0.0.1:8765`

If the browser runs on another Linux host while the OAuth script runs on `fhc2`, create an SSH local-forward tunnel from the browser host:

`ssh -L 8765:127.0.0.1:8765 root@fhc2`

Then run the OAuth flow on `fhc2`.

The browser displays Google's unverified-app warning while the application is External and Testing. Continue only with the account explicitly configured as a test user.

After consent, Google redirects to the local loopback callback and the script writes:

`/root/.config/mini-kuzai-youtube/token.json`

The verified token contains:

- refresh token
- `youtube.upload`
- `youtube.readonly`

The token file must remain mode `600`.

## `10 - Verify the authenticated YouTube channel`

Before any upload, call:

`channels.list(part="id,snippet", mine=True)`

The result must resolve exactly to:

- Channel title --> `THE KUZ NETWORK`
- Channel ID --> `UC9MDfq5s-6j_twe4xJH_XXA`

Any mismatch blocks publication.

This check is implemented in:

`app/youtube_upload.py`

## `11 - Upload preflight`

The uploader defaults to preflight mode.

Without `--execute`, it verifies:

- media file exists
- media is MP4
- credentials are present and mode `600`
- both OAuth scopes are present
- authenticated channel matches the frozen target
- SHA256 is calculated
- upload journal is checked
- duplicate media SHA256 is blocked
- no upload is performed

The uploader is currently frozen to `PRIVATE_ONLY`.

## `12 - Private pilot upload`

The first automated upload was VIDEO-001.

Verified pilot:

- Video ID --> `pexXCUznWRk`
- title --> `THE KUZ NETWORK // MINI-KUZAI - LLM FROM SCRATCH`
- initial visibility --> `private`
- target channel match --> PASS
- private status verified through YouTube Data API --> PASS
- upload journal entry --> PASS
- media idempotence --> PASS

The journal is stored outside Git:

`/root/.local/state/mini-kuzai-youtube/upload-journal.json`

## `13 - YouTube Short metadata policy`

The project applies the following description rules to every future Short:

- no colon character
- colons supplied to the uploader are normalized to ` → `
- no `<` or `>`
- no `http://`
- no `https://`
- no `www.` URL
- descriptive text only
- permanent project references remain visible inside the video itself as `KUZAI.ORG` and `GITHUB.COM/KUSANAGI8200`

YouTube officially rejects `<` and `>` in video titles and descriptions.

The no-URL and no-colon rules are stricter Mini-Kuzai editorial policy.

The current uploader enforces these constraints before upload.

## `14 - Public visibility`

The current OAuth scopes intentionally remain limited to:

- `youtube.upload`
- `youtube.readonly`

The YouTube `videos.update` method requires a broader write scope such as `youtube` or `youtube.force-ssl`.

For the first pilot, the private-to-public transition is therefore performed manually in YouTube Studio instead of broadening OAuth permissions.

Future automated publication has two possible designs:

- direct public upload through `videos.insert` after all local checks pass
- explicit visibility transition using a broader OAuth scope after a separate security review

Neither behavior is enabled automatically at this stage.

Official reference:

https://developers.google.com/youtube/data/reference/rest/v3/videos/update

## `15 - Testing-mode refresh-token limitation`

Google OAuth applications configured as External with publishing status `Testing` issue refresh tokens that expire after seven days when scopes exceed basic identity scopes.

This is acceptable for the initial pilot but not for unattended long-term automation.

Before STEP-07 production automation, review the Google Auth Platform publishing/verification requirements and move the application to an appropriate production state.

Official reference:

https://developers.google.com/identity/protocols/oauth2/

## `Security rules`

Never commit or publish:

- OAuth client secret
- OAuth token JSON
- access token
- refresh token
- authorization URL
- Google account email addresses
- private upload journal

Credentials and runtime state stay outside the repository.

The repository may contain only:

- code
- sanitized configuration policy
- public Channel ID
- sanitized GOGIT evidence
- documentation

## `Verified STEP-05 evidence`

GOGIT reports:

- `STEP-05-PRIVATE-UPLOAD-001` --> PASS
- `STEP-05-PRIVATE-VERIFY-001` --> PASS

STEP-05 exit criteria are satisfied.

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
