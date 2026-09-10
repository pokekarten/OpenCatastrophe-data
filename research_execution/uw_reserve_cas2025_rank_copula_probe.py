#!/usr/bin/env python3
import bisect, hashlib, json, math, random, statistics
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist
import numpy as np
import uw_reserve_cas2025_dependence_probe as base

OUT=Path('research_execution/result_rank.json')
N=NormalDist()

def normal_scores(train, test):
    a=np.asarray(train,float); order=np.argsort(a,kind='mergesort'); n=len(a)
    ztrain=np.empty(n,float)
    k=0
    while k<n:
        j=k+1
        while j<n and a[order[j]]==a[order[k]]: j+=1
        p=((k+j-1)/2+1)/(n+1)
        z=N.inv_cdf(min(1-0.5/(n+1),max(0.5/(n+1),p)))
        ztrain[order[k:j]]=z
        k=j
    s=sorted(float(v) for v in a)
    ztest=[]
    for v in test:
        p=(bisect.bisect_right(s,float(v))+0.5)/(n+1)
        p=min(1-0.5/(n+1),max(0.5/(n+1),p))
        ztest.append(N.inv_cdf(p))
    return ztrain,np.asarray(ztest,float)

def eval_split(train,test,kind,label):
    if len(train)<100 or len(test)<20:return None
    tr1,tr2,te1,te2=base.fit_residuals(train,test)
    tr1,te1=normal_scores(tr1,te1); tr2,te2=normal_scores(tr2,te2)
    rg,rh,tau2=base.hierarchical_rhos(train,tr1,tr2)
    rec=[]
    for i,r in enumerate(test):
        sg=base.copula_score(te1[i],te2[i],rg); sh=base.copula_score(te1[i],te2[i],rh.get(r['lob'],rg))
        rec.append({'company':r['company'],'lob':r['lob'],'year':r['year'],'global':sg,'hier':sh})
    return {'kind':kind,'label':label,'n_train':len(train),'n_test':len(test),'rho_global':rg,'rho_by_lob':rh,'tau2_fisher':tau2,'test_score_global_vs_ind':float(np.mean([z['global'] for z in rec])),'test_score_hier_vs_ind':float(np.mean([z['hier'] for z in rec])),'test_score_hier_vs_global':float(np.mean([z['hier']-z['global'] for z in rec])),'records':rec}

def boot(records,key,seed,reps=2000):
    by=defaultdict(list)
    for r in records: by[r['company']].append(r[key])
    co=sorted(by); rng=random.Random(seed); vals=[]
    for _ in range(reps):
        z=[]
        for __ in co: z.extend(by[rng.choice(co)])
        vals.append(sum(z)/len(z))
    vals.sort(); return [vals[int(.025*reps)],vals[min(reps-1,int(.975*reps))]]

def main():
    panel=[]; src={}
    for lob,(url,h) in base.SOURCES.items():
        p,n,got=base.download(lob,url,h); dat,_,_=base.build_panel(lob,p); panel.extend(dat); src[lob]={'url':url,'bytes':n,'sha256':got}
    splits=[]
    for fold in range(5):
        train=[];test=[]
        for r in panel:
            f=int(hashlib.sha256(f'{base.SALT}|{r["company"]}'.encode()).hexdigest(),16)%5
            (test if f==fold else train).append(r)
        q=eval_split(train,test,'company_holdout',str(fold))
        if q:splits.append(q)
    years=sorted({r['year'] for r in panel})
    for y in years[-3:]:
        q=eval_split([r for r in panel if r['year']<y],[r for r in panel if r['year']==y],'temporal_holdout',str(y))
        if q:splits.append(q)
    summary={}
    for kind in ('company_holdout','temporal_holdout'):
        ss=[s for s in splits if s['kind']==kind]; rec=[r for s in ss for r in s['records']]
        g=[r['global'] for r in rec]; h=[r['hier'] for r in rec]
        rr=[{**r,'hg':r['hier']-r['global']} for r in rec]
        summary[kind]={'splits':len(ss),'n_scored':len(rec),'global_vs_ind_mean':sum(g)/len(g),'global_vs_ind_cluster_boot_95':boot(rec,'global',20260920),'hier_vs_ind_mean':sum(h)/len(h),'hier_vs_ind_cluster_boot_95':boot(rec,'hier',20260921),'hier_vs_global_mean':sum(r['hg'] for r in rr)/len(rr),'hier_vs_global_cluster_boot_95':boot(rr,'hg',20260922),'rho_global_by_split':[s['rho_global'] for s in ss],'rho_by_lob_by_split':[s['rho_by_lob'] for s in ss],'tau2_by_split':[s['tau2_fisher'] for s in ss]}
    ch=summary['company_holdout']; th=summary['temporal_holdout']
    if ch['global_vs_ind_cluster_boot_95'][0]>0 and th['global_vs_ind_cluster_boot_95'][0]>0:
        status='GLOBAL_SCALAR_SUPPORTED_ON_RANK_COPULA_SCORE'
    elif ch['global_vs_ind_mean']<=0 or th['global_vs_ind_mean']<=0 or ch['global_vs_ind_cluster_boot_95'][1]<=0 or th['global_vs_ind_cluster_boot_95'][1]<=0:
        status='NO_GLOBAL_SCALAR_PROMOTION_SUPPORTED'
    else: status='INCONCLUSIVE_NO_GLOBAL_SCALAR_PROMOTION'
    out={'schema_version':1,'question':'Rank-marginal sensitivity: does a global residual Gaussian-copula scalar improve held-out joint prediction after training-only empirical marginal transform?','status':status,'promotion':'NO_PROMOTION','source_identity':src,'panel':{'n':len(panel),'companies':len({r['company'] for r in panel}),'lobs':len({r['lob'] for r in panel}),'years':years},'method':{'marginal_residuals':'same training-only OLS as primary probe','copula_margins':'training-only empirical CDF residual ranks mapped to Normal scores; held-out residuals mapped through training ECDF only','dependence':'rho=0 vs global Gaussian-copula rho vs LoB Fisher-z empirical-Bayes partial pooling','validation':'5 deterministic grouped-company folds + last 3 rolling temporal years; company-cluster bootstrap'},'holdout_summary':summary,'splits':[{k:v for k,v in s.items() if k!='records'} for s in splits],'limitations':['Rank transform isolates copula dependence better than raw Gaussian residual scoring but does not validate tail dependence or capital adequacy.','The Schedule-P reserve target remains a displayed-cohort development proxy rather than a full one-year CDR.','Empirical-Bayes LoB pooling is a challenger, not a selected production hierarchy.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
