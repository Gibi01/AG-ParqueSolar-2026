"""Replay reference AG once, observing evaluated parks without altering decisions."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.config.settings import Settings
from src.database.spatial import SpatialRepository
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.optimization.spatial import ParkEvaluator
from tasks.compare_search_quality import export_candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    out = args.output
    manifest = json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    reference_path = Path(manifest['reference'])
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    settings = Settings.model_validate(reference['configuration'])
    repo = SpatialRepository(settings.paths.database)
    try:
        data = repo.load_dataset(reference['dataset']['config_signature'])
        assert data['dataset_id']==reference['dataset_id']
        ev = ParkEvaluator(data['grid'],data['neighbors'],data['lines'],data['transformers'],settings.park,settings.fitness)
        observed = {}
        original = ev.evaluate
        def trace(individual):
            park = original(individual)
            observed[park.cell_ids] = park
            return park
        trace.cache_info = original.cache_info
        ev.evaluate = trace
        try:
            ga = GeneticAlgorithm(ev,settings.genetic_algorithm).run()
        finally:
            ev.evaluate = original
        current = pd.read_csv(reference_path.parent/'ranking.csv')
        assert ga.top5.cell_ids.tolist()==current.cell_ids.tolist()
        assert np.allclose(ga.top5.fitness,current.fitness,atol=1e-12)
        original_history=pd.read_csv(reference_path.parent/'history.csv')
        assert ga.history.iloc[-1].decoded_individuals==original_history.iloc[-1].decoded_individuals
        frame = pd.DataFrame([dict(cell_ids=json.dumps(p.cell_ids),**p.metrics) for p in observed.values()])
        _, observed_top = export_candidates(frame,ev,out/'audit_archive/all_evaluated')
        rectangles = pd.read_csv(out/'rectangles/candidates.csv')
        rectangles['candidate_source']='rectangle'
        candidates=ga.candidates.copy()
        candidates['candidate_source']='ag_archive'
        merged=pd.concat([candidates,rectangles],ignore_index=True).sort_values('fitness',ascending=False).drop_duplicates('cell_ids')
        _, merged_top = export_candidates(merged,ev,out/'audit_archive/ag_plus_rectangles')
        reported=pd.read_csv(reference_path.parent/'ranking_territorial.csv')
        comparison=pd.DataFrame({'rank':range(1,6),'reported_ag':reported.fitness.to_numpy(),
                                 'all_evaluated_ag':observed_top.fitness.to_numpy(),
                                 'ag_plus_rectangles':merged_top.fitness.to_numpy()})
        comparison.to_csv(out/'audit_archive/comparison.csv',index=False)
        info=dict(seed=settings.genetic_algorithm.random_seed,unmodified_replay=True,
                  replayed_top5_matches=True,evaluation_budget_matches=True,
                  evaluated_distinct_parks=len(observed),retained_parks=len(ga.candidates),
                  original_top5_mean=float(reported.fitness.mean()),
                  all_evaluated_top5_mean=float(observed_top.fitness.mean()),
                  ag_plus_rectangles_top5_mean=float(merged_top.fitness.mean()),
                  code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  interpretation='All evaluated includes internal crossover and mutation probes, not only retained populations; no new search moves or changed RNG.')
        (out/'audit_archive/analysis.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(info,ensure_ascii=False,indent=2))
        print(comparison.to_string(index=False))
    finally:
        repo.engine.dispose()


if __name__=='__main__':
    main()
