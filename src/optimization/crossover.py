"""Sequence crossover: each child keeps the seed associated with its prefix."""
from src.optimization.spatial import Individual


def crossover_pair(a, b, rng):
    cut_a = int(rng.integers(len(a.growth_genes) + 1))
    cut_b = int(rng.integers(len(b.growth_genes) + 1))
    return (Individual(a.seed_cell_id, a.growth_genes[:cut_a] + b.growth_genes[cut_b:]),
            Individual(b.seed_cell_id, b.growth_genes[:cut_b] + a.growth_genes[cut_a:]))


def competitive_crossover_pair(a, b, rng, evaluator):
    """Try up to three homologous cuts; each child competes with its own parent.

    Remove neutral skipped/unprocessed instructions before exchanging suffixes.
    Fitness cannot decrease here; subsequent mutation or duplicate replacement
    can still replace the accepted child. Tied, different parks allow exploration.
    """
    parents = (a, b)
    parks = [evaluator.evaluate(parent) for parent in parents]
    compact = [Individual(parent.seed_cell_id, tuple(parent.growth_genes[i] for i in park.accepted_gene_indices))
               for parent, park in zip(parents, parks)]
    best = list(compact)
    best_parks = list(parks)
    positions = min(len(parent.growth_genes) for parent in compact) + 1
    cuts = rng.choice(positions, size=min(3, positions), replace=False)
    for cut in cuts:
        for index in (0, 1):
            own, donor = compact[index], compact[1 - index]
            child = Individual(own.seed_cell_id, own.growth_genes[:cut] + donor.growth_genes[cut:])
            park = evaluator.evaluate(child)
            fitness, previous = park.metrics['fitness'], best_parks[index].metrics['fitness']
            if fitness > previous or (fitness == previous and park.cell_ids != best_parks[index].cell_ids):
                best[index] = Individual(child.seed_cell_id, tuple(child.growth_genes[i] for i in park.accepted_gene_indices))
                best_parks[index] = park
    return tuple(best)
