#!/usr/bin/env python3
"""Temporary independent reimplementation of FFBK PR #1319 scientific protocol.

This file lives only on a disposable public execution branch. It is not an
OpenCatastrophe model contribution. Consumer: duration-marginalized policy-row
pure-premium mean on frozen random-policy holdouts. It independently reimplements
rather than imports FFBK PR #1319 code so agreement can count as implementation
replication, not merely rerunning the same Python functions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

SEEDS = (0, 17, 42)
FIT_POWERS = (1.5, 1.9)
EVAL_POWERS = (1.5, 1.7, 1.8, 1.9)
FREQ_ALPHAS = (1e-4, 1e-3)
SEV_ALPHAS = (1.0, 10.0)
TW_ALPHAS = (0.05, 0.1, 0.5)
BANDS = ((0,.25,"(0,0.25]"),(.25,.5,"(0.25,0.50]"),(.5,.75,"(0.50,0.75]"),(.75,1,"(0.75,1.00]"))


def meta(data_id: int) -> dict:
    with urllib.request.urlopen(f"https://www.openml.org/api/v1/json/data/{data_id}", timeout=60) as r:
        d = json.load(r)["data_set_description"]
    return {k: d.get(k) for k in ("id","name","version","file_id","md5_checksum","status","url","parquet_url")}


def load() -> tuple[pd.DataFrame,pd.DataFrame,dict]:
    from sklearn.datasets import fetch_openml
    f = fetch_openml(data_id=41214, as_frame=True).data.copy()
    s = fetch_openml(data_id=41215, as_frame=True).data.copy()
    f["IDpol"] = f["IDpol"].astype("int64")
    s["IDpol"] = s["IDpol"].astype("int64")
    s["ClaimAmount"] = s["ClaimAmount"].astype(float)
    return f, s, {"frequency":meta(41214),"severity":meta(41215)}


def prepare(f: pd.DataFrame, s: pd.DataFrame, capped: bool) -> tuple[pd.DataFrame,dict]:
    x=f.copy()
    for c in x.columns:
        if x[c].dtype == object or isinstance(x[c].dtype,pd.CategoricalDtype):
            x[c]=x[c].astype(str).str.strip("'")
    amounts=s.groupby("IDpol",sort=False)["ClaimAmount"].sum()
    d=x.set_index("IDpol")
    raw_nb=d["ClaimNb"].astype(float)
    raw_exp=d["Exposure"].astype(float)
    d["ClaimAmount"]=d.index.to_series().map(amounts).fillna(0.0).astype(float)
    raw_amt=d["ClaimAmount"].copy()
    d["ClaimNb"]=raw_nb.clip(upper=4)
    d["Exposure"]=raw_exp.clip(upper=1)
    if capped:
        d["ClaimAmount"]=d["ClaimAmount"].clip(upper=200000.0)
    reset=(d["ClaimAmount"]==0)&(d["ClaimNb"]>=1)
    d.loc[reset,"ClaimNb"]=0
    if not (d["Exposure"]>0).all(): raise ValueError("non-positive exposure")
    d["PurePremium"]=d["ClaimAmount"]/d["Exposure"]
    d["Frequency"]=d["ClaimNb"]/d["Exposure"]
    d["AvgClaimAmount"]=d["ClaimAmount"]/np.fmax(d["ClaimNb"],1)
    receipt={
      "rows":len(d),"idpol_unique":bool(d.index.is_unique),
      "severity_rows":len(s),"severity_orphans":int((~s.IDpol.isin(f.IDpol)).sum()),
      "claimnb_cap_rows":int((raw_nb>4).sum()),"exposure_cap_rows":int((raw_exp>1).sum()),
      "amount_gt_200k_rows":int((raw_amt>200000).sum()),"zero_amount_reset_rows":int(reset.sum()),
      "prepared_total_exposure":float(d.Exposure.sum()),"prepared_total_claim_amount":float(d.ClaimAmount.sum()),
      "positive_claim_rows":int((d.ClaimAmount>0).sum()),
    }
    return d,receipt


def preprocessor():
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import FunctionTransformer,KBinsDiscretizer,OneHotEncoder,StandardScaler
    return ColumnTransformer([
      ("bin",KBinsDiscretizer(n_bins=10,quantile_method="averaged_inverted_cdf",random_state=0),["VehAge","DrivAge"]),
      ("cat",OneHotEncoder(handle_unknown="ignore"),["VehBrand","VehPower","VehGas","Region","Area"]),
      ("num","passthrough",["BonusMalus"]),
      ("density",make_pipeline(FunctionTransformer(func=np.log),StandardScaler()),["Density"]),
    ])


def gini(y,p,w):
    y,p,w=map(lambda z:np.asarray(z,float),(y,p,w)); o=np.argsort(p,kind="stable")
    sp,sw,sl=p[o],w[o],(w*y)[o]; starts=np.r_[0,1+np.flatnonzero(sp[1:]!=sp[:-1])]
    gw=np.add.reduceat(sw,starts); gl=np.add.reduceat(sl,starts)
    cw=np.r_[0.,np.cumsum(gw)/w.sum()]; cl=np.r_[0.,np.cumsum(gl)/np.sum(w*y)]
    return float(1-2*np.trapezoid(cl,cw))


def metric(te,pred):
    from sklearn.metrics import mean_tweedie_deviance
    y=te.PurePremium.to_numpy(float); w=te.Exposure.to_numpy(float); p=np.asarray(pred,float)
    obs=float(np.sum(w*y)); fit=float(np.sum(w*p)); ratio=fit/obs
    bands={}
    for lo,hi,label in BANDS:
        m=(w>lo)&(w<=hi); bo=float(np.sum(w[m]*y[m])); bf=float(np.sum(w[m]*p[m]))
        bands[label]={"rows":int(m.sum()),"positive":int((te.loc[m,"ClaimAmount"]>0).sum()),"ratio":None if bo<=0 else bf/bo}
    return {"ratio":ratio,"abs_cal":abs(ratio-1),"gini":gini(y,p,w),"bands":bands,
      "deviance":{str(q):float(mean_tweedie_deviance(y,p,sample_weight=w,power=q)) for q in EVAL_POWERS}}


def one_split(d,seed):
    from sklearn.linear_model import PoissonRegressor,GammaRegressor,TweedieRegressor
    from sklearn.metrics import mean_poisson_deviance,mean_gamma_deviance,mean_tweedie_deviance
    from sklearn.model_selection import train_test_split
    oi,oj=train_test_split(np.arange(len(d)),test_size=.25,random_state=seed)
    tr,te=d.iloc[oi],d.iloc[oj]
    ii,iv=train_test_split(np.arange(len(tr)),test_size=.2,random_state=seed+10000)
    a,b=tr.iloc[ii],tr.iloc[iv]
    ip=preprocessor(); xa=ip.fit_transform(a); xb=ip.transform(b)
    fp={}; fscore={}
    for alpha in FREQ_ALPHAS:
        m=PoissonRegressor(alpha=alpha,solver="newton-cholesky").fit(xa,a.Frequency,sample_weight=a.Exposure)
        fp[alpha]=m.predict(xb); fscore[alpha]=float(mean_poisson_deviance(b.Frequency,fp[alpha],sample_weight=b.Exposure))
    pos=a.ClaimAmount.to_numpy()>0; vpos=b.ClaimAmount.to_numpy()>0; sp={}; sscore={}
    for alpha in SEV_ALPHAS:
        m=GammaRegressor(alpha=alpha,solver="newton-cholesky").fit(xa[pos],a.loc[pos,"AvgClaimAmount"],sample_weight=a.loc[pos,"ClaimNb"])
        sp[alpha]=m.predict(xb); sscore[alpha]=float(mean_gamma_deviance(b.loc[vpos,"AvgClaimAmount"],sp[alpha][vpos],sample_weight=b.loc[vpos,"ClaimNb"]))
    yb=b.PurePremium.to_numpy(float); wb=b.Exposure.to_numpy(float)
    joint={}
    for q in FIT_POWERS:
        scores={(fa,sa):float(mean_tweedie_deviance(yb,fp[fa]*sp[sa],sample_weight=wb,power=q)) for fa in FREQ_ALPHAS for sa in SEV_ALPHAS}
        joint[q]=min(scores,key=lambda z:(scores[z],z[0],z[1]))
    twsel={}
    for q in FIT_POWERS:
        scores={}
        for alpha in TW_ALPHAS:
            m=TweedieRegressor(power=q,alpha=alpha,solver="newton-cholesky").fit(xa,a.PurePremium,sample_weight=a.Exposure)
            scores[alpha]=float(mean_tweedie_deviance(yb,m.predict(xb),sample_weight=wb,power=q))
        twsel[q]=min(scores,key=lambda z:(scores[z],z))
    op=preprocessor(); xt=op.fit_transform(tr); xe=op.transform(te)
    # Cache all two-by-two outer component models so componentwise and joint candidates share exact fitted pieces.
    fmods={alpha:PoissonRegressor(alpha=alpha,solver="newton-cholesky").fit(xt,tr.Frequency,sample_weight=tr.Exposure).predict(xe) for alpha in FREQ_ALPHAS}
    tpos=tr.ClaimAmount.to_numpy()>0
    smods={alpha:GammaRegressor(alpha=alpha,solver="newton-cholesky").fit(xt[tpos],tr.loc[tpos,"AvgClaimAmount"],sample_weight=tr.loc[tpos,"ClaimNb"]).predict(xe) for alpha in SEV_ALPHAS}
    cf=min(FREQ_ALPHAS,key=lambda z:(fscore[z],z)); cs=min(SEV_ALPHAS,key=lambda z:(sscore[z],z))
    preds={"product_componentwise":fmods[cf]*smods[cs]}
    for q in FIT_POWERS:
        fa,sa=joint[q]; preds[f"product_joint_p{q}"]=fmods[fa]*smods[sa]
        tm=TweedieRegressor(power=q,alpha=twsel[q],solver="newton-cholesky").fit(xt,tr.PurePremium,sample_weight=tr.Exposure)
        preds[f"direct_tweedie_p{q}"]=tm.predict(xe)
    ids=np.sort(d.index.to_numpy(np.int64)[oj])
    return {"seed":seed,"train_rows":len(tr),"test_rows":len(te),"test_id_sha256":hashlib.sha256(ids.tobytes()).hexdigest(),
      "selected":{"componentwise":[cf,cs],"joint":{str(k):list(v) for k,v in joint.items()},"direct_alpha":{str(k):v for k,v in twsel.items()}},
      "metrics":{n:metric(te,p) for n,p in preds.items()}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--variant",choices=("capped","uncapped"),required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    f,s,m=load(); d,receipt=prepare(f,s,a.variant=="capped")
    splits=[one_split(d,k) for k in SEEDS]
    out={"schema":1,"protocol_source":"independent reimplementation of FFBK PR #1319 head ed56efe52b336c805165d935db37a86e6c9787a2","variant":a.variant,"openml":m,"data_receipt":receipt,"seeds":list(SEEDS),"splits":splits}
    out["canonical_sha256"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"variant":a.variant,"receipt":out["canonical_sha256"],"rows":len(d)},sort_keys=True))

if __name__=="__main__": main()
