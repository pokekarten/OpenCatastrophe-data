#!/usr/bin/env python3
"""Exact-source CLRD2025 Commercial Auto / Private Passenger Auto dependence probe.

This probe is research-only. It fails closed unless the input bytes have the
pre-registered Git blob identity before parsing or computing any statistic.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

EXPECTED_GIT_BLOB = "8d0400f1ace87c3e1e1202d359ef3bb6111b3dd0"
EXPECTED_SOURCE_COMMIT = "e07c09e506d27a522e5e678e532fd4352a82ac17"
LOBS = ("comauto", "ppauto")


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def verify_source(path: Path, expected_blob: str = EXPECTED_GIT_BLOB) -> Dict[str, object]:
    data = path.read_bytes()
    blob = git_blob_sha1(data)
    if blob != expected_blob:
        raise ValueError(f"source Git blob mismatch: expected {expected_blob}, got {blob}")
    return {
        "git_blob": blob,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires data")
    return sum(values) / len(values)


def sample_sd(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise ValueError("sample SD requires at least two values")
    mu = mean(values)
    return math.sqrt(sum((x - mu) ** 2 for x in values) / (len(values) - 1))


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mx, my = mean(xs), mean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    sx = math.sqrt(sum(x * x for x in dx))
    sy = math.sqrt(sum(y * y for y in dy))
    if sx == 0.0 or sy == 0.0:
        return None
    return sum(x * y for x, y in zip(dx, dy)) / (sx * sy)


def average_ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        rank = (i + 1 + j) / 2.0
        for idx in order[i:j]:
            out[idx] = rank
        i = j
    return out


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    return pearson(average_ranks(xs), average_ranks(ys))


def association(pairs: Sequence[Tuple[float, float, str]]) -> Dict[str, object]:
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    return {
        "n_records": len(pairs),
        "n_companies": len({p[2] for p in pairs}),
        "pearson": pearson(xs, ys),
        "spearman": spearman(xs, ys),
    }


def load_paid(path: Path) -> Tuple[Dict[Tuple[str, str, int, int], float], Dict[str, str]]:
    paid: Dict[Tuple[str, str, int, int], float] = {}
    names: Dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"GRCODE", "GRNAME", "AccidentYear", "DevelopmentLag", "CumPaidLoss", "LOB"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"missing required columns: {sorted(missing)}")
        for row in reader:
            lob = row["LOB"].strip().lower()
            if lob not in LOBS:
                continue
            grcode = row["GRCODE"].strip()
            names[grcode] = row["GRNAME"].strip()
            ay = int(row["AccidentYear"])
            lag = int(row["DevelopmentLag"])
            value = float(row["CumPaidLoss"])
            key = (grcode, lob, ay, lag)
            if key in paid:
                raise ValueError(f"duplicate source cell: {key}")
            paid[key] = value
    return paid, names


def build_links(
    paid: Mapping[Tuple[str, str, int, int], float]
) -> Dict[Tuple[str, str, int], Dict[int, float]]:
    cells: Dict[Tuple[str, str, int], Dict[int, float]] = defaultdict(dict)
    for (grcode, lob, ay, lag), value in paid.items():
        cells[(grcode, lob, ay)][lag] = value

    links: Dict[Tuple[str, str, int], Dict[int, float]] = defaultdict(dict)
    for (grcode, lob, ay), by_lag in cells.items():
        max_lag = max(by_lag, default=0)
        for lag in range(1, max_lag):
            v0 = by_lag.get(lag)
            v1 = by_lag.get(lag + 1)
            if v0 is None or v1 is None or v0 <= 0.0 or v1 <= 0.0:
                continue
            links[(grcode, lob, lag)][ay] = math.log(v1 / v0)
    return links


def block_transforms(
    links: Mapping[Tuple[str, str, int], Mapping[int, float]]
) -> Tuple[
    Dict[Tuple[str, str, int], Dict[int, float]],
    Dict[Tuple[str, str, int], Dict[int, float]],
]:
    centered: Dict[Tuple[str, str, int], Dict[int, float]] = {}
    normalized: Dict[Tuple[str, str, int], Dict[int, float]] = {}
    for key, by_ay in links.items():
        vals = list(by_ay.values())
        if not vals:
            continue
        mu = mean(vals)
        centered[key] = {ay: value - mu for ay, value in by_ay.items()}
        if len(vals) < 2:
            continue
        sd = sample_sd(vals)
        if sd == 0.0:
            continue
        normalized[key] = {ay: (value - mu) / sd for ay, value in by_ay.items()}
    return centered, normalized


RELATIONS = {
    "same_step": lambda lag: (("comauto", lag), ("ppauto", lag)),
    "ca_to_pa_next": lambda lag: (("comauto", lag), ("ppauto", lag + 1)),
    "pa_to_ca_next": lambda lag: (("ppauto", lag), ("comauto", lag + 1)),
}


def max_link(links: Mapping[Tuple[str, str, int], Mapping[int, float]]) -> int:
    return max((k[2] for k in links), default=0)


def paired_records(
    transformed: Mapping[Tuple[str, str, int], Mapping[int, float]],
    relation: str,
    lag: int,
) -> List[Tuple[float, float, str]]:
    (x_lob, x_lag), (y_lob, y_lag) = RELATIONS[relation](lag)
    companies = sorted({key[0] for key in transformed})
    out: List[Tuple[float, float, str]] = []
    for grcode in companies:
        xs = transformed.get((grcode, x_lob, x_lag), {})
        ys = transformed.get((grcode, y_lob, y_lag), {})
        for ay in sorted(set(xs).intersection(ys)):
            out.append((xs[ay], ys[ay], grcode))
    return out


def pool_relation(
    transformed: Mapping[Tuple[str, str, int], Mapping[int, float]],
    relation: str,
    lag_values: Iterable[int],
) -> List[Tuple[float, float, str]]:
    out: List[Tuple[float, float, str]] = []
    for lag in lag_values:
        out.extend(paired_records(transformed, relation, lag))
    return out


def company_mean_association(pairs: Sequence[Tuple[float, float, str]]) -> Dict[str, object]:
    by_company: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for x, y, company in pairs:
        by_company[company].append((x, y))
    company_pairs = [
        (mean([p[0] for p in vals]), mean([p[1] for p in vals]), company)
        for company, vals in sorted(by_company.items())
        if vals
    ]
    result = association(company_pairs)
    result["company_means"] = len(company_pairs)
    return result


def jackknife_companies(pairs: Sequence[Tuple[float, float, str]]) -> Dict[str, object]:
    companies = sorted({p[2] for p in pairs})
    estimates: List[Tuple[str, float]] = []
    for omitted in companies:
        kept = [p for p in pairs if p[2] != omitted]
        value = association(kept)["pearson"]
        if value is not None:
            estimates.append((omitted, float(value)))
    if not estimates:
        return {"n": 0, "min": None, "max": None, "median": None, "sign_counts": {}}
    vals = [v for _, v in estimates]
    min_item = min(estimates, key=lambda item: item[1])
    max_item = max(estimates, key=lambda item: item[1])
    signs = {
        "negative": sum(v < 0 for v in vals),
        "zero": sum(v == 0 for v in vals),
        "positive": sum(v > 0 for v in vals),
    }
    return {
        "n": len(estimates),
        "min": min_item[1],
        "min_omitted": min_item[0],
        "max": max_item[1],
        "max_omitted": max_item[0],
        "median": statistics.median(vals),
        "sign_counts": signs,
    }


def analyze(path: Path, expected_blob: str = EXPECTED_GIT_BLOB) -> Dict[str, object]:
    source = verify_source(path, expected_blob)
    paid, names = load_paid(path)
    raw_links = build_links(paid)
    centered_links, normalized_links = block_transforms(raw_links)
    max_lag = max_link(raw_links)

    result: Dict[str, object] = {
        "source": {
            **source,
            "source_commit": EXPECTED_SOURCE_COMMIT,
            "path": "chainladder/utils/data/clrd2025.csv",
        },
        "scope": {
            "lobs": list(LOBS),
            "max_adjacent_link_start": max_lag,
            "companies_in_source_two_lobs": len(
                set(k[0] for k in raw_links if k[1] == "comauto").intersection(
                    k[0] for k in raw_links if k[1] == "ppauto"
                )
            ),
        },
        "pair_specific": {},
        "pooled": {},
    }

    for relation in RELATIONS:
        last = max_lag if relation == "same_step" else max(0, max_lag - 1)
        lags = list(range(1, last + 1))
        result["pair_specific"][relation] = {}
        for lag in lags:
            result["pair_specific"][relation][str(lag)] = {
                "raw": association(paired_records(raw_links, relation, lag)),
                "centered": association(paired_records(centered_links, relation, lag)),
                "normalized": association(paired_records(normalized_links, relation, lag)),
            }

        raw_pairs = pool_relation(raw_links, relation, lags)
        centered_pairs = pool_relation(centered_links, relation, lags)
        normalized_pairs = pool_relation(normalized_links, relation, lags)
        result["pooled"][relation] = {
            "raw": association(raw_pairs),
            "centered": association(centered_pairs),
            "normalized": association(normalized_pairs),
            "company_mean_raw": company_mean_association(raw_pairs),
            "leave_one_company_centered": jackknife_companies(centered_pairs),
            "leave_one_company_normalized": jackknife_companies(normalized_pairs),
        }

    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--expected-blob",
        default=EXPECTED_GIT_BLOB,
        help="Git blob SHA-1 gate; override only for deterministic test fixtures.",
    )
    args = parser.parse_args()
    result = analyze(args.csv, args.expected_blob)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
