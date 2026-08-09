# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 1024 * 1024
BLOCKED_SUFFIXES = {'.csv','.tsv','.parquet','.feather','.geojson','.jsonl','.ndjson','.arrow','.avro','.orc','.shp','.shx','.dbf','.prj','.cpg','.las','.laz','.nc','.nc4','.grib','.grib2','.h5','.hdf5','.gpkg','.sqlite','.db','.zip','.7z','.tar','.gz','.pdf'}
SECRET_MARKERS = ['gh'+'p_', 'github_'+'pat_', 'AK'+'IA', 'BEGIN '+'RSA PRIVATE KEY', 'BEGIN '+'OPENSSH PRIVATE KEY']
EXEMPT_LICENSE = {'LICENSE'}

def git(*args: str) -> str:
    cp = subprocess.run(['git', *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cp.returncode:
        raise RuntimeError(cp.stderr.strip() or 'git command failed')
    return cp.stdout

def tracked() -> list[str]:
    return [x for x in git('ls-files').splitlines() if x]

def check_hygiene() -> None:
    entries = git('ls-files','-s').splitlines()
    for line in entries:
        mode, _, _, path = line.split(maxsplit=3)
        if mode != '100644':
            raise AssertionError(f'non-regular tracked entry: {path} ({mode})')
    for rel in tracked():
        p = ROOT / rel
        if p.stat().st_size > MAX_BYTES:
            raise AssertionError(f'tracked file exceeds 1 MiB: {rel}')
        lower = rel.lower()
        if any(lower.endswith(s) for s in BLOCKED_SUFFIXES):
            raise AssertionError(f'high-risk data/archive format is blocked by default: {rel}')
        if rel in EXEMPT_LICENSE or rel.startswith('LICENSES/'):
            continue
        text = p.read_text(encoding='utf-8')
        head = '\n'.join(text.splitlines()[:14])
        if 'SPDX-License-Identifier:' not in head:
            raise AssertionError(f'missing SPDX licence metadata: {rel}')
        for marker in SECRET_MARKERS:
            if marker in text:
                raise AssertionError(f'secret-like marker detected: {rel}')

def main() -> int:
    try:
        if git('rev-parse','--is-inside-work-tree').strip() != 'true':
            raise AssertionError('must run from a Git checkout')
        check_hygiene()
        commands = [
            [sys.executable,'-m','compileall','-q','scripts','tests'],
            [sys.executable,'-m','unittest','discover','-s','tests','-p','test*.py','-v'],
            ['git','diff','--check'],
            ['git','diff','--cached','--check'],
        ]
        for cmd in commands:
            cp = subprocess.run(cmd, cwd=ROOT)
            if cp.returncode:
                return cp.returncode
        print(f'PASS: public foundation checks succeeded ({len(tracked())} tracked files)')
        return 0
    except (AssertionError, RuntimeError, UnicodeDecodeError) as exc:
        print(f'BLOCKED: {exc}')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
