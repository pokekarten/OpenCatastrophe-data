#!/usr/bin/env python3
import csv, hashlib, json, math, os, random, statistics, urllib.request
from collections import defaultdict
from pathlib import Path
import numpy as np

SOURCES = {
  "ppauto": ("https://www.casact.org/sites/default/files/2026-03/ppauto_pos98-07%20%281%29.csv", "6e838f1e44c67218133ef1c8e28ca2b34b9f21ba4ee94de408c412638f798d96"),
  "wkcomp": ("https://www.casact.org/sites/default/files/2026-03/wkcomp_pos_98-07.csv", "8d0b02bed0939e932f9078f65266e9a398f580f90e5227cde053dd5b520affef"),
  "comauto": ("https://www.casact.org/sites/default/files/2026-03/comauto_pos_98-07.csv", "5012bd4c9048e300669e2f4fc915850449099e159481b4c3349b574f6f00afe1"),
  "medmal": ("https://www.casact.org/sites/default/files/2026-03/medmal_pos_98-07.csv", "50ea237914797562661b82996765e40b1fd09784a63130463bbd4972f74dbba3"),
  "prodliab": ("https://www.casact.org/sites/default/files/2026-03/prodliab_pos_98-07.csv", "f1070b5a95658bfeb6719fdf4ffdabc8b7e3f97771cdb4b3f503eb7d6e486f01"),
  "othliab": ("https://www.casact.org/sites/default/files/2026-03/othliab_pos_98-07.csv", "f514136de4be7b5ac114346709c309cd2464861e9fbb683051849f9fa6eadc50"),
}
SALT = "cas2025-uw-reserve-dependence-v0"
OUT = Path("research_execution/result.json")
DATA = Path("research_execution/data"); DATA.mkdir(parents=True, exist_ok=True)

def fnum(x):
    try: return float(str(x).replace(",", "").strip())
    except: return float("nan")

def inum(x):
    try: return int(float(str(x).strip()))
    except: return None

def download(lob, url, expected):
    p = DATA / f"{lob}.csv"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 research-reproducibility-probe/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r: b = r.read()
    got = hashlib.sha256(b).hexdigest()
    if got != expected: raise RuntimeError(f"sha256 mismatch {lob}: {got} != {expected}")
    p.write_bytes(b)
    return p, len(b), got

def pick(row, *names):
    for n in names:
        if n in row: return row[n]
    return None

def build_panel(lob, path):
    rows=[]
    with path.open(newline='', encoding='utf-8-sig') as fh:
        rd=csv.DictReader(fh)
        fields=rd.fieldnames or []
        required={"GRCODE","AccidentYear","DevelopmentYear","CumPaidLoss","EarnedPremNet"}
        if not required.issubset(fields): raise RuntimeError(f"schema {lob}: {fields}")
        incur_name="IncurLoss" if "IncurLoss" in fields else "IncurredLosses" if "IncurredLosses" in fields else None
        if not incur_name: raise RuntimeError(f"no incurred column {lob}: {fields}")
        for r in rd:
            c=str(r.get("GRCODE","")).strip(); ay=inum(r.get("AccidentYear")); dy=inum(r.get("DevelopmentYear"))
            if not c or ay is None or dy is None: continue
            inc=fnum(r.get(incur_name)); paid=fnum(r.get("CumPaidLoss")); prem=fnum(r.get("EarnedPremNet"))
            if not all(math.isfinite(v) for v in (inc,paid,prem)): continue
            rows.append((c,ay,dy,inc,paid,prem))
    by=defaultdict(dict); prem0={}; names=set()
    for c,ay,dy,inc,paid,prem in rows:
        by[(c,ay)][dy]=(inc,paid,prem); names.add(c)
        if dy==ay: prem0[(c,ay)]=prem
    years=sorted({ay for c,ay in by if (c,ay) in prem0})
    panel=[]
    for c in sorted(names):
      for t in years:
        cur=by.get((c,t),{}).get(t)
        if cur is None: continue
        prem=cur[2]
        if not math.isfinite(prem) or prem<=0: continue
        num=0.0; den=0.0; cohorts=0
        for ay in years:
            if ay>=t: continue
            prev=by.get((c,ay),{}).get(t-1); now=by.get((c,ay),{}).get(t)
            if prev is None or now is None: continue
            open_res=prev[0]-prev[1]
            num += now[0]-prev[0]
            den += open_res
            cohorts += 1
        if cohorts<1 or not math.isfinite(den) or den<=0: continue
        uw=cur[0]/prem
        reserve=num/den
        if not (math.isfinite(uw) and math.isfinite(reserve)): continue
        panel.append({"lob":lob,"company":c,"year":t,"premium":prem,"open_reserve":den,"uw":uw,"reserve":reserve,"cohorts":cohorts})
    return panel, len(rows), years

def rank_corr(x,y):
    def ranks(a):
        order=sorted(range(len(a)), key=lambda i:a[i]); out=[0.0]*len(a); k=0
        while k<len(order):
            j=k+1
            while j<len(order) and a[order[j]]==a[order[k]]: j+=1
            r=(k+j-1)/2+1
            for z in order[k:j]: out[z]=r
            k=j
        return np.array(out,float)
    if len(x)<3:return float('nan')
    return float(np.corrcoef(ranks(x),ranks(y))[0,1])

def design(rows, lobs, year_center, year_scale):
    X=[]
    for r in rows:
        z=[1.0,(r['year']-year_center)/year_scale,math.log(r['premium']),math.log(r['open_reserve'])]
        for lob in lobs[1:]: z.append(1.0 if r['lob']==lob else 0.0)
        X.append(z)
    return np.asarray(X,float)

def fit_residuals(train,test):
    lobs=sorted({r['lob'] for r in train})
    yc=statistics.mean([r['year'] for r in train]); ys=statistics.pstdev([r['year'] for r in train]) or 1.0
    X=design(train,lobs,yc,ys); Xt=design(test,lobs,yc,ys)
    out=[]
    for target in ('uw','reserve'):
        y=np.array([r[target] for r in train],float); yt=np.array([r[target] for r in test],float)
        beta=np.linalg.lstsq(X,y,rcond=None)[0]
        er=y-X@beta; sd=float(np.sqrt(np.mean(er*er)))
        if not math.isfinite(sd) or sd<=1e-12: raise RuntimeError('degenerate residual scale')
        out.append((er/sd,(yt-Xt@beta)/sd))
    return out[0][0],out[1][0],out[0][1],out[1][1]

def safe_rho(x,y):
    if len(x)<4:return 0.0
    r=float(np.corrcoef(x,y)[0,1]);
    if not math.isfinite(r): r=0.0
    return max(-0.95,min(0.95,r))

def hierarchical_rhos(train, e1,e2):
    by=defaultdict(list)
    for i,r in enumerate(train): by[r['lob']].append(i)
    global_r=safe_rho(e1,e2); zg=math.atanh(global_r)
    zs=[]; vs=[]; ns=[]
    for lob,ix in by.items():
        if len(ix)>=4:
            rr=safe_rho(e1[ix],e2[ix]); zs.append(math.atanh(rr)); vs.append(1.0/(len(ix)-3)); ns.append((lob,len(ix),math.atanh(rr)))
    if len(zs)>1:
        w=np.array([1/v for v in vs]); mu=float(np.average(zs,weights=w))
        q=float(np.sum(w*(np.array(zs)-mu)**2)); c=float(np.sum(w)-np.sum(w*w)/np.sum(w))
        tau2=max(0.0,(q-(len(zs)-1))/c) if c>0 else 0.0
    else: tau2=0.0
    out={}
    for lob,n,z in ns:
        v=1.0/(n-3); a=tau2/(tau2+v) if tau2>0 else 0.0
        out[lob]=max(-0.95,min(0.95,math.tanh(a*z+(1-a)*zg)))
    return global_r,out,tau2

def copula_score(x,y,rho):
    r=max(-0.95,min(0.95,float(rho))); d=1-r*r
    return -0.5*math.log(d) -0.5*((x*x-2*r*x*y+y*y)/d-(x*x+y*y))

def eval_split(train,test,kind,label):
    if len(train)<100 or len(test)<20:return None
    tr1,tr2,te1,te2=fit_residuals(train,test)
    rg,rh,tau2=hierarchical_rhos(train,tr1,tr2)
    rec=[]
    for i,r in enumerate(test):
        sg=copula_score(te1[i],te2[i],rg); sh=copula_score(te1[i],te2[i],rh.get(r['lob'],rg))
        rec.append({"company":r['company'],"lob":r['lob'],"year":r['year'],"global":sg,"hier":sh})
    return {"kind":kind,"label":label,"n_train":len(train),"n_test":len(test),"rho_global":rg,"rho_by_lob":rh,"tau2_fisher":tau2,"test_score_global_vs_ind":float(np.mean([z['global'] for z in rec])),"test_score_hier_vs_ind":float(np.mean([z['hier'] for z in rec])),"test_score_hier_vs_global":float(np.mean([z['hier']-z['global'] for z in rec])),"records":rec}

def cluster_boot(records,key,seed=20260910,reps=2000):
    by=defaultdict(list)
    for r in records: by[r['company']].append(r[key])
    companies=sorted(by)
    if len(companies)<10:return [None,None]
    vals=[]; rng=random.Random(seed)
    for _ in range(reps):
        draw=[rng.choice(companies) for __ in companies]
        z=[v for c in draw for v in by[c]]; vals.append(sum(z)/len(z))
    vals.sort(); return [vals[int(.025*reps)],vals[min(reps-1,int(.975*reps))]]

def main():
    panel=[]; src={}; triangle_rows={}; years={}
    for lob,(url,h) in SOURCES.items():
        p,n,got=download(lob,url,h); dat,nrows,yrs=build_panel(lob,p)
        panel.extend(dat); triangle_rows[lob]=nrows; years[lob]=yrs
        src[lob]={"url":url,"bytes":n,"sha256":got}
    if len(panel)<500: raise RuntimeError(f"insufficient panel {len(panel)}")
    # Raw evidence by LoB and pooled.
    raw={}
    for lob in ['ALL']+sorted(SOURCES):
        rr=panel if lob=='ALL' else [r for r in panel if r['lob']==lob]
        raw[lob]={"n":len(rr),"companies":len({r['company'] for r in rr}),"pearson":safe_rho(np.array([r['uw'] for r in rr]),np.array([r['reserve'] for r in rr])) if len(rr)>=4 else None,"spearman":rank_corr([r['uw'] for r in rr],[r['reserve'] for r in rr]) if len(rr)>=4 else None}
    splits=[]
    # Grouped company 5-fold; same GRCODE stays out across all LoBs.
    for fold in range(5):
        test=[]; train=[]
        for r in panel:
            f=int(hashlib.sha256(f"{SALT}|{r['company']}".encode()).hexdigest(),16)%5
            (test if f==fold else train).append(r)
        z=eval_split(train,test,'company_holdout',str(fold))
        if z:splits.append(z)
    # Strict rolling temporal holdout on last three origin/calendar years with >=4 prior years.
    all_years=sorted({r['year'] for r in panel})
    for y in all_years[-3:]:
        train=[r for r in panel if r['year']<y]; test=[r for r in panel if r['year']==y]
        z=eval_split(train,test,'temporal_holdout',str(y))
        if z:splits.append(z)
    summary={}
    for kind in ('company_holdout','temporal_holdout'):
        ss=[s for s in splits if s['kind']==kind]; rec=[r for s in ss for r in s['records']]
        if rec:
            g=[r['global'] for r in rec]; h=[r['hier'] for r in rec]; hg=[r['hier']-r['global'] for r in rec]
            summary[kind]={"splits":len(ss),"n_scored":len(rec),"global_vs_ind_mean":sum(g)/len(g),"global_vs_ind_cluster_boot_95":cluster_boot(rec,'global'),"hier_vs_ind_mean":sum(h)/len(h),"hier_vs_ind_cluster_boot_95":cluster_boot(rec,'hier',20260911),"hier_vs_global_mean":sum(hg)/len(hg),"hier_vs_global_cluster_boot_95":cluster_boot([{**r,'hg':r['hier']-r['global']} for r in rec],'hg',20260912),"rho_global_by_split":[s['rho_global'] for s in ss],"tau2_by_split":[s['tau2_fisher'] for s in ss]}
    verdict='INCONCLUSIVE'; promotion='NO_PROMOTION'
    ch=summary.get('company_holdout',{}); th=summary.get('temporal_holdout',{})
    # Strong global promotion requires positive mean + positive cluster CI in both holdout families.
    if ch and th and ch['global_vs_ind_cluster_boot_95'][0] is not None and th['global_vs_ind_cluster_boot_95'][0] is not None:
        if ch['global_vs_ind_mean']>0 and th['global_vs_ind_mean']>0 and ch['global_vs_ind_cluster_boot_95'][0]>0 and th['global_vs_ind_cluster_boot_95'][0]>0:
            verdict='GLOBAL_SCALAR_SUPPORTED_ON_GAUSSIAN_RESIDUAL_SCORE'
        elif ch['global_vs_ind_mean']<=0 or th['global_vs_ind_mean']<=0:
            verdict='MIXED_NO_GLOBAL_SCALAR_PROMOTION'
        else: verdict='INCONCLUSIVE_NO_GLOBAL_SCALAR_PROMOTION'
    result={"schema_version":1,"question":"Does a global residual UW-reserve dependence scalar improve held-out joint prediction versus conditional independence and LoB hierarchical partial pooling on current CAS Schedule-P data?","status":verdict,"promotion":promotion,"source_identity":src,"target_semantics":{"uw":"current AY first-diagonal net incurred / net earned premium","reserve":"calendar-year prior-AY incurred emergence / opening reported net reserve proxy=sum(prior incurred-prior cumulative paid), restricted to displayed 1998-2007 AY cohorts","warning":"reserve target is a Schedule-P development proxy, not a full model-based one-year CDR"},"conditioning":{"marginals":"training-only OLS; intercept + calendar trend + log net earned premium + log opening reserve + LoB fixed effects","dependence":"standardized marginal residuals; independence rho=0 vs one global Gaussian rho vs LoB Fisher-z empirical-Bayes partial pooling","score":"held-out Gaussian copula log-score contribution; higher is better; company-cluster bootstrap"},"panel":{"n":len(panel),"companies":len({r['company'] for r in panel}),"lobs":len({r['lob'] for r in panel}),"years":sorted({r['year'] for r in panel}),"triangle_rows":triangle_rows,"raw":raw},"holdout_summary":summary,"splits":[{k:v for k,v in s.items() if k!='records'} for s in splits],"limitations":["CAS Schedule-P public data cover a bounded historical accident-year panel and listed cohorts, not a complete modern insurer risk-factor panel.","The reserve target is closer to prior-year development economics than the earlier adjacent-AY proxy but is not a full one-year re-reserving CDR.","Gaussian residual copula score tests a scalar conditional-dependence representation, not tail dependence or capital adequacy.","No model-selection claims are made from raw correlations alone."]}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
