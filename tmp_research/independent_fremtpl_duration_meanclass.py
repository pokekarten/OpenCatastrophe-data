#!/usr/bin/env python3
"""Independent execution of the frozen FFBK freMTPL2 duration mean-class contract.

This is a temporary public-runner research executable. It is deliberately
implemented independently from FFBK PR #1334 and does not authorize a model
promotion. Frozen target/model choices are taken from merged FFBK main prereg.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import urllib.request
from dataclasses import dataclass

import numpy as np
import pandas as pd

FREQ_ID = 41214
FREQ_VERSION = 1
FREQ_MD5 = "f8875568bf0ca622929105197e2db613"
QUESTION_FINGERPRINT = "underwriting/fremtpl2/duration-risk/meanclass/m0-m1-m2-m3a-m3b/v1"
QUESTION_SHA256 = "9fd5d48fef5528d1112401df64e8c74b881a413f0d92ac518d2a14786d312ed8"
OUTER_SEEDS = (2681590927, 4015335633, 287572447)
GLM_ALPHA = 1e-4
DURATION_BANDS = ((0.0,0.25,"(0,.25]"),(0.25,0.5,"(.25,.50]"),(0.5,0.75,"(.50,.75]"),(0.75,1.0,"(.75,1]"))
CAT_COLS = ("VehBrand","VehPower","VehGas","Region","Area")
HGB_CONFIGS = (
    ("H1", {"max_leaf_nodes":15,"min_samples_leaf":100,"max_iter":150,"l2_regularization":1.0}),
    ("H2", {"max_leaf_nodes":31,"min_samples_leaf":100,"max_iter":150,"l2_regularization":1.0}),
    ("H3", {"max_leaf_nodes":31,"min_samples_leaf":50,"max_iter":200,"l2_regularization":1.0}),
    ("H4", {"max_leaf_nodes":63,"min_samples_leaf":100,"max_iter":200,"l2_regularization":1.0}),
)
CONTRASTS = (("M1-M0","M1","M0"),("M2-M1","M2","M1"),("M3a-M0","M3a","M0"),("M3b-M3a","M3b","M3a"),("M3b-M2","M3b","M2"))


def openml_meta():
    with urllib.request.urlopen(f"https://www.openml.org/api/v1/json/data/{FREQ_ID}", timeout=60) as r:
        d = json.loads(r.read().decode())["data_set_description"]
    out = {"data_id":int(d["id"]),"name":d.get("name"),"version":int(d["version"]),"md5_checksum":d.get("md5_checksum"),"status":d.get("status")}
    if (out["data_id"],out["version"],out["md5_checksum"]) != (FREQ_ID,FREQ_VERSION,FREQ_MD5):
        raise RuntimeError(f"OpenML identity mismatch: {out}")
    return out


def load_data():
    from sklearn.datasets import fetch_openml
    meta = openml_meta()
    raw = fetch_openml(data_id=FREQ_ID, as_frame=True).data.copy()
    for c in raw.columns:
        if raw[c].dtype == object or isinstance(raw[c].dtype, pd.CategoricalDtype):
            raw[c] = raw[c].astype(str).str.strip("'")
    raw["IDpol"] = raw["IDpol"].astype("int64")
    if raw["IDpol"].duplicated().any(): raise RuntimeError("duplicate IDpol")
    raw["ClaimNb"] = raw["ClaimNb"].astype(float).clip(upper=4)
    raw["Exposure"] = raw["Exposure"].astype(float).clip(upper=1)
    if not (raw["Exposure"] > 0).all(): raise RuntimeError("nonpositive exposure")
    raw["Frequency"] = raw["ClaimNb"] / raw["Exposure"]
    raw["logExposure"] = np.log(raw["Exposure"])
    raw["logDensity"] = np.log(raw["Density"].astype(float))
    receipt = {"rows":len(raw),"exposure_sum":float(raw.Exposure.sum()),"claim_count":float(raw.ClaimNb.sum()),"idpol_min":int(raw.IDpol.min()),"idpol_max":int(raw.IDpol.max())}
    return raw.reset_index(drop=True), meta, receipt


def glm_pre(extra=()):
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import FunctionTransformer, KBinsDiscretizer, OneHotEncoder, StandardScaler
    tx = [
        ("bin",KBinsDiscretizer(n_bins=10,quantile_method="averaged_inverted_cdf",random_state=0),["VehAge","DrivAge"]),
        ("cat",OneHotEncoder(handle_unknown="ignore"),["VehBrand","VehPower","VehGas","Region","Area"]),
        ("num","passthrough",["BonusMalus"]),
        ("density",make_pipeline(FunctionTransformer(func=np.log),StandardScaler()),["Density"]),
    ]
    if extra: tx.append(("extra",StandardScaler(),list(extra)))
    return ColumnTransformer(tx)

@dataclass
class GLM:
    pre: object
    model: object

def fit_glm(d, extra=()):
    from sklearn.linear_model import PoissonRegressor
    pre = glm_pre(extra); x = pre.fit_transform(d)
    model = PoissonRegressor(alpha=GLM_ALPHA,solver="newton-cholesky").fit(x,d.Frequency,sample_weight=d.Exposure)
    return GLM(pre,model)
def pred_glm(m,d): return np.asarray(m.model.predict(m.pre.transform(d)),float)


def crossfit_m0(train, seed):
    from sklearn.model_selection import KFold
    out=np.empty(len(train)); kf=KFold(5,shuffle=True,random_state=(seed+30000)%(2**32-1))
    for fi,vi in kf.split(train): out[vi]=pred_glm(fit_glm(train.iloc[fi]),train.iloc[vi])
    if np.any(out<=0): raise RuntimeError("bad OOF risk")
    return out


def add_m2(train,test,m0,seed):
    tr=train.copy(); te=test.copy(); oof=crossfit_m0(tr,seed)
    lr=np.log(oof); mean=float(lr.mean()); sd=float(lr.std(ddof=0))
    ztr=(lr-mean)/sd; zte=(np.log(pred_glm(m0,te))-mean)/sd
    tr["durationRiskInteraction"]=tr.logExposure.to_numpy()*ztr
    te["durationRiskInteraction"]=te.logExposure.to_numpy()*zte
    return tr,te,{"oof_sha256":hashlib.sha256(np.asarray(oof,dtype="<f8").tobytes()).hexdigest(),"mean":mean,"sd":sd}


def hgb_frames(train, other, duration):
    nums=["VehAge","DrivAge","BonusMalus","logDensity"] + (["logExposure"] if duration else [])
    tr=pd.DataFrame(index=train.index); ot=pd.DataFrame(index=other.index); unseen={}
    for c in nums: tr[c]=train[c].astype(float); ot[c]=other[c].astype(float)
    for c in CAT_COLS:
        levels=sorted(pd.Series(train[c].astype(str).unique()).tolist())
        seen=set(levels); unseen[c]=int((~other[c].astype(str).isin(seen)).sum())
        tr[c]=pd.Categorical(train[c].astype(str),categories=levels)
        ot[c]=pd.Categorical(other[c].astype(str),categories=levels)
    return tr,ot,unseen

def hgb(cfg):
    from sklearn.ensemble import HistGradientBoostingRegressor
    return HistGradientBoostingRegressor(loss="poisson",learning_rate=.05,early_stopping=False,random_state=0,categorical_features="from_dtype",max_bins=255,**cfg)

def select_hgb(train,seed):
    from sklearn.metrics import mean_poisson_deviance
    from sklearn.model_selection import train_test_split
    fi,vi=train_test_split(np.arange(len(train)),test_size=.2,random_state=(seed+20000)%(2**32-1))
    fit,val=train.iloc[fi],train.iloc[vi]; xf,xv,_=hgb_frames(fit,val,False); scores={}
    for cid,cfg in HGB_CONFIGS:
        m=hgb(cfg).fit(xf,fit.Frequency,sample_weight=fit.Exposure)
        scores[cid]=float(mean_poisson_deviance(val.Frequency,m.predict(xv),sample_weight=val.Exposure))
    cid=min((x for x,_ in HGB_CONFIGS),key=lambda x:(scores[x],x))
    return cid,dict(dict(HGB_CONFIGS)[cid]),scores

def fit_hgb_pair(train,test,sel):
    xa,xta,ua=hgb_frames(train,test,False); xb,xtb,ub=hgb_frames(train,test,True)
    if ua!=ub: raise RuntimeError("unknown-category receipt mismatch")
    a=hgb(sel).fit(xa,train.Frequency,sample_weight=train.Exposure)
    b=hgb(sel).fit(xb,train.Frequency,sample_weight=train.Exposure)
    return np.asarray(a.predict(xta),float),np.asarray(b.predict(xtb),float),ua


def dev_contrib(y,p):
    y=np.asarray(y,float); p=np.asarray(p,float); out=np.empty_like(y); z=y==0
    out[z]=2*p[z]; nz=~z; out[nz]=2*(y[nz]*np.log(y[nz]/p[nz])-(y[nz]-p[nz])); return out
def score(d,p): return float(np.average(dev_contrib(d.Frequency,p),weights=d.Exposure))
def po(d,p,mask=None):
    if mask is None: mask=np.ones(len(d),bool)
    obs=float(d.ClaimNb.to_numpy()[mask].sum()); pred=float((d.Exposure.to_numpy()[mask]*np.asarray(p)[mask]).sum())
    return None if obs==0 else pred/obs

def risk_groups(trainp,testp):
    cuts=np.quantile(trainp,[.25,.5,.75],method="linear");
    if not np.all(np.diff(cuts)>0): raise RuntimeError("duplicate risk cuts")
    return [float(x) for x in cuts],np.searchsorted(cuts,testp,side="right")
def cal(d,p,g):
    ex=d.Exposure.to_numpy(); out={"total":po(d,p),"duration":{},"risk":{},"duration_x_risk":{}}
    dm={}
    for lo,hi,l in DURATION_BANDS:
        m=(ex>lo)&(ex<=hi); dm[l]=m; out["duration"][l]={"rows":int(m.sum()),"claims":float(d.ClaimNb.to_numpy()[m].sum()),"po":po(d,p,m)}
    for q in range(4):
        m=g==q; out["risk"][f"Q{q+1}"]={"rows":int(m.sum()),"claims":float(d.ClaimNb.to_numpy()[m].sum()),"po":po(d,p,m)}
    for l,m0 in dm.items():
        for q in range(4):
            m=m0&(g==q); out["duration_x_risk"][f"{l}|Q{q+1}"]={"rows":int(m.sum()),"claims":float(d.ClaimNb.to_numpy()[m].sum()),"po":po(d,p,m)}
    return out

def bootstrap(d,preds,seed,n=1000):
    w=d.Exposure.to_numpy(float); y=d.Frequency.to_numpy(float); cols=[]; names=[]
    for name,ch,ref in CONTRASTS:
        names.append(name); cols.append(w*(dev_contrib(y,preds[ch])-dev_contrib(y,preds[ref])))
    delta=np.column_stack(cols); rng=np.random.default_rng(seed^0x5A17); prob=np.full(len(d),1/len(d)); vals=np.empty((n,len(names)))
    for i in range(n):
        cnt=rng.multinomial(len(d),prob); vals[i]=(cnt@delta)/(cnt@w)
    return {name:{"mean":float(vals[:,j].mean()),"q025":float(np.quantile(vals[:,j],.025)),"q975":float(np.quantile(vals[:,j],.975))} for j,name in enumerate(names)}


def split_run(d,seed):
    from sklearn.model_selection import train_test_split
    fi,ti=train_test_split(np.arange(len(d)),test_size=.25,random_state=seed); tr=d.iloc[fi].copy(); te=d.iloc[ti].copy()
    m0=fit_glm(tr); p0=pred_glm(m0,te); trp0=pred_glm(m0,tr)
    m1=fit_glm(tr,["logExposure"]); p1=pred_glm(m1,te)
    tr2,te2,nest=add_m2(tr,te,m0,seed); m2=fit_glm(tr2,["logExposure","durationRiskInteraction"]); p2=pred_glm(m2,te2)
    cid,cfg,inner=select_hgb(tr,seed); p3a,p3b,unknown=fit_hgb_pair(tr,te,cfg)
    preds={"M0":p0,"M1":p1,"M2":p2,"M3a":p3a,"M3b":p3b}; scores={k:score(te,v) for k,v in preds.items()}; cuts,g=risk_groups(trp0,p0)
    cals={k:cal(te,v,g) for k,v in preds.items()}; contrasts={}
    for name,ch,ref in CONTRASTS:
        diff=scores[ch]-scores[ref]; contrasts[name]={"diff":diff,"relative_improvement":(scores[ref]-scores[ch])/scores[ref]}
    return {"seed":seed,"train_rows":len(tr),"test_rows":len(te),"test_claims":float(te.ClaimNb.sum()),"risk_cuts":cuts,"selected_hgb":cid,"hgb_inner_scores":inner,"unknown_test_categories":unknown,"m2_nesting":nest,"scores":scores,"contrasts":contrasts,"calibration":cals,"bootstrap":bootstrap(te,preds,seed,1000)}


def max_worsening(ch,ref,view):
    vals=[]
    for k in ref[view]:
        a=ref[view][k]["po"]; b=ch[view][k]["po"]
        if a is not None and b is not None: vals.append(abs(b-1)-abs(a-1))
    return max(vals) if vals else None

def directional_gate(results,contrast,ch,ref):
    rel=[r["contrasts"][contrast]["relative_improvement"] for r in results]; dif=[r["contrasts"][contrast]["diff"] for r in results]
    worsen=[]
    for r in results:
        worsen.append(max(max_worsening(r["calibration"][ch],r["calibration"][ref],"duration"),max_worsening(r["calibration"][ch],r["calibration"][ref],"risk")))
    return {"favourable_all_three":all(x<0 for x in dif),"mean_relative_improvement":float(np.mean(rel)),"max_predeclared_band_worsening":float(max(worsen)),"passes_same_lineage_directional_rule":all(x<0 for x in dif) and np.mean(rel)>=.005 and max(worsen)<=.10}


def main():
    if hashlib.sha256(QUESTION_FINGERPRINT.encode()).hexdigest()!=QUESTION_SHA256: raise RuntimeError("fingerprint")
    if tuple(int.from_bytes(bytes.fromhex(QUESTION_SHA256)[i*4:(i+1)*4],"big") for i in range(3))!=OUTER_SEEDS: raise RuntimeError("seeds")
    d,meta,data=load_data(); results=[]
    for seed in OUTER_SEEDS:
        print(f"RUN_SEED {seed}",flush=True); results.append(split_run(d,seed)); print(f"DONE_SEED {seed}",flush=True)
    gates={
        "M1-M0":directional_gate(results,"M1-M0","M1","M0"),
        "M2-M1":directional_gate(results,"M2-M1","M2","M1"),
        "M3a-M0":directional_gate(results,"M3a-M0","M3a","M0"),
        "M3b-M3a":directional_gate(results,"M3b-M3a","M3b","M3a"),
    }
    out={"classification":"INDEPENDENT_IMPLEMENTATION_REPLICATION_SAME_OPENML_LINEAGE","question_sha256":QUESTION_SHA256,"openml":meta,"data":data,"runtime":{"python":sys.version,"platform":platform.platform(),"numpy":np.__version__,"pandas":pd.__version__},"results":results,"directional_gates":gates,"nextgen_promotion":"NONE"}
    open("independent_fremtpl_duration_result.json","w").write(json.dumps(out,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n")
    summary={"classification":out["classification"],"question_sha256":QUESTION_SHA256,"openml":meta,"data":data,"runtime":out["runtime"],"per_seed":[{"seed":r["seed"],"selected_hgb":r["selected_hgb"],"unknown_test_categories":r["unknown_test_categories"],"scores":r["scores"],"contrasts":r["contrasts"],"bootstrap":r["bootstrap"],"duration_po":{m:r["calibration"][m]["duration"] for m in r["calibration"]}} for r in results],"directional_gates":gates,"result_sha256":hashlib.sha256(open("independent_fremtpl_duration_result.json","rb").read()).hexdigest(),"nextgen_promotion":"NONE"}
    print("INDEPENDENT_RESULT_SUMMARY="+json.dumps(summary,sort_keys=True,separators=(",",":"),allow_nan=False),flush=True)

if __name__=="__main__": main()
