#!/usr/bin/env python3
"""Public-runner bridge for FFBK PR #1480.

Known CAS Schedule-P source family; target bytes are never committed.
The model contract was frozen in FFBK before this lane scores 2009 outcomes.
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

VALUATION_YEAR = 2008
TARGET_YEAR = 2009
SALT = "cas2025-paid-incurred-multistep-2009-v0"
SEED = 2026090709
REPS = 2000
MIN_TRAIN = 30
MIN_FINAL = 10
MIN_LAGS = 3

EXPECTED_SHA = {
    "ppauto": "6e838f1e44c67218133ef1c8e28ca2b34b9f21ba4ee94de408c412638f798d96",
    "wkcomp": "8d0b02bed0939e932f9078f65266e9a398f580f90e5227cde053dd5b520affef",
    "comauto": "5012bd4c9048e300669e2f4fc915850449099e159481b4c3349b574f6f00afe1",
    "medmal": "50ea237914797562661b82996765e40b1fd09784a63130463bbd4972f74dbba3",
    "prodliab": "f1070b5a95658bfeb6719fdf4ffdabc8b7e3f97771cdb4b3f503eb7d6e486f01",
    "othliab": "f514136de4be7b5ac114346709c309cd2464861e9fbb683051849f9fa6eadc50",
}


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def bucket(lob: str, grcode: str) -> int:
    token = f"{SALT}|{lob}|{grcode}".encode("utf-8")
    return int(hashlib.sha256(token).hexdigest(), 16) % 5


def norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def col(fields: list[str], *aliases: str) -> str:
    for stem in aliases:
        n = norm(stem)
        exact = [x for x in fields if norm(x) == n]
        if len(exact) == 1:
            return exact[0]
        pref = [x for x in fields if norm(x).startswith(n)]
        if len(pref) == 1:
            return pref[0]
    raise ValueError(f"cannot resolve any of {aliases}: {fields}")


def read_rows(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        fields = list(rd.fieldnames or [])
        cg = col(fields, "GRCODE")
        co = col(fields, "AccidentYear")
        cy = col(fields, "DevelopmentYear")
        cl = col(fields, "DevelopmentLag")
        ci = col(fields, "IncurLoss", "IncurredLosses")
        cp = col(fields, "CumPaidLoss")
        out = {}
        for r in rd:
            try:
                g = str(r[cg]).strip()
                o = int(float(r[co]))
                year = int(float(r[cy]))
                lag = int(float(r[cl]))
                inc = float(r[ci])
                paid = float(r[cp])
            except (TypeError, ValueError):
                continue
            if not g:
                continue
            k = (g, o, lag)
            if k in out:
                raise ValueError(f"duplicate key {k}")
            out[k] = (year, inc, paid)
    return out, fields


def transitions(rows):
    train, target = [], []
    for (g, o, lag), (year, inc, paid) in rows.items():
        if lag < 3:
            continue
        prev1 = rows.get((g, o, lag - 1))
        prev2 = rows.get((g, o, lag - 2))
        nxt = rows.get((g, o, lag + 1))
        if prev1 is None or prev2 is None or nxt is None:
            continue
        y1, inc1, p1 = prev1
        y2, inc2, p2 = prev2
        yn, incn, pn = nxt
        if min(p2, p1, paid, inc, pn) <= 0:
            continue
        if y2 != year - 2 or y1 != year - 1 or yn != year + 1:
            continue
        t = (
            g,
            lag,
            math.log(pn / paid),
            math.log(paid / p1),
            math.log(p1 / p2),
            math.log(paid / inc),
        )
        response_year = yn
        if response_year <= VALUATION_YEAR:
            train.append(t)
        elif year == VALUATION_YEAR and response_year == TARGET_YEAR:
            target.append(t)
    return train, target


def means(rows, pos):
    d = defaultdict(list)
    for r in rows:
        d[r[1]].append(r[pos])
    return {k: float(np.mean(v)) for k, v in d.items()}


def design(rows, ages, h1m, h2m, qm, arm):
    xx = []
    for r in rows:
        g, lag, y, h1, h2, q = r
        if lag not in ages or lag not in h1m or lag not in h2m or lag not in qm:
            raise ValueError(f"unseen lag {lag}")
        x = [1.0] + [1.0 if lag == a else 0.0 for a in ages[1:]]
        if arm in ("MH1", "MH12", "MH12Q"):
            x.append(h1 - h1m[lag])
        if arm in ("MH12", "MH12Q"):
            x.append(h2 - h2m[lag])
        if arm == "MH12Q":
            x.append(q - qm[lag])
        xx.append(x)
    return np.asarray(xx, float)


def fit(rows, ages, h1m, h2m, qm, arm):
    x = design(rows, ages, h1m, h2m, qm, arm)
    y = np.asarray([r[2] for r in rows], dtype=float)
    beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    if rank < x.shape[1]:
        raise ValueError(f"rank deficient {arm}: rank={rank}, p={x.shape[1]}")
    resid = y - x @ beta
    sigma = math.sqrt(float(np.mean(resid * resid)))
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError(f"bad sigma {arm}")
    return beta, sigma


def logscore(y, mu, sigma):
    return -0.5 * math.log(2.0 * math.pi) - math.log(sigma) - 0.5 * ((y - mu) / sigma) ** 2


def eval_lob(lob: str, path: Path, url: str):
    sha = file_sha(path)
    if lob not in EXPECTED_SHA:
        raise ValueError(f"unknown lob {lob}")
    if sha != EXPECTED_SHA[lob]:
        raise ValueError(f"source identity mismatch {lob}: {sha} != {EXPECTED_SHA[lob]}")

    rows, fields = read_rows(path)
    all_train, all_target = transitions(rows)
    train_g = {r[0] for r in all_train if bucket(lob, r[0]) != 0}
    final_g = {r[0] for r in all_target if bucket(lob, r[0]) == 0}
    train = [r for r in all_train if r[0] in train_g]
    target = [r for r in all_target if r[0] in final_g]
    if {r[0] for r in train} & final_g:
        raise AssertionError("company leakage")

    ages = sorted({r[1] for r in train})
    target_lags = sorted({r[1] for r in target})
    base = {
        "lob": lob,
        "source_url": url,
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha,
        "header": fields,
        "triangle_rows": len(rows),
        "train_companies": len(train_g),
        "final_companies": len(final_g),
        "train_transitions": len(train),
        "final_transitions": len(target),
        "target_lags": target_lags,
    }
    adequate = (
        len(train_g) >= MIN_TRAIN
        and len(final_g) >= MIN_FINAL
        and len(target_lags) >= MIN_LAGS
    )
    if not adequate or not target or not set(target_lags).issubset(ages):
        return base | {"status": "BLOCKED_BY_DATA"}

    h1m, h2m, qm = means(train, 3), means(train, 4), means(train, 5)
    fitted = {}
    pred = {}
    for arm in ("M0", "MH1", "MH12", "MH12Q"):
        beta, sigma = fit(train, ages, h1m, h2m, qm, arm)
        fitted[arm] = (beta, sigma)
        pred[arm] = design(target, ages, h1m, h2m, qm, arm) @ beta

    y = np.asarray([r[2] for r in target], dtype=float)
    common_sigma = fitted["M0"][1]
    common_scores = {a: logscore(y, pred[a], common_sigma) for a in pred}
    arm_scores = {
        a: logscore(y, pred[a], fitted[a][1])
        for a in ("MH1", "MH12", "MH12Q")
    }

    by_company = defaultdict(list)
    for i, r in enumerate(target):
        by_company[r[0]].append(i)

    companies = {}
    for g, idx0 in sorted(by_company.items()):
        idx = np.asarray(idx0, dtype=int)
        companies[g] = {
            "n": len(idx0),
            "primary_delta_mh12q_minus_mh12": float(
                np.mean(common_scores["MH12Q"][idx] - common_scores["MH12"][idx])
            ),
            "paid_history_delta_mh12_minus_mh1": float(
                np.mean(common_scores["MH12"][idx] - common_scores["MH1"][idx])
            ),
            "net_delta_mh12q_minus_mh1": float(
                np.mean(common_scores["MH12Q"][idx] - common_scores["MH1"][idx])
            ),
            "mae_mh1": float(np.mean(np.abs(y[idx] - pred["MH1"][idx]))),
            "mae_mh12": float(np.mean(np.abs(y[idx] - pred["MH12"][idx]))),
            "mae_mh12q": float(np.mean(np.abs(y[idx] - pred["MH12Q"][idx]))),
            "rmse_mh1": float(np.sqrt(np.mean((y[idx] - pred["MH1"][idx]) ** 2))),
            "rmse_mh12": float(np.sqrt(np.mean((y[idx] - pred["MH12"][idx]) ** 2))),
            "rmse_mh12q": float(np.sqrt(np.mean((y[idx] - pred["MH12Q"][idx]) ** 2))),
            "arm_scale_primary_delta": float(
                np.mean(arm_scores["MH12Q"][idx] - arm_scores["MH12"][idx])
            ),
        }

    primary = np.asarray(
        [v["primary_delta_mh12q_minus_mh12"] for v in companies.values()], dtype=float
    )
    paid_hist = np.asarray(
        [v["paid_history_delta_mh12_minus_mh1"] for v in companies.values()], dtype=float
    )
    return base | {
        "status": "EXECUTED",
        "common_sigma_m0": common_sigma,
        "training_sigma_mh1": fitted["MH1"][1],
        "training_sigma_mh12": fitted["MH12"][1],
        "training_sigma_mh12q": fitted["MH12Q"][1],
        "mh12q_h1_coefficient": float(fitted["MH12Q"][0][-3]),
        "mh12q_h2_coefficient": float(fitted["MH12Q"][0][-2]),
        "mh12q_q_coefficient": float(fitted["MH12Q"][0][-1]),
        "primary_delta_mh12q_minus_mh12": float(np.mean(primary)),
        "positive_company_fraction_primary": float(np.mean(primary > 0)),
        "paid_history_delta_mh12_minus_mh1": float(np.mean(paid_hist)),
        "positive_company_fraction_paid_history": float(np.mean(paid_hist > 0)),
        "net_delta_mh12q_minus_mh1": float(
            np.mean([v["net_delta_mh12q_minus_mh1"] for v in companies.values()])
        ),
        "mae_mh1": float(np.mean([v["mae_mh1"] for v in companies.values()])),
        "mae_mh12": float(np.mean([v["mae_mh12"] for v in companies.values()])),
        "mae_mh12q": float(np.mean([v["mae_mh12q"] for v in companies.values()])),
        "rmse_mh1": float(np.mean([v["rmse_mh1"] for v in companies.values()])),
        "rmse_mh12": float(np.mean([v["rmse_mh12"] for v in companies.values()])),
        "rmse_mh12q": float(np.mean([v["rmse_mh12q"] for v in companies.values()])),
        "arm_scale_primary_delta": float(
            np.mean([v["arm_scale_primary_delta"] for v in companies.values()])
        ),
        "company_results": companies,
    }


def bootstrap(results):
    ok = [r for r in results if r["status"] == "EXECUTED"]
    if len(ok) < 4:
        return {"eligible_lobs": len(ok), "classification": "BLOCKED_BY_DATA"}
    rng = np.random.default_rng(SEED)
    primary_draws = {}
    paid_history_draws = {}
    pooled = np.empty(REPS, dtype=float)
    for r in ok:
        primary = np.asarray(
            [x["primary_delta_mh12q_minus_mh12"] for x in r["company_results"].values()],
            dtype=float,
        )
        paid_hist = np.asarray(
            [x["paid_history_delta_mh12_minus_mh1"] for x in r["company_results"].values()],
            dtype=float,
        )
        idx = rng.integers(0, len(primary), size=(REPS, len(primary)))
        primary_draws[r["lob"]] = primary[idx].mean(axis=1)
        paid_history_draws[r["lob"]] = paid_hist[idx].mean(axis=1)

    for i in range(REPS):
        pooled[i] = float(np.mean([primary_draws[r["lob"]][i] for r in ok]))

    point = float(np.mean([r["primary_delta_mh12q_minus_mh12"] for r in ok]))
    lo, hi = map(float, np.quantile(pooled, [0.025, 0.975]))
    positive_lobs = sum(r["primary_delta_mh12q_minus_mh12"] > 0 for r in ok)
    required = 5 if len(ok) == 6 else len(ok)
    if lo > 0 and positive_lobs >= required:
        verdict = "SUPPORTED"
    elif hi < 0:
        verdict = "WEAKENED"
    else:
        verdict = "MIXED"

    return {
        "eligible_lobs": len(ok),
        "positive_lobs": positive_lobs,
        "required_positive_lobs": required,
        "pooled_primary_delta": point,
        "bootstrap_95pct": [lo, hi],
        "lob_bootstrap_95pct": {
            k: list(map(float, np.quantile(v, [0.025, 0.975])))
            for k, v in primary_draws.items()
        },
        "paid_history_lob_bootstrap_95pct": {
            k: list(map(float, np.quantile(v, [0.025, 0.975])))
            for k, v in paid_history_draws.items()
        },
        "lobs_paid_history_positive": sum(
            r["paid_history_delta_mh12_minus_mh1"] > 0 for r in ok
        ),
        "bootstrap_seed": SEED,
        "bootstrap_reps": REPS,
        "classification": verdict,
    }


def kv(spec):
    k, v = spec.split("=", 1)
    return k, v


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", action="append", required=True)
    p.add_argument("--source-url", action="append", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    paths = dict((k, Path(v)) for k, v in map(kv, a.dataset))
    urls = dict(map(kv, a.source_url))
    if set(paths) != set(EXPECTED_SHA) or set(urls) != set(EXPECTED_SHA):
        raise ValueError("must provide exactly the six frozen LoBs")
    results = [eval_lob(k, paths[k], urls[k]) for k in sorted(paths)]
    receipt = {
        "schema": "reserving-cas2025-paid-incurred-multistep-2009-v0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "ffbk_pr": 1480,
        "protocol": {
            "valuation_year": VALUATION_YEAR,
            "target_year": TARGET_YEAR,
            "split_salt": SALT,
            "models": ["M0", "MH1", "MH12", "MH12Q"],
            "primary_contrast": "MH12Q - MH12",
            "common_scale": "M0 training residual RMS",
            "bootstrap_seed": SEED,
            "bootstrap_reps": REPS,
        },
        "lob_results": results,
        "aggregate": bootstrap(results),
    }
    Path(a.output).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt["aggregate"], sort_keys=True))


if __name__ == "__main__":
    main()
