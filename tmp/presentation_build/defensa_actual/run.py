import sys, json, copy, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import yaml
import src.optimization.genetic_algorithm as gm
from src.config.settings import load_settings
from src.database.spatial import SpatialRepository
from src.optimization.spatial import ParkEvaluator, Individual
from src.pipeline.reporting import write_run_outputs

OUT=Path(__file__).parent
cfg=yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8'))
cfg['genetic_algorithm']['random_seed']=20261007
(OUT/'config.yaml').write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False),encoding='utf-8')
settings=load_settings(OUT/'config.yaml')
ref=json.loads((ROOT/'results/spatial/run-20261007T003424-8b60c1ab/optimization_run.json').read_text(encoding='utf-8'))
repo=SpatialRepository(settings.paths.database)
data=repo.load_dataset(ref['dataset']['config_signature'])
ev=ParkEvaluator(data['grid'],data['neighbors'],data['lines'],data['transformers'],settings.park,settings.fitness)
generation=0
leaders=[]; initial=[]; crosses=[]; mutations=[]
def rec(i):
    p=ev._evaluate(i)
    return dict(seed=i.seed_cell_id,genes=list(i.growth_genes),cells=list(p.cell_ids),accepted=list(p.accepted_gene_indices),**p.metrics)
orig_sel=gm.tournament_selection;orig_cross=gm.competitive_crossover_pair;orig_mut=gm.mutate_effectively
def sel(pop,fitness,*args):
    global generation
    if generation==0:initial.extend(rec(i) for i in pop)
    if generation in [0,1,5,20,50,100]:leaders.append(dict(generation=generation,**rec(pop[int(np.argmax(fitness))])))
    generation+=1
    return orig_sel(pop,fitness,*args)
def cross(a,b,rng,e):
    state=copy.deepcopy(rng.bit_generator.state)
    children=orig_cross(a,b,rng,e)
    if len(crosses)<30:
        parents=[a,b]; ps=[ev._evaluate(i) for i in parents]
        compact=[Individual(i.seed_cell_id,tuple(i.growth_genes[k] for k in p.accepted_gene_indices)) for i,p in zip(parents,ps)]
        clone=np.random.default_rng();clone.bit_generator.state=state
        positions=min(len(i.growth_genes) for i in compact)+1
        cuts=clone.choice(positions,size=min(3,positions),replace=False)
        for j,child in enumerate(children):
            p=ev._evaluate(child)
            if p.metrics['fitness']<=ps[j].metrics['fitness'] or p.cell_ids==ps[j].cell_ids:continue
            for cut in cuts:
                candidate=Individual(compact[j].seed_cell_id,compact[j].growth_genes[:cut]+compact[1-j].growth_genes[cut:])
                cp=ev._evaluate(candidate)
                if cp.cell_ids==p.cell_ids and 0<int(cut)<min(len(i.growth_genes) for i in compact):
                    crosses.append(dict(generation=generation,cut=int(cut),cuts=cuts.tolist(),a=rec(compact[j]),b=rec(compact[1-j]),child=rec(child),raw_child=rec(candidate)))
                    break
    return children
def mut(a,e,rng,attempts):
    child,n,changed=orig_mut(a,e,rng,attempts)
    if changed and len(mutations)<100:mutations.append(dict(generation=generation,parent=rec(a),child=rec(child),attempts=n))
    return child,n,changed
gm.tournament_selection=sel;gm.competitive_crossover_pair=cross;gm.mutate_effectively=mut
result=gm.GeneticAlgorithm(ev,settings.genetic_algorithm).run()
gm.tournament_selection=orig_sel;gm.competitive_crossover_pair=orig_cross;gm.mutate_effectively=orig_mut
outputs=write_run_outputs(settings,repo,result,data,ev)
run=outputs['optimization_run_json'].parent
row=result.top5.iloc[0]
best=rec(Individual(int(row.seed_cell_id),tuple(json.loads(row.growth_genes))))
leaders.append(dict(generation=200,**best))
c=next((x for x in crosses if len(x['a']['genes'])<=6 and len(x['b']['genes'])<=7),crosses[0])
m=next((x for x in mutations if x['parent']['seed']==x['child']['seed'] and len(x['child']['cells'])==len(x['parent']['cells'])+1),mutations[0])
example=next(x for x in initial if 3<=len(x['genes'])<=5)
prefixes=[rec(Individual(example['seed'],tuple(example['genes'][:n]))) for n in range(len(example['genes'])+1)]
payload=dict(run_dir=str(run),metadata=json.loads(outputs['optimization_run_json'].read_text(encoding='utf-8')),initial=initial,leaders=leaders,crossover=c,mutation=m,example=example,prefixes=prefixes,first=best,history=result.history.to_dict('records'),territorial=pd.read_csv(run/'ranking_territorial.csv').to_dict('records'),total_cells=len(data['grid']),valid_cells=int(data['grid'].valid.sum()))
(OUT/'evidence.json').write_text(json.dumps(payload,ensure_ascii=False,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
selected=set()
for p in initial+leaders+prefixes+[c['a'],c['b'],c['child'],m['parent'],m['child']]:selected.update(p['cells'])
data['grid'].loc[data['grid'].cell_id.isin(selected)].to_file(OUT/'cells.geojson',driver='GeoJSON')
data['region'].to_crs(data['grid'].crs).to_file(OUT/'region.geojson',driver='GeoJSON')
print(json.dumps(dict(run=str(run),best=best,cross=c,mutation=m),ensure_ascii=False))
repo.engine.dispose()
