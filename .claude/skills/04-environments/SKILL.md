---
name: environment-check
description: Use when switching environments, updating config values, or verifying URLs/settings. Triggers on "check environment", "switch to production", "update URLs", "check config", "is this prod-ready".
allowed-tools: Read, Grep, Glob, Edit
---

## Environment Check

1. **Identify the target environment** — local, staging, or production?

2. **Scan for hardcoded environment-specific values:**
   - Grep for `localhost`, `127.0.0.1`, dev URLs, test credentials, debug flags
   - Check any config constants file for values that differ between environments

3. **Verify config separation:**
   - Are environment-specific values in a dedicated config location (constants file, env vars, config file)?
   - Is there a clear process for switching environments without touching business logic?

4. **Pre-deploy checklist:**
   - [ ] All localhost/dev URLs replaced or behind config
   - [ ] No debug logging or test credentials in production path
   - [ ] Dependencies match production environment
   - [ ] Any required env vars documented and set

5. **Report:** "Environment: [local/staging/prod]. Issues found: [list or none]. Ready to deploy: [yes/no]."

6. If changes are needed: show exactly what to change and ask for confirmation before editing.
