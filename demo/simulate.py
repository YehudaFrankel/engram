#!/usr/bin/env python3
"""
Simulates the Claude Code Memory Starter Kit workflow in your terminal.
Record it with any screen capture tool to create the demo GIF.

Usage:
  python demo/simulate.py

Recommended recorder:
  Windows: ScreenToGif (free) — https://www.screentogif.com
  Mac:     Gifox or Kap
  Linux:   Peek or Byzanz

Crop your terminal window tight before recording.
Suggested terminal size: 90 cols x 24 rows.
"""

import time
import sys

CYAN   = '\033[1;36m'
GREEN  = '\033[1;32m'
YELLOW = '\033[1;33m'
RED    = '\033[1;31m'
BOLD   = '\033[1m'
DIM    = '\033[2m'
RESET  = '\033[0m'


def type_out(text, delay=0.045):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)


def println(text='', delay=0):
    print(text)
    if delay:
        time.sleep(delay)


def prompt(cmd, pre=1.4):
    time.sleep(pre)
    sys.stdout.write(f'{GREEN}$ {RESET}')
    sys.stdout.flush()
    time.sleep(0.4)
    type_out(cmd)
    time.sleep(0.3)
    print()


def pause(n=1.0):
    time.sleep(n)


# ── INTRO ────────────────────────────────────────────────────────────────────
println()
println(f'{BOLD}  Claude Code Memory Starter Kit{RESET}')
println(f'{DIM}  Persistent context across every session{RESET}')
println()
pause(1.2)

# ── STEP 1: Start Session ────────────────────────────────────────────────────
println(f'{DIM}  ❯ User types "Start Session" in Claude Code chat{RESET}')
pause(1.0)
println()
println(f'{CYAN}  Start Session{RESET}')
pause(0.6)

println(f'{DIM}  Reading STATUS.md...{RESET}', delay=0.3)
println(f'{DIM}  Loading tasks/lessons.md — 12 lessons{RESET}', delay=0.2)
println(f'{DIM}  Loading tasks/errors.md — 7 known bugs{RESET}', delay=0.2)
println(f'{DIM}  Loading tasks/decisions.md — 8 decisions{RESET}', delay=0.2)
println(f'{DIM}  Running drift check...{RESET}', delay=0.4)
println()
println(f'{GREEN}  Session 89 ready.{RESET}')
println(f'  Last change: Fixed Feed page "Could not load feed" (Resin $1.class bug).')
println(f'  Memory: OK — 8 files loaded. 12 lessons. What are we working on?')
pause(2.0)

# ── STEP 2: Code change ──────────────────────────────────────────────────────
println()
println(f'{DIM}  ❯ Developer adds 2 new JS functions to app.js{RESET}')
pause(1.5)

println()
println(f'{DIM}  // app.js{RESET}')
pause(0.3)
println(f'{DIM}  function handleUserLogin(email, password) {{ ... }}{RESET}', delay=0.2)
println(f'{DIM}  function validateFormInput(field, value) {{ ... }}{RESET}', delay=0.2)
pause(1.5)

# ── STEP 3: Check Drift ──────────────────────────────────────────────────────
println()
println(f'{DIM}  ❯ User types "Check Drift" in Claude Code chat{RESET}')
pause(0.8)
println()
println(f'{CYAN}  Check Drift{RESET}')
pause(0.5)

prompt('python tools/check_memory.py')
pause(0.3)
println(f'{DIM}  Scanning: 5 JS (auto), 3 CSS (auto) | memory: .claude/memory{RESET}', delay=0.2)
pause(0.5)
println(f'{YELLOW}  DRIFT DETECTED — MISSING from js_functions.md (exist in code):{RESET}')
pause(0.2)
println(f'    {GREEN}+ handleUserLogin   [app.js]{RESET}', delay=0.15)
println(f'    {GREEN}+ validateFormInput [app.js]{RESET}', delay=0.15)
pause(0.6)
println(f'{YELLOW}  DRIFT DETECTED — STALE in js_functions.md (no longer in code):{RESET}')
pause(0.2)
println(f'    {RED}- initLegacyForm    [app.js]{RESET}', delay=0.15)
pause(1.8)

println()
println(f'  Updating js_functions.md — adding 2 functions, removing 1 stale entry.')
pause(0.5)
println(f'{GREEN}  Memory updated. No drift remaining.{RESET}')
pause(2.0)

# ── STEP 4: End Session ──────────────────────────────────────────────────────
println()
println(f'{DIM}  ❯ User types "End Session" in Claude Code chat{RESET}')
pause(0.8)
println()
println(f'{CYAN}  End Session{RESET}')
pause(0.5)

println(f'{DIM}  Updating STATUS.md — Session 89{RESET}', delay=0.3)
println(f'{DIM}  Syncing js_functions.md to system memory path{RESET}', delay=0.2)
println(f'{DIM}  Running final drift check...{RESET}', delay=0.4)
pause(0.4)
println()
println(f'{GREEN}  Session 89 complete.{RESET}')
println(f'  Updated: STATUS.md, js_functions.md.')
println(f'  Memory clean. See you next session.')
println()
pause(2.5)
