[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    # All mutations stay in disposable containers, never in repository manifests.
    $pythonCheck = @'
from pathlib import Path
import hashlib
import shutil
import subprocess
import tempfile

path = Path(tempfile.mkdtemp())
for name in ("pyproject.toml", "uv.lock"):
    shutil.copy(Path("/app") / name, path / name)
lock = path / "uv.lock"
before = hashlib.sha256(lock.read_bytes()).hexdigest()
manifest = path / "pyproject.toml"
manifest.write_text(manifest.read_text().replace('version = "0.1.0"', 'version = "0.1.1"'))
result = subprocess.run(
    ["uv", "sync", "--locked", "--no-dev", "--project", str(path)],
    capture_output=True, text=True,
)
assert result.returncode != 0 and "lockfile" in (result.stdout + result.stderr).lower()
assert hashlib.sha256(lock.read_bytes()).hexdigest() == before
print("PASS: uv sync --locked rejects manifest drift without changing uv.lock")
'@
    docker compose run --rm --no-deps -e UV_PROJECT_ENVIRONMENT=/tmp/drift-venv -e UV_CACHE_DIR=/tmp/drift-cache backend python -c $pythonCheck
    if ($LASTEXITCODE -ne 0) { throw 'Python lockfile drift check failed.' }

    $nodeCheck = @'
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';

const path = mkdtempSync(join(tmpdir(), 'lock-check-'));
for (const name of ['package.json', 'package-lock.json', '.npmrc']) {
  copyFileSync(join('/app', name), join(path, name));
}
const lock = join(path, 'package-lock.json');
const hash = () => createHash('sha256').update(readFileSync(lock)).digest('hex');
const before = hash();
const manifestPath = join(path, 'package.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
// Verified registry fixture only; the repository remains pinned to 7.0.2.
manifest.devDependencies.typescript = '5.9.3';
writeFileSync(manifestPath, JSON.stringify(manifest));
const result = spawnSync('npm', ['ci', '--ignore-scripts', '--no-audit', '--no-fund'], {
  cwd: path, encoding: 'utf8',
});
assert.notEqual(result.status, 0);
assert.match(result.stdout + result.stderr, /in sync|Invalid:|Missing:/i);
assert.equal(hash(), before);
console.log('PASS: npm ci rejects manifest drift without changing package-lock.json');
'@
    docker compose run --rm --no-deps frontend node --input-type=module -e $nodeCheck
    if ($LASTEXITCODE -ne 0) { throw 'npm lockfile drift check failed.' }
}
finally {
    Pop-Location
}
