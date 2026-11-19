# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only security and data-grain regression tests for BNPB XLSX preflight."""
import hashlib
import io
import unittest
import warnings
import zipfile

from research_runners import bnpb_2025_damage_workbook_preflight_v0 as m

N=m.NS
R=m.REL
P=m.PKG
CT='http://schemas.openxmlformats.org/package/2006/content-types'
BASE={
    '[Content_Types].xml':f'<Types xmlns="{CT}"/>'.encode(),
    'xl/workbook.xml':f'<workbook xmlns="{N}" xmlns:r="{R}"><sheets><sheet name="SYNTHETIC_BNPB" sheetId="1" r:id="rId1"/></sheets></workbook>'.encode(),
    'xl/_rels/workbook.xml.rels':f'<Relationships xmlns="{P}"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>'.encode(),
}


def cell(ref, val, kind='inlineStr'):
    if kind=='inlineStr':return f'<c r="{ref}" t="inlineStr"><is><t>{val}</t></is></c>'
    return f'<c r="{ref}" t="{kind}"><v>{val}</v></c>'


def sheet(headers, data):
    if len(headers)>25:raise ValueError
    rows=[]
    for ix, vals in enumerate([headers,*data], start=1):
        line=[]
        for col,(v,k) in enumerate(vals):
            if v is not None:line.append(cell(chr(65+col)+str(ix),v,k))
        rows.append(f'<row r="{ix}">{"".join(line)}</row>')
    return f'<worksheet xmlns="{N}"><sheetData>{"".join(rows)}</sheetData></worksheet>'.encode()


def workbook(sheetxml, **additional):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        for path,blob in {**BASE,'xl/worksheets/sheet1.xml':sheetxml,**additional}.items():
            z.writestr(path,blob)
    return b.getvalue()

PROVINCE=[('Provinsi','inlineStr'),('BANJIR','inlineStr'),('GEMPABUMI','inlineStr'),('TANAH LONGSOR','inlineStr'),('KEKERINGAN','inlineStr'),('TSUNAMI','inlineStr')]
PROWS=[ [('Aceh','inlineStr'),('12','n'),('0','n'),('2','n'),('-','inlineStr'),('','inlineStr')], [('Sumut','inlineStr'),('0','n'),('1','n'),('4','n'),('5','inlineStr'),('–','inlineStr')] ]
SUMMARY=[('Jenis Bencana','inlineStr'),('Jumlah Kejadian','inlineStr'),('Rumah Rusak Berat','inlineStr'),('Rumah Rusak Sedang','inlineStr'),('Rumah Rusak Ringan','inlineStr')]
SROWS=[ [('Banjir','inlineStr'),('2','n'),('1','n'),('3','n'),('5','n')], [('Tsunami','inlineStr'),('0','n'),('0','n'),('0','n'),('0','n')] ]


class BnpbPreflightTests(unittest.TestCase):
    def test_province_grain_and_missing_are_not_zero(self):
        raw=workbook(sheet(PROVINCE, PROWS))
        out=m.inspect_original(raw,resource='province_houses',expected_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(out['source_data_row_count'],2)
        self.assertEqual(out['province_key_count'],2)
        self.assertEqual(out['missing_cell_counts_not_zero']['kekeringan'],1)
        self.assertEqual(out['missing_cell_counts_not_zero']['tsunami'],2)
        self.assertTrue(out['independent_sha256_pin_verified'])
        self.assertFalse(out['model_input_admitted'])
        self.assertFalse(out['province_peril_severity_crosswalk_established'])
        self.assertNotIn('Aceh',str(out))
        self.assertNotIn('Sumut',str(out))

    def test_summary_grain_is_separate(self):
        out=m.inspect_original(workbook(sheet(SUMMARY,SROWS)),resource='peril_severity_summary')
        self.assertEqual(out['source_data_row_count'],2)
        self.assertIsNone(out['province_key_count'])
        self.assertFalse(out['province_peril_severity_crosswalk_established'])
        self.assertEqual(out['missing_cell_counts_not_zero']['rumah rusak berat'],0)

    def test_national_total_is_excluded_from_province_count(self):
        total = [('Indonesia','inlineStr'),('12','n'),('1','n'),('6','n'),('5','inlineStr'),('','inlineStr')]
        # Missing tsunami/detail values prevent an authoritative reconciliation.
        with self.assertRaisesRegex(m.BnpbWorkbookError, 'duplicate or incomplete national source total'):
            m.inspect_original(workbook(sheet(PROVINCE,[*PROWS,total])),resource='province_houses')
        rows = [
            [('Aceh','inlineStr'),('12','n'),('0','n'),('2','n'),('5','inlineStr'),('0','inlineStr')],
            [('Sumut','inlineStr'),('0','n'),('1','n'),('4','n'),('0','inlineStr'),('0','inlineStr')],
            [('INDONESIA','inlineStr'),('12','n'),('1','n'),('6','n'),('5','inlineStr'),('0','inlineStr')],
        ]
        receipt=m.inspect_original(workbook(sheet(PROVINCE,rows)),resource='province_houses')
        self.assertEqual(receipt['province_key_count'],2)
        self.assertEqual(receipt['source_data_row_count'],2)
        self.assertEqual(receipt['national_total_rows_excluded'],1)
        self.assertTrue(receipt['national_total_reconciled'])

    def test_national_total_mismatch_blocks_instead_of_double_counting(self):
        rows = [
            [('Aceh','inlineStr'),('12','n'),('0','n'),('2','n'),('5','inlineStr'),('0','inlineStr')],
            [('Sumut','inlineStr'),('0','n'),('1','n'),('4','n'),('0','inlineStr'),('0','inlineStr')],
            [('INDONESIA','inlineStr'),('13','n'),('1','n'),('6','n'),('5','inlineStr'),('0','inlineStr')],
        ]
        with self.assertRaisesRegex(m.BnpbWorkbookError,'national source total mismatch'):
            m.inspect_original(workbook(sheet(PROVINCE,rows)),resource='province_houses')

    def test_summary_grand_total_not_an_observation(self):
        rows=[*SROWS,[('Total','inlineStr'),('2','n'),('1','n'),('3','n'),('5','n')]]
        receipt=m.inspect_original(workbook(sheet(SUMMARY,rows)),resource='peril_severity_summary')
        self.assertEqual(receipt['source_data_row_count'],2)
        self.assertEqual(receipt['national_total_rows_excluded'],1)
        self.assertTrue(receipt['national_total_reconciled'])

    def test_wrong_resource_identity_is_blocked(self):
        raw=workbook(sheet(PROVINCE,PROWS))
        with self.assertRaisesRegex(m.BnpbWorkbookError,'exactly one sheet'):
            m.inspect_original(raw,resource='peril_severity_summary')
        with self.assertRaisesRegex(m.BnpbWorkbookError,'unknown BNPB'):
            m.inspect_original(raw,resource='arbitrary')

    def test_bad_hash_or_unpinned(self):
        raw=workbook(sheet(PROVINCE,PROWS))
        out=m.inspect_original(raw,resource='province_houses')
        self.assertFalse(out['independent_sha256_pin_verified'])
        for pin in ['0'*64,'ABC','A'*64]:
            with self.assertRaisesRegex(m.BnpbWorkbookError,'SHA-256'):
                m.inspect_original(raw,resource='province_houses',expected_sha256=pin)

    def test_missing_not_observed_as_zero(self):
        rows=[list(r) for r in PROWS]
        rows[0][1]=('n/a','inlineStr')
        out=m.inspect_original(workbook(sheet(PROVINCE,rows)),resource='province_houses')
        self.assertEqual(out['missing_cell_counts_not_zero']['banjir'],1)

    def test_bad_counts_fail_closed(self):
        for val in ['-5','1.5','not available','NaN','100000001','Infinity']:
            rows=[list(r) for r in PROWS];rows[0][1]=(val,'inlineStr')
            with self.subTest(val=val),self.assertRaises(m.BnpbWorkbookError):
                m.inspect_original(workbook(sheet(PROVINCE,rows)),resource='province_houses')

    def test_duplicate_provinces_rejected(self):
        rows=[list(r) for r in PROWS];rows[1][0]=('aceh','inlineStr')
        with self.assertRaisesRegex(m.BnpbWorkbookError,'duplicate province'):
            m.inspect_original(workbook(sheet(PROVINCE,rows)),resource='province_houses')

    def test_severity_cannot_join_province_grain(self):
        headers=[*PROVINCE,('Rumah Rusak Berat','inlineStr')]
        rows=[[*r,('1','n')] for r in PROWS]
        with self.assertRaisesRegex(m.BnpbWorkbookError,'distinct source grains'):
            m.inspect_original(workbook(sheet(headers,rows)),resource='province_houses')
        headers=[*SUMMARY,('Provinsi','inlineStr')]
        rows=[[*r,('Aceh','inlineStr')] for r in SROWS]
        with self.assertRaisesRegex(m.BnpbWorkbookError,'crosswalk'):
            m.inspect_original(workbook(sheet(headers,rows)),resource='peril_severity_summary')

    def test_duplicate_peril_summary_identity_rejected(self):
        rows=[list(r) for r in SROWS];rows[1][0]=('banjir','inlineStr')
        with self.assertRaisesRegex(m.BnpbWorkbookError,'duplicate event/peril'):
            m.inspect_original(workbook(sheet(SUMMARY,rows)),resource='peril_severity_summary')

    def test_excel_shared_strings_headers_supported(self):
        headers=[v for v,_ in PROVINCE]
        strings=f'<sst xmlns="{N}">'+''.join(f'<si><t>{x}</t></si>' for x in headers)+'</sst>'
        original=sheet(PROVINCE,PROWS)
        for idx,name in enumerate(headers):
            original=original.replace(cell(f'{chr(65+idx)}1',name).encode(),cell(f'{chr(65+idx)}1',str(idx),'s').encode())
        data=workbook(original,**{'xl/sharedStrings.xml':strings.encode()})
        out=m.inspect_original(data,resource='province_houses')
        self.assertEqual(out['province_key_count'],2)

    def test_duplicate_or_mismatched_row_number_rejected(self):
        xml=sheet(PROVINCE,PROWS)
        for bad in [xml.replace(b'<row r="2">',b'<row r="1">'),
                    xml.replace(b'<c r="A2"',b'<c r="A1"')]:
            with self.assertRaises(m.BnpbWorkbookError):
                m.inspect_original(workbook(bad),resource='province_houses')

    def test_excel_formula_forbids_cached_value_trust(self):
        xml=sheet(PROVINCE,PROWS).replace(b'<v>12</v>',b'<f>6+6</f><v>12</v>')
        with self.assertRaisesRegex(m.BnpbWorkbookError,'formula'):
            m.inspect_original(workbook(xml),resource='province_houses')

    def test_block_external_links_and_traversal(self):
        raw=workbook(sheet(PROVINCE,PROWS),**{'xl/externalLinks/externalLink1.xml':b'oops'})
        with self.assertRaisesRegex(m.BnpbWorkbookError,'external'):
            m.inspect_original(raw,resource='province_houses')
        raw=workbook(sheet(PROVINCE,PROWS),**{'../invalid':b'oops'})
        with self.assertRaisesRegex(m.BnpbWorkbookError,'unsafe'):
            m.inspect_original(raw,resource='province_houses')

    def test_duplicate_zip_member(self):
        b=io.BytesIO(workbook(sheet(PROVINCE,PROWS)))
        with warnings.catch_warnings(),zipfile.ZipFile(b,'a') as z:
            warnings.simplefilter('ignore')
            z.writestr('xl/workbook.xml',BASE['xl/workbook.xml'])
        with self.assertRaisesRegex(m.BnpbWorkbookError,'duplicate'):
            m.inspect_original(b.getvalue(),resource='province_houses')

    def test_oversized_and_corrupt_file(self):
        for raw in [b'',b'not an xlsx'*50,b'!'*(m.MAX_ORIGINAL_BYTES+1)]:
            with self.assertRaises(m.BnpbWorkbookError):
                m.inspect_original(raw,resource='province_houses')

if __name__=='__main__':
    unittest.main()
