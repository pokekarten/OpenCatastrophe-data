#!/usr/bin/env python3
import hashlib, json, math, random, statistics
from collections import defaultdict
from pathlib import Path
import numpy as np
import uw_reserve_cas2025_dependence_probe as base
import uw_reserve_cas2025_rank_copula_probe as rank

OUT=Path('research_execution/result_conditioning.json')
FEATURE_SETS={
  'calendar_lob': ('calendar','lob'),
  'calendar_lob_premium': ('calendar','lob','premium'),
  'calendar_lob_premium_openreserve': ('calendar','lob','premium','openreserve'),
}

def design(rows,lobs,yc,ys,features):
    X=[]
    for r in rows:
        z=[1.0]
        if 'calendar' in features: z.append((r['year']-yc)/ys)
        if 'premium' in features: z.append(math.log(r['premium']))
        if 'openreserve' in features: z.append(math.log(r['open_reserve']))
        if 'lob' in features:
            for lob in lobs[1:]: z.append(1.0 if r['lob']==lob else 0.0)
        X.append(z)
    return np.asarray(X,float)

def fit(train,test,features):
    lobs=sorted({r['lob'] for r in train}); yc=statistics.mean(r['year'] for r in train); ys=statistics.pstdev(r['year'] for r in train) or 1.0
    X=design(train,lobs,yc,ys,features); Xt=design(test,lobs,yc,ys,features)
    out=[]
    for target in ('uw','reserve'):
        y=np.asarray([r[target] for r in train],float); yt=np.asarray([r[target] for r in test],float)
        b=np.linalg.lstsq(X,y,rcond=None)[0]; er=y-X@b; et=yt-Xt@b
        sd=float(np.sqrt(np.mean(er*er)))
        out.append((er/sd,et/sd))
    return out[0][0],out[1][0],out[0][1],out[1][1]

def eval_split(train,test,features,kind,label):
    a,b,c,d=fit(train,test,features)
    raw_pearson=base.safe_rho(a,b); raw_spearman=base.rank_corr(list(a),list(b))
    za,zc=rank.normal_scores(a,c); zb,zd=rank.normal_scores(b,d)
    rho=base.safe_rho(za,zb)
    rec=[]
    for i,r in enumerate(test): rec.append({'company':r['company'],'lob':r['lob'],'year':r['year'],'score':base.copula_score(zc[i],zd[i],rho)})
    return {'kind':kind,'label':label,'n_train':len(train),'n_test':len(test),'train_residual_pearson':raw_pearson,'train_residual_spearman':raw_spearman,'train_rank_gaussian_rho':rho,'records':rec}

def boot(rec,seed,reps=2000):
    by=defaultdict(list)
    for r in rec: by[r['company']].append(r['score'])
    co=sorted(by); rng=random.Random(seed); vals=[]
    for _ in range(reps):
        z=[]
        for __ in co: z.extend(by[rng.choice(co)])
        vals.append(sum(z)/len(z))
    vals.sort(); return [vals[int(.025*reps)], vals[min(reps-1,int(.975*reps))]]

def main():
    panel=[]; src={}
    for lob,(url,h) in base.SOURCES.items():
        p,n,got=base.download(lob,url,h); dat,_,_=base.build_panel(lob,p); panel.extend(dat); src[lob]={'url':url,'bytes':n,'sha256':got}
    outsets={}
    years=sorted({r['year'] for r in panel})
    for si,(name,features) in enumerate(FEATURE_SETS.items()):
        ss=[]
        for fold in range(5):
            tr=[];te=[]
            for r in panel:
                f=int(hashlib.sha256(f'{base.SALT}|{r["company"]}'.encode()).hexdigest(),16)%5
                (te if f==fold else tr).append(r)
            ss.append(eval_split(tr,te,features,'company_holdout',str(fold)))
        for y in years[-3:]:
            ss.append(eval_split([r for r in panel if r['year']<y],[r for r in panel if r['year']==y],features,'temporal_holdout',str(y)))
        summ={}
        for kind in ('company_holdout','temporal_holdout'):
            qq=[s for s in ss if s['kind']==kind]; rec=[r for s in qq for r in s['records']]
            m=sum(r['score'] for r in rec)/len(rec)
            summ[kind]={'n_scored':len(rec),'global_rank_copula_vs_ind_mean':m,'company_cluster_boot_95':boot(rec,20260930+si+(0 if kind=='company_holdout' else 10)),'train_residual_pearson_by_split':[s['train_residual_pearson'] for s in qq],'train_residual_spearman_by_split':[s['train_residual_spearman'] for s in qq],'train_rank_gaussian_rho_by_split':[s['train_rank_gaussian_rho'] for s in qq]}
        outsets[name]={'features':features,'summary':summ}
    out={'schema_version':1,'question':'Is the apparent residual UW-reserve copula dependence stable to reasonable shared-conditioning choices?','status':'SENSITIVITY_ONLY_NO_PROMOTION','promotion':'NO_PROMOTION','source_identity':src,'panel':{'n':len(panel),'companies':len({r['company'] for r in panel}),'lobs':len({r['lob'] for r in panel}),'years':years},'feature_sets':outsets,'interpretation_rule':'A global scalar is not robust if sign/magnitude or held-out score materially changes across plausible predeclared conditioning sets. This sensitivity does not select a conditioning set.','limitations':['All targets are the bounded Schedule-P proxy used in the companion probe, not realised one-year CDR.','Feature sets are simple linear controls and do not establish causal adjustment sets.','The exercise diagnoses specification sensitivity only; it does not select a production marginal model or dependence family.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__': main()
