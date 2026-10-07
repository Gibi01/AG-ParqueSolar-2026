import sys,json,copy,logging
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import yaml
import src.main as main
import src.optimization.genetic_algorithm as ga
from src.config.settings import load_settings
from src.database.spatial import SpatialRepository
from src.optimization.spatial import Individual

OUT=ROOT/'tmp/presentation_build/defensa_nueva'
OUT.mkdir(parents=True,exist_ok=True)
cfg=yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8'))
cfg['genetic_algorithm']['random_seed']=20261006
config_path=OUT/'config_corrida.yaml'
config_path.write_text(yaml.safe_dump(cfg,sort_keys=False,allow_unicode=True),encoding='utf-8')
settings=load_settings(config_path)
main.setup_logging(settings)
evaluator=None
generation=0
leaders=[]; crosses=[]; mutations=[]; initial=[]
def record(ind):
    p=evaluator.evaluate(ind)
    coords=[dict(cell_id=int(c),row=int(evaluator.grid.iloc[evaluator.positions[c]]['row']),column=int(evaluator.grid.iloc[evaluator.positions[c]]['column'])) for c in p.cell_ids]
    return dict(seed=ind.seed_cell_id,genes=list(ind.growth_genes),cells=list(p.cell_ids),coordinates=coords,accepted=list(p.accepted_gene_indices),skipped=list(p.skipped_gene_indices),**p.metrics)
orig_select=ga.tournament_selection;orig_cross=ga.crossover_pair;orig_mut=ga.mutate_effectively
def select(pop,fitness,*args):
    global generation
    if generation==0:initial.extend(record(i) for i in pop)
    if generation in [0,1,5,20,50,100]:leaders.append(dict(generation=generation,**record(pop[int(np.argmax(fitness))])))
    generation+=1
    return orig_select(pop,fitness,*args)
def cross(a,b,rng):
    clone=np.random.default_rng();clone.bit_generator.state=copy.deepcopy(rng.bit_generator.state)
    cut_a=int(clone.integers(len(a.growth_genes)+1));cut_b=int(clone.integers(len(b.growth_genes)+1))
    ca,cb=orig_cross(a,b,rng)
    if generation<=3 and len(crosses)<100 and 2<=len(a.growth_genes)<=7 and 2<=len(b.growth_genes)<=7 and 0<cut_a<len(a.growth_genes) and 0<cut_b<len(b.growth_genes):
        crosses.append(dict(generation=generation,cut_a=cut_a,cut_b=cut_b,a=record(a),b=record(b),child=record(ca),other=record(cb)))
    return ca,cb
def mutation(a,e,rng,attempts):
    child,n,changed=orig_mut(a,e,rng,attempts)
    if changed and len(mutations)<120:mutations.append(dict(generation=generation,parent=record(a),child=record(child),attempts=n))
    return child,n,changed
ga.tournament_selection=select;ga.crossover_pair=cross;ga.mutate_effectively=mutation
class TracedGA(ga.GeneticAlgorithm):
    def run(self,*args,**kwargs):
        global evaluator
        evaluator=self.evaluator
        return super().run(*args,**kwargs)
main.GeneticAlgorithm=TracedGA
repo=SpatialRepository(settings.paths.database)
result=main.cmd_optimize(settings,repo)
runs=[p for p in settings.paths.results.glob('run-*') if (p/'optimization_run.json').exists()]
run_dir=max(runs,key=lambda p:p.name)
metadata=json.loads((run_dir/'optimization_run.json').read_text(encoding='utf-8'))
assert metadata['random_seed']==20261006
best=result.top5.iloc[0]
final=record(Individual(int(best.seed_cell_id),tuple(json.loads(best.growth_genes))))
leaders.append(dict(generation=200,**final))
c=next((c for c in crosses if c['child']['genes']!=c['a']['genes'] and c['child']['cells']!=c['a']['cells']),crosses[0])
m=next((m for m in mutations if m['parent']['seed']==m['child']['seed'] and len(m['child']['cells'])==len(m['parent']['cells'])+1),mutations[0])
example=c['a'];ind=Individual(example['seed'],tuple(example['genes']))
prefixes=[record(Individual(ind.seed_cell_id,ind.growth_genes[:n])) for n in range(len(ind.growth_genes)+1)]
dataset=repo.load_dataset(metadata['dataset']['config_signature'])
payload=dict(run_dir=str(run_dir),metadata=metadata,initial=initial,leaders=leaders,crossover=c,mutation=m,example=example,prefixes=prefixes,first=final,history=result.history.to_dict('records'),territorial=json.loads((run_dir/'ranking_territorial.csv').read_text()) if False else [],total_cells=len(dataset['grid']),valid_cells=int(dataset['grid'].valid.sum()),stations=dataset['transformers'].drop(columns='geometry').to_dict('records'))
import pandas as pd
payload['territorial']=pd.read_csv(run_dir/'ranking_territorial.csv').to_dict('records')
payload['region_geojson']=json.loads(dataset['region'].to_json())
selected=set(final['cells'])|set(example['cells'])|set(c['child']['cells'])|set(m['parent']['cells'])|set(m['child']['cells'])
for leader in leaders:selected.update(leader['cells'])
payload['selected_geojson']=json.loads(dataset['grid'].loc[dataset['grid'].cell_id.isin(selected)].to_crs(4326).to_json())
(OUT/'evidence.json').write_text(json.dumps(payload,ensure_ascii=False,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
print('EVIDENCE',OUT/'evidence.json')
print('FINAL',json.dumps(final,ensure_ascii=False))
