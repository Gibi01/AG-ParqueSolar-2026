"""Analyze paired 100/150-generation experiments without changing the GA."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tasks.analyze_crossover import common_budget_scores, difference_statistics
from tasks.compare_crossover import paired_results


ROOT = Path('results/experiments')
SEEDS = list(range(301, 311))
THRESHOLDS = (0.70, 0.72)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    output = ROOT / 'crossover-100-150-comparacion'
    output.mkdir(exist_ok=True)
    prior_path = ROOT / 'crossover-competitivo-validacion'
    prior_manifest = json.loads((prior_path / 'manifest.json').read_text(encoding='utf-8'))
    prior_runs = pd.read_csv(prior_path / 'runs.csv').set_index(['seed', 'variant'])
    prior_history = pd.read_csv(prior_path / 'histories.csv')
    results, runs_all, hits_all = {}, [], []
    report = ['# Crossover competitivo: 100 y 150 generaciones', '',
        '40 corridas nuevas: 10 semillas (301–310) × 2 variantes × 2 presupuestos. '
        'Crossover actual competitivo 0,75 frente a 0; población 50, mutación 0,20, elitismo 2, torneo 3. '
        'Mismo dataset local y mismos hashes de población inicial por semilla. Condiciones ejecutadas secuencialmente.', '',
        'Diseño previo: tasks/crossover-short-runs/plan.md. Las semillas ya se usaron en el estudio anterior; '
        'este es un análisis exploratorio, no una validación independiente nueva. '
        '100 y 150 generaciones son puntos dependientes de las mismas trayectorias; no se suman como 20 semillas.', '']
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout='constrained')
    colors = {'con_cruce': '#247b45', 'sin_cruce': '#d46c22'}
    labels = {'con_cruce': 'Con crossover', 'sin_cruce': 'Sin crossover'}
    for generations, ax in zip((100, 150), axes):
        path = ROOT / f'crossover-competitivo-{generations}gen'
        manifest = json.loads((path / 'manifest.json').read_text(encoding='utf-8'))
        assert manifest['status'] == 'complete' and manifest['completed_runs'] == 20
        assert manifest['seeds'] == SEEDS and manifest['generations'] == generations
        assert manifest['dataset_id'] == prior_manifest['dataset_id']
        assert manifest['crossover_operator'] == 'competitive'
        for module, digest in prior_manifest['code_sha256'].items():
            assert manifest['code_sha256'][module] == digest, module
        runs = pd.read_csv(path / 'runs.csv')
        histories = pd.read_csv(path / 'histories.csv')
        assert len(histories) == 20 * (generations + 1)
        assert runs.groupby('seed').initial_population_sha256.nunique().eq(1).all()
        for (seed, variant), frame in histories.groupby(['seed', 'variant']):
            expected = prior_history.loc[(prior_history.seed == seed) &
                (prior_history.variant == variant) & (prior_history.generation <= generations)]
            assert frame.generation.tolist() == list(range(generations + 1))
            pd.testing.assert_frame_equal(frame.drop(columns='elapsed_seconds').reset_index(drop=True),
                expected.drop(columns='elapsed_seconds').reset_index(drop=True), check_exact=True)
            row = runs.loc[(runs.seed == seed) & (runs.variant == variant)].iloc[0]
            assert row.initial_population_sha256 == prior_runs.loc[(seed, variant), 'initial_population_sha256']
            assert np.isclose(row.best_fitness, frame.iloc[-1].best_historical_fitness, rtol=0, atol=1e-14)
        pairs = paired_results(runs)
        pairs.to_csv(output / f'paired_{generations}.csv', index=False)
        summary = runs.groupby('variant').agg(mean=('best_fitness', 'mean'),
            std=('best_fitness', 'std'), seconds=('seconds', 'mean'),
            requests=('evaluation_requests', 'mean'), decoded=('decoded_individuals', 'mean'))
        summary.to_csv(output / f'summary_{generations}.csv')
        stats = difference_statistics(pairs.delta)
        values = {'fitness': stats, 'summary': summary.to_dict(orient='index'), 'common_budgets': {}}
        for metric in ('evaluation_requests', 'decoded_individuals'):
            budget, scores = common_budget_scores(histories, metric)
            comparison = difference_statistics(paired_results(scores).delta)
            scores.to_csv(output / f'{metric}_{generations}.csv', index=False)
            values['common_budgets'][metric] = {'budget': budget, **comparison}
        hits = []
        for (seed, variant), frame in histories.groupby(['seed', 'variant']):
            for threshold in THRESHOLDS:
                reached = frame.loc[frame.best_historical_fitness >= threshold].sort_values('generation')
                first = reached.iloc[0] if len(reached) else None
                hits.append(dict(generations=generations, seed=seed, variant=variant,
                    threshold=threshold, reached=first is not None,
                    first_generation=int(first.generation) if first is not None else None,
                    evaluation_requests=int(first.evaluation_requests) if first is not None else None,
                    decoded_individuals=int(first.decoded_individuals) if first is not None else None))
        hit_frame = pd.DataFrame(hits)
        hits_all.append(hit_frame)
        threshold_values = []
        for (threshold, variant), frame in hit_frame.groupby(['threshold', 'variant']):
            threshold_values.append(dict(threshold=threshold, variant=variant,
                reached=int(frame.reached.sum()), total=len(frame),
                median_generation_among_reached=float(frame.first_generation.median())
                    if frame.reached.any() else None))
        values['thresholds'] = threshold_values
        results[str(generations)] = values
        runs_all.append(runs.assign(generations=generations))
        low, high = stats['bootstrap_95_ci']
        report += [f'## {generations} generaciones', '',
            '| Variante | Fitness medio ± desvío | Segundos medios | Solicitudes medias | Decodificaciones medias |',
            '|---|---:|---:|---:|---:|']
        for variant in colors:
            row = summary.loc[variant]
            report.append(f'| {labels[variant]} | {row["mean"]:.6f} ± {row["std"]:.6f} | '
                f'{row.seconds:.2f} | {row.requests:.0f} | {row.decoded:.0f} |')
        report += ['', f'Diferencia pareada con − sin: {stats["mean_delta"]:+.6f}; '
            f'IC bootstrap 95 % [{low:+.6f}, {high:+.6f}]; '
            f'victorias {stats["crossover_wins"]}/10, derrotas {stats["no_crossover_wins"]}/10, '
            f'empates {stats["ties"]}/10; p bilateral por signos {stats["sign_flip_p_two_sided"]:.4f}.', '',
            '| Presupuesto común | Límite | Diferencia media con − sin | IC 95 % | Victorias |',
            '|---|---:|---:|---:|---:|']
        for metric, comp in values['common_budgets'].items():
            lo, hi = comp['bootstrap_95_ci']
            report.append(f'| {metric} | {comp["budget"]} | {comp["mean_delta"]:+.6f} | '
                f'[{lo:+.6f}, {hi:+.6f}] | {comp["crossover_wins"]}/10 |')
        report += ['', '| Umbral | Variante | Corridas que lo alcanzan | Mediana generación entre las que lo alcanzan |',
            '|---|---|---:|---:|']
        for row in threshold_values:
            report.append(f'| {row["threshold"]:.2f} | {labels[row["variant"]]} | {row["reached"]}/10 | '
                f'{row["median_generation_among_reached"]} |')
        report.append('')
        for variant in colors:
            frame = histories.loc[histories.variant == variant].pivot(index='generation', columns='seed', values='best_historical_fitness')
            ax.plot(frame.index, frame.mean(axis=1), color=colors[variant], label=labels[variant])
        ax.set_title(f'{generations} generaciones · 10 semillas')
        ax.set_xlabel('Generación'); ax.set_ylabel('Mejor fitness histórico promedio')
        ax.grid(alpha=.2); ax.legend(); ax.set_ylim(.645, .73)
    report += ['## Resultado observado', '']
    for generations, values in results.items():
        stats = values['fitness']
        lo, hi = stats['bootstrap_95_ci']
        certainty = ('El intervalo incluye cero; la diferencia no es concluyente en esta muestra.'
            if lo <= 0 <= hi else 'El intervalo excluye cero en este contraste exploratorio.')
        report.append(f'A {generations} generaciones, diferencia media con − sin '
            f'{stats["mean_delta"]:+.6f}, con {stats["crossover_wins"]}/10 victorias. {certainty}')
        report.append('')
    report += ['A 100 generaciones no se observa ventaja media del crossover. A 150 aparece una mejora '
        'media y menor dispersión, pero el intervalo pareado incluye cero. El umbral 0,72 lo alcanzan '
        '7/10 corridas con cruce y 5/10 sin cruce a 150; esto indica mayor cobertura de buenos puntajes '
        'en esta muestra, sin demostrar aceleración universal.', '',
        'Las diferencias medias con presupuestos comunes de solicitudes y de decodificaciones son '
        'negativas en ambos horizontes. Por tanto, no se demuestra una mejora de eficiencia. '
        'Algunos intervalos bootstrap de presupuesto excluyen cero a favor de no cruzar, pero '
        'las pruebas bilaterales por signos tienen p > 0,05; con diez pares y múltiples contrastes '
        'no se presenta esto como una superioridad estadística confirmada de una variante.', '',
        '## Interpretación y límites', '',
        'Un fitness mayor a igual generación muestra ventaja por iteración; no prueba menor costo computacional. '
        'El crossover competitivo prueba hasta tres cortes y evalúa propuestas: consume más evaluaciones por generación.',
        'Los umbrales 0,70 y 0,72 se fijaron antes de estas corridas para describir la convergencia. '
        'No representan viabilidad eléctrica/económica ni un óptimo conocido. Las medianas excluyen las corridas '
        'que no alcanzaron el umbral: deben leerse junto al número de alcanzados, sin interpretar esas medianas como comparación pareada.',
        'Presupuestos comunes: último registro de generación que no supera el menor presupuesto final entre las 20 corridas; '
        'son aproximaciones conservadoras con distintas fracciones sobrantes. Solicitudes incluyen caché; '
        'decodificaciones cuentan genotipos evaluados sin caché. Tiempos medidos secuencialmente, sujetos a carga del equipo y cachés del sistema.',
        'Se verificó que cada trayectoria nueva coincide exactamente con el prefijo de la corrida previa de 200 generaciones, '
        'incluyendo fitness y conteos: cambiar el límite no cambia el camino anterior a ese límite.',
        'Bootstrap pareado de 20.000 muestras con semilla fija; prueba exacta de cambio de signos asumiendo '
        'simetría/intercambiabilidad bajo la hipótesis nula. Contrastes exploratorios sin corrección por multiplicidad.', '',
        '![Evolución media](convergencia.png)', '', '## Reproducir', '', '```powershell',
        r'.\.venv\Scripts\python.exe -m tasks.compare_crossover --operator competitive --generations 100 --seeds 301 302 303 304 305 306 307 308 309 310 --output results/experiments/crossover-competitivo-100gen',
        r'.\.venv\Scripts\python.exe -m tasks.compare_crossover --operator competitive --generations 150 --seeds 301 302 303 304 305 306 307 308 309 310 --output results/experiments/crossover-competitivo-150gen',
        r'.\.venv\Scripts\python.exe -m tasks.analyze_short_crossover', '```', '',
        'Los directorios de corridas deben ser nuevos. El análisis requiere también el experimento previo de 200 generaciones.']
    fig.savefig(output / 'convergencia.png', dpi=160)
    plt.close(fig)
    pd.concat(runs_all, ignore_index=True).to_csv(output / 'runs.csv', index=False)
    pd.concat(hits_all, ignore_index=True).to_csv(output / 'thresholds.csv', index=False)
    (output / 'analysis.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'informe.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
