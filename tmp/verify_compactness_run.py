import json, math, unittest
from pathlib import Path
import numpy as np
import pandas as pd
import shapely
from src.config.settings import FitnessWeights
from src.optimization.fitness import compute_fitness

root = Path(__file__).resolve().parents[1]
run = root / 'results/spatial/run-20261007T003424-8b60c1ab'
meta = json.loads((run/'optimization_run.json').read_text(encoding='utf-8'))
frame = pd.read_csv(run/'candidates.csv')
geometry = shapely.from_wkt(frame.geometry_wkt.to_numpy())
perimeter = shapely.length(geometry)
area = shapely.area(geometry)
assert np.allclose(frame.park_perimeter_m, perimeter, rtol=1e-10, atol=1e-6)
assert np.allclose(frame.compactness_score, 4*math.pi*area/perimeter**2, rtol=1e-10, atol=1e-10)
weights = FitnessWeights.model_validate(meta['configuration']['fitness'])
assert np.allclose(frame.fitness, compute_fitness(frame, weights), atol=1e-12)
assert frame.compactness_score.between(0, 1).all()
assert frame.installed_power_mw.le(80).all()
first = frame.iloc[0]
print(json.dumps({'verified_candidates':len(frame), 'seed':meta['random_seed'],
                  'generations':meta['configuration']['genetic_algorithm']['generations'],
                  'winner':{k:float(first[k]) for k in ('installed_power_mw','park_perimeter_m','compactness_score','fitness')},
                  'test_count':unittest.TestLoader().discover(str(root/'tests')).countTestCases()}, indent=2))
