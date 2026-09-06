#!/usr/bin/env python3
"""DIAGNOSTIC ONLY: characterize norauto Expo values after preregistered fail-closed stop.

This script must not fit, score, compare or promote any model. It exists only to
characterize the source-semantics blocker revealed by FFBK PR #1415 run 1.
"""
from __future__ import annotations
import hashlib, json, urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
import pyreadr

SOURCE_COMMIT = "ef06f44b8669908925b5a590c8a2313723cf504c"
SOURCE_URL = f"https://raw.githubusercontent.com/dutangc/CASdatasets/{SOURCE_COMMIT}/data/norauto.rda"

out = Path("norauto_exposure_diagnostic_artifact")
out.mkdir(exist_ok=True)
path = out / "norauto.rda"
with urllib.request.urlopen(SOURCE_URL, timeout=60) as r:
    raw = r.read()
path.write_bytes(raw)
objects = pyreadr.read_r(str(path))
if len(objects) != 1:
    raise RuntimeError(f"expected one R object, got {list(objects)}")
name, df = next(iter(objects.items()))
expo = pd.to_numeric(df["Expo"], errors="raise").to_numpy(float)
claims = pd.to_numeric(df["NbClaim"], errors="raise").to_numpy(float)
amount = pd.to_numeric(df["ClaimAmount"], errors="raise").to_numpy(float)
if not np.all(np.isfinite(expo)):
    raise RuntimeError("non-finite Expo")
mask = expo > 1.0
q = np.quantile(expo, [0, .25, .5, .75, .9, .95, .99, .995, .999, 1])
values, counts = np.unique(expo[mask], return_counts=True)
order = np.argsort(values)[::-1]
receipt = {
  "status": "DIAGNOSTIC_ONLY_NO_MODEL_SCORES",
  "source": {"repository":"dutangc/CASdatasets","path":"data/norauto.rda","commit":SOURCE_COMMIT,
             "downloaded_byte_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"r_object":str(name)},
  "rows": int(len(df)),
  "schema": list(df.columns),
  "expo": {
    "min": float(expo.min()), "max": float(expo.max()), "mean": float(expo.mean()),
    "sum": float(expo.sum()),
    "quantiles": {str(k):float(v) for k,v in zip([0,.25,.5,.75,.9,.95,.99,.995,.999,1],q)},
    "rows_gt_1": int(mask.sum()), "share_rows_gt_1": float(mask.mean()),
    "exposure_sum_gt_1": float(expo[mask].sum()),
    "share_exposure_gt_1": float(expo[mask].sum()/expo.sum()),
    "distinct_values_gt_1": int(len(values)),
    "largest_distinct_values_gt_1": [{"value":float(values[i]),"rows":int(counts[i])} for i in order[:20]],
  },
  "claims": {
    "total": float(claims.sum()),
    "positive_policies": int((claims>0).sum()),
    "total_on_expo_gt_1": float(claims[mask].sum()),
    "positive_policies_on_expo_gt_1": int((claims[mask]>0).sum()),
    "max_claim_count": float(claims.max()),
    "claim_amount_sum_on_expo_gt_1": float(amount[mask].sum()),
  },
  "authority_boundary": "Post-failure data-semantics diagnostic only. No filtering/capping rule, model score, causal interpretation, or NextGen promotion is authorized."
}
(out/"diagnostic.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
