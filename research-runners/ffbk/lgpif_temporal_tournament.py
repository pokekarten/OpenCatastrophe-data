#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, sys, urllib.request
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import gammaln
from scipy.stats import poisson, nbinom

SOURCE_COMMIT='8410b067ed2548e0e09077bbb880a476a0a2cdf9'
SOURCE_PATH='Data/WiscPropFund.csv'
SOURCE_URL=f'https://raw.githubusercontent.com/OpenActTextDev/LDA_Ed2/{SOURCE_COMMIT}/{SOURCE_PATH}'
EXPECTED_GIT_BLOB='267025ccdbff95d47706fd65241f52049243effc'
DELTA_GRID=(0.0,0.25,0.5,0.75,0.9)
BOOT_SEED=20260906
BOOT_REPS=20000
EPS=1e-12

def git_blob_sha1(b:bytes)->str:
    return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def load_payload(path:Path|None):
    if path: return path.read_bytes(), str(path)
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as r: return r.read(), SOURCE_URL

def parse(payload:bytes):
    rows=[]
    reader=csv.DictReader(io.StringIO(payload.decode('utf-8-sig')))
    expected=['PolicyNum','Year','Premium','Deduct','BCcov','Freq','Fire5','NoClaimCredit','EntityType','AlarmCredit','BCClaim']
    if reader.fieldnames != expected: raise ValueError(f'columns {reader.fieldnames}')
    for r in reader:
        rows.append({
            'PolicyNum':int(r['PolicyNum']),'Year':int(r['Year']),'Deduct':float(r['Deduct']),
            'BCcov':float(r['BCcov']),'Freq':int(float(r['Freq'])),'Fire5':int(float(r['Fire5'])),
            'NoClaimCredit':int(float(r['NoClaimCredit'])),'EntityType':str(r['EntityType']),
            'AlarmCredit':str(r['AlarmCredit'])})
    years=sorted({r['Year'] for r in rows})
    if years != [2006,2007,2008,2009,2010]: raise ValueError(years)
    if any(r['BCcov']<=0 or r['Deduct']<=0 or r['Freq']<0 for r in rows): raise ValueError('invalid positive/count fields')
    return rows

def design_spec(rows):
    dev=[r for r in rows if 2006<=r['Year']<=2008]
    logbc=np.array([math.log(r['BCcov']) for r in dev]); logded=np.array([math.log(r['Deduct']) for r in dev])
    return {'bc_center':float(np.mean(logbc)),'ded_center':float(np.mean(logded)),
            'entity_levels':sorted({r['EntityType'] for r in dev}), 'alarm_levels':sorted({r['AlarmCredit'] for r in dev})}

def xrow(r,spec, include_noclaim=False):
    x=[1.0, math.log(r['BCcov'])-spec['bc_center'], math.log(r['Deduct'])-spec['ded_center'], float(r['Fire5'])]
    for lvl in spec['entity_levels'][1:]: x.append(float(r['EntityType']==lvl))
    for lvl in spec['alarm_levels'][1:]: x.append(float(r['AlarmCredit']==lvl))
    if include_noclaim: x.append(float(r['NoClaimCredit']))
    if r['EntityType'] not in spec['entity_levels'] or r['AlarmCredit'] not in spec['alarm_levels']: raise ValueError('unseen category')
    return x

def fit_poisson_mean(rows,spec,end_year, include_noclaim=False):
    rr=[r for r in rows if r['Year']<=end_year]
    X=np.asarray([xrow(r,spec,include_noclaim) for r in rr],float); y=np.asarray([r['Freq'] for r in rr],float)
    def fun(b):
        eta=np.clip(X@b,-30,30); mu=np.exp(eta)
        return float(np.sum(mu-y*eta+gammaln(y+1)))
    def jac(b):
        eta=np.clip(X@b,-30,30); mu=np.exp(eta)
        return X.T@(mu-y)
    b0=np.zeros(X.shape[1]); b0[0]=math.log(max(float(np.mean(y)),1e-4))
    res=minimize(fun,b0,jac=jac,method='BFGS',options={'gtol':1e-8,'maxiter':2000})
    if not res.success and np.linalg.norm(jac(res.x))>1e-4: raise RuntimeError(f'poisson mean fit failed {res.message}')
    return np.asarray(res.x,float)

def mu_for(r,beta,spec,include_noclaim=False): return float(np.exp(np.clip(np.dot(xrow(r,spec,include_noclaim),beta),-30,30)))

def nb_logpmf(y,mu,alpha):
    a=max(float(alpha),1e-10); r=1.0/a; p=r/(r+mu)
    return float(nbinom.logpmf(y,r,p))

def fit_nb2_alpha(rows,beta,spec,end_year,include_noclaim=False):
    rr=[r for r in rows if r['Year']<=end_year]
    def obj(loga): return -sum(nb_logpmf(r['Freq'],mu_for(r,beta,spec,include_noclaim),math.exp(loga)) for r in rr)
    z=minimize_scalar(obj,bounds=(-8,4),method='bounded',options={'xatol':1e-10}); return float(math.exp(z.x))

def histories(rows,end_year):
    d={}
    for r in sorted((q for q in rows if q['Year']<=end_year), key=lambda z:(z['PolicyNum'],z['Year'])): d.setdefault(r['PolicyNum'],[]).append(r)
    return d

def gp_predictive_params(target, prior_rows, beta,spec,alpha,delta,include_noclaim=False):
    a=1.0/max(alpha,1e-10)
    sh=a; rate=a
    ty=target['Year']
    for h in prior_rows:
        lag=ty-h['Year']
        if lag<=0: continue
        w=(delta**(lag-1)) if delta>0 else (1.0 if lag==1 else 0.0)
        sh += w*h['Freq']; rate += w*mu_for(h,beta,spec,include_noclaim)
    mt=mu_for(target,beta,spec,include_noclaim)
    p=rate/(rate+mt)
    return float(sh),float(p),mt

def seq_gp_nll(rows,beta,spec,end_year,alpha,delta,include_noclaim=False,start_year=2007):
    hs=histories(rows,end_year)
    total=0.0;n=0
    for pol, rr in hs.items():
        for j,t in enumerate(rr):
            if t['Year']<start_year: continue
            prior=[h for h in rr[:j] if h['Year']<t['Year']]
            if not prior: continue
            sh,p,_=gp_predictive_params(t,prior,beta,spec,alpha,delta,include_noclaim)
            total -= float(nbinom.logpmf(t['Freq'],sh,p)); n+=1
    return total/max(n,1)

def fit_gp_alpha(rows,beta,spec,end_year,delta,include_noclaim=False):
    def obj(loga): return seq_gp_nll(rows,beta,spec,end_year,math.exp(loga),delta,include_noclaim)
    z=minimize_scalar(obj,bounds=(-8,4),method='bounded',options={'xatol':1e-9}); return float(math.exp(z.x))

def validation_delta(rows,beta_dev,spec,include_noclaim=False):
    out=[]
    for d in DELTA_GRID:
        a=fit_gp_alpha(rows,beta_dev,spec,2008,d,include_noclaim)
        hs=histories(rows,2009); scores=[]
        for pol,rr in hs.items():
            for j,t in enumerate(rr):
                if t['Year']!=2009: continue
                prior=[h for h in rr[:j] if h['Year']<2009]
                if not prior: continue
                sh,p,_=gp_predictive_params(t,prior,beta_dev,spec,a,d,include_noclaim)
                scores.append(-float(nbinom.logpmf(t['Freq'],sh,p)))
        out.append({'delta':d,'alpha_dev':a,'n2009':len(scores),'mean_nll_2009':float(np.mean(scores))})
    best=min(out,key=lambda z:(z['mean_nll_2009'],z['delta']))
    return best['delta'],out

def predict_final(rows,beta,spec,alpha_nb,alpha_static,alpha_dyn,delta_dyn,include_noclaim=False):
    hist=histories(rows,2010); recs=[]
    for pol,rr in hist.items():
        for j,t in enumerate(rr):
            if t['Year']!=2010: continue
            prior=[h for h in rr[:j] if h['Year']<2010]
            if not prior: continue
            y=t['Freq']; mu=mu_for(t,beta,spec,include_noclaim)
            shs,ps,_=gp_predictive_params(t,prior,beta,spec,alpha_static,1.0,include_noclaim)
            shd,pd,_=gp_predictive_params(t,prior,beta,spec,alpha_dyn,delta_dyn,include_noclaim)
            rnb=1/alpha_nb; pnb=rnb/(rnb+mu)
            models={
              'M0_poisson':(float(poisson.logpmf(y,mu)),float(poisson.pmf(0,mu)),float(poisson.cdf(y,mu))),
              'M1_independent_NB2':(float(nbinom.logpmf(y,rnb,pnb)),float(nbinom.pmf(0,rnb,pnb)),float(nbinom.cdf(y,rnb,pnb))),
              'M2_static_gamma_poisson':(float(nbinom.logpmf(y,shs,ps)),float(nbinom.pmf(0,shs,ps)),float(nbinom.cdf(y,shs,ps))),
              'M3_discounted_gamma_poisson':(float(nbinom.logpmf(y,shd,pd)),float(nbinom.pmf(0,shd,pd)),float(nbinom.cdf(y,shd,pd))),
            }
            recs.append({'policy':pol,'y':y,'history_len':len(prior),'models':models})
    return recs

def paired_boot(scores_a,scores_b):
    a=np.asarray(scores_a); b=np.asarray(scores_b); d=a-b; rng=np.random.default_rng(BOOT_SEED); n=len(d)
    means=np.empty(BOOT_REPS)
    for i in range(BOOT_REPS): means[i]=np.mean(d[rng.integers(0,n,n)])
    return {'mean_delta_nll':float(np.mean(d)),'ci95':[float(np.quantile(means,.025)),float(np.quantile(means,.975))]}

def summarize(recs):
    names=list(recs[0]['models']); out={}
    obs_zero=float(np.mean([r['y']==0 for r in recs]))
    for m in names:
        nll=[-r['models'][m][0] for r in recs]
        out[m]={'mean_nll':float(np.mean(nll)),'total_nll':float(np.sum(nll)),'predicted_zero_rate':float(np.mean([r['models'][m][1] for r in recs])),'observed_zero_rate':obs_zero}
    scores={m:[-r['models'][m][0] for r in recs] for m in names}
    for m in names[1:]: out[m]['paired_vs_M0']=paired_boot(scores[m],scores['M0_poisson'])
    out['pairwise_discriminators']={
      'M1_minus_M0':paired_boot(scores['M1_independent_NB2'],scores['M0_poisson']),
      'M2_minus_M1':paired_boot(scores['M2_static_gamma_poisson'],scores['M1_independent_NB2']),
      'M3_minus_M2':paired_boot(scores['M3_discounted_gamma_poisson'],scores['M2_static_gamma_poisson']),
      'M3_minus_M1':paired_boot(scores['M3_discounted_gamma_poisson'],scores['M1_independent_NB2']),
    }
    out['primary_n']=len(recs); out['observed_mean_count']=float(np.mean([r['y'] for r in recs])); out['max_count']=int(max(r['y'] for r in recs))
    return out

def run(rows, include_noclaim=False):
    spec=design_spec(rows)
    beta_dev=fit_poisson_mean(rows,spec,2008,include_noclaim)
    delta, val=validation_delta(rows,beta_dev,spec,include_noclaim)
    beta_final=fit_poisson_mean(rows,spec,2009,include_noclaim)
    alpha_nb=fit_nb2_alpha(rows,beta_final,spec,2009,include_noclaim)
    alpha_static=fit_gp_alpha(rows,beta_final,spec,2009,1.0,include_noclaim)
    alpha_dyn=fit_gp_alpha(rows,beta_final,spec,2009,delta,include_noclaim)
    recs=predict_final(rows,beta_final,spec,alpha_nb,alpha_static,alpha_dyn,delta,include_noclaim)
    return {'design_spec':spec,'beta_dev':beta_dev.tolist(),'delta_selection_2009':val,'selected_delta':delta,'beta_refit_2006_2009':beta_final.tolist(),'alpha_refit':{'M1_NB2':alpha_nb,'M2_static':alpha_static,'M3_discounted':alpha_dyn},'final_2010':summarize(recs)}

def self_check():
    rows=[]
    for p in range(20):
        for y in range(2006,2011):
            rows.append({'PolicyNum':p,'Year':y,'Deduct':1000.0,'BCcov':1e6*(1+p/20),'Freq':int((p+y)%3==0),'Fire5':p%2,'NoClaimCredit':0,'EntityType':str(1+p%2),'AlarmCredit':str(1+p%2)})
    z=run(rows); assert z['final_2010']['primary_n']==20; print('LGPIF_TEMPORAL_TOURNAMENT_SELF_CHECK_OK')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--csv',type=Path); ap.add_argument('--output',type=Path); ap.add_argument('--self-check',action='store_true'); args=ap.parse_args()
    if args.self_check: self_check(); return
    payload,source=load_payload(args.csv); blob=git_blob_sha1(payload)
    if blob!=EXPECTED_GIT_BLOB: raise ValueError(f'blob mismatch {blob}')
    rows=parse(payload)
    primary=run(rows,False)
    sensitivity=run(rows,True)
    receipt={'status':'RESEARCH_ONLY_NO_PROMOTION','source':source,'source_commit':SOURCE_COMMIT,'source_path':SOURCE_PATH,'git_blob_sha1':blob,'rows':len(rows),'protocol':{'development':'2006-2008','validation':'2009','final':'2010','primary_population':'2010 policies with >=1 prior observation','mean_covariates':['log(BCcov)','log(Deduct)','Fire5','EntityType','AlarmCredit'],'NoClaimCredit_primary':'excluded','M3':'discounted Gamma-Poisson one-step predictive; delta selected on 2009 from fixed grid','delta_grid':list(DELTA_GRID),'bootstrap_reps':BOOT_REPS,'bootstrap_seed':BOOT_SEED},'primary':primary,'NoClaimCredit_sensitivity':sensitivity,'runtime':{'python':sys.version,'numpy':np.__version__}}
    text=json.dumps(receipt,indent=2,sort_keys=True); print(text)
    if args.output: args.output.write_text(text+'\n')
if __name__=='__main__': main()
