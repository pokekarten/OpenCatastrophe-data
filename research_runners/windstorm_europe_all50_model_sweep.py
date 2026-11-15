# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Sweep all source-selected storms through the fictional three-site model."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research_runners.windstorm_europe_model_v1 import execute


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hazard', type=Path, required=True)
    p.add_argument('--curves', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(argv)
    if args.output.exists():
        p.error('refuse overwrite')
    fixture = (ROOT / 'research/fixtures/windstorm_europe_v1_synthetic.toml').read_bytes()
    config = tomllib.loads(fixture.decode())
    config['hazard_source'] = str(args.hazard.resolve())
    for spec in config['responses'].values():
        spec['path'] = str(args.curves.resolve())
    config['year_ids'] = [1]
    results = []
    for index in range(50):
        scenario = copy.deepcopy(config)
        scenario['occurrences'] = [dict(year_id=1, occurrence_id=f'source-event-{index}',
                                        sample_id=0, storm_index=index)]
        try:
            result = execute(scenario, Path('/'))
            results.append(dict(storm_index=index, status='executed',
                                occurrence=result['occurrences'][0],
                                hazard_provenance=result['hazard_provenance']))
        except ValueError as exc:
            results.append(dict(storm_index=index, status='blocked', reason=str(exc)))
    completed = sum(row['status'] == 'executed' for row in results)
    receipt = dict(schema='WINDSTORM_ALL50_MODEL_SWEEP_V1',
                   annual_frequency_established=False, fictional_exposure=True,
                   source_fixture_sha256=hashlib.sha256(fixture).hexdigest(),
                   hazard_sha256=hashlib.sha256(args.hazard.read_bytes()).hexdigest(),
                   curves_sha256=hashlib.sha256(args.curves.read_bytes()).hexdigest(),
                   completed=completed, blocked=50-completed,
                   source_selected_events=results)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
    print(json.dumps(dict(completed=completed, blocked=50-completed)))
    return 0 if completed == 50 else 1


if __name__ == '__main__':
    raise SystemExit(main())
