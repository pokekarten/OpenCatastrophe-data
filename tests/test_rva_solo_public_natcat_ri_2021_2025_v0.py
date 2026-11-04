# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Offline 2021-2025 R+V Allgemeine RI treaty-family research guards."""
from decimal import Decimal
from pathlib import Path
import tomllib
import unittest
from urllib.parse import urlsplit

PATH = Path(__file__).resolve().parents[1] / "research/observations/rva_solo_public_natcat_ri_2021_2025_v0.toml"
KNOWN = {
    2021: ("470.6", True, True),
    2022: ("-59.8", False, False),
    2023: ("-116.6", False, True),
    2024: ("-153.5", False, True),
    2025: ("-166.1", False, True),
}
NONCLAIMS = (
    "original_source_pdf_sha256_verified_here",
    "exact_attachment_eur_observed", "exact_exhaustion_eur_observed",
    "exact_treaty_quota_observed", "aggregate_or_occurrence_basis_known",
    "inuring_order_known", "reinstatements_known",
    "non_cat_claims_ceded_aggregation_known",
)

def source():
    return tomllib.loads(PATH.read_text(encoding="utf-8"))

def check(d):
    if (d.get("target_legal_entity") != "R+V Allgemeine Versicherung AG"
        or d.get("schema_version") != "RVA_SOLO_PUBLIC_OUTWARD_NATCAT_2021_2025_V0"
        or d.get("currency") != "EUR"
        or d.get("financial_terms_status") != "UNKNOWN_NOT_APPROVED"
        or any(d.get(x) is not False for x in (
            "insurer_specific_gross_or_net_cat_loss_observed",
            "company_geocoded_sites_or_tiv_observed",
            "real_treaty_attachments_or_limits_observed",
            "native_cat_loss_model_admitted"))):
        raise ValueError("R+V legal perimeter or CAT/RI science status changed")
    rows=d.get("years",[])
    if [x.get("year") for x in rows] != list(KNOWN):
        raise ValueError("RI observation year missing or duplicate")
    for row in rows:
        amount,trigger,quota=KNOWN[row["year"]]
        url=urlsplit(row.get("source_url",""))
        if url.scheme!="https" or url.hostname!="www.ruv.de" or not url.path.endswith(".pdf"):
            raise ValueError("Issuer original report URL changed")
        if (row.get("report_perimeter")!="solo_RV_Allgemeine_self_written_direct"
            or Decimal(row.get("signed_outward_technical_result_direct_eur_million"))!=Decimal(amount)
            or row.get("reported_natcat_large_loss_protection_in_force") is not True
            or row.get("reported_natcat_large_loss_protection_used") is not trigger
            or row.get("quota_treaty_explicitly_stated") is not quota
            or row.get("quota_not_mentioned_is_proof_absent") is not False
            or row.get("supplementary_internal_natcat_xl_counterparty") != "R+V Versicherung AG"
            or row.get("parent_retrossession_to_external_reinsurers_disclosed") is not True
            or "excess_of_loss" not in row.get("reinsurance_treaty_families_observed", [])
            or (quota and "quota_share" not in row["reinsurance_treaty_families_observed"])):
            raise ValueError("RI original source observation or trigger drift")
        if any(row.get(k) is not False for k in NONCLAIMS):
            raise ValueError("Actual RI financial layer/source permission falsely admitted")
        if row.get("signed_outward_result_is_ceded_cat_loss_only") is not False or row.get("signed_outward_result_is_a_treaty_premium_or_claim") is not False:
            raise ValueError("Annual technical result misrepresented as CAT claim or premium")
    return rows

class RvaSourcedRiTests(unittest.TestCase):
    def test_years_exact_and_2021_trigger_and_signed_results(self):
        self.assertEqual(len(check(source())),5)

    def test_natcat_was_used_2021_not_in_following_years(self):
        d=source()
        self.assertEqual([y["year"] for y in d["years"] if y["reported_natcat_large_loss_protection_used"]],[2021])

    def test_positive_2021_annual_result_not_same_as_bernd_recovery(self):
        d=source()
        self.assertFalse(d["years"][0]["signed_outward_result_is_ceded_cat_loss_only"])
        self.assertFalse(d["years"][0]["signed_outward_result_is_a_treaty_premium_or_claim"])
        self.assertFalse(d["insurer_specific_gross_or_net_cat_loss_observed"])

    def test_2022_missing_quota_wording_not_asserted_absent(self):
        d=source()
        self.assertFalse(d["years"][1]["quota_treaty_explicitly_stated"])
        self.assertFalse(d["years"][1]["quota_not_mentioned_is_proof_absent"])

    def test_reject_false_actual_tower_size(self):
        d=source();d["years"][0]["exact_attachment_eur_observed"]=True
        with self.assertRaises(ValueError):check(d)

    def test_reject_incorrect_2024_natcat_trigger(self):
        d=source();d["years"][3]["reported_natcat_large_loss_protection_used"]=True
        with self.assertRaises(ValueError):check(d)

    def test_reject_2021_technical_result_as_gross_cat_loss(self):
        d=source();d["years"][0]["signed_outward_result_is_ceded_cat_loss_only"]=True
        with self.assertRaises(ValueError):check(d)

    def test_reject_outward_ceded_result_scaling(self):
        d=source();d["years"][0]["signed_outward_technical_result_direct_eur_million"]="470600000"
        with self.assertRaises(ValueError):check(d)

    def test_reject_parent_treated_as_proven_reinsurance_tower_end(self):
        d=source();d["years"][2]["inuring_order_known"]=True
        with self.assertRaises(ValueError):check(d)

    def test_reject_solo_group_mismatch(self):
        d=source();d["target_legal_entity"]="R+V Versicherung AG"
        with self.assertRaises(ValueError):check(d)

if __name__=="__main__":
    unittest.main()
