#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy import optimize, stats
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_gamma_deviance
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import statsmodels
import statsmodels.api as sm
import rdata

SOURCE_URL = "https://raw.githubusercontent.com/henckr/treeML/71bf218fa3528fd66dd3c6f9eed9a4bf06e58a22/mtpl_data.rds"
SOURCE_SHA256 = "2d08a6b2cdc5b3eac8e38cd9b1aeedadaa4955ecebfb9280365ff763683ea1db"
SOURCE_BLOB = "11b3aa146f426eef59044884208d921ca56d370d"
EXPECTED_ROWS = 163212
OUTER_SALT = "bemtpl97-sev-outer|"
INNER_SALT = "bemtpl97-sev-inner|outer={outer}|"
CATEGORICAL = ["coverage", "fuel", "sex", "use", "fleet"]
NUMERIC = ["ageph", "power", "agec", "bm", "long", "lat"]
PREDICTORS = CATEGORICAL + NUMERIC
GRID = [(leaf, minleaf, it) for leaf in (15, 31) for minleaf in (50, 150) for it in (100, 200)]
BOOT_REPS = 10000
BOOT_SEED = 20260908


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_id(x) -> str:
    xf = float(x)
    if not math.isfinite(xf) or xf != math.floor(xf):
        raise RuntimeError(f"FAIL_CLOSED non-integer id: {x!r}")
    return str(int(xf))


def hash_bucket(salt: str, ident, mod: int = 5) -> int:
    b = hashlib.sha256((salt + canonical_id(ident)).encode("utf-8")).digest()
    return int.from_bytes(b[:8], "big") % mod


def outer_fold(ids: pd.Series) -> np.ndarray:
    return np.array([hash_bucket(OUTER_SALT, x) for x in ids], dtype=int)


def inner_valid(ids: pd.Series, outer: int) -> np.ndarray:
    salt = INNER_SALT.format(outer=outer)
    return np.array([hash_bucket(salt, x) == 0 for x in ids], dtype=bool)


def make_preprocessor():
    return ColumnTransformer(
        [
            ("cat", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False), CATEGORICAL),
            ("num", StandardScaler(), NUMERIC),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )


def fit_glm(train: pd.DataFrame, family: str):
    prep = make_preprocessor()
    X = prep.fit_transform(train[PREDICTORS])
    X = sm.add_constant(np.asarray(X, dtype=float), has_constant="add")
    y = train["average"].to_numpy(float)
    w = train["nclaims"].to_numpy(float)
    if family == "gamma":
        fam = sm.families.Gamma(link=sm.families.links.Log())
    elif family == "ig":
        fam = sm.families.InverseGaussian(link=sm.families.links.Log())
    else:
        raise ValueError(family)
    model = sm.GLM(y, X, family=fam, var_weights=w)
    fit = model.fit(maxiter=300, tol=1e-9)
    mu = np.asarray(fit.predict(X), dtype=float)
    return prep, fit, mu


def predict_glm(obj, frame: pd.DataFrame) -> np.ndarray:
    prep, fit, _ = obj
    X = prep.transform(frame[PREDICTORS])
    X = sm.add_constant(np.asarray(X, dtype=float), has_constant="add")
    out = np.asarray(fit.predict(X), dtype=float)
    if np.any(~np.isfinite(out)) or np.any(out <= 0):
        raise RuntimeError("FAIL_CLOSED non-positive/non-finite GLM mean")
    return out


def fit_flexible(train: pd.DataFrame, outer: int):
    is_val = inner_valid(train["id"], outer)
    if is_val.sum() < 100 or (~is_val).sum() < 100:
        raise RuntimeError("FAIL_CLOSED insufficient inner split")
    fit_df = train.loc[~is_val].copy()
    val_df = train.loc[is_val].copy()
    prep = make_preprocessor()
    Xfit = np.asarray(prep.fit_transform(fit_df[PREDICTORS]), dtype=float)
    Xval = np.asarray(prep.transform(val_df[PREDICTORS]), dtype=float)
    yfit = fit_df["average"].to_numpy(float)
    yval = val_df["average"].to_numpy(float)
    wfit = fit_df["nclaims"].to_numpy(float)
    wval = val_df["nclaims"].to_numpy(float)
    scores = []
    for leaf, minleaf, it in GRID:
        m = HistGradientBoostingRegressor(
            loss="gamma",
            learning_rate=0.05,
            max_leaf_nodes=leaf,
            min_samples_leaf=minleaf,
            max_iter=it,
            l2_regularization=1.0,
            early_stopping=False,
            random_state=0,
        )
        m.fit(Xfit, yfit, sample_weight=wfit)
        pv = np.clip(m.predict(Xval), 1e-12, None)
        score = float(mean_gamma_deviance(yval, pv, sample_weight=wval))
        scores.append((score, leaf, minleaf, it))
    scores.sort(key=lambda z: (z[0], z[1], z[2], z[3]))
    _, leaf, minleaf, it = scores[0]
    prep_full = make_preprocessor()
    Xfull = np.asarray(prep_full.fit_transform(train[PREDICTORS]), dtype=float)
    mfull = HistGradientBoostingRegressor(
        loss="gamma",
        learning_rate=0.05,
        max_leaf_nodes=leaf,
        min_samples_leaf=minleaf,
        max_iter=it,
        l2_regularization=1.0,
        early_stopping=False,
        random_state=0,
    )
    mfull.fit(Xfull, train["average"].to_numpy(float), sample_weight=train["nclaims"].to_numpy(float))
    mu_train = np.clip(np.asarray(mfull.predict(Xfull), dtype=float), 1e-12, None)
    return (prep_full, mfull, mu_train), {
        "selected": {"max_leaf_nodes": leaf, "min_samples_leaf": minleaf, "max_iter": it},
        "inner_validation_rows": int(is_val.sum()),
        "inner_fit_rows": int((~is_val).sum()),
        "grid_scores": [
            {"gamma_deviance": s, "max_leaf_nodes": l, "min_samples_leaf": ml, "max_iter": ii}
            for s, l, ml, ii in scores
        ],
    }


def predict_flexible(obj, frame: pd.DataFrame) -> np.ndarray:
    prep, model, _ = obj
    X = np.asarray(prep.transform(frame[PREDICTORS]), dtype=float)
    out = np.asarray(model.predict(X), dtype=float)
    if np.any(~np.isfinite(out)) or np.any(out <= 0):
        raise RuntimeError("FAIL_CLOSED non-positive/non-finite flexible mean")
    return out


def logpdf(family: str, y, mu, n, phi: float):
    y = np.asarray(y, float)
    mu = np.asarray(mu, float)
    n = np.asarray(n, float)
    if phi <= 0 or np.any(y <= 0) or np.any(mu <= 0) or np.any(n <= 0):
        raise RuntimeError("FAIL_CLOSED density inputs")
    if family == "gamma":
        return stats.gamma.logpdf(y, a=n / phi, scale=phi * mu / n)
    if family == "ig":
        return stats.invgauss.logpdf(y, mu=phi * mu / n, scale=n / phi)
    raise ValueError(family)


def sf(family: str, threshold: float, mu, n, phi: float):
    mu = np.asarray(mu, float)
    n = np.asarray(n, float)
    if family == "gamma":
        return stats.gamma.sf(threshold, a=n / phi, scale=phi * mu / n)
    if family == "ig":
        return stats.invgauss.sf(threshold, mu=phi * mu / n, scale=n / phi)
    raise ValueError(family)


def fit_phi(family: str, y, mu, n) -> float:
    def objective(logphi):
        phi = math.exp(float(logphi))
        lp = logpdf(family, y, mu, n, phi)
        if np.any(~np.isfinite(lp)):
            return 1e100
        return float(-np.mean(lp))

    res = optimize.minimize_scalar(
        objective,
        bounds=(-20.0, 20.0),
        method="bounded",
        options={"xatol": 1e-9, "maxiter": 500},
    )
    if not res.success:
        raise RuntimeError(f"FAIL_CLOSED dispersion optimization {family}: {res.message}")
    phi = math.exp(float(res.x))
    if not math.isfinite(phi) or phi <= 0:
        raise RuntimeError("FAIL_CLOSED invalid phi")
    return phi


def truth_known_parameterization_guard():
    checks = []
    for mu in (500.0, 2000.0):
        for n in (1.0, 2.0, 7.0):
            phi_g = 0.7
            a, scale = n / phi_g, phi_g * mu / n
            mg, vg = stats.gamma.stats(a=a, scale=scale, moments="mv")
            eg, vg0 = mu, phi_g * mu * mu / n
            phi_i = 2e-4
            shape, scale_i = phi_i * mu / n, n / phi_i
            mi, vi = stats.invgauss.stats(mu=shape, scale=scale_i, moments="mv")
            ei, vi0 = mu, phi_i * mu**3 / n
            for name, got, want in [
                ("gamma_mean", float(mg), eg),
                ("gamma_var", float(vg), vg0),
                ("ig_mean", float(mi), ei),
                ("ig_var", float(vi), vi0),
            ]:
                rel = abs(got - want) / max(1.0, abs(want))
                if rel > 1e-10:
                    raise RuntimeError(f"FAIL_CLOSED parameterization {name} rel={rel}")
                checks.append({"name": name, "mu": mu, "n": n, "relative_error": rel})
    return checks


def brier(y_event, p):
    y_event = np.asarray(y_event, float)
    p = np.asarray(p, float)
    return (p - y_event) ** 2


def ae(obs, pred, weight=None):
    obs = np.asarray(obs, float)
    pred = np.asarray(pred, float)
    if weight is None:
        return float(obs.sum() / pred.sum())
    w = np.asarray(weight, float)
    return float(np.sum(w * obs) / np.sum(w * pred))


def load_data(path: Path) -> pd.DataFrame:
    if sha256_path(path) != SOURCE_SHA256:
        raise RuntimeError("FAIL_CLOSED source SHA256")
    obj = rdata.read_rds(path)
    if not isinstance(obj, pd.DataFrame):
        obj = pd.DataFrame(obj)
    d = obj.copy()
    if len(d) != EXPECTED_ROWS:
        raise RuntimeError(f"FAIL_CLOSED row count {len(d)}")
    required = {"id", "nclaims", "amount", "average", *PREDICTORS}
    if not required.issubset(d.columns):
        raise RuntimeError(f"FAIL_CLOSED missing columns {sorted(required - set(d.columns))}")
    if d["id"].nunique(dropna=False) != EXPECTED_ROWS:
        raise RuntimeError("FAIL_CLOSED id uniqueness")
    for c in NUMERIC + ["id", "nclaims", "amount", "average"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in CATEGORICAL:
        d[c] = d[c].astype(str)
    eligible = d.loc[d["nclaims"] > 0].copy()
    if eligible.empty:
        raise RuntimeError("FAIL_CLOSED no positive-claim rows")
    if eligible[PREDICTORS + ["id", "nclaims", "amount", "average"]].isna().any().any():
        raise RuntimeError("FAIL_CLOSED missing eligible value")
    if np.any(eligible["nclaims"].to_numpy(float) != np.floor(eligible["nclaims"].to_numpy(float))):
        raise RuntimeError("FAIL_CLOSED noninteger nclaims")
    if np.any(eligible["amount"].to_numpy(float) <= 0) or np.any(eligible["average"].to_numpy(float) <= 0):
        raise RuntimeError("FAIL_CLOSED nonpositive severity target")
    implied = eligible["amount"].to_numpy(float) / eligible["nclaims"].to_numpy(float)
    if not np.allclose(implied, eligible["average"].to_numpy(float), rtol=1e-10, atol=1e-8):
        raise RuntimeError("FAIL_CLOSED amount/nclaims != average")
    eligible["outer_fold"] = outer_fold(eligible["id"])
    return eligible.reset_index(drop=True)


def run_fold(d: pd.DataFrame, k: int):
    train = d.loc[d["outer_fold"] != k].copy()
    test = d.loc[d["outer_fold"] == k].copy()
    if len(test) < 100:
        raise RuntimeError("FAIL_CLOSED small outer fold")
    g_obj = fit_glm(train, "gamma")
    i_obj = fit_glm(train, "ig")
    f_obj, fdiag = fit_flexible(train, k)
    g_mu_tr = g_obj[2]
    i_mu_tr = i_obj[2]
    f_mu_tr = f_obj[2]
    ytr = train["average"].to_numpy(float)
    ntr = train["nclaims"].to_numpy(float)
    phi_g0 = fit_phi("gamma", ytr, g_mu_tr, ntr)
    phi_i0 = fit_phi("ig", ytr, i_mu_tr, ntr)
    phi_fg = fit_phi("gamma", ytr, f_mu_tr, ntr)
    phi_fi = fit_phi("ig", ytr, f_mu_tr, ntr)
    g_mu = predict_glm(g_obj, test)
    i_mu = predict_glm(i_obj, test)
    f_mu = predict_flexible(f_obj, test)
    y = test["average"].to_numpy(float)
    n = test["nclaims"].to_numpy(float)
    means = {"G0": g_mu, "I0": i_mu, "FG": f_mu, "FI": f_mu}
    fams = {
        "G0": ("gamma", phi_g0),
        "I0": ("ig", phi_i0),
        "FG": ("gamma", phi_fg),
        "FI": ("ig", phi_fi),
    }
    nll = {arm: -logpdf(fam, y, means[arm], n, phi) for arm, (fam, phi) in fams.items()}
    thresholds = {"q99": float(np.quantile(ytr, 0.99)), "q995": float(np.quantile(ytr, 0.995))}
    tail = {}
    for qname, t in thresholds.items():
        ye = (y > t).astype(float)
        tail[qname] = {}
        for arm, (fam, phi) in fams.items():
            p = sf(fam, t, means[arm], n, phi)
            if np.any(~np.isfinite(p)) or np.any((p < 0) | (p > 1)):
                raise RuntimeError("FAIL_CLOSED tail probability")
            tail[qname][arm] = {"brier_values": brier(ye, p), "probabilities": p, "events": ye}
    subgroups = {}
    buckets = np.where(n == 1, "1", np.where(n == 2, "2", "3+"))
    for b in ("1", "2", "3+"):
        m = buckets == b
        if not m.any():
            continue
        subgroups[b] = {
            "n": int(m.sum()),
            "claim_weight": float(n[m].sum()),
            "ae_policy": {arm: ae(y[m], means[arm][m]) for arm in means},
            "ae_claim_weighted": {arm: ae(y[m], means[arm][m], n[m]) for arm in means},
        }
    return {
        "fold": k,
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "test_claims": float(n.sum()),
        "thresholds": thresholds,
        "phis": {"G0": phi_g0, "I0": phi_i0, "FG": phi_fg, "FI": phi_fi},
        "flexible": fdiag,
        "nll_mean": {arm: float(v.mean()) for arm, v in nll.items()},
        "nll_delta_I0_minus_G0": float(np.mean(nll["I0"] - nll["G0"])),
        "nll_delta_FI_minus_FG": float(np.mean(nll["FI"] - nll["FG"])),
        "tail_brier": {q: {arm: float(z["brier_values"].mean()) for arm, z in arms.items()} for q, arms in tail.items()},
        "tail_delta": {
            q: {
                "I0_minus_G0": float(np.mean(arms["I0"]["brier_values"] - arms["G0"]["brier_values"])),
                "FI_minus_FG": float(np.mean(arms["FI"]["brier_values"] - arms["FG"]["brier_values"])),
            }
            for q, arms in tail.items()
        },
        "ae_policy": {arm: ae(y, means[arm]) for arm in means},
        "ae_claim_weighted": {arm: ae(y, means[arm], n) for arm in means},
        "subgroups": subgroups,
        "_rows": {
            "id": test["id"].astype(int).tolist(),
            "fold": [k] * len(test),
            "y": y.tolist(),
            "n": n.tolist(),
            **{f"mu_{arm}": means[arm].tolist() for arm in means},
            **{f"nll_{arm}": nll[arm].tolist() for arm in nll},
            **{f"brier_{q}_{arm}": tail[q][arm]["brier_values"].tolist() for q in tail for arm in tail[q]},
        },
    }


def paired_boot(delta: np.ndarray):
    rng = np.random.default_rng(BOOT_SEED)
    n = len(delta)
    vals = np.empty(BOOT_REPS, dtype=float)
    for i in range(BOOT_REPS):
        idx = rng.integers(0, n, size=n)
        vals[i] = float(np.mean(delta[idx]))
    return {
        "reps": BOOT_REPS,
        "seed": BOOT_SEED,
        "q025": float(np.quantile(vals, 0.025)),
        "median": float(np.quantile(vals, 0.5)),
        "q975": float(np.quantile(vals, 0.975)),
    }


def main():
    outdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    outdir.mkdir(parents=True, exist_ok=True)
    data_path = outdir / "mtpl_data.rds"
    if not data_path.exists():
        urllib.request.urlretrieve(SOURCE_URL, data_path)
    guard = truth_known_parameterization_guard()
    d = load_data(data_path)
    print("DATA", json.dumps({
        "rows": EXPECTED_ROWS,
        "eligible_positive_claim_rows": int(len(d)),
        "eligible_claim_count": float(d["nclaims"].sum()),
        "average_mean_policy": float(d["average"].mean()),
        "average_mean_claim_weighted": float(np.average(d["average"], weights=d["nclaims"])),
        "average_q99": float(np.quantile(d["average"], .99)),
        "average_q995": float(np.quantile(d["average"], .995)),
        "average_max": float(d["average"].max()),
        "outer_fold_counts": {str(k): int((d["outer_fold"] == k).sum()) for k in range(5)},
    }, sort_keys=True), flush=True)
    folds = []
    rows = []
    for k in range(5):
        print("START_FOLD", k, flush=True)
        r = run_fold(d, k)
        rows.append(pd.DataFrame(r.pop("_rows")))
        folds.append(r)
        print("DONE_FOLD", k, json.dumps({
            "nll_delta_I0_minus_G0": r["nll_delta_I0_minus_G0"],
            "nll_delta_FI_minus_FG": r["nll_delta_FI_minus_FG"],
            "q995": r["tail_delta"]["q995"],
            "selected_flexible": r["flexible"]["selected"],
        }, sort_keys=True), flush=True)
    oof = pd.concat(rows, ignore_index=True).sort_values("id").reset_index(drop=True)
    if len(oof) != len(d) or oof["id"].nunique() != len(d):
        raise RuntimeError("FAIL_CLOSED OOF row identity")
    d_i0g0 = (oof["nll_I0"] - oof["nll_G0"]).to_numpy(float)
    d_fifg = (oof["nll_FI"] - oof["nll_FG"]).to_numpy(float)
    summary = {
        "n_eligible": int(len(oof)),
        "primary_nll": {
            "G0": float(oof["nll_G0"].mean()),
            "I0": float(oof["nll_I0"].mean()),
            "I0_minus_G0": float(d_i0g0.mean()),
            "I0_better_folds": int(sum(x["nll_delta_I0_minus_G0"] < 0 for x in folds)),
            "bootstrap": paired_boot(d_i0g0),
        },
        "mean_matched_nll": {
            "FG": float(oof["nll_FG"].mean()),
            "FI": float(oof["nll_FI"].mean()),
            "FI_minus_FG": float(d_fifg.mean()),
            "FI_better_folds": int(sum(x["nll_delta_FI_minus_FG"] < 0 for x in folds)),
            "bootstrap": paired_boot(d_fifg),
        },
        "tail": {},
        "leave_one_fold_out": {},
    }
    for q in ("q99", "q995"):
        for key, a, b in (("I0_minus_G0", "I0", "G0"), ("FI_minus_FG", "FI", "FG")):
            delta = (oof[f"brier_{q}_{a}"] - oof[f"brier_{q}_{b}"]).to_numpy(float)
            summary["tail"].setdefault(q, {})[key] = {
                "delta": float(delta.mean()),
                "better_folds": int(sum(x["tail_delta"][q][key] < 0 for x in folds)),
                "bootstrap": paired_boot(delta),
            }
    for heldout in range(5):
        m = oof["fold"].to_numpy(int) != heldout
        summary["leave_one_fold_out"][str(heldout)] = {
            "I0_minus_G0": float(d_i0g0[m].mean()),
            "FI_minus_FG": float(d_fifg[m].mean()),
        }
    i0 = summary["primary_nll"]["I0_minus_G0"]
    fi = summary["mean_matched_nll"]["FI_minus_FG"]
    if i0 < 0 and fi < 0:
        verdict = "SUPPORTED_TRANSFER"
        hypothesis = "H1_DISTRIBUTION_FAMILY_TRANSFER"
    elif i0 < 0 and fi >= 0:
        verdict = "MIXED_MEAN_STRUCTURE_EXPLAINS_OR_REVERSES"
        hypothesis = "H2_MEAN_STRUCTURE_EXPLANATION"
    elif i0 >= 0 and fi >= 0:
        verdict = "WEAKENED_NO_TRANSFER"
        hypothesis = "H0_NO_TRANSFER"
    else:
        verdict = "MIXED_CONSUMER_OR_MEAN_DEPENDENT"
        hypothesis = "H3_MIXED"
    receipt = {
        "schema": "ffbk-bemtpl97-severity-family-transfer-v0",
        "status": "EXECUTED_SUCCESS",
        "research_verdict": verdict,
        "most_consistent_hypothesis": hypothesis,
        "source": {
            "repository": "henckr/treeML",
            "commit": "71bf218fa3528fd66dd3c6f9eed9a4bf06e58a22",
            "path": "mtpl_data.rds",
            "git_blob_sha1": SOURCE_BLOB,
            "sha256": SOURCE_SHA256,
            "rows": EXPECTED_ROWS,
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "statsmodels": statsmodels.__version__,
            "rdata": getattr(rdata, "__version__", "unknown"),
        },
        "parameterization_guard_max_relative_error": float(max(x["relative_error"] for x in guard)),
        "data": {
            "eligible_positive_claim_rows": int(len(d)),
            "eligible_claim_count": float(d["nclaims"].sum()),
            "average_mean_policy": float(d["average"].mean()),
            "average_mean_claim_weighted": float(np.average(d["average"], weights=d["nclaims"])),
            "average_q99": float(np.quantile(d["average"], .99)),
            "average_q995": float(np.quantile(d["average"], .995)),
            "average_max": float(d["average"].max()),
            "outer_fold_counts": {str(k): int((d["outer_fold"] == k).sum()) for k in range(5)},
        },
        "folds": folds,
        "summary": summary,
        "interpretation_boundary": {
            "no_universal_severity_default": True,
            "no_individual_event_identity": True,
            "no_portfolio_dependence_validation": True,
            "no_capital_validation": True,
            "external_dataset_previously_published": True,
        },
    }
    out = outdir / "bemtpl97-severity-family-transfer-receipt-v0.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    print("SUMMARY", json.dumps({"research_verdict": verdict, "most_consistent_hypothesis": hypothesis, **summary}, sort_keys=True), flush=True)
    print("RECEIPT", out, flush=True)


if __name__ == "__main__":
    main()
