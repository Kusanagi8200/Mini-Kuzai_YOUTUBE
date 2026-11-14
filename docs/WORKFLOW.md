# `Project workflow policy`

## `Objective`

Keep the Mini-Kuzai YouTube pipeline reproducible, auditable and fast to operate while minimizing manual terminal relay.

## `Execution model`

```text
review scope
  -> backup existing files when modification is required
  -> execute the largest safe bounded sequence
  -> verify locally
  -> publish sanitized results through GOGIT
  -> ChatGPT reviews GitHub evidence
  -> update code + documentation
  -> commit / push
  -> close the step
```

## `Loop policy`

Commands and tests should be looped automatically when:
- the next action is deterministic
- no destructive decision is required
- no secret is exposed
- failures stop the loop immediately
- each completed stage remains auditable

Stop and request operator feedback when:
- an operation requires interactive authentication
- a destructive or irreversible choice is required
- a failure has not been diagnosed
- credentials or external account configuration are involved
- a public YouTube publication is about to be enabled for the first time

## `Backup policy`

Before modifying an existing tracked file, create a timestamped backup either in Git when public-safe or outside Git for runtime configuration and secrets.

Never commit secret-bearing backups.

## `GOGIT policy`

Successful command results intended for ChatGPT review should be published as structured reports through `tools/gogit_publish.py`.

Public GOGIT reports must never contain passwords, tokens, API keys, OAuth tokens, cookies, private keys, secret files or private user data.

A local failure that prevents GOGIT publication may be pasted manually for diagnosis.

## `Git policy`

- branch --> `main`
- no force push
- clean synchronized worktree before GOGIT publication
- one unique STEP_ID per immutable GOGIT history report
- documentation update at the end of every completed step

## `Execution target policy`

Every operator command must state its execution target before the command block.

Canonical targets:

- `fhc2` --> Mini-Kuzai scientific repository and Mini-Kuzai_YOUTUBE runtime
- `VPS KUZAI.ORG / ov-19d492` --> production website repository under `/var/www/kuzai.org`
- `fhc` --> interactive browser / SSH tunnel helper when an OAuth loopback flow requires a graphical browser

Rules:

- never leave the target machine implicit
- when one workflow spans several hosts, separate the commands by machine
- GOGIT instructions must also identify the machine and repository that publish the report
- do not repeat a machine question when the execution target is already known from the active workflow

## `Scientific boundary`

This repository publishes communication assets. It does not authorize Mini-Kuzai training, BLIND access, checkpoint changes or scientific experiments.

## `Cross-channel media publication`

A scientific FINAL and a media publication are separate transactions.

For V81+ the active production sequence is:

```text
scientific FINAL receipt
  -> deterministic committed Short brief
  -> media build + audit
  -> YouTube public publication
  -> LinkedIn native video publication through KUZ-DIN
  -> GitHub verified public YouTube fallback
  -> committed cross-channel media receipt
```

Rules:

- no media generation from START-DEV-FLOW
- no media publication before a committed FINAL receipt
- YouTube / LinkedIn / GitHub media failures never invalidate the scientific FINAL
- duplicate media is blocked by SHA256 journals where available
- LinkedIn native video publication must use a separate live gate
- GitHub Discussion MP4 attachment automation must be independently validated before enabling it
- a verified public YouTube URL is the GitHub fallback when native Discussion attachment automation is unavailable
- `tools/dev_flow_media_worker.py` is the production systemd entry point
- each invocation performs at most one bounded state transition
- cross-channel publication runs only after YouTube state is `PUBLIC_PUBLISHED`
- a media receipt is committed only after LinkedIn and GitHub publication are verified
- absence of a V81+ FINAL receipt keeps the worker idle

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
