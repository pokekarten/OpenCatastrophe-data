# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Adversarial synthetic metadata ZIPs; NOT original 2007 instrument proof."""
from __future__ import annotations

from io import BytesIO
from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.dwd_kyrill_2007_station_metadata_probe_v0 import (
    inspect_original_metadata, MetadataProbeBlocked, classify, CONTRACT, STATIONS,
)


def make_zip(*, omit=(), extra=None, traversal=False, symlink=False) -> bytes:
    data={
      "Metadaten_Geographie_00433.txt": "STATIONS_ID;von;bis;LAT;LON\n00433;2000;2010;52.47;13.39\n",
      "Metadaten_Geraete_00433.txt": "STATIONS_ID;von;bis;Geraetehoehe\n00433;2000;2010;10\n",
      "Metadaten_Parameter_00433.txt": "STATIONS_ID;Parameter\n00433;FX_10\n",
      "Metadaten_Stationsname_00433.txt": "STATIONS_ID;Name\n00433;Berlin-Tempelhof\n",
    }
    for k in omit: data.pop(k)
    if extra:data.update(extra)
    if traversal:data['../Metadaten_Geraete_00433.txt']='unsafe\n'
    b=BytesIO()
    with ZipFile(b,"w",ZIP_DEFLATED) as z:
      for name,source in data.items():
        if symlink and 'Geographie' in name:
          info=ZipInfo(name)
          info.create_system=3
          info.external_attr=(0o120777 << 16)
          z.writestr(info,source)
        else:z.writestr(name,source)
    return b.getvalue()

class MetadataProbeTests(unittest.TestCase):
    def test_classifications(self):
        for key, expected in [('Metadaten_Geographie','geography'),('Metadaten_Geraete','instruments'),('Metadaten_Parameter','parameters'),('Metadaten_Stationsname','station_names')]:
            self.assertEqual(classify(key),expected)
        self.assertIsNone(classify('produkt_wind_foo'))

    def test_all_stations_but_no_2007_scientific_admission(self):
        for station in STATIONS:
            with self.subTest(station=station):
                z=make_zip()
                r=inspect_original_metadata(z,station=station)
                self.assertEqual(r['original_zip_sha256'],sha256(z).hexdigest())
                self.assertEqual(r['contract'],CONTRACT)
                self.assertEqual(len(r['metadata_schemas_reproduced']),4)
                self.assertFalse(r['source_2007_instrument_validity_resolved'])
                self.assertFalse(r['source_2007_sensor_height_resolved'])
                self.assertFalse(r['QN1_data_promoted_to_QN3'])
                self.assertIsNone(r['annual_AAL'])

    def test_reject_missing_required_classes(self):
        for k in ['Metadaten_Geographie_00433.txt','Metadaten_Geraete_00433.txt','Metadaten_Parameter_00433.txt']:
            with self.subTest(k=k):
                report=inspect_original_metadata(make_zip(omit=(k,)),station='00433')
                self.assertFalse(report['original_metadata_schema_unambiguous'])
                self.assertFalse(report['source_2007_instrument_validity_resolved'])

    def test_reject_duplicate_class(self):
        z=make_zip(extra={'copy_Metadaten_Geraete_00433.txt':'foo\n'})
        report=inspect_original_metadata(z,station='00433')
        self.assertFalse(report['original_metadata_schema_unambiguous'])

    def test_reject_invalid_zip_and_station_id(self):
        for inp in (None,b'',b'not a zip',{},'zip'):
            with self.subTest(input=str(type(inp))):
                with self.assertRaises(MetadataProbeBlocked):
                    inspect_original_metadata(inp,station='00433')
        with self.assertRaises(MetadataProbeBlocked):inspect_original_metadata(make_zip(),station='03478')

    def test_reject_path_traversal(self):
        with self.assertRaises(MetadataProbeBlocked):inspect_original_metadata(make_zip(traversal=True),station='00433')

    def test_reject_symlink(self):
        with self.assertRaises(MetadataProbeBlocked):inspect_original_metadata(make_zip(symlink=True),station='00433')

    def test_output_does_not_claim_measured_storm_damage_or_annual_frequency(self):
        r=inspect_original_metadata(make_zip(),station='00433')
        self.assertFalse(r['calibrated_physical_or_insured_damage'])
        self.assertFalse(r['fit_of_any_ERA5_wind_model'])
        self.assertIsNone(r['annual_OEP'])
        self.assertNotIn('FX_10_measurement',json.dumps(r))

    def test_no_observation_member_retained(self):
        r=inspect_original_metadata(make_zip(extra={'produkt_00433.txt':'20070118;9999\n'}),station='00433')
        self.assertEqual(len(r['metadata_schemas_reproduced']),4)
        self.assertNotIn('9999',json.dumps(r))

    def test_members_and_headers_are_bounded(self):
        z=make_zip(extra={'Metadaten_Geographie_more_00433.txt':'x'*500000})
        with self.assertRaises(MetadataProbeBlocked): inspect_original_metadata(z,station='00433')

    def test_cp1252_metadata_source_supported(self):
        z=make_zip(extra={'Metadaten_Stationsname_00433.txt':b'STATIONS_ID;Name\n00433;M\xfcnchen\n'})
        r=inspect_original_metadata(z,station='00433')
        self.assertTrue(any(x['encoding']=='cp1252' for x in r['metadata_schemas_reproduced']))

if __name__=='__main__':unittest.main()
