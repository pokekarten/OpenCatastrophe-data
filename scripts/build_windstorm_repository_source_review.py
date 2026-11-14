# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Render windstorm candidates from existing canonical landscape catalogues."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/research/windstorm-repository-source-review.md'


def render():
    rows = []
    for path in sorted((ROOT / 'landscape').glob('*.json')):
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            continue
        for entry in data.get('entries', []):
            if not isinstance(entry, dict):
                continue
            categories = entry.get('categories', [])
            if 'windstorm' not in categories:
                continue
            identity = entry.get('candidate_id', '')
            name = str(entry.get('name', identity)).replace('|', '\\|')
            rows.append(f'| `{identity}` | {name} | [{path.name}](../../landscape/{path.name}) |')
    return '''<!-- SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- GENERATED FILE — DO NOT EDIT DIRECTLY; scripts/build_windstorm_repository_source_review.py -->

# Windstorm: Quellen aus den vorhandenen Repository-Katalogen

Diese Übersicht erfasst alle Einträge mit der kanonischen Kategorie
`windstorm` aus `landscape/*.json`. Mehrfachnennungen in verschiedenen
Katalogen bleiben sichtbar. Gebäude-, Bewertungs- und allgemeine
Wetterkataloge ohne diese Kategorie sind nicht vollständig erfasst.
Die Aufnahme belegt weder einen Download noch die Eignung als Modelleingabe.
Quellenstatus, Lizenz und Einschränkungen bleiben im jeweiligen Katalog
maßgeblich. Die Übersicht prüft keine aktuellen Provider-Endpunkte.

| Kandidat | Quelle | Kanonischer Katalog |
|---|---|---|
''' + '\n'.join(rows) + '\n'


if __name__ == '__main__':
    OUTPUT.write_text(render(), encoding='utf-8')
