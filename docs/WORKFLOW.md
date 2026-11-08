# Project workflow policy

## Objective

Keep the Mini-Kuzai YouTube pipeline reproducible, auditable and fast to operate while minimizing manual terminal relay.

## Execution model

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

## Loop policy

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

## Backup policy

Before modifying an existing tracked file, create a timestamped backup either in Git when public-safe or outside Git for runtime configuration and secrets.

Never commit secret-bearing backups.

## GOGIT policy

Successful command results intended for ChatGPT review should be published as structured reports through `tools/gogit_publish.py`.

Public GOGIT reports must never contain passwords, tokens, API keys, OAuth tokens, cookies, private keys, secret files or private user data.

A local failure that prevents GOGIT publication may be pasted manually for diagnosis.

## Git policy

- branch --> `main`
- no force push
- clean synchronized worktree before GOGIT publication
- one unique STEP_ID per immutable GOGIT history report
- documentation update at the end of every completed step

## Scientific boundary

This repository publishes communication assets. It does not authorize Mini-Kuzai training, BLIND access, checkpoint changes or scientific experiments.

---

**THE KUZ NETWORK - KUSANAGI8200 - @2026**
