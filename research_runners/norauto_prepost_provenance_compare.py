#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""PROVENANCE ONLY: compare norauto.rda immediately before/after CASdatasets 8205811c.

This diagnostic answers one bounded source-history question about the public CASdatasets lineage:
did the 2017 commit labelled ``rescale data file 11`` change the materialized
``norauto`` table, and specifically its ``Expo`` values?

It must not fit, score, repair, rescale, filter, or promote any insurance model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import urllib.request

import numpy as np
import pandas as pd
import pyreadr

REPOSITORY = "dutangc/CASdatasets"
PATH = "pkg/data/norauto.rda"
PRE_COMMIT = "cbd599f50028d3bf0a7504ab3963542e1a709eb5"
POST_COMMIT = "8205811c107b450229fd91925f3cbf326f45d54d"
EXPECTED_PRE_BLOB = "c9901042ec187cdae00fae3d88b65f1c9177fc2a"
EXPECTED_POST_BLOB = "5e3a047ebf8f2834b021af7a68b2855ce2ebdbd7"

OUT = Path("norauto_prepost_provenance_artifact")
OUT.mkdir(exist_ok=True)


def git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def download(
    commit: str, expected_blob: str, name: str, scratch: Path
) -> tuple[bytes, Path]:
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}/{PATH}"
    with urllib.request.urlopen(url, timeout=120) as response:
        raw = response.read()
    observed_blob = git_blob_sha1(raw)
    if observed_blob != expected_blob:
        raise RuntimeError(
            f"{name} blob mismatch: expected {expected_blob}, observed {observed_blob}"
        )
    path = scratch / f"{name}.rda"
    path.write_bytes(raw)
    return raw, path


def read_single(path: Path) -> tuple[str, pd.DataFrame]:
    objects = pyreadr.read_r(str(path))
    if len(objects) != 1:
        raise RuntimeError(
            f"expected exactly one R object in {path}, got {list(objects)}"
        )
    name, df = next(iter(objects.items()))
    if not isinstance(df, pd.DataFrame):
        raise RuntimeError(f"expected data.frame, got {type(df)!r}")
    return str(name), df


def equal_mask(a: pd.Series, b: pd.Series) -> np.ndarray:
    if len(a) != len(b):
        raise RuntimeError("row count mismatch prevents rowwise comparison")
    both_na = a.isna().to_numpy() & b.isna().to_numpy()
    try:
        eq = a.eq(b).fillna(False).to_numpy(dtype=bool)
    except Exception:
        eq = (
            a.astype("string").fillna("<NA>")
            == b.astype("string").fillna("<NA>")
        ).to_numpy(dtype=bool)
    return eq | both_na


def numeric_profile(a: pd.Series, b: pd.Series, changed: np.ndarray) -> dict:
    aa = pd.to_numeric(a, errors="coerce").to_numpy(dtype=float)
    bb = pd.to_numeric(b, errors="coerce").to_numpy(dtype=float)
    finite = np.isfinite(aa) & np.isfinite(bb)
    changed_finite = changed & finite
    profile: dict[str, object] = {
        "finite_pairs": int(finite.sum()),
        "changed_finite_pairs": int(changed_finite.sum()),
    }
    if changed_finite.any():
        delta = bb[changed_finite] - aa[changed_finite]
        profile.update(
            {
                "min_delta_post_minus_pre": float(delta.min()),
                "max_delta_post_minus_pre": float(delta.max()),
                "mean_delta_post_minus_pre": float(delta.mean()),
            }
        )
        ratio_mask = changed_finite & (aa != 0)
        if ratio_mask.any():
            ratios = bb[ratio_mask] / aa[ratio_mask]
            finite_ratios = ratios[np.isfinite(ratios)]
            if finite_ratios.size:
                rounded = np.round(finite_ratios, 12)
                unique, counts = np.unique(rounded, return_counts=True)
                order = np.argsort(counts)[::-1]
                profile["ratio_post_over_pre"] = {
                    "min": float(finite_ratios.min()),
                    "max": float(finite_ratios.max()),
                    "median": float(np.median(finite_ratios)),
                    "top_rounded_ratios": [
                        {"ratio": float(unique[i]), "rows": int(counts[i])}
                        for i in order[:10]
                    ],
                }
    return profile


with tempfile.TemporaryDirectory(prefix="norauto-prepost-") as tmp:
    scratch = Path(tmp)
    pre_raw, pre_path = download(PRE_COMMIT, EXPECTED_PRE_BLOB, "pre", scratch)
    post_raw, post_path = download(POST_COMMIT, EXPECTED_POST_BLOB, "post", scratch)
    pre_name, pre = read_single(pre_path)
    post_name, post = read_single(post_path)

same_shape = pre.shape == post.shape
same_columns = list(pre.columns) == list(post.columns)
if not same_shape or not same_columns:
    # Preserve the structural result, but fail before pretending rowwise comparability.
    structural = {
        "status": "STRUCTURAL_CHANGE_ROW_ALIGNMENT_NOT_ASSUMED",
        "pre_shape": list(pre.shape),
        "post_shape": list(post.shape),
        "pre_columns": list(pre.columns),
        "post_columns": list(post.columns),
        "external_bytes_persisted": False,
    }
    (OUT / "result.json").write_text(
        json.dumps(structural, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(structural, indent=2, sort_keys=True))
    raise SystemExit(0)

columns: dict[str, object] = {}
changed_column_names: list[str] = []
for col in pre.columns:
    equal = equal_mask(pre[col], post[col])
    changed = ~equal
    changed_rows = int(changed.sum())
    item: dict[str, object] = {
        "pre_dtype": str(pre[col].dtype),
        "post_dtype": str(post[col].dtype),
        "changed_rows": changed_rows,
        "share_changed_rows": float(changed.mean()),
        "exact_rowwise_equal": changed_rows == 0,
    }
    if changed_rows:
        changed_column_names.append(str(col))
        # Add numeric diagnostics only when both columns can be materially parsed as numbers.
        pre_num = pd.to_numeric(pre[col], errors="coerce")
        post_num = pd.to_numeric(post[col], errors="coerce")
        numeric_fraction = float((pre_num.notna() & post_num.notna()).mean())
        if numeric_fraction > 0.99:
            item["numeric_change_profile"] = numeric_profile(
                pre[col], post[col], changed
            )
        examples = []
        for idx in np.flatnonzero(changed)[:10]:
            av = pre[col].iloc[int(idx)]
            bv = post[col].iloc[int(idx)]
            examples.append(
                {
                    "row_position_0based": int(idx),
                    "pre": None if pd.isna(av) else str(av),
                    "post": None if pd.isna(bv) else str(bv),
                }
            )
        item["first_changed_examples"] = examples
    columns[str(col)] = item

expo = {}
if "Expo" in pre.columns:
    pre_expo = pd.to_numeric(pre["Expo"], errors="raise").to_numpy(dtype=float)
    post_expo = pd.to_numeric(post["Expo"], errors="raise").to_numpy(dtype=float)
    expo_changed = ~(
        np.isclose(pre_expo, post_expo, rtol=0.0, atol=0.0)
        | (np.isnan(pre_expo) & np.isnan(post_expo))
    )
    expo = {
        "changed_rows_exact": int(expo_changed.sum()),
        "pre_min": float(np.nanmin(pre_expo)),
        "pre_max": float(np.nanmax(pre_expo)),
        "post_min": float(np.nanmin(post_expo)),
        "post_max": float(np.nanmax(post_expo)),
        "pre_rows_gt_1": int(np.sum(pre_expo > 1.0)),
        "post_rows_gt_1": int(np.sum(post_expo > 1.0)),
        "pre_sum": float(np.nansum(pre_expo)),
        "post_sum": float(np.nansum(post_expo)),
    }

all_cells_equal = len(changed_column_names) == 0
non_expo_changed = [c for c in changed_column_names if c != "Expo"]
if all_cells_equal:
    conclusion = "MATERIALIZED_TABLE_IDENTICAL_PRE_POST"
elif changed_column_names == ["Expo"]:
    conclusion = "EXPO_ONLY_CHANGED_PRE_POST"
else:
    conclusion = "MULTIPLE_COLUMNS_CHANGED_PRE_POST"

receipt = {
    "status": "PROVENANCE_DIAGNOSTIC_ONLY_NO_MODEL_SCORES",
    "question": (
        "Did CASdatasets commit 8205811c ('rescale data file 11') alter norauto "
        "materialized data, especially Expo?"
    ),
    "source": {
        "repository": REPOSITORY,
        "path": PATH,
        "pre_commit": PRE_COMMIT,
        "post_commit": POST_COMMIT,
        "pre_expected_git_blob_sha1": EXPECTED_PRE_BLOB,
        "post_expected_git_blob_sha1": EXPECTED_POST_BLOB,
        "pre_downloaded_git_blob_sha1": git_blob_sha1(pre_raw),
        "post_downloaded_git_blob_sha1": git_blob_sha1(post_raw),
        "pre_downloaded_sha256": hashlib.sha256(pre_raw).hexdigest(),
        "post_downloaded_sha256": hashlib.sha256(post_raw).hexdigest(),
        "pre_bytes": len(pre_raw),
        "post_bytes": len(post_raw),
        "pre_r_object": pre_name,
        "post_r_object": post_name,
        "external_bytes_persisted": False,
    },
    "shape": {"rows": int(len(pre)), "columns": int(len(pre.columns))},
    "same_column_order": True,
    "changed_columns": changed_column_names,
    "non_expo_changed_columns": non_expo_changed,
    "all_materialized_cells_equal": all_cells_equal,
    "expo": expo,
    "columns": columns,
    "conclusion": conclusion,
    "authority_boundary": (
        "This result characterizes exact pre/post source objects only. It does not "
        "authorize reverse-rescaling, row filtering, duration-model fitting, model "
        "promotion, or a causal interpretation of Expo."
    ),
}

(OUT / "result.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
summary = [
    f"conclusion={conclusion}",
    f"shape={pre.shape}",
    f"changed_columns={changed_column_names}",
    f"expo_changed_rows={expo.get('changed_rows_exact', 'NA')}",
    f"pre_expo_max={expo.get('pre_max', 'NA')}",
    f"post_expo_max={expo.get('post_max', 'NA')}",
]
(OUT / "summary.txt").write_text("\n".join(summary) + "\n")
print(json.dumps(receipt, indent=2, sort_keys=True))
