#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import urllib.request

import numpy as np
import pandas as pd
import rdata
from sklearn.datasets import fetch_openml

CAS_SHA = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
FREQ_ID = 41214
SEV_ID = 41215
EXPECTED_CURRENT_SHA256 = {
    "frequency": "82c8598513d9fa78226b6c7d271a9940eca4b8083e9e32320a75d377bdfe15a3",
    "severity": "78e6e5016ae046603b37e88ff8ad8ca327f5d59f827c1f75d140388de09b14b3",
}
OUT = Path("tmp_ffbk_severity_transfer_result.json")


def fetch_bytes(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "ffbk-research-reconciliation/1"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    return data, hashlib.sha256(data).hexdigest()


def openml_meta(data_id: int) -> dict:
    url = f"https://www.openml.org/api/v1/json/data/{data_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "ffbk-research-reconciliation/1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode())["data_set_description"]
    keys = ("id", "name", "version", "md5_checksum", "status", "upload_date", "processing_date", "file_id", "url", "parquet_url")
    return {k: d.get(k) for k in keys}


def read_current_rda(kind: str) -> tuple[pd.DataFrame, dict]:
    object_name = "freMTPL2freq" if kind == "frequency" else "freMTPL2sev"
    url = f"https://raw.githubusercontent.com/dutangc/CASdatasets/{CAS_SHA}/data/{object_name}.rda"
    raw, sha256 = fetch_bytes(url)
    with tempfile.NamedTemporaryFile(suffix=".rda") as f:
        f.write(raw)
        f.flush()
        obj = rdata.read_rda(f.name)
    if object_name not in obj:
        raise RuntimeError(f"{object_name} absent from current RData: {list(obj)}")
    df = pd.DataFrame(obj[object_name]).copy()
    return df, {
        "repository": "dutangc/CASdatasets",
        "commit": CAS_SHA,
        "path": f"data/{object_name}.rda",
        "bytes": len(raw),
        "sha256": sha256,
        "independent_manifest_expected_sha256": EXPECTED_CURRENT_SHA256[kind],
        "independent_manifest_hash_match": sha256 == EXPECTED_CURRENT_SHA256[kind],
    }


def normalize_severity(df: pd.DataFrame) -> pd.DataFrame:
    out = df[["IDpol", "ClaimAmount"]].copy()
    out["IDpol"] = pd.to_numeric(out["IDpol"], errors="raise").astype("int64")
    out["ClaimAmount"] = pd.to_numeric(out["ClaimAmount"], errors="raise").astype("float64")
    return out


def normalize_frequency(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["IDpol"] = pd.to_numeric(out["IDpol"], errors="raise").astype("int64")
    for col in out.columns:
        if col == "IDpol":
            continue
        if col in {"VehBrand", "VehGas", "Area", "Region"}:
            out[col] = out[col].astype(str).str.strip("'")
        else:
            out[col] = pd.to_numeric(out[col], errors="raise")
    return out


def float_bits(x: float) -> int:
    return int(np.asarray([x], dtype=np.float64).view(np.uint64)[0])


def bits_float(bits: int) -> float:
    return float(np.asarray([bits], dtype=np.uint64).view(np.float64)[0])


def claim_counter(df: pd.DataFrame) -> Counter:
    return Counter((int(i), float_bits(float(a))) for i, a in zip(df["IDpol"], df["ClaimAmount"]))


def counter_digest(counter: Counter) -> str:
    h = hashlib.sha256()
    for (idpol, amount_bits), n in sorted(counter.items()):
        h.update(struct.pack(">qQI", idpol, amount_bits, n))
    return h.hexdigest()


def counter_examples(counter: Counter, limit: int = 20) -> list[dict]:
    out = []
    for (idpol, amount_bits), n in sorted(counter.items())[:limit]:
        out.append({"IDpol": idpol, "ClaimAmount": bits_float(amount_bits), "float64_bits_hex": f"{amount_bits:016x}", "multiplicity": int(n)})
    return out


def compare_frequency(openml_freq: pd.DataFrame, current_freq: pd.DataFrame) -> dict:
    o = normalize_frequency(openml_freq)
    c = normalize_frequency(current_freq)
    oid = set(o["IDpol"])
    cid = set(c["IDpol"])
    openml_only = sorted(oid - cid)
    current_only = sorted(cid - oid)
    common = sorted(oid & cid)

    oi = o.set_index("IDpol").loc[common].sort_index()
    ci = c.set_index("IDpol").loc[common].sort_index()
    shared_cols = [x for x in oi.columns if x in ci.columns]
    mismatch = {}
    for col in shared_cols:
        a = oi[col]
        b = ci[col]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            av = a.to_numpy()
            bv = b.to_numpy()
            same = (av == bv) | (pd.isna(av) & pd.isna(bv))
        else:
            av = a.astype(str).to_numpy()
            bv = b.astype(str).to_numpy()
            same = av == bv
        mismatch[col] = int((~same).sum())

    return {
        "openml_rows": int(len(o)),
        "current_rows": int(len(c)),
        "openml_unique_ids": int(len(oid)),
        "current_unique_ids": int(len(cid)),
        "openml_only_id_count": len(openml_only),
        "current_only_id_count": len(current_only),
        "openml_only_ids": openml_only,
        "current_only_ids": current_only,
        "common_id_count": len(common),
        "common_row_value_mismatches_by_column": mismatch,
    }


def main() -> None:
    current_freq_raw, current_freq_src = read_current_rda("frequency")
    current_sev_raw, current_sev_src = read_current_rda("severity")

    openml_freq_raw = fetch_openml(data_id=FREQ_ID, as_frame=True).data.copy()
    openml_sev_raw = fetch_openml(data_id=SEV_ID, as_frame=True).data.copy()

    current_sev = normalize_severity(current_sev_raw)
    openml_sev = normalize_severity(openml_sev_raw)
    openml_freq = normalize_frequency(openml_freq_raw)
    current_freq = normalize_frequency(current_freq_raw)

    openml_positive = openml_sev.loc[openml_sev["ClaimAmount"] > 0].copy()
    legacy_unmatched_mask = ~openml_positive["IDpol"].isin(openml_freq["IDpol"])
    openml_matched = openml_positive.loc[~legacy_unmatched_mask].copy()
    current_unmatched_mask = ~current_sev["IDpol"].isin(current_freq["IDpol"])

    current_counter = claim_counter(current_sev)
    matched_counter = claim_counter(openml_matched)
    current_minus_matched = current_counter - matched_counter
    matched_minus_current = matched_counter - current_counter

    frequency_compare = compare_frequency(openml_freq, current_freq)
    removed_freq_ids = set(frequency_compare["openml_only_ids"])
    openml_claim_rows_on_removed_freq_ids = openml_positive[openml_positive["IDpol"].isin(removed_freq_ids)]

    legacy_orphan = openml_positive.loc[legacy_unmatched_mask]
    legacy_orphan_amount = float(legacy_orphan["ClaimAmount"].sum())
    legacy_total_amount = float(openml_positive["ClaimAmount"].sum())

    exact_equal = current_counter == matched_counter
    verdict = "SUPPORTED" if exact_equal else "FALSIFIED"

    payload = {
        "research_question": (
            "Is current CASdatasets freMTPL2sev exactly the OpenML 41215 positive-claim subset "
            "whose IDpol is present in OpenML 41214, or did the publisher revision change additional claim rows/amounts?"
        ),
        "hypothesis_tested": {
            "H0": "current CASdatasets severity multiset == OpenML positive severity restricted only by policy linkage",
            "H1": "current CASdatasets changes additional claim rows and/or ClaimAmount values beyond policy-linkage restriction",
        },
        "result": {
            "verdict_for_H0": verdict,
            "bitwise_float64_claim_multiset_equal": exact_equal,
            "current_minus_openml_matched_count": int(sum(current_minus_matched.values())),
            "openml_matched_minus_current_count": int(sum(matched_minus_current.values())),
            "current_minus_openml_matched_examples": counter_examples(current_minus_matched),
            "openml_matched_minus_current_examples": counter_examples(matched_minus_current),
            "current_claim_multiset_sha256": counter_digest(current_counter),
            "openml_matched_claim_multiset_sha256": counter_digest(matched_counter),
        },
        "sources": {
            "current_casdatasets": {
                "frequency": current_freq_src,
                "severity": current_sev_src,
            },
            "openml": {
                "frequency": openml_meta(FREQ_ID),
                "severity": openml_meta(SEV_ID),
            },
        },
        "population_reconciliation": {
            "openml_frequency_rows": int(len(openml_freq)),
            "openml_positive_severity_rows": int(len(openml_positive)),
            "openml_positive_severity_rows_without_openml_policy": int(legacy_unmatched_mask.sum()),
            "openml_matched_positive_severity_rows": int(len(openml_matched)),
            "legacy_orphan_claim_amount": legacy_orphan_amount,
            "legacy_orphan_row_share": float(legacy_unmatched_mask.mean()),
            "legacy_orphan_amount_share": legacy_orphan_amount / legacy_total_amount,
            "current_frequency_rows": int(len(current_freq)),
            "current_severity_rows": int(len(current_sev)),
            "current_severity_rows_without_current_policy": int(current_unmatched_mask.sum()),
            "current_positive_severity_rows": int((current_sev["ClaimAmount"] > 0).sum()),
        },
        "frequency_version_diff": {
            **frequency_compare,
            "openml_positive_claim_rows_on_frequency_ids_removed_in_current_casdatasets": int(len(openml_claim_rows_on_removed_freq_ids)),
            "openml_positive_claim_amount_on_frequency_ids_removed_in_current_casdatasets": float(openml_claim_rows_on_removed_freq_ids["ClaimAmount"].sum()),
        },
        "method": {
            "claim_identity": "exact multiset of (IDpol, IEEE-754 float64 ClaimAmount bits), preserving duplicates",
            "policy_linkage_rule": "OpenML positive severity row retained iff IDpol occurs in OpenML frequency table; no ClaimAmount threshold beyond >0 and no model output used",
            "frequency_identity": "IDpol set comparison plus exact value mismatch counts on common IDs after quote stripping for categorical columns",
            "model_fit_executed": False,
        },
        "consumer_boundary": (
            "claim-level severity conditional on rating covariates. This test does not authorize exclusion "
            "for an all-legacy-claims consumer and does not rank Gamma versus Inverse Gaussian."
        ),
    }

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    payload["receipt_sha256_without_receipt_field"] = hashlib.sha256(canonical).hexdigest()
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
