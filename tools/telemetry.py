#!/usr/bin/env python3
"""
tools/telemetry.py — Anonymous usage telemetry for Clankbrain.

Sends a single fire-and-forget HTTP POST to PostHog on:
  - setup completion (event: "setup")
  - session start     (event: "session_start")

No personal data is collected. A random anonymous ID is generated once
and stored in .claude/.clankbrain-id. The ID cannot be traced back to
any individual or project.

Opt out: set CLANKBRAIN_NO_TELEMETRY=1 in your environment.
"""

import json
import os
import sys
import uuid
from pathlib import Path

# ── PostHog config ─────────────────────────────────────────────────────────────
# Replace with your PostHog project API key from posthog.com/settings/project
_POSTHOG_KEY    = 'phc_kQyQfXxpDn5Z7CvtN4GoqQACiULxACgSFmzrNrGVgZx8'
_POSTHOG_HOST   = 'https://app.posthog.com'
_CAPTURE_URL    = f'{_POSTHOG_HOST}/capture/'

# ── Version ────────────────────────────────────────────────────────────────────
def _get_version():
    here = Path(__file__).resolve().parent.parent
    try:
        return (here / 'VERSION').read_text(encoding='utf-8').strip()
    except Exception:
        return 'unknown'


# ── Anonymous ID ───────────────────────────────────────────────────────────────
def _get_anon_id():
    """Return a stable anonymous ID for this install, creating it if needed."""
    # Walk up from tools/ to find .claude/
    candidate = Path(__file__).resolve().parent.parent / '.claude' / '.clankbrain-id'
    try:
        if candidate.exists():
            return candidate.read_text(encoding='utf-8').strip()
        new_id = str(uuid.uuid4())
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(new_id, encoding='utf-8')
        return new_id
    except Exception:
        return str(uuid.uuid4())  # ephemeral — fine if we can't persist


# ── Fire-and-forget POST ───────────────────────────────────────────────────────
def ping(event, properties=None):
    """
    Send a single telemetry event. Silent on any failure.

    Args:
        event:      event name string, e.g. 'setup' or 'session_start'
        properties: optional dict of extra properties (mode, platform, etc.)
    """
    if os.environ.get('CLANKBRAIN_NO_TELEMETRY'):
        return
    if 'phc_REPLACE' in _POSTHOG_KEY:
        return  # key not configured — skip silently

    try:
        import urllib.request as req

        props = {
            'version':  _get_version(),
            'platform': sys.platform,
            'python':   f'{sys.version_info.major}.{sys.version_info.minor}',
        }
        if properties:
            props.update(properties)

        body = json.dumps({
            'api_key':    _POSTHOG_KEY,
            'event':      event,
            'distinct_id': _get_anon_id(),
            'properties': props,
        }).encode('utf-8')

        request = req.Request(
            _CAPTURE_URL,
            data=body,
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        # 3-second timeout — never block the user
        req.urlopen(request, timeout=3)
    except Exception:
        pass  # telemetry must never surface errors
