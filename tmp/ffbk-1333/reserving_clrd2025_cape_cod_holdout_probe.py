#!/usr/bin/env python3
"""Preregistered CLRD2025 Cape Cod / Chain Ladder / external-BF next-diagonal probe.

Research only. The probe fails closed unless the source has the pinned Git-blob
identity and computes only leakage-safe next-calendar-diagonal paid increments.
No third-party packages are required.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from collections import defaultdict
from pathlib import Path

EXPECTED_GIT_BLOB = "8d0400f1ace87c3e1e1202d359ef3bb6111b3dd0"
EXPECTED_SHA256 = "045f10559ec9ed2bb0b4e5f74f9d611e20723ce51c7192a30b0dabcb75111456"
EXPECTED_BYTES = 5868245
SOURCE_COMMIT = "e07c09e506d27a522e5e678e532fd4352a82ac17"
SOURCE_PATH = "chainladder/utils/data/clrd2025.csv"

def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def verify_source(path: Path) -> dict:
    data = path.read_bytes()
    got = {"bytes": len(data), "git_blob": git_blob_sha1(data),
           "sha256": hashlib.sha256(data).hexdigest()}
    exp = {"bytes": EXPECTED_BYTES, "git_blob": EXPECTED_GIT_BLOB, "sha256": EXPECTED_SHA256}
    if got != exp:
        raise ValueError(f"source identity mismatch: expected={exp}, got={got}")
    return {**got, "source_commit": SOURCE_COMMIT, "path": SOURCE_PATH}

def load(path: Path):
    triangles = defaultdict(lambda: defaultdict(dict))
    premium, names = {}, {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        req = {"GRCODE","GRNAME","AccidentYear","DevelopmentLag","DevelopmentYear",
               "CumPaidLoss","EarnedPremNet","LOB"}
        miss = req - set(r.fieldnames or ())
        if miss:
            raise ValueError(f"missing columns: {sorted(miss)}")
        for row in r:
            g, lob = row["GRCODE"].strip(), row["LOB"].strip().lower()
            ay, lag = int(row["AccidentYear"]), int(row["DevelopmentLag"])
            cy = int(row["DevelopmentYear"])
            if cy != ay + lag - 1:
                raise ValueError(f"calendar identity mismatch {(g,lob,ay,lag,cy)}")
            group = (g,lob)
            if lag in triangles[group][ay]:
                raise ValueError(f"duplicate cell {(g,lob,ay,lag)}")
            triangles[group][ay][lag] = float(row["CumPaidLoss"])
            pkey, p = (g,lob,ay), float(row["EarnedPremNet"])
            if pkey in premium and premium[pkey] != p:
                raise ValueError(f"premium drift within origin {pkey}")
            premium[pkey] = p
            names[g] = row["GRNAME"].strip()
    return {k:dict(v) for k,v in triangles.items()}, premium, names

def factors(triangle, cutoff):
    num, den = defaultdict(float), defaultdict(float)
    for ay, by_lag in triangle.items():
        for lag, c0 in by_lag.items():
            c1 = by_lag.get(lag+1)
            if c1 is None or ay+lag > cutoff:
                continue
            den[lag] += c0
            num[lag] += c1
    return {lag:num[lag]/den[lag] for lag in num if den[lag] > 0 and num[lag] >= 0}

def pct_reported(fs, max_lag):
    out = {max_lag: 1.0}
    prod, complete = 1.0, True
    for lag in range(max_lag-1, 0, -1):
        factor = fs.get(lag)
        if factor is None or factor <= 0 or not complete:
            complete = False
            out[lag] = None
        else:
            prod *= factor
            out[lag] = 1.0/prod
    return out

def latest_train(triangle, cutoff):
    out = {}
    for ay, by_lag in triangle.items():
        visible = [(lag,v) for lag,v in by_lag.items() if ay+lag-1 <= cutoff]
        if visible:
            out[ay] = max(visible)
    return out

def cape_components(triangle, premium, group, cutoff, pct):
    g,lob = group
    num=den=0.0
    for ay,(lag,val) in latest_train(triangle,cutoff).items():
        pr, prem = pct.get(lag), premium.get((g,lob,ay))
        if pr is None or prem is None or prem <= 0 or pr <= 0:
            continue
        num += val
        den += prem*pr
    return num,den

def group_cutoffs(triangle):
    cys = sorted({ay+lag-1 for ay,by_lag in triangle.items() for lag in by_lag})
    return cys[:-1]

def build_states(triangles,premium):
    states={}
    donor_pool=defaultdict(lambda:[0.0,0.0])
    for group,tri in triangles.items():
        max_lag=max((lag for by_lag in tri.values() for lag in by_lag),default=0)
        for cutoff in group_cutoffs(tri):
            fs=factors(tri,cutoff)
            pct=pct_reported(fs,max_lag) if fs and max_lag else {}
            num,den=cape_components(tri,premium,group,cutoff,pct) if pct else (0.0,0.0)
            cc=num/den if den>0 else None
            states[(group,cutoff)]={"factors":fs,"pct":pct,"cc_num":num,"cc_den":den,"cc_elr":cc}
            if den>0:
                pool=donor_pool[(group[1],cutoff)]
                pool[0]+=num; pool[1]+=den
    return states,donor_pool

def make_rows(triangles,premium,names,states,donor_pool):
    rows=[]
    for group,tri in triangles.items():
        g,lob=group
        for cutoff in group_cutoffs(tri):
            st=states[(group,cutoff)]
            fs,pct,cc=st["factors"],st["pct"],st["cc_elr"]
            pool_num,pool_den=donor_pool[(lob,cutoff)]
            bf_den=pool_den-st["cc_den"]
            bf=(pool_num-st["cc_num"])/bf_den if bf_den>0 else None
            if cc is None or bf is None:
                continue
            for ay,by_lag in tri.items():
                for target_lag,actual_cum in by_lag.items():
                    if target_lag < 2 or ay+target_lag-1 != cutoff+1:
                        continue
                    prev=by_lag.get(target_lag-1)
                    factor=fs.get(target_lag-1)
                    p0,p1=pct.get(target_lag-1),pct.get(target_lag)
                    prem=premium.get((g,lob,ay))
                    if (prev is None or factor is None or p0 is None or p1 is None
                            or prem is None or prem<=0):
                        continue
                    actual=actual_cum-prev
                    rows.append({
                        "grcode":g,"grname":names.get(g,""),"lob":lob,"cutoff":cutoff,
                        "accident_year":ay,"target_lag":target_lag,"actual":actual,
                        "chain_ladder":prev*(factor-1.0),
                        "cape_cod":cc*prem*(p1-p0),
                        "bornhuetter_ferguson":bf*prem*(p1-p0),
                    })
    return rows

def score(errors):
    if not errors:
        return {"mse":None,"rmse":None,"mae":None,"signed_mean_error":None}
    sse=sum(e*e for e in errors)
    return {"mse":sse/len(errors),"rmse":math.sqrt(sse/len(errors)),
            "mae":sum(abs(e) for e in errors)/len(errors),
            "signed_mean_error":sum(errors)/len(errors)}

def summarize(rows):
    methods=("chain_ladder","cape_cod","bornhuetter_ferguson")
    out={"n_cells":len(rows),"methods":{}}
    for m in methods:
        out["methods"][m]=score([r[m]-r["actual"] for r in rows])
    buckets=defaultdict(list)
    for r in rows:
        buckets[(r["grcode"],r["lob"],r["cutoff"])].append(r)
    out["n_diagonals"]=len(buckets)
    out["diagonal_methods"]={}
    for m in methods:
        errs=[sum(r[m] for r in rs)-sum(r["actual"] for r in rs) for rs in buckets.values()]
        out["diagonal_methods"][m]=score(errs)
    company_sse=defaultdict(lambda:defaultdict(float))
    for r in rows:
        for m in methods:
            company_sse[r["grcode"]][m]+=(r[m]-r["actual"])**2
    out["n_companies"]=len(company_sse)
    out["company_sse_win_counts"]={
        m:sum(company_sse[g][m]==min(company_sse[g].values()) for g in company_sse)
        for m in methods
    }
    return out

def analyze(path: Path):
    source=verify_source(path)
    triangles,premium,names=load(path)
    states,donor_pool=build_states(triangles,premium)
    rows=make_rows(triangles,premium,names,states,donor_pool)
    return {
        "status":"COMPUTED",
        "question":"CLRD2025 next-calendar-diagonal mean: volume Chain Ladder vs Cape Cod vs leave-one-company-out BF",
        "source":source,
        "selection":{
            "target":"next cumulative-paid increment",
            "score":"squared error",
            "fairness":"target_lag>=2; held-out claims excluded from factors and ELRs",
            "cape_cod":"company x LoB train-only ELR from earned premium and used-up exposure",
            "bornhuetter_ferguson":"same development pattern; LoB donor ELR pooled across other companies only",
        },
        "summary":summarize(rows),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("source",type=Path)
    ap.add_argument("--json-out",type=Path)
    args=ap.parse_args()
    result=analyze(args.source)
    text=json.dumps(result,indent=2,sort_keys=True)
    if args.json_out:
        args.json_out.write_text(text+"\n",encoding="utf-8")
    print(text)

if __name__=="__main__":
    main()
