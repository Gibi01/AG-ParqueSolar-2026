import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from src.config.settings import load_settings
from src.database.spatial import SpatialRepository
from src.optimization.spatial import ParkEvaluator,Individual
from src.optimization.initialization import TerritorialSampler
import src.optimization.genetic_algorithm as ga
from tools.reporting.current_run import RUN

out=Path(__file__).parent
settings=load_settings('config.yaml')
repo=SpatialRepository(settings.paths.database)
dataset=repo.load_dataset(RUN['metadata']['dataset']['config_signature'])
e=ParkEvaluator(dataset['grid'],dataset['neighbors'],dataset['lines'],dataset['transformers'],settings.park,settings.fitness)
leaders=[]; events=[]; gen=[0]
def record(i):
 p=e.evaluate(i)
 coords=[dict(cell_id=int(c),row=int(e.grid.iloc[e.positions[c]]['row']),column=int(e.grid.iloc[e.positions[c]]['column'])) for c in p.cell_ids]
 return dict(seed=i.seed_cell_id,genes=list(i.growth_genes),cells=list(p.cell_ids),coordinates=coords,accepted=list(p.accepted_gene_indices),skipped=list(p.skipped_gene_indices),unprocessed=p.unprocessed_genes,**p.metrics)
orig_select=ga.tournament_selection; orig_cross=ga.crossover_pair; orig_mut=ga.mutate_effectively
def selection(pop,fitness,*args):
 leaders.append(dict(generation=gen[0],**record(pop[int(np.argmax(fitness))])))
 gen[0]+=1
 return orig_select(pop,fitness,*args)
def cross(a,b,rng):
 ca,cb=orig_cross(a,b,rng)
 if len(events)<100 and 2<=len(a.growth_genes)<=8 and 2<=len(b.growth_genes)<=8:
  events.append(dict(kind='cross',generation=gen[0],a=record(a),b=record(b),child=record(ca)))
 return ca,cb
mutations=[]
def mutation(a,evaluator,rng,attempts):
 child,n,changed=orig_mut(a,evaluator,rng,attempts)
 if changed and len(mutations)<100:
  mutations.append(dict(generation=gen[0],parent=record(a),child=record(child),attempts=n))
 return child,n,changed
ga.tournament_selection=selection;ga.crossover_pair=cross;ga.mutate_effectively=mutation
random_ind=TerritorialSampler(e,np.random.default_rng(42),50).individual()
result=ga.GeneticAlgorithm(e,settings.genetic_algorithm).run()
final=RUN['first']
final_ind=Individual(int(final.seed_cell_id),tuple(json.loads(final.growth_genes)))
leaders.append(dict(generation=200,**record(final_ind)))
assert abs(result.history.iloc[-1].best_fitness-RUN['history'].iloc[-1].best_fitness)<1e-10
example=record(random_ind)
# Use the actual decoder on every prefix of this sampled chromosome.
prefixes=[record(Individual(random_ind.seed_cell_id,random_ind.growth_genes[:n])) for n in range(min(4,len(random_ind.growth_genes))+1)]
mutation_example=next((m for m in mutations if m['parent']['seed']==m['child']['seed'] and len(m['child']['cells'])==len(m['parent']['cells'])+1 and m['child']['fitness']>m['parent']['fitness']),mutations[0])
cross_example=next(x for x in events if x['a']['genes']!=x['child']['genes'] and x['child']['genes'])
random_ind=Individual(cross_example['a']['seed'],tuple(cross_example['a']['genes']))
example=record(random_ind)
prefixes=[record(Individual(random_ind.seed_cell_id,random_ind.growth_genes[:n])) for n in range(len(random_ind.growth_genes)+1)]
trace=[]
for n,gene in enumerate(random_ind.growth_genes):
 selected=set(prefixes[n]['cells'])
 frontier=set().union(*(set(e.neighbors.get(cid,())) for cid in selected))-selected
 ordered=sorted(frontier & e.positions.keys(),key=e.positions.__getitem__)
 trace.append(dict(gene=int(gene),frontier=ordered,index=int(gene)%len(ordered),chosen=ordered[int(gene)%len(ordered)]))
region=dataset['region'].geometry.iloc[0].simplify(.015,preserve_topology=True)
poly=max(region.geoms,key=lambda g:g.area) if region.geom_type=='MultiPolygon' else region
boundary=list(poly.exterior.coords)
payload=dict(random=example,prefixes=prefixes,leaders=[leaders[g] for g in [0,1,5,20,100,200]],mutation=mutation_example,crossover=cross_example,history=result.history.to_dict('records'),first=record(final_ind),stations=dataset['transformers'].drop(columns='geometry').to_dict('records'),bounds=e.bounds,total_cells=RUN['total_cells'],valid_cells=RUN['valid_cells'],urban_excluded=RUN['urban_excluded'],dataset_id=dataset['dataset_id'],run_dir=str(RUN['run_dir']),config=RUN['configuration'])
payload.update(trace=trace,boundary=boundary,territorial=RUN['territorial'][['rank','latitude','longitude','fitness','installed_power_mw','station_name']].to_dict('records'))
(out/'evidence.json').write_text(json.dumps(payload,ensure_ascii=False,default=lambda x:int(x) if isinstance(x,np.integer) else float(x)),encoding='utf-8')
print(json.dumps({k:payload[k] for k in ['random','mutation','crossover','stations']},ensure_ascii=False))
