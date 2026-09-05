#!/usr/bin/env python3
"""Temporary independent ClaimNb-cap sensitivity for FFBK PR #1319 current head.

This extends the independent execution probe after PR #1319 added an isolated
raw-ClaimNb sensitivity. The direct Tweedie response PurePremium is unchanged;
the Poisson/Gamma decomposition is intentionally allowed to move.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import independent_fremtpl_runner as core


def prepare_raw_claimnb(freq: pd.DataFrame, sev: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    f = freq.copy()
    for c in f.columns:
        if f[c].dtype == object or isinstance(f[c].dtype, pd.CategoricalDtype):
            f[c] = f[c].astype(str).str.strip("'")
    amounts = sev.groupby("IDpol", sort=False)["ClaimAmount"].sum()
    d = f.set_index("IDpol")
    raw_nb = d["ClaimNb"].astype(float)
    raw_exp = d["Exposure"].astype(float)
    d["ClaimNb"] = raw_nb
    d["Exposure"] = raw_exp.clip(upper=1)
    d["ClaimAmount"] = d.index.to_series().map(amounts).fillna(0.0).astype(float).clip(upper=200000.0)
    reset = (d["ClaimAmount"] == 0) & (d["ClaimNb"] >= 1)
    d.loc[reset, "ClaimNb"] = 0
    if not (d["Exposure"] > 0).all():
        raise ValueError("non-positive exposure")
    d["PurePremium"] = d["ClaimAmount"] / d["Exposure"]
    d["Frequency"] = d["ClaimNb"] / d["Exposure"]
    d["AvgClaimAmount"] = d["ClaimAmount"] / np.fmax(d["ClaimNb"], 1)
    receipt = {
        "rows": int(len(d)),
        "idpol_unique": bool(d.index.is_unique),
        "claimnb_gt_4_rows": int((raw_nb > 4).sum()),
        "claimnb_excess_above_4": float((raw_nb - raw_nb.clip(upper=4)).sum()),
        "exposure_cap_rows": int((raw_exp > 1).sum()),
        "prepared_total_exposure": float(d["Exposure"].sum()),
        "prepared_total_claim_amount": float(d["ClaimAmount"].sum()),
        "prepared_total_claimnb": float(d["ClaimNb"].sum()),
        "positive_claim_rows": int((d["ClaimAmount"] > 0).sum()),
    }
    return d, receipt


def main() -> None:
    freq, sev, meta = core.load()
    raw, receipt = prepare_raw_claimnb(freq, sev)
    reference, _ = core.prepare(freq, sev, True)
    if not raw.index.equals(reference.index):
        raise ValueError("policy identity/order drift")
    # PurePremium and Exposure must be exactly unchanged by this isolated sensitivity.
    if not np.array_equal(raw["PurePremium"].to_numpy(), reference["PurePremium"].to_numpy()):
        raise AssertionError("raw ClaimNb sensitivity moved PurePremium")
    if not np.array_equal(raw["Exposure"].to_numpy(), reference["Exposure"].to_numpy()):
        raise AssertionError("raw ClaimNb sensitivity moved Exposure")
    splits = [core.one_split(raw, seed) for seed in core.SEEDS]
    out = {
        "schema": 1,
        "protocol_source": "independent current-head ClaimNb-cap sensitivity for FFBK PR #1319 head 19c329ec37734837cee32182feb3be597ddefb8b",
        "variant": "raw_claimnb_reference_amount_cap",
        "openml": meta,
        "data_receipt": receipt,
        "seeds": list(core.SEEDS),
        "splits": splits,
    }
    out["canonical_sha256"] = hashlib.sha256(
        json.dumps(out, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    Path("ffbk1319-raw-claimnb.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"variant": out["variant"], "receipt": out["canonical_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
