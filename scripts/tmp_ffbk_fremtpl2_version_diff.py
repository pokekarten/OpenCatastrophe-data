#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

import numpy as np
import pandas as pd
from sklearn.datasets import fetch_openml

CAS_REPO_SHA = "227fb56b8734bdb7c0327a41180e01d2ddaeaf26"
OPENML_FREQ_ID = 41214
OPENML_SEV_ID = 41215
OUT = Path("tmp_ffbk_fremtpl2_version_diff_result.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_current_rda(name: str) -> tuple[Path, str]:
    url = f"https://raw.githubusercontent.com/dutangc/CASdatasets/{CAS_REPO_SHA}/data/{name}.rda"
    path = Path(f"current_{name}.rda")
    urllib.request.urlretrieve(url, path)
    return path, url


def rda_to_csv(rda: Path, object_name: str) -> Path:
    out = Path(f"{object_name}_current.csv")
    expr = (
        f'load("{rda.as_posix()}"); '
        f'if (!exists("{object_name}")) stop("missing object {object_name}"); '
        f'write.csv({object_name}, "{out.as_posix()}", row.names=FALSE, quote=TRUE)'
    )
    subprocess.run(["Rscript", "-e", expr], check=True)
    return out


def openml_meta(data_id: int) -> dict:
    url = f"https://www.openml.org/api/v1/json/data/{data_id}"
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.loads(r.read().decode())["data_set_description"]
    return {
        "data_id": int(d["id"]),
        "name": d.get("name"),
        "version": int(d["version"]) if d.get("version") else None,
        "md5_checksum": d.get("md5_checksum"),
        "upload_date": d.get("upload_date"),
        "status": d.get("status"),
    }


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object or isinstance(df[c].dtype, pd.CategoricalDtype):
            df[c] = df[c].astype(str).str.strip("'").str.strip()
    return df


def cents(x: pd.Series) -> np.ndarray:
    arr = pd.to_numeric(x, errors="raise").to_numpy(float)
    q = np.rint(arr * 100.0).astype(np.int64)
    err = np.max(np.abs(arr * 100.0 - q)) if len(arr) else 0.0
    if err > 1e-6:
        raise RuntimeError(f"ClaimAmount is not cent-exact; max residual={err}")
    return q


def counter_diff(a: Counter, b: Counter) -> dict:
    a_only = a - b
    b_only = b - a
    return {
        "a_only_rows": int(sum(a_only.values())),
        "b_only_rows": int(sum(b_only.values())),
        "a_only_unique_pairs": int(len(a_only)),
        "b_only_unique_pairs": int(len(b_only)),
        "a_only_amount_cents": int(sum(pair[1] * n for pair, n in a_only.items())),
        "b_only_amount_cents": int(sum(pair[1] * n for pair, n in b_only.items())),
        "a_only_examples": [[int(k[0]), int(k[1]), int(v)] for k, v in list(a_only.items())[:20]],
        "b_only_examples": [[int(k[0]), int(k[1]), int(v)] for k, v in list(b_only.items())[:20]],
    }


def compare_shared_covariates(current: pd.DataFrame, legacy: pd.DataFrame) -> dict:
    c = clean_strings(current)
    l = clean_strings(legacy)
    c["IDpol"] = pd.to_numeric(c["IDpol"], errors="raise").astype("int64")
    l["IDpol"] = pd.to_numeric(l["IDpol"], errors="raise").astype("int64")
    if not c["IDpol"].is_unique or not l["IDpol"].is_unique:
        raise RuntimeError("frequency IDpol must be unique in each lineage")
    c = c.set_index("IDpol").sort_index()
    l = l.set_index("IDpol").sort_index()
    common = c.index.intersection(l.index)
    cols = [x for x in c.columns if x in l.columns]
    result: dict[str, dict] = {}
    any_changed = np.zeros(len(common), dtype=bool)
    for col in cols:
        a = c.loc[common, col]
        b = l.loc[common, col]
        an = pd.to_numeric(a, errors="coerce")
        bn = pd.to_numeric(b, errors="coerce")
        numeric = bool(an.notna().all() and bn.notna().all())
        if numeric:
            av = an.to_numpy(float)
            bv = bn.to_numpy(float)
            changed = ~np.isclose(av, bv, rtol=0.0, atol=1e-12, equal_nan=True)
            max_abs = float(np.max(np.abs(av - bv))) if len(av) else 0.0
        else:
            av = a.astype(str).to_numpy()
            bv = b.astype(str).to_numpy()
            changed = av != bv
            max_abs = None
        any_changed |= changed
        idx = np.flatnonzero(changed)[:10]
        result[col] = {
            "changed_rows": int(changed.sum()),
            "numeric_comparison": numeric,
            "max_abs_difference": max_abs,
            "examples": [
                {
                    "IDpol": int(common[i]),
                    "current": str(a.iloc[i]),
                    "legacy": str(b.iloc[i]),
                }
                for i in idx
            ],
        }
    return {
        "common_policy_rows": int(len(common)),
        "rows_with_any_covariate_change": int(any_changed.sum()),
        "columns": result,
    }


def main() -> None:
    freq_rda, freq_url = download_current_rda("freMTPL2freq")
    sev_rda, sev_url = download_current_rda("freMTPL2sev")
    current_freq_csv = rda_to_csv(freq_rda, "freMTPL2freq")
    current_sev_csv = rda_to_csv(sev_rda, "freMTPL2sev")

    current_freq = pd.read_csv(current_freq_csv, low_memory=False)
    current_sev = pd.read_csv(current_sev_csv, low_memory=False)
    legacy_freq = fetch_openml(data_id=OPENML_FREQ_ID, as_frame=True).data.copy()
    legacy_sev = fetch_openml(data_id=OPENML_SEV_ID, as_frame=True).data.copy()

    for d in (current_freq, current_sev, legacy_freq, legacy_sev):
        d["IDpol"] = pd.to_numeric(d["IDpol"], errors="raise").astype("int64")

    current_freq_ids = set(current_freq["IDpol"].tolist())
    legacy_freq_ids = set(legacy_freq["IDpol"].tolist())
    legacy_match = legacy_sev[legacy_sev["IDpol"].isin(legacy_freq_ids)].copy()
    legacy_orphan = legacy_sev[~legacy_sev["IDpol"].isin(legacy_freq_ids)].copy()

    current_pairs = Counter(zip(current_sev["IDpol"].astype(int), cents(current_sev)))
    legacy_matched_pairs = Counter(zip(legacy_match["IDpol"].astype(int), cents(legacy_match)))
    claim_diff = counter_diff(current_pairs, legacy_matched_pairs)

    current_only_ids = sorted(current_freq_ids - legacy_freq_ids)
    legacy_only_ids = sorted(legacy_freq_ids - current_freq_ids)
    legacy_only = legacy_freq[legacy_freq["IDpol"].isin(legacy_only_ids)].copy()
    current_only = current_freq[current_freq["IDpol"].isin(current_only_ids)].copy()

    shared_cov = compare_shared_covariates(current_freq, legacy_freq)

    result = {
        "verdict": "UNSET",
        "sources": {
            "current_casdatasets": {
                "repository": "dutangc/CASdatasets",
                "commit": CAS_REPO_SHA,
                "frequency_url": freq_url,
                "severity_url": sev_url,
                "frequency_rda_sha256": sha256(freq_rda),
                "severity_rda_sha256": sha256(sev_rda),
            },
            "legacy_openml": {
                "frequency": openml_meta(OPENML_FREQ_ID),
                "severity": openml_meta(OPENML_SEV_ID),
            },
        },
        "dimensions": {
            "current_frequency_rows": int(len(current_freq)),
            "current_severity_rows": int(len(current_sev)),
            "legacy_frequency_rows": int(len(legacy_freq)),
            "legacy_severity_rows": int(len(legacy_sev)),
            "legacy_matched_severity_rows": int(len(legacy_match)),
            "legacy_orphan_severity_rows": int(len(legacy_orphan)),
        },
        "claim_population": {
            "legacy_orphan_claim_amount_cents": int(cents(legacy_orphan).sum()),
            "current_claim_amount_cents": int(cents(current_sev).sum()),
            "legacy_matched_claim_amount_cents": int(cents(legacy_match).sum()),
            "current_vs_legacy_matched_pair_multiset": claim_diff,
        },
        "policy_population": {
            "current_only_id_count": int(len(current_only_ids)),
            "legacy_only_id_count": int(len(legacy_only_ids)),
            "current_only_ids": [int(x) for x in current_only_ids],
            "legacy_only_ids": [int(x) for x in legacy_only_ids],
            "current_only_claimnb_sum": float(pd.to_numeric(current_only.get("ClaimNb", pd.Series(dtype=float)), errors="coerce").sum()),
            "legacy_only_claimnb_sum": float(pd.to_numeric(legacy_only.get("ClaimNb", pd.Series(dtype=float)), errors="coerce").sum()),
            "current_only_exposure_sum": float(pd.to_numeric(current_only.get("Exposure", pd.Series(dtype=float)), errors="coerce").sum()),
            "legacy_only_exposure_sum": float(pd.to_numeric(legacy_only.get("Exposure", pd.Series(dtype=float)), errors="coerce").sum()),
        },
        "shared_policy_covariates": shared_cov,
    }

    exact_claim_match = (
        claim_diff["a_only_rows"] == 0
        and claim_diff["b_only_rows"] == 0
        and len(current_sev) == len(legacy_match)
    )
    result["verdict"] = "EXACT_MATCHED_CLAIM_POPULATION" if exact_claim_match else "CLAIM_POPULATION_DIFFERS"
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
