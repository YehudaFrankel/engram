#!/usr/bin/env python3
"""
sync.py — Clankbrain memory sync

Personal sync:  your memory follows you across machines via your own private repo.
Team sync:      share what you learn with your whole team via a shared private repo.

Both are opt-in. Memory stays local by default.

Personal sync commands:
  python sync.py setup <url>      First-time setup — point memory at your private repo
  python sync.py push             Push memory after End Session
  python sync.py pull             Pull memory on a new machine
  python sync.py status           Check what's synced and what isn't

Team sync commands:
  python sync.py setup-team <url> Manager runs once — seeds shared repo, prints join URL
  python sync.py join <url>       New member runs once — loads team knowledge locally
  python sync.py team-push        Share what you learned. Run at End Session.
  python sync.py team-pull        Get teammates' latest. Runs automatically at Start Session.
  python sync.py team-status      Check last sync times and recent commits

Diagnostics:
  python sync.py diagnose         Show last 20 sync operations with status and any error detail
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT        = Path(__file__).resolve().parent
MEMORY_DIR  = ROOT / '.claude' / 'memory'
CONFIG_FILE = ROOT / '.claude' / '.sync-config.json'
TEAM_REPO_DIR = ROOT / '.claude' / 'team_repo'
SYNC_LOG    = ROOT / '.claude' / '.sync-log.json'
SYNC_LOG_MAX = 20

# Files shared with the team — flat name in team repo → local path relative to memory dir
TEAM_FILES = {
    'decisions.md':         'decisions.md',
    'lessons.md':           'lessons.md',
    'regret.md':            'tasks/regret.md',
    'error-lookup.md':      'error-lookup.md',
    'critical-notes.md':    'critical-notes.md',
    'agreed-flow.md':       'agreed-flow.md',
}

# guard-patterns.md and complexity_profile.md handled separately (different locations)

# Table header values to skip during merge
_HEADER_KEYS = {
    'error message', 'symptom', 'issue', 'error', 'approach',
    'what was tried', 'rejected approach', 'decision', 'what was decided',
    'date', 'session', 'title', 'flow', 'note', 'gotcha', 'notes', 'lesson',
}


# ─── CONFIG ───────────────────────────────────────────────────────────────────

def load_config():
    # Migrate team_config.json → .sync-config.json if it exists
    old_team_cfg = ROOT / '.claude' / 'team_config.json'
    if old_team_cfg.exists():
        try:
            old = json.loads(old_team_cfg.read_text(encoding='utf-8'))
            cfg = load_config_raw()
            if old.get('repo') and not cfg.get('team_repo'):
                cfg['team_repo']        = old['repo']
                cfg['team_joined']      = old.get('joined_date', old.get('setup_date', ''))
                cfg['team_last_pull']   = old.get('last_pull', '')
                cfg['team_last_push']   = old.get('last_push', '')
                save_config(cfg)
                old_team_cfg.rename(old_team_cfg.with_suffix('.json.migrated'))
                print('Migrated team_config.json → .sync-config.json')
        except Exception:
            pass
    return load_config_raw()


def load_config_raw():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding='utf-8')


# ─── SYNC LOG ─────────────────────────────────────────────────────────────────

def _log_sync(op, status, detail=''):
    """Append one entry to .sync-log.json, keep last SYNC_LOG_MAX entries."""
    try:
        entries = []
        if SYNC_LOG.exists():
            try:
                entries = json.loads(SYNC_LOG.read_text(encoding='utf-8'))
            except Exception:
                entries = []
        entries.append({
            'ts':     datetime.now().strftime('%Y-%m-%d %H:%M'),
            'op':     op,
            'status': status,
            'detail': detail,
        })
        entries = entries[-SYNC_LOG_MAX:]
        SYNC_LOG.parent.mkdir(parents=True, exist_ok=True)
        SYNC_LOG.write_text(json.dumps(entries, indent=2), encoding='utf-8')
    except Exception:
        pass  # Never let logging break the actual operation


def cmd_diagnose():
    """Print the last N sync operations with their status and any error detail."""
    if not SYNC_LOG.exists():
        print('No sync log found. Run push, pull, team-push, or team-pull first.')
        return

    try:
        entries = json.loads(SYNC_LOG.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'Could not read sync log: {e}')
        return

    if not entries:
        print('Sync log is empty.')
        return

    ok_count  = sum(1 for e in entries if e.get('status') == 'ok')
    err_count = len(entries) - ok_count

    print(f'Last {len(entries)} sync operation(s)  —  {ok_count} ok, {err_count} error(s)\n')
    for e in reversed(entries):
        status_str = 'ok   ' if e.get('status') == 'ok' else 'ERROR'
        detail = e.get('detail', '')
        line = f"  {e.get('ts', '?')}  {status_str}  {e.get('op', '?')}"
        if detail:
            line += f'\n           {detail}'
        print(line)


# ─── GIT HELPERS ──────────────────────────────────────────────────────────────

def run(cmd, cwd=None, capture=False):
    result = subprocess.run(
        cmd, shell=True, cwd=str(cwd) if cwd else None,
        capture_output=capture, text=True
    )
    return result


def git(args, cwd):
    try:
        r = subprocess.run(
            ['git'] + args, cwd=str(cwd),
            capture_output=True, text=True
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return 1, '', 'git not found — install git and ensure it is in PATH'


def check_git_auth(repo_url):
    """Best-effort check git can reach the remote. Returns (ok, hint)."""
    rc, out, err = git(['ls-remote', '--exit-code', repo_url], cwd=ROOT)
    if rc == 0:
        return True, ''
    combined = (out + err).lower()
    if 'authentication' in combined or 'permission' in combined or '403' in combined:
        hint = (
            'Git auth failed. Fix with one of:\n'
            '  gh auth login                        # GitHub CLI (recommended)\n'
            '  git config --global credential.helper manager  # Windows Credential Manager\n'
            'Then retry.'
        )
    elif 'not found' in combined or '404' in combined:
        hint = (
            f'Repo not found: {repo_url}\n'
            'Check the URL and make sure the repo exists (create it at github.com/new — set to Private).\n'
            'Then retry.'
        )
    elif 'could not resolve' in combined or 'unable to connect' in combined:
        hint = 'No network access — check your internet connection and try again.'
    else:
        hint = f'git ls-remote failed:\n  {err or out}\nCheck the repo URL and git auth, then retry.'
    return False, hint


# ─── HEALTH CHECK ─────────────────────────────────────────────────────────────

def health_check():
    """
    Check which team files actually exist locally.
    Returns (found: list, missing: list).
    """
    found, missing = [], []
    for team_name, local_rel in TEAM_FILES.items():
        path = MEMORY_DIR / local_rel
        if path.exists():
            found.append(team_name)
        else:
            missing.append((team_name, str(path)))

    gp = ROOT / '.claude' / 'rules' / 'guard-patterns.md'
    if gp.exists():
        found.append('guard-patterns.md')
    else:
        missing.append(('guard-patterns.md', str(gp)))

    return found, missing


def print_health(found, missing):
    print(f'\n  Shared files found ({len(found)}): {", ".join(found) if found else "none"}')
    if missing:
        print(f'  Not found ({len(missing)}) — will be skipped until created:')
        for name, path in missing:
            print(f'    {name}  ({path})')


# ─── MERGE LOGIC ──────────────────────────────────────────────────────────────

def _parse_rows(text):
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith('|'):
            continue
        cells = [c.strip() for c in s.split('|') if c.strip()]
        if not cells:
            continue
        if all(set(c) <= set('-: ') for c in cells):
            continue  # separator row
        rows.append(cells)
    return rows


def merge_table(local_path, remote_path):
    """Append rows from remote not already in local (keyed by first column). Returns count added."""
    if not remote_path.exists():
        return 0

    local_text  = local_path.read_text(encoding='utf-8', errors='ignore') if local_path.exists() else ''
    remote_text = remote_path.read_text(encoding='utf-8', errors='ignore')

    local_rows  = _parse_rows(local_text)
    remote_rows = _parse_rows(remote_text)

    local_keys = {r[0].lower() for r in local_rows if r}
    local_keys -= _HEADER_KEYS

    new_rows = []
    for row in remote_rows:
        if not row:
            continue
        key = row[0].lower()
        if key in _HEADER_KEYS:
            continue
        if key not in local_keys:
            new_rows.append(row)
            local_keys.add(key)

    if not new_rows:
        return 0

    local_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ['| ' + ' | '.join(row) + ' |' for row in new_rows]
    with open(local_path, 'a', encoding='utf-8') as f:
        f.write('\n' + '\n'.join(lines) + '\n')

    return len(new_rows)


def merge_guard_patterns(local_path, remote_path):
    """Append guard sections (## GUARD_ID blocks) from remote not in local. Returns count added."""
    if not remote_path.exists():
        return 0

    local_text  = local_path.read_text(encoding='utf-8', errors='ignore') if local_path.exists() else ''
    remote_text = remote_path.read_text(encoding='utf-8', errors='ignore')

    local_ids = set(re.findall(r'^## ([A-Z_0-9]+)', local_text, re.MULTILINE))

    sections = re.split(r'\n(?=## [A-Z_0-9]+)', remote_text)
    new_sections = []
    for section in sections:
        m = re.match(r'## ([A-Z_0-9]+)', section.strip())
        if m and m.group(1) not in local_ids:
            new_sections.append(section.strip())
            local_ids.add(m.group(1))

    if not new_sections:
        return 0

    local_path.parent.mkdir(parents=True, exist_ok=True)
    with open(local_path, 'a', encoding='utf-8') as f:
        f.write('\n\n' + '\n\n'.join(new_sections) + '\n')

    return len(new_sections)


# ─── COPY LOCAL → TEAM REPO ───────────────────────────────────────────────────

def _copy_to_team_repo():
    """Copy current team files into the team_repo checkout. Returns count copied."""
    copied = 0
    for team_name, local_rel in TEAM_FILES.items():
        src = MEMORY_DIR / local_rel
        if src.exists():
            shutil.copy2(src, TEAM_REPO_DIR / team_name)
            copied += 1

    gp = ROOT / '.claude' / 'rules' / 'guard-patterns.md'
    if gp.exists():
        shutil.copy2(gp, TEAM_REPO_DIR / 'guard-patterns.md')
        copied += 1

    cp = MEMORY_DIR / 'complexity_profile.md'
    if cp.exists():
        shutil.copy2(cp, TEAM_REPO_DIR / 'complexity_profile.md')
        copied += 1

    return copied


# ─── PERSONAL SYNC COMMANDS ───────────────────────────────────────────────────

def cmd_setup(repo_url):
    if not MEMORY_DIR.exists():
        print('ERROR: .claude/memory/ not found. Run Setup Memory first.')
        sys.exit(1)

    cfg = load_config()
    cfg['repo'] = repo_url
    save_config(cfg)

    git_dir = MEMORY_DIR / '.git'
    if not git_dir.exists():
        print('Initialising git in .claude/memory/...')
        run('git init', cwd=MEMORY_DIR)
        run('git checkout -b main', cwd=MEMORY_DIR, capture=True)
        run(f'git remote add origin {repo_url}', cwd=MEMORY_DIR)
    else:
        print('Git already initialised — updating remote URL...')
        run(f'git remote set-url origin {repo_url}', cwd=MEMORY_DIR)

    gitignore = MEMORY_DIR / '.gitignore'
    if not gitignore.exists():
        gitignore.write_text('*.pyc\n__pycache__/\n', encoding='utf-8')

    run('git add -A', cwd=MEMORY_DIR)
    result = run('git commit -m "Initial memory sync from clankbrain"', cwd=MEMORY_DIR, capture=True)

    if 'nothing to commit' in (result.stdout + result.stderr):
        print('Memory directory is empty — nothing committed yet.')
        print(f'\nPersonal sync configured. Remote: {repo_url}')
        print('After your first End Session, run: python sync.py push')
        return

    push_result = run('git push -u origin main', cwd=MEMORY_DIR, capture=True)
    if push_result.returncode != 0:
        print('\nPush failed. This usually means:')
        print('  1. The GitHub repo does not exist yet — create it at github.com/new (private)')
        print('  2. Authentication is needed — run: gh auth login')
        print(f'\nError: {push_result.stderr.strip()}')
        sys.exit(1)

    print(f'\nPersonal sync set up. Remote: {repo_url}')
    print('After each End Session run: python sync.py push')
    print('On a new machine run:       python sync.py pull')


def cmd_push():
    if not MEMORY_DIR.exists():
        print('ERROR: .claude/memory/ not found.')
        sys.exit(1)

    git_dir = MEMORY_DIR / '.git'
    if not git_dir.exists():
        print('Personal sync not set up. Run: python sync.py setup https://github.com/you/repo')
        sys.exit(1)

    run('git add -A', cwd=MEMORY_DIR)
    result = run('git commit -m "Session memory update"', cwd=MEMORY_DIR, capture=True)

    if 'nothing to commit' in (result.stdout + result.stderr):
        print('Memory already up to date — nothing to push.')
        return

    push_result = run('git push origin main', cwd=MEMORY_DIR, capture=True)
    if push_result.returncode == 0:
        print('Memory pushed to remote.')
        _log_sync('push', 'ok', 'Memory pushed to remote')
    else:
        detail = push_result.stderr.strip()
        print(f'Push failed: {detail}')
        print('Check your network connection and GitHub authentication.')
        _log_sync('push', 'error', detail)
        sys.exit(1)


def cmd_pull():
    cfg = load_config()
    repo_url = cfg.get('repo')
    git_dir  = MEMORY_DIR / '.git'

    if git_dir.exists():
        result = run('git pull origin main', cwd=MEMORY_DIR, capture=True)
        if result.returncode == 0:
            print('Memory pulled from remote.')
            _log_sync('pull', 'ok', 'Memory pulled from remote')
        else:
            detail = result.stderr.strip()
            print(f'Pull failed: {detail}')
            _log_sync('pull', 'error', detail)
            sys.exit(1)
    elif repo_url:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        result = run(f'git clone {repo_url} .', cwd=MEMORY_DIR, capture=True)
        if result.returncode == 0:
            print('Memory pulled from remote.')
            _log_sync('pull', 'ok', 'Cloned memory from remote')
        else:
            detail = result.stderr.strip()
            print(f'Clone failed: {detail}')
            _log_sync('pull', 'error', detail)
            sys.exit(1)
    else:
        print('No personal sync configured on this machine.')
        print('Run: python sync.py setup https://github.com/you/repo')
        sys.exit(1)


def cmd_status():
    cfg     = load_config()
    git_dir = MEMORY_DIR / '.git'

    # Personal sync status
    if not MEMORY_DIR.exists():
        print('Personal: memory directory not found — run Setup Memory first')
    elif not git_dir.exists():
        print('Personal: local only (no sync configured)')
        print('  To enable: python sync.py setup https://github.com/you/repo')
    else:
        repo_url = cfg.get('repo', 'unknown')
        print(f'Personal: {repo_url}')
        result = run('git status --short', cwd=MEMORY_DIR, capture=True)
        lines = result.stdout.strip()
        if lines:
            print('  Unpushed changes:')
            for line in lines.splitlines():
                print(f'    {line}')
            print('  Run: python sync.py push')
        else:
            print('  Up to date')

    # Team sync status
    team_repo = cfg.get('team_repo')
    if not team_repo:
        print('\nTeam:     not configured')
        print('  To set up: python sync.py setup-team https://github.com/team/shared-memory')
        return

    print(f'\nTeam:     {team_repo}')
    print(f'  Last pull: {cfg.get("team_last_pull", "never")}')
    print(f'  Last push: {cfg.get("team_last_push", "never")}')

    if TEAM_REPO_DIR.exists() and (TEAM_REPO_DIR / '.git').exists():
        rc, out, _ = git(['log', '--oneline', '-3'], cwd=TEAM_REPO_DIR)
        if rc == 0 and out:
            print('  Recent commits:')
            for line in out.splitlines():
                print(f'    {line}')
        rc2, out2, _ = git(['status', '--short'], cwd=TEAM_REPO_DIR)
        if rc2 == 0 and out2:
            print('  Unpushed local changes:')
            for line in out2.splitlines():
                print(f'    {line}')
            print('  Run: python sync.py team-push')
    else:
        print('  Team repo not found locally — re-run setup-team or join')


# ─── TEAM SYNC COMMANDS ───────────────────────────────────────────────────────

def cmd_setup_team(repo_url):
    print(f'Setting up team sync → {repo_url}')

    print('Checking git access...')
    ok, hint = check_git_auth(repo_url)
    if not ok:
        print(f'\n{hint}')
        return

    # Health check — show what will actually sync
    found, missing = health_check()
    print_health(found, missing)
    if not found:
        print('\nNo shared files found locally. Create at least one memory file first.')
        return

    if TEAM_REPO_DIR.exists() and (TEAM_REPO_DIR / '.git').exists():
        print('\nTeam repo already initialised.')
        print('Run "team-pull" to sync latest, or "team-status" to check.')
        return

    TEAM_REPO_DIR.mkdir(parents=True, exist_ok=True)

    print('\nCloning team repo...')
    rc, out, err = git(['clone', repo_url, '.'], cwd=TEAM_REPO_DIR)

    if rc != 0:
        git(['init'], cwd=TEAM_REPO_DIR)
        rc2, _, _ = git(['remote', 'add', 'origin', repo_url], cwd=TEAM_REPO_DIR)
        if rc2 != 0:
            git(['remote', 'set-url', 'origin', repo_url], cwd=TEAM_REPO_DIR)
        print('Initialised new team repo.')

    print('Seeding with your memory files...')
    _copy_to_team_repo()

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    git(['add', '-A'], cwd=TEAM_REPO_DIR)
    rc, out, err = git(['commit', '-m', f'team sync init {now}'], cwd=TEAM_REPO_DIR)

    if rc == 0 or 'nothing to commit' not in (out + err).lower():
        for branch in ('main', 'master'):
            rc2, _, _ = git(['push', '--set-upstream', 'origin', branch], cwd=TEAM_REPO_DIR)
            if rc2 == 0:
                break

    cfg = load_config()
    cfg['team_repo']      = repo_url
    cfg['team_setup']     = datetime.now().strftime('%Y-%m-%d')
    cfg['team_last_push'] = now
    save_config(cfg)

    print(f'\nTeam sync enabled.')
    print(f'Repo: {repo_url}')
    print(f'\nShare this with your team:')
    print(f'  python sync.py join {repo_url}')
    print(f'\nAt End Session, run: python sync.py team-push')


def cmd_join(repo_url):
    cfg = load_config()

    if cfg.get('team_repo'):
        print(f'Already on a team: {cfg["team_repo"]}')
        print('Run "team-status" to check, or remove "team_repo" from .claude/.sync-config.json to reset.')
        return

    if TEAM_REPO_DIR.exists() and (TEAM_REPO_DIR / '.git').exists():
        print('Team repo already exists locally. Run "team-pull" to sync.')
        return

    print(f'Joining team memory at {repo_url}...')

    print('Checking git access...')
    ok, hint = check_git_auth(repo_url)
    if not ok:
        print(f'\n{hint}')
        return

    TEAM_REPO_DIR.mkdir(parents=True, exist_ok=True)
    rc, out, err = git(['clone', repo_url, '.'], cwd=TEAM_REPO_DIR)
    if rc != 0:
        print(f'Clone failed: {err or out}')
        shutil.rmtree(TEAM_REPO_DIR, ignore_errors=True)
        return

    # Show what's in the team repo before touching anything
    available = []
    for team_name in list(TEAM_FILES.keys()) + ['guard-patterns.md', 'complexity_profile.md']:
        remote = TEAM_REPO_DIR / team_name
        if remote.exists():
            lines = len(remote.read_text(encoding='utf-8', errors='ignore').splitlines())
            available.append((team_name, lines))

    # Also run local health check
    found, missing = health_check()

    if not available:
        print('\nTeam repo is empty — nothing to merge yet.')
    else:
        print(f'\nTeam repo contains {len(available)} shared file(s):')
        for team_name, lines in available:
            print(f'  {team_name}: {lines} lines')

        if missing:
            print(f'\nNote: {len(missing)} file(s) missing locally (will be created on merge):')
            for name, path in missing:
                print(f'  {name}')

        try:
            answer = input('\nMerge these into your local memory? (y/n): ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = 'n'

        if answer != 'y':
            print('\nCancelled. Team repo cloned but not merged.')
            print('Run "python sync.py team-pull" when ready to merge.')
        else:
            total = 0
            for team_name, local_rel in TEAM_FILES.items():
                remote = TEAM_REPO_DIR / team_name
                local  = MEMORY_DIR / local_rel
                n = merge_table(local, remote)
                total += n

            remote_gp = TEAM_REPO_DIR / 'guard-patterns.md'
            local_gp  = ROOT / '.claude' / 'rules' / 'guard-patterns.md'
            n = merge_guard_patterns(local_gp, remote_gp)
            total += n

            remote_cp = TEAM_REPO_DIR / 'complexity_profile.md'
            local_cp  = MEMORY_DIR / 'complexity_profile.md'
            if remote_cp.exists() and not local_cp.exists():
                shutil.copy2(remote_cp, local_cp)
                total += 1

            print(f'\n{total} entries merged from team.')

    cfg['team_repo']      = repo_url
    cfg['team_joined']    = datetime.now().strftime('%Y-%m-%d')
    cfg['team_last_pull'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    save_config(cfg)

    print(f'\nJoined. Team memory pulls automatically at each Start Session.')
    print('Run "python sync.py team-push" at End Session to share what you learn.')


def cmd_team_pull():
    cfg = load_config()
    if not cfg.get('team_repo'):
        print('Team sync not configured.')
        print('Run: python sync.py setup-team https://github.com/team/shared-memory')
        return

    if not TEAM_REPO_DIR.exists() or not (TEAM_REPO_DIR / '.git').exists():
        print('Team repo missing locally — re-run setup-team or join.')
        return

    for branch in ('main', 'master'):
        rc, out, err = git(['pull', 'origin', branch], cwd=TEAM_REPO_DIR)
        if rc == 0 or 'already up to date' in (out + err).lower():
            break

    total     = 0
    additions = []

    for team_name, local_rel in TEAM_FILES.items():
        remote = TEAM_REPO_DIR / team_name
        local  = MEMORY_DIR / local_rel
        n = merge_table(local, remote)
        if n:
            additions.append(f'  {team_name}: +{n} new entr{"y" if n == 1 else "ies"} from team')
            total += n

    remote_gp = TEAM_REPO_DIR / 'guard-patterns.md'
    local_gp  = ROOT / '.claude' / 'rules' / 'guard-patterns.md'
    n = merge_guard_patterns(local_gp, remote_gp)
    if n:
        additions.append(f'  guard-patterns.md: +{n} new guard{"" if n == 1 else "s"} from team')
        total += n

    remote_cp = TEAM_REPO_DIR / 'complexity_profile.md'
    local_cp  = MEMORY_DIR / 'complexity_profile.md'
    if remote_cp.exists() and not local_cp.exists():
        shutil.copy2(remote_cp, local_cp)
        additions.append('  complexity_profile.md: copied from team')
        total += 1

    cfg['team_last_pull'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    save_config(cfg)

    if additions:
        print('\n'.join(additions))
        print(f'\n{total} new entries merged from team.')
        _log_sync('team-pull', 'ok', f'+{total} entries merged from team')
    else:
        print('Already up to date — no new entries from team.')
        _log_sync('team-pull', 'ok', 'already up to date')


def cmd_team_push():
    cfg = load_config()
    if not cfg.get('team_repo'):
        print('Team sync not configured.')
        print('Run: python sync.py setup-team https://github.com/team/shared-memory')
        return

    if not TEAM_REPO_DIR.exists() or not (TEAM_REPO_DIR / '.git').exists():
        print('Team repo missing locally — re-run setup-team or join.')
        return

    # Pull latest first to minimise conflicts
    for branch in ('main', 'master'):
        rc, out, err = git(['pull', 'origin', branch], cwd=TEAM_REPO_DIR)
        if rc == 0 or 'already up to date' in (out + err).lower():
            break

    count = _copy_to_team_repo()

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    git(['add', '-A'], cwd=TEAM_REPO_DIR)
    rc, out, err = git(['commit', '-m', f'team sync {now}'], cwd=TEAM_REPO_DIR)

    if 'nothing to commit' in (out + err).lower():
        print('Nothing new to push — team files already up to date.')
        return

    push_ok = False
    for branch in ('main', 'master'):
        rc2, _, _ = git(['push', 'origin', branch], cwd=TEAM_REPO_DIR)
        if rc2 == 0:
            push_ok = True
            break

    if not push_ok:
        for branch in ('main', 'master'):
            rc2, _, _ = git(['push', '--set-upstream', 'origin', branch], cwd=TEAM_REPO_DIR)
            if rc2 == 0:
                push_ok = True
                break

    cfg['team_last_push'] = now
    save_config(cfg)

    if push_ok:
        print(f'Pushed {count} team file(s) to {cfg["team_repo"]}')
        _log_sync('team-push', 'ok', f'{count} file(s) pushed to {cfg["team_repo"]}')
    else:
        print('Committed locally but push failed. Check git auth and try again.')
        _log_sync('team-push', 'error', 'committed locally but git push failed — check auth')


def cmd_team_status():
    cfg = load_config()
    if not cfg.get('team_repo'):
        print('Team sync not configured.')
        print('Run: python sync.py setup-team https://github.com/team/shared-memory')
        return

    print(f'Team repo:  {cfg["team_repo"]}')
    print(f'Last pull:  {cfg.get("team_last_pull", "never")}')
    print(f'Last push:  {cfg.get("team_last_push", "never")}')

    if TEAM_REPO_DIR.exists() and (TEAM_REPO_DIR / '.git').exists():
        rc, out, _ = git(['log', '--oneline', '-5'], cwd=TEAM_REPO_DIR)
        if rc == 0 and out:
            print('\nRecent commits:')
            for line in out.splitlines():
                print(f'  {line}')
        rc2, out2, _ = git(['status', '--short'], cwd=TEAM_REPO_DIR)
        if rc2 == 0 and out2:
            print('\nUnpushed local changes:')
            for line in out2.splitlines():
                print(f'  {line}')
            print('Run: python sync.py team-push')
    else:
        print('\nTeam repo not found locally — re-run setup-team or join.')

    found, missing = health_check()
    print_health(found, missing)

    personal = ['velocity.md', 'skill_scores.md', 'user_preferences.md', 'session_journal.md', 'todo.md']
    print(f'\nPersonal (never shared): {", ".join(personal)}')


# ─── DISPATCH ─────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # Auto-migrate team_config.json on any command
    load_config()

    cmd = args[0]

    if cmd == 'setup':
        if len(args) < 2:
            print('Usage: python sync.py setup https://github.com/you/private-repo')
            sys.exit(1)
        cmd_setup(args[1])

    elif cmd == 'push':
        cmd_push()

    elif cmd == 'pull':
        cmd_pull()

    elif cmd == 'status':
        cmd_status()

    elif cmd == 'setup-team':
        if len(args) < 2:
            print('Usage: python sync.py setup-team https://github.com/team/shared-memory')
            sys.exit(1)
        cmd_setup_team(args[1])

    elif cmd == 'join':
        if len(args) < 2:
            print('Usage: python sync.py join https://github.com/team/shared-memory')
            sys.exit(1)
        cmd_join(args[1])

    elif cmd == 'team-pull':
        cmd_team_pull()

    elif cmd == 'team-push':
        cmd_team_push()

    elif cmd == 'team-status':
        cmd_team_status()

    elif cmd == 'diagnose':
        cmd_diagnose()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
