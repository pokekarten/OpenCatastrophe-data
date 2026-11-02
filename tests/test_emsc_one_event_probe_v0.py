# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline deterministic EMSC adapter regression tests (all examples synthetic)."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import Mock

from research_runners.emsc_one_event_probe_v0 import (
    URL, MAX_BYTES, PARAMS, ProbeBlocked, fetch_one, main, validate_response,
)


def valid():
    return {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [8.0, 50.0, 10.0]},
         'properties': {'source_id': 'synthetic-event-1', 'time': '2025-10-01T12:00:00Z', 'mag': 4.3}}
    ]}


def check(data=None):
    return validate_response(json.dumps(valid() if data is None else data).encode(), media_type='application/json')


class EmscOneEventTests(unittest.TestCase):
    def test_fixed_single_event_query(self):
        self.assertIn('limit=1', URL)
        self.assertIn('includeallorigins=false', URL)
        self.assertIn('includearrivals=false', URL)
        self.assertNotIn('offset=', URL)
        self.assertEqual(len(PARAMS), 6)

    def test_accepted_synthetic_response_still_unadmitted(self):
        result = check()
        self.assertEqual(result['event_count'], 1)
        for field in ['raw_data_admitted', 'hazard_model_admitted', 'insurer_exposure_admitted',
                      'insured_loss_computed', 'original_event_completeness_verified']:
            self.assertIs(result[field], False)

    def test_provider_error_is_not_success(self):
        with self.assertRaises(ProbeBlocked):
            check({'error': {'message': 'unsupported'}})

    def test_empty_feature_collection_rejected(self):
        d = valid(); d['features'] = []
        with self.assertRaises(ProbeBlocked):
            check(d)

    def test_two_events_rejected(self):
        d = valid(); d['features'] *= 2
        with self.assertRaises(ProbeBlocked):
            check(d)

    def test_geojson_structure_rejected(self):
        d = valid(); d['features'][0]['geometry']['type'] = 'Polygon'
        with self.assertRaises(ProbeBlocked):
            check(d)

    def test_bad_coordinates_and_boolean_rejected(self):
        for value in [False, 181, float('inf'), None, '5']:
            d = valid(); d['features'][0]['geometry']['coordinates'][0] = value
            with self.assertRaises(ProbeBlocked):
                check(d)

    def test_bad_event_time_rejected(self):
        for value in ['2025-13-01T12:00:00Z', 'yesterday', '2025-10-01']:
            d = valid(); d['features'][0]['properties']['time'] = value
            with self.assertRaises(ProbeBlocked):
                check(d)

    def test_bad_event_id_rejected(self):
        d = valid(); d['features'][0]['properties']['source_id'] = '../../secrets'
        with self.assertRaises(ProbeBlocked):
            check(d)

    def test_invalid_magnitude_rejected(self):
        d = valid(); d['features'][0]['properties']['mag'] = True
        with self.assertRaises(ProbeBlocked):
            check(d)

    def test_duplicate_key_and_nan_rejected(self):
        for raw in [b'{"type":"FeatureCollection","type":"FeatureCollection"}', b'{"type":NaN}']:
            with self.assertRaises(ProbeBlocked):
                validate_response(raw, media_type='application/json')

    def test_non_json_and_status_rejected(self):
        raw = json.dumps(valid()).encode()
        for kwargs in [{'media_type': 'text/plain'}, {'media_type': 'application/json', 'status': 204}]:
            with self.assertRaises(ProbeBlocked):
                validate_response(raw, **kwargs)

    def test_oversized_and_empty_rejected(self):
        for raw in [b'', b' ' * (MAX_BYTES + 1)]:
            with self.assertRaises(ProbeBlocked):
                validate_response(raw, media_type='application/json')

    def test_local_fixture_cli_is_offline_and_has_no_live_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'synthetic.json'; p.write_text(json.dumps(valid()), encoding='utf-8')
            out = io.StringIO()
            with redirect_stdout(out):
                result = main(['--fixture', str(p)])
            self.assertEqual(result, 0)
            parsed = json.loads(out.getvalue())
            self.assertIsNone(parsed['retrieval_utc'])
            self.assertFalse(parsed['network_provider_get_performed'])
            self.assertFalse(parsed['external_bytes_persisted'])

    def test_no_symlink_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'synthetic.json'; p.write_text(json.dumps(valid()), encoding='utf-8')
            (Path(tmp)/'link.json').symlink_to(p)
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(['--fixture', str(Path(tmp)/'link.json')]), 1)

    def test_fake_network_client_does_not_follow_or_accept_wrong_url(self):
        raw = json.dumps(valid()).encode()
        class Response:
            status = 200
            headers = {'Content-Type': 'application/json', 'Content-Length': str(len(raw))}
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def geturl(self): return URL + '?mutated=1'
            def read(self, n): return raw
        client = Mock(); client.open.return_value = Response()
        with self.assertRaises(ProbeBlocked):
            fetch_one(opener=client)

    def test_fake_network_client_blocks_oversize_before_read(self):
        class Response:
            status = 200
            headers = {'Content-Type': 'application/json', 'Content-Length': str(MAX_BYTES + 1)}
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def geturl(self): return URL
            def read(self, n): raise AssertionError('must not read oversized body')
        client = Mock(); client.open.return_value = Response()
        with self.assertRaises(ProbeBlocked):
            fetch_one(opener=client)


if __name__ == '__main__':
    unittest.main()
