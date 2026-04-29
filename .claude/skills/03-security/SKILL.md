---
name: security-check
description: Security audit — checks auth, SQL injection, exposed endpoints, and sensitive data. Triggers on "security check", "is this secure", "check for vulnerabilities", "check auth", "audit security", "security audit".
allowed-tools: Read, Grep, Glob
---

## Security Check

1. **Read the target file(s)** fully before reporting anything

2. **Check for authentication issues:**
   - Endpoints that should require auth but don't
   - Auth checks that can be bypassed (missing early return on auth failure)
   - Admin routes accessible without privilege check

3. **Check for injection vulnerabilities:**
   - SQL values concatenated directly into query strings instead of parameterized
   - User input passed to shell commands, eval, or dynamic code execution
   - Unescaped output rendered as HTML (XSS)

4. **Check for secrets and sensitive data:**
   - Hardcoded credentials, API keys, passwords in source files
   - Sensitive data returned in API responses (passwords, internal tokens)
   - Plain-text sensitive values in URLs or logs

5. **Check for insecure direct object references:**
   - IDs in requests not validated against the current user's ownership
   - File paths constructed from user input

6. **Report findings** in a table:
   | File | Line | Issue | Severity |
   |------|------|-------|----------|

7. Ask: "Fix any of these now, or just flag for later?"

8. **Do not change anything** until the user confirms.
