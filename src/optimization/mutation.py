"""Equally likely applicable mutations; immutable parents, no geometry repair."""
from src.optimization.spatial import Individual
import math


def random_gene(rng):
    return int(rng.integers(0, 2**31))


def mutate_individual(individual, seed_ids, rng):
    genes = list(individual.growth_genes)
    operations = ['append', 'seed'] + (['change', 'delete'] if genes else [])
    operation = rng.choice(operations)
    seed = individual.seed_cell_id
    if operation == 'append':
        genes.append(random_gene(rng))
    elif operation == 'delete':
        genes.pop()
    elif operation == 'change':
        genes[int(rng.integers(len(genes)))] = random_gene(rng)
    else:
        seed = int(rng.choice(seed_ids))
    return Individual(seed, tuple(genes))


def mutate_effectively(individual, evaluator, rng, max_attempts=4):
    """Retry bounded phenotype changes; preserve the original when none succeeds."""
    original = evaluator.evaluate(individual)
    selected = set(original.cell_ids)
    frontier = set().union(*(set(evaluator.neighbors.get(cid, ())) for cid in selected))
    frontier = sorted((frontier & evaluator.positions.keys()) - selected, key=evaluator.positions.__getitem__)
    fitting = [index for index, cid in enumerate(frontier)
               if math.fsum(evaluator.area[evaluator.positions[c]] for c in selected | {cid})
               * evaluator.config.pv_power_density_mw_per_km2 <= evaluator.config.max_connection_capacity_mw]
    operations = (['append'] if fitting else []) + (['delete', 'change'] if original.accepted_gene_indices else [])
    if len(evaluator.seed_ids) > 1:
        operations.append('seed')
    if not operations:
        return individual, 0, False
    for attempt in range(1, max_attempts + 1):
        operation = rng.choice(operations)
        genes, seed = list(individual.growth_genes), individual.seed_cell_id
        if operation == 'append':
            genes.append(int(rng.choice(fitting)))
        elif operation == 'delete':
            genes = genes[:original.accepted_gene_indices[-1]]
        elif operation == 'change':
            genes[int(rng.choice(original.accepted_gene_indices))] = random_gene(rng)
        else:
            seed = int(rng.choice(evaluator.seed_ids))
        child = Individual(seed, tuple(genes))
        if evaluator.evaluate(child).cell_ids != original.cell_ids:
            return child, attempt, True
    return individual, max_attempts, False
