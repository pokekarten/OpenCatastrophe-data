# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Sweep all source-selected storms through the fictional three-site model."""
import sys,tomllib,json,copy,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research_runners.windstorm_europe_model_v1 import execute
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--hazard',type=Path,required=True)
p.add_argument('--curves',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
if a.output.exists():p.error('refuse overwrite')
c=tomllib.loads((ROOT/'research/fixtures/windstorm_europe_v1_synthetic.toml').read_text())
c['hazard_source']=str(a.hazard.resolve())
for r in c['responses'].values():r['path']=str(a.curves.resolve())
c['year_ids']=[1];results=[]
for i in range(50):
 x=copy.deepcopy(c);x['occurrences']=[dict(year_id=1,occurrence_id='source-event-'+str(i),sample_id=0,storm_index=i)]
 try:
  r=execute(x,Path('/'));results.append(dict(storm_index=i,status='executed',occurrence=r['occurrences'][0]))
 except ValueError as e:results.append(dict(storm_index=i,status='blocked',reason=str(e)))
with a.output.open('x') as f:json.dump(dict(annual_frequency_established=False,fictional_exposure=True,source_selected_events=results),f,indent=2,allow_nan=False);print('executed',sum(r['status']=='executed' for r in results),'blocked',sum(r['status']=='blocked' for r in results));print({r.get('reason') for r in results if r['status']=='blocked'})
