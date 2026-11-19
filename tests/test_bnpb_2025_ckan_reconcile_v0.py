# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Synthetic-only 2025 CKAN cross-resource and national-total regression tests."""
import json
import unittest

from research_runners import bnpb_2025_ckan_reconcile_v0 as m


def payloads():
    prow = []
    for i in range(1, 39):
        record = {"Provinsi": f"SYNTHETIC_{i}", "Kode Wilayah Provinsi": i}
        record.update({name: j + 1 for j, name in enumerate(m.PERILS)})
        prow.append(record)
    national = {"Provinsi": "INDONESIA", "Kode Wilayah Provinsi": None}
    national.update({name: 38 * (j + 1) for j, name in enumerate(m.PERILS)})
    prow.append(national)
    srow = []
    for j, name in enumerate(m.PERILS):
        srow.append({"Jenis Bencana": name, "Jumlah Kejadian": 1,
                     m.SEVERITY[0]: 38 * (j + 1), m.SEVERITY[1]: 0, m.SEVERITY[2]: 0})
    srow.append({"Jenis Bencana": "Total", "Jumlah Kejadian": len(m.PERILS),
                 m.SEVERITY[0]: sum(38 * (j + 1) for j in range(len(m.PERILS))),
                 m.SEVERITY[1]: 0, m.SEVERITY[2]: 0})
    def wrap(resource, records):
        return {"success": True, "result": {"resource_id": resource,
            "total": len(records), "records": records,
            "fields": [{"id": k, "type": "text"} for k in records[0].keys()]}}
    return wrap(m.PROVINCE_RESOURCE_ID, prow), wrap(m.SUMMARY_RESOURCE_ID, srow)


def run(a, b):
    return m.reconcile(json.dumps(a).encode(), json.dumps(b).encode())


class BNPBCkanReconcileTests(unittest.TestCase):
    def test_valid_source_grain_and_two_totals_excluded(self):
        a, b = payloads()
        out = run(a, b)
        self.assertEqual(out["province_observation_rows"], 38)
        self.assertEqual(out["peril_observation_rows"], 9)
        self.assertEqual(out["national_total_rows_excluded"], 1)
        self.assertEqual(out["summary_total_rows_excluded"], 1)
        self.assertTrue(out["all_nine_peril_and_severity_reconciliations_passed"])
        self.assertFalse(out["exact_original_xlsx_verified"])
        self.assertFalse(out["model_data_admitted"])
        self.assertNotIn("SYNTHETIC_1", str(out))

    def test_double_counting_national_row_rejected_if_not_named(self):
        a, b = payloads()
        a["result"]["records"][-1]["Provinsi"] = "SYNTHETIC_39"
        a["result"]["records"][-1]["Kode Wilayah Provinsi"] = 39
        with self.assertRaisesRegex(m.BNPBReconciliationError, "38 distinct provinces"):
            run(a, b)

    def test_national_sum_mismatch_rejected(self):
        a, b = payloads()
        a["result"]["records"][-1]["BANJIR"] += 1
        with self.assertRaisesRegex(m.BNPBReconciliationError, "mismatch"):
            run(a, b)

    def test_summary_peril_severity_mismatch_rejected(self):
        a, b = payloads()
        b["result"]["records"][0][m.SEVERITY[0]] += 1
        with self.assertRaisesRegex(m.BNPBReconciliationError, "mismatch"):
            run(a, b)

    def test_grand_total_mismatch_rejected(self):
        a, b = payloads()
        b["result"]["records"][-1]["Jumlah Kejadian"] += 1
        with self.assertRaisesRegex(m.BNPBReconciliationError, "grand total mismatch"):
            run(a, b)

    def test_partial_response_never_accepted_as_complete(self):
        a, b = payloads()
        a["result"]["records"].pop()
        with self.assertRaisesRegex(m.BNPBReconciliationError, "truncated"):
            run(a, b)

    def test_duplicate_region_code_rejected(self):
        a, b = payloads()
        a["result"]["records"][1]["Kode Wilayah Provinsi"] = 1
        with self.assertRaisesRegex(m.BNPBReconciliationError, "duplicate province"):
            run(a, b)

    def test_missing_and_non_numeric_not_coerced_zero(self):
        for invalid in (None, "", "—", "NA", "NaN", "Infinity", "-1", "3.5"):
            a, b = payloads()
            a["result"]["records"][0]["KEKERINGAN"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(m.BNPBReconciliationError):
                run(a, b)

    def test_decimal_text_zero_is_valid(self):
        a, b = payloads()
        a["result"]["records"][0]["TSUNAMI"] = "9.0"
        a["result"]["records"][-1]["TSUNAMI"] = 38 * 9
        out = run(a, b)
        self.assertTrue(out["all_nine_peril_and_severity_reconciliations_passed"])

    def test_wrong_resource_id_rejected(self):
        a, b = payloads()
        b["result"]["resource_id"] = m.PROVINCE_RESOURCE_ID
        with self.assertRaisesRegex(m.BNPBReconciliationError, "wrong CKAN"):
            run(a, b)

    def test_duplicate_json_keys_rejected(self):
        a, b = payloads()
        raw = json.dumps(a).encode().replace(b'"success": true', b'"success": true, "success": true', 1)
        with self.assertRaisesRegex(m.BNPBReconciliationError, "invalid CKAN response JSON"):
            m.reconcile(raw, json.dumps(b).encode())

    def test_extra_unknown_peril_rejected(self):
        a, b = payloads()
        b["result"]["records"][2]["Jenis Bencana"] = "NEW PERIL"
        with self.assertRaisesRegex(m.BNPBReconciliationError, "unexpected/duplicate summary peril"):
            run(a, b)

    def test_summary_missing_grand_total_rejected(self):
        a, b = payloads()
        b["result"]["records"][-1]["Jenis Bencana"] = "BANJIR"
        with self.assertRaises(m.BNPBReconciliationError):
            run(a, b)

    def test_duplicate_field_names_rejected(self):
        a, b = payloads()
        a["result"]["fields"].append({"id": "BANJIR", "type": "numeric"})
        with self.assertRaisesRegex(m.BNPBReconciliationError, "duplicate required CKAN fields"):
            run(a, b)

    def test_wrong_boolean_total_rejected(self):
        a, b = payloads()
        a["result"]["total"] = True
        with self.assertRaisesRegex(m.BNPBReconciliationError, "truncated"):
            run(a, b)


if __name__ == "__main__":
    unittest.main()
