#!/usr/bin/env python3
"""Public-runner execution bridge for FFBK PR #1473.

No external CAS bytes are committed.  This independently implements the frozen
scientific contract in FFBK/scripts/reserving_cas_paid_incurred_company_holdout.py
at FFBK branch head 0156dbb0ad6c9a1a20e51401bd7629d6ec7981b9.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

VALUATION_YEAR = 2007
TARGET_YEAR = 2008
SALT = "cas2025-paid-incurred-v0"
SEED = 20260907
REPS = 2000
MIN_TRAIN = 30
MIN_FINAL = 10
MIN_LAGS = 3


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def bucket(lob: str, grcode: str) -> int:
    return int(hashlib.sha256(f"{SALT}|{lob}|{grcode}".encode()).hexdigest(), 16) % 5


def norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def col(fields: list[str], stem: str) -> str:
    n = norm(stem)
    exact = [x for x in fields if norm(x) == n]
    if len(exact) == 1:
        return exact[0]
    pref = [x for x in fields if norm(x).startswith(n)]
    if len(pref) == 1:
        return pref[0]
    raise ValueError(f"cannot resolve {stem}: {fields}")


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        fields = list(rd.fieldnames or [])
        cg, co, cy, cl = (col(fields, x) for x in ("GRCODE", "AccidentYear", "DevelopmentYear", "DevelopmentLag"))
        ci, cp = col(fields, "IncurLoss"), col(fields, "CumPaidLoss")
        out = {}
        for r in rd:
            try:
                g = str(r[cg]).strip()
                o = int(float(r[co])); y = int(float(r[cy])); lag = int(float(r[cl]))
                inc = float(r[ci]); paid = float(r[cp])
            except (TypeError, ValueError):
                continue
            if not g:
                continue
            k = (g, o, lag)
            if k in out:
                raise ValueError(f"duplicate key {k}")
            out[k] = (y, inc, paid)
    return out, fields


def transitions(rows):
    train, target = [], []
    for (g, o, lag), (year, inc, paid) in rows.items():
        if lag < 2:
            continue
        prev = rows.get((g, o, lag - 1)); nxt = rows.get((g, o, lag + 1))
        if prev is None or nxt is None:
            continue
        py, pinc, ppaid = prev
        ny, ninc, npaid = nxt
        if min(ppaid, paid, inc, npaid) <= 0 or ny != year + 1:
            continue
        t = (g, lag, math.log(npaid / paid), math.log(paid / ppaid), math.log(paid / inc))
        if ny <= VALUATION_YEAR:
            train.append(t)
        elif year == VALUATION_YEAR and ny == TARGET_YEAR:
            target.append(t)
    return train, target


def means(rows, pos):
    d = defaultdict(list)
    for r in rows: d[r[1]].append(r[pos])
    return {k: float(np.mean(v)) for k, v in d.items()}


def design(rows, ages, hm, qm, arm):
    xx = []
    for r in rows:
        g, lag, y, h, q = r
        if lag not in ages or lag not in hm or lag not in qm:
            raise ValueError(f"unseen lag {lag}")
        x = [1.0] + [1.0 if lag == a else 0.0 for a in ages[1:]]
        if arm in ("MH", "MHQ"): x.append(h - hm[lag])
        if arm in ("MQ", "MHQ"): x.append(q - qm[lag])
        xx.append(x)
    return np.asarray(xx, float)


def fit(rows, ages, hm, qm, arm):
    x = design(rows, ages, hm, qm, arm); y = np.asarray([r[2] for r in rows])
    b, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    if rank < x.shape[1]: raise ValueError(f"rank deficient {arm}")
    resid = y - x @ b
    sig = math.sqrt(float(np.mean(resid * resid)))
    if not math.isfinite(sig) or sig <= 0: raise ValueError(f"bad sigma {arm}")
    return b, sig


def logscore(y, mu, sig):
    return -0.5 * math.log(2 * math.pi) - math.log(sig) - 0.5 * ((y - mu) / sig) ** 2


def eval_lob(lob: str, path: Path, url: str):
    rows, fields = read_rows(path); all_train, all_target = transitions(rows)
    train_g = {r[0] for r in all_train if bucket(lob, r[0]) != 0}
    final_g = {r[0] for r in all_target if bucket(lob, r[0]) == 0}
    tr = [r for r in all_train if r[0] in train_g]
    te = [r for r in all_target if r[0] in final_g]
    if {r[0] for r in tr} & final_g: raise AssertionError("company leakage")
    ages = sorted({r[1] for r in tr}); tlags = sorted({r[1] for r in te})
    base = dict(lob=lob, source_url=url, filename=path.name, bytes=path.stat().st_size,
                sha256=file_sha(path), header=fields, triangle_rows=len(rows),
                train_companies=len(train_g), final_companies=len(final_g),
                train_transitions=len(tr), final_transitions=len(te), target_lags=tlags)
    adequate = len(train_g) >= MIN_TRAIN and len(final_g) >= MIN_FINAL and len(tlags) >= MIN_LAGS
    if not adequate or not set(tlags).issubset(ages):
        return base | {"status": "BLOCKED_BY_DATA"}
    hm, qm = means(tr, 3), means(tr, 4)
    arms = {}
    for arm in ("M0", "MH", "MQ", "MHQ"):
        b, s = fit(tr, ages, hm, qm, arm)
        arms[arm] = (b, s, design(te, ages, hm, qm, arm) @ b)
    y = np.asarray([r[2] for r in te]); common = arms["M0"][1]
    cs = {a: logscore(y, arms[a][2], common) for a in arms}
    ads = {a: logscore(y, arms[a][2], arms[a][1]) for a in ("MH", "MHQ")}
    by = defaultdict(list)
    for i, r in enumerate(te): by[r[0]].append(i)
    companies = {}
    for g, ii0 in sorted(by.items()):
        ii = np.asarray(ii0, int)
        companies[g] = {
            "n": len(ii0),
            "primary_delta_mhq_minus_mh": float(np.mean(cs["MHQ"][ii] - cs["MH"][ii])),
            "mq_minus_mh": float(np.mean(cs["MQ"][ii] - cs["MH"][ii])),
            "mae_mh": float(np.mean(np.abs(y[ii] - arms["MH"][2][ii]))),
            "mae_mhq": float(np.mean(np.abs(y[ii] - arms["MHQ"][2][ii]))),
            "rmse_mh": float(np.sqrt(np.mean((y[ii] - arms["MH"][2][ii]) ** 2))),
            "rmse_mhq": float(np.sqrt(np.mean((y[ii] - arms["MHQ"][2][ii]) ** 2))),
            "arm_scale_delta_mhq_minus_mh": float(np.mean(ads["MHQ"][ii] - ads["MH"][ii])),
        }
    vals = np.asarray([v["primary_delta_mhq_minus_mh"] for v in companies.values()])
    return base | {
        "status": "EXECUTED", "common_sigma_m0": common,
        "training_sigma_mh": arms["MH"][1], "training_sigma_mhq": arms["MHQ"][1],
        "mhq_q_coefficient": float(arms["MHQ"][0][-1]),
        "primary_delta_mhq_minus_mh": float(np.mean(vals)),
        "positive_company_fraction": float(np.mean(vals > 0)),
        "mq_minus_mh": float(np.mean([v["mq_minus_mh"] for v in companies.values()])),
        "mae_mh": float(np.mean([v["mae_mh"] for v in companies.values()])),
        "mae_mhq": float(np.mean([v["mae_mhq"] for v in companies.values()])),
        "rmse_mh": float(np.mean([v["rmse_mh"] for v in companies.values()])),
        "rmse_mhq": float(np.mean([v["rmse_mhq"] for v in companies.values()])),
        "arm_scale_delta_mhq_minus_mh": float(np.mean([v["arm_scale_delta_mhq_minus_mh"] for v in companies.values()])),
        "company_results": companies,
    }


def bootstrap(rr):
    ok = [r for r in rr if r["status"] == "EXECUTED"]
    if len(ok) < 4: return {"eligible_lobs": len(ok), "classification": "BLOCKED_BY_DATA"}
    rng = np.random.default_rng(SEED); draws = {}; pooled = np.empty(REPS)
    for r in ok:
        v = np.asarray([x["primary_delta_mhq_minus_mh"] for x in r["company_results"].values()])
        draws[r["lob"]] = v[rng.integers(0, len(v), size=(REPS, len(v)))].mean(1)
    for i in range(REPS): pooled[i] = np.mean([draws[r["lob"]][i] for r in ok])
    point = float(np.mean([r["primary_delta_mhq_minus_mh"] for r in ok]))
    lo, hi = map(float, np.quantile(pooled, [0.025, 0.975])); pos = sum(r["primary_delta_mhq_minus_mh"] > 0 for r in ok)
    req = 5 if len(ok) == 6 else len(ok)
    verdict = "SUPPORTED" if lo > 0 and pos >= req else ("WEAKENED" if hi < 0 else "MIXED")
    return {"eligible_lobs": len(ok), "positive_lobs": pos, "required_positive_lobs": req,
            "pooled_primary_delta": point, "bootstrap_95pct": [lo, hi],
            "lob_bootstrap_95pct": {k: list(map(float, np.quantile(v, [0.025, 0.975]))) for k, v in draws.items()},
            "bootstrap_seed": SEED, "bootstrap_reps": REPS, "classification": verdict}


def kv(spec):
    k, v = spec.split("=", 1); return k, v


def main():
    p = argparse.ArgumentParser(); p.add_argument("--dataset", action="append", required=True); p.add_argument("--source-url", action="append", required=True); p.add_argument("--output", required=True)
    a = p.parse_args(); paths = dict((k, Path(v)) for k, v in map(kv, a.dataset)); urls = dict(map(kv, a.source_url))
    rr = [eval_lob(k, paths[k], urls[k]) for k in paths]
    receipt = {"schema": "reserving-cas2025-paid-incurred-company-holdout-v0", "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "bridge": {"repository": "pokekarten/OpenCatastrophe-data", "purpose": "public runner only", "ffbk_pr": 1473},
               "lob_results": rr, "aggregate": bootstrap(rr)}
    Path(a.output).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt["aggregate"], sort_keys=True))

if __name__ == "__main__": main()
