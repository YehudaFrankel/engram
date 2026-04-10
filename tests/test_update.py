"""
tests/test_update.py — Tests for update.py

Covers: CLAUDE.md block extraction, project patching, python binary detection,
settings.json hook fixing, VERSION comparison, and memory.py write.

Run:
  pip install pytest
  pytest tests/test_update.py -v
"""

import json
import sys
from pathlib import Path

import pytest

KIT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT_ROOT))

import update  # noqa: E402


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _claude_md(commands_block, project_config="## What This Project Is\nA test app."):
    """Build a minimal CLAUDE.md with a commands block + project config."""
    return f"{commands_block}\n\n---\n\n{project_config}"


_KIT_BLOCK = """\
## Session Commands

### `Start Session`
Do start stuff.

### `End Session`
Do end stuff.

## Auto-Save Rule
Save memory at the end of every session.

---"""


_PROJECT_CLAUDE = """\
## Session Commands

### `Start Session`
OLD start stuff.

## Auto-Save Rule
OLD auto-save stuff.

---

## What This Project Is
My project.

## Tech Stack
Node.js"""


# ─── extract_kit_block ────────────────────────────────────────────────────────

def test_extract_kit_block_returns_block():
    block, err = update.extract_kit_block(_KIT_BLOCK)
    assert err is None
    assert "## Session Commands" in block
    assert "## Auto-Save Rule" in block


def test_extract_kit_block_missing_start():
    _, err = update.extract_kit_block("## Something Else\nno commands here")
    assert err is not None
    assert "Session Commands" in err


def test_extract_kit_block_missing_end():
    text = "## Session Commands\n\nDo stuff.\n\n## Something Else\nno crash section"
    _, err = update.extract_kit_block(text)
    assert err is not None


# ─── apply_to_project ─────────────────────────────────────────────────────────

def test_apply_to_project_replaces_commands_block():
    updated, err = update.apply_to_project(_PROJECT_CLAUDE, _KIT_BLOCK)
    assert err is None
    assert "OLD start stuff" not in updated
    assert "Do start stuff." in updated
    assert "My project." in updated          # project config preserved
    assert "Node.js" in updated             # tech stack preserved


def test_apply_to_project_preserves_content_below_separator():
    updated, err = update.apply_to_project(_PROJECT_CLAUDE, _KIT_BLOCK)
    assert err is None
    assert "## What This Project Is" in updated
    assert "## Tech Stack" in updated


def test_apply_to_project_missing_commands_heading():
    bad = "## Random Heading\nsome content\n---\n## What This Project Is\nstuff"
    _, err = update.apply_to_project(bad, _KIT_BLOCK)
    assert err is not None


def test_apply_to_project_fallback_heading():
    project = _PROJECT_CLAUDE.replace("## Session Commands", "## Commands")
    updated, err = update.apply_to_project(project, _KIT_BLOCK)
    assert err is None
    assert "Do start stuff." in updated


def test_apply_to_project_quick_commands_heading():
    project = _PROJECT_CLAUDE.replace("## Session Commands", "## Quick Commands")
    updated, err = update.apply_to_project(project, _KIT_BLOCK)
    assert err is None
    assert "Do start stuff." in updated


# ─── detect_commands_heading ──────────────────────────────────────────────────

def test_detect_commands_heading_standard():
    heading, label = update.detect_commands_heading("## Session Commands\nstuff")
    assert heading == "## Session Commands"
    assert label is None   # no note needed for standard heading


def test_detect_commands_heading_fallback():
    heading, label = update.detect_commands_heading("## Quick Commands\nstuff")
    assert heading == "## Quick Commands"
    assert label is not None


def test_detect_commands_heading_not_found():
    heading, err = update.detect_commands_heading("## Random\nstuff")
    assert heading is None
    assert "Tried" in err


# ─── _detect_python_bin ───────────────────────────────────────────────────────

def test_detect_python_bin_returns_string():
    result = update._detect_python_bin()
    assert result in ("python", "python3")


def test_detect_python_bin_works():
    """The detected binary should actually run."""
    import subprocess
    result = update._detect_python_bin()
    r = subprocess.run([result, "--version"], capture_output=True)
    assert r.returncode == 0


# ─── settings.json hook fixing ────────────────────────────────────────────────

def test_settings_hooks_fixed_to_python3(tmp_path):
    """update.py patches 'python tools/memory.py' → correct binary in settings.json."""
    settings = {
        "hooks": {
            "UserPromptSubmit": [{"hooks": [{"command": "python tools/memory.py --capture-correction"}]}],
            "Stop": [{"hooks": [{"command": "python tools/memory.py --stop-check"}]}]
        }
    }
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(json.dumps(settings), encoding="utf-8")

    import re
    python_bin = update._detect_python_bin()
    text = settings_path.read_text(encoding="utf-8")
    fixed = re.sub(r'\bpython3?\b(?= tools/memory\.py)', python_bin, text)
    settings_path.write_text(fixed, encoding="utf-8")

    result = json.loads(settings_path.read_text(encoding="utf-8"))
    cmd = result["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert cmd.startswith(python_bin)


def test_settings_hooks_no_change_if_already_correct(tmp_path):
    """If hooks already use the right binary, settings.json is unchanged."""
    import re
    python_bin = update._detect_python_bin()
    settings = {"hooks": {"UserPromptSubmit": [{"hooks": [
        {"command": f"{python_bin} tools/memory.py --capture-correction"}
    ]}]}}
    settings_path = tmp_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    original = json.dumps(settings)
    settings_path.write_text(original, encoding="utf-8")

    text = settings_path.read_text(encoding="utf-8")
    fixed = re.sub(r'\bpython3?\b(?= tools/memory\.py)', python_bin, text)
    assert fixed == original   # no change


# ─── _read_local_version ──────────────────────────────────────────────────────

def test_read_local_version_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(update, "ROOT", tmp_path)
    (tmp_path / "VERSION").write_text("2.6.4\n", encoding="utf-8")
    assert update._read_local_version() == "2.6.4"


def test_read_local_version_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(update, "ROOT", tmp_path)
    assert update._read_local_version() is None


def test_read_local_version_strips_whitespace(tmp_path, monkeypatch):
    monkeypatch.setattr(update, "ROOT", tmp_path)
    (tmp_path / "VERSION").write_text("  2.5.0  \n", encoding="utf-8")
    assert update._read_local_version() == "2.5.0"


# ─── memory.py written during update ─────────────────────────────────────────

def test_memory_py_written_when_fetched(tmp_path):
    """If kit_memory content is available, it gets written to tools/memory.py."""
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    kit_memory_content = "# memory.py stub\nprint('ok')\n"
    (tools_dir / "memory.py").write_text(kit_memory_content, encoding="utf-8")
    result = (tools_dir / "memory.py").read_text(encoding="utf-8")
    assert result == kit_memory_content


def test_memory_py_not_written_when_none(tmp_path):
    """If kit_memory is None (fetch failed), tools/memory.py is untouched."""
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    original = "# original\n"
    mem_path = tools_dir / "memory.py"
    mem_path.write_text(original, encoding="utf-8")

    kit_memory = None
    if kit_memory:
        mem_path.write_text(kit_memory, encoding="utf-8")

    assert mem_path.read_text(encoding="utf-8") == original


# ─── migrate_old_refs ─────────────────────────────────────────────────────────

def test_migrate_old_refs_rewrites_old_repo_name(tmp_path, monkeypatch):
    monkeypatch.setattr(update, "ROOT", tmp_path)
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "See YehudaFrankel/claude-recall for more info.\n",
        encoding="utf-8"
    )
    update.migrate_old_refs()
    content = claude_md.read_text(encoding="utf-8")
    assert "clankbrain" in content
    assert "claude-recall" not in content


def test_migrate_old_refs_no_change_if_current(tmp_path, monkeypatch):
    monkeypatch.setattr(update, "ROOT", tmp_path)
    claude_md = tmp_path / "CLAUDE.md"
    original = "See YehudaFrankel/clankbrain for more info.\n"
    claude_md.write_text(original, encoding="utf-8")
    update.migrate_old_refs()
    assert claude_md.read_text(encoding="utf-8") == original
