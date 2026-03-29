#!/usr/bin/env node

'use strict';

const https    = require('https');
const fs       = require('fs');
const path     = require('path');
const os       = require('os');
const { spawnSync } = require('child_process');

const SETUP_URL = 'https://raw.githubusercontent.com/YehudaFrankel/clankbrain/main/setup.py';

// ── Find Python ──────────────────────────────────────────────────────────────
function findPython() {
  for (const cmd of ['python3', 'python']) {
    try {
      const r = spawnSync(cmd, ['--version'], { encoding: 'utf8' });
      if (r.status === 0) return cmd;
    } catch (_) {}
  }
  return null;
}

// ── Download file ─────────────────────────────────────────────────────────────
function download(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode} fetching ${url}`));
        return;
      }
      res.pipe(file);
      file.on('finish', () => file.close(resolve));
    }).on('error', reject);
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main() {
  console.log('\nClankbrain — setting up memory for Claude Code...\n');

  const python = findPython();
  if (!python) {
    console.error('Error: Python 3.7+ is required.');
    console.error('Download from https://python.org/downloads (check "Add to PATH")\n');
    process.exit(1);
  }

  const tmp = path.join(os.tmpdir(), `clankbrain_setup_${Date.now()}.py`);

  try {
    process.stdout.write('Fetching setup.py from GitHub... ');
    await download(SETUP_URL, tmp);
    console.log('done.\n');

    const result = spawnSync(python, [tmp], {
      stdio: 'inherit',
      cwd:   process.cwd()
    });

    process.exit(result.status || 0);
  } catch (err) {
    console.error(`\nError: ${err.message}`);
    console.error('Check your internet connection and try again.\n');
    process.exit(1);
  } finally {
    try { fs.unlinkSync(tmp); } catch (_) {}
  }
}

main();
