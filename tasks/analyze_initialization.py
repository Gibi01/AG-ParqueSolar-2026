"""Analyze initialization × crossover factorial runs and their interaction."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tasks.analyze_crossover import common_budget_scores
from tasks.compare_crossover import paired_results
from tasks.compare_initialization import fast_difference_statistics


def factorial_differences(rows):
    pairs = {}
    for method in ('territorial', 'uniforme'):
        pairs[method] = paired_results(rows.loc[rows.initialization == method]).set_index('seed')
    if not pairs['territorial'].index.equals(pairs['uniforme'].index):
        raise ValueError('Different seed sets across initialization methods.')
    return pd.DataFrame(dict(territorial=pairs['territorial'].delta,
        uniforme=pairs['uniforme'].delta)).assign(interaction=lambda frame: frame.uniforme - frame.territorial)


def contrasts(rows):
    differences = factorial_differences(rows)
    return {name: fast_difference_statistics(differences[name]) for name in differences.columns}, differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('results/experiments/initialization-crossover-20-pares'))
    args = parser.parse_args()
    root = args.input
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status'] == 'complete' and manifest['completed_runs'] == 80
    assert hashlib.sha256(Path('tasks/compare_initialization.py').read_bytes()).hexdigest() == manifest['runner_sha256']
    assert len(manifest['seeds']) == len(set(manifest['seeds'])) == 20
    generations = manifest['generations']
    runs_all, histories_all, mode_manifests = [], [], []
    for method in ('territorial', 'uniforme'):
        mode_manifest = json.loads((root / method / 'manifest.json').read_text(encoding='utf-8'))
        mode_manifests.append(mode_manifest)
        assert mode_manifest['status'] == 'complete' and mode_manifest['completed_runs'] == 40
        assert mode_manifest['dataset_id'] == manifest['dataset_id']
        assert mode_manifest['seeds'] == manifest['seeds']
        assert mode_manifest['generations'] == generations and mode_manifest['initialization'] == method
        runs = pd.read_csv(root / method / 'runs.csv').assign(initialization=method)
        histories = pd.read_csv(root / method / 'histories.csv').assign(initialization=method)
        assert len(runs) == 40 and len(histories) == 40 * (generations + 1)
        assert runs.groupby('seed').initial_population_sha256.nunique().eq(1).all()
        for seed, pair in histories.groupby('seed'):
            zero = pair.loc[pair.generation == 0].set_index('variant')
            assert len(zero) == 2
            columns = [c for c in zero.select_dtypes(include='number').columns if c != 'elapsed_seconds']
            np.testing.assert_allclose(zero.loc['con_cruce', columns].to_numpy(dtype=float),
                zero.loc['sin_cruce', columns].to_numpy(dtype=float), rtol=0, atol=0, equal_nan=True)
        for (seed, variant), frame in histories.groupby(['seed', 'variant']):
            assert frame.generation.tolist() == list(range(generations + 1))
            assert frame.population_size.eq(50).all()
            assert frame.best_historical_fitness.diff().dropna().ge(-1e-14).all()
            row = runs.loc[(runs.seed == seed) & (runs.variant == variant)].iloc[0]
            assert np.isclose(row.best_fitness, frame.iloc[-1].best_historical_fitness, rtol=0, atol=1e-14)
        runs_all.append(runs)
        histories_all.append(histories)
    assert mode_manifests[0]['code_sha256'] == mode_manifests[1]['code_sha256']
    for module, digest in mode_manifests[0]['code_sha256'].items():
        assert hashlib.sha256(Path(module).read_bytes()).hexdigest() == digest, module
    runs, histories = pd.concat(runs_all, ignore_index=True), pd.concat(histories_all, ignore_index=True)
    runs['condition'] = runs.initialization + '/' + runs.variant
    histories['condition'] = histories.initialization + '/' + histories.variant
    initial = pd.read_csv(root / 'initial_populations.csv')
    diversity = pd.read_csv(root / 'initial_diversity.csv')
    assert len(initial) == 2000 and len(diversity) == 40
    assert initial.groupby(['initialization', 'seed']).size().eq(50).all()
    for (method, seed), frame in initial.groupby(['initialization', 'seed']):
        payload = [(int(row.seed_cell_id), tuple(json.loads(row.growth_genes))) for row in frame.sort_values('slot').itertuples()]
        digest = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
        assert runs.loc[(runs.initialization == method) & (runs.seed == seed)].initial_population_sha256.eq(digest).all()
    output = root / 'analysis'
    output.mkdir(exist_ok=True)
    final_stats, differences = contrasts(runs)
    summary = runs.groupby(['initialization', 'variant']).agg(mean=('best_fitness', 'mean'),
        std=('best_fitness', 'std'), median=('best_fitness', 'median'), seconds=('seconds', 'mean'),
        requests=('evaluation_requests', 'mean'), decoded=('decoded_individuals', 'mean'))
    diversity_summary = diversity.groupby('initialization').mean(numeric_only=True).drop(columns='seed')
    result = dict(final=final_stats, summary={'/'.join(k): v for k, v in summary.to_dict(orient='index').items()},
        diversity=diversity_summary.to_dict(orient='index'), common_budgets={}, checkpoints={})
    for generation in (100, generations):
        scores = histories.loc[histories.generation == generation].rename(columns={'best_historical_fitness': 'checkpoint_fitness'})
        score_rows = scores[['seed', 'variant', 'initialization', 'checkpoint_fitness']].rename(columns={'checkpoint_fitness': 'best_fitness'})
        result['checkpoints'][str(generation)] = contrasts(score_rows)[0]
    for metric in ('evaluation_requests', 'decoded_individuals'):
        budget_history = histories.drop(columns='variant').rename(columns={'condition': 'variant'})
        budget, scores = common_budget_scores(budget_history, metric)
        scores[['initialization', 'variant']] = scores.variant.str.split('/', expand=True)
        values, deltas = contrasts(scores)
        result['common_budgets'][metric] = dict(budget=budget, contrasts=values)
        scores.to_csv(output / f'{metric}_scores.csv', index=False)
        deltas.to_csv(output / f'{metric}_paired.csv')
    hits = []
    for (method, variant, seed), frame in histories.groupby(['initialization', 'variant', 'seed']):
        for threshold in (.70, .72):
            reached = frame.loc[frame.best_historical_fitness >= threshold].sort_values('generation')
            hits.append(dict(initialization=method, variant=variant, seed=seed, threshold=threshold,
                reached=bool(len(reached)), first_generation=int(reached.iloc[0].generation) if len(reached) else None))
    hits = pd.DataFrame(hits)
    hit_summary = hits.groupby(['initialization', 'variant', 'threshold']).agg(reached=('reached', 'sum'),
        total=('reached', 'size'), median_generation_among_reached=('first_generation', 'median'))
    result['thresholds'] = [{**dict(zip(('initialization', 'variant', 'threshold'), key)), **value}
        for key, value in hit_summary.to_dict(orient='index').items()]
    for frame, name in ((runs, 'runs'), (histories, 'histories'), (differences, 'paired'),
        (summary, 'summary'), (diversity_summary, 'initial_diversity_summary'), (hits, 'thresholds')):
        frame.to_csv(output / f'{name}.csv', index=name in ('paired', 'summary', 'initial_diversity_summary'))
    labels = {'territorial/con_cruce': 'Sectores + cruce', 'territorial/sin_cruce': 'Sectores sin cruce',
        'uniforme/con_cruce': 'Aleatoria + cruce', 'uniforme/sin_cruce': 'Aleatoria sin cruce'}
    report = ['# Inicialización y aporte del crossover: 80 corridas', '',
        '20 semillas nuevas (501–520) × 2 inicializaciones × 2 variantes de crossover. '
        f'{generations} generaciones, población 50, crossover competitivo 0,75 frente a 0, '
        'mutación 0,20, elitismo 2 y torneo 3. Dataset y pesos guardados del experimento original '
        '(solar 0,4, líneas 0,1, estaciones 0,4, potencia 0,1; compactación 0).', '',
        '## Alcance de la intervención', '',
        'En la condición aleatoria, las 50 semillas iniciales se eligen uniformemente entre todas las celdas '
        'semilla válidas, con reemplazo. En la condición territorial se conserva el muestreo por sectores de 50 km. '
        'Los genes conservan su distribución aleatoria original. En ambas condiciones, los reemplazos de '
        'duplicados durante la búsqueda usan el muestreo territorial original; el archivo territorial también '
        'se conserva. Así se modifica exclusivamente la población inicial.', '',
        'Las poblaciones iniciales coinciden exactamente con/sin crossover dentro de cada método. '
        'Entre métodos son diferentes. Las 20 semillas se fijaron antes de observar resultados, '
        'en tasks/crossover-initialization/plan.md. El AG de producción no se modificó.', '',
        '## Resultados a igual generación', '',
        '| Condición | Fitness medio ± desvío | Mediana | Segundos medios | Solicitudes medias | Decodificaciones medias |',
        '|---|---:|---:|---:|---:|---:|']
    for key, row in summary.iterrows():
        report.append(f'| {labels["/".join(key)]} | {row["mean"]:.6f} ± {row["std"]:.6f} | '
            f'{row["median"]:.6f} | {row.seconds:.2f} | {row.requests:.0f} | {row.decoded:.0f} |')
    for title, values in [(f'{generations} generaciones (interacción principal)', final_stats)] + [
        (f'Presupuesto común: {v["budget"]} {metric}', v['contrasts']) for metric, v in result['common_budgets'].items()]:
        report += ['', f'## {title}', '', '| Contraste | Diferencia media | IC bootstrap 95 % | Diferencias positivas | p bilateral |',
            '|---|---:|---:|---:|---:|']
        for contrast, value in values.items():
            lo, hi = value['bootstrap_95_ci']
            description = {'territorial': 'Con−sin, sectores', 'uniforme': 'Con−sin, aleatoria',
                'interaction': 'Interacción: delta aleatoria−delta sectores'}[contrast]
            report.append(f'| {description} | {value["mean_delta"]:+.6f} | [{lo:+.6f}, {hi:+.6f}] | '
                f'{value["crossover_wins"]}/20 | {value["sign_flip_p_two_sided"]:.4f} |')
    report += ['', '## Diversidad de la población inicial', '',
        '| Método | Sectores 50 km ocupados | Semillas distintas | Parques distintos | Distancia media entre semillas (km) | Fitness inicial medio |',
        '|---|---:|---:|---:|---:|---:|']
    for method, row in diversity_summary.iterrows():
        report.append(f'| {method} | {row.occupied_sectors_50km:.2f} | {row.distinct_seed_cells:.2f} | '
            f'{row.distinct_initial_parks:.2f} | {row.mean_seed_distance_km:.2f} | {row.mean_initial_fitness:.6f} |')
    report += ['', '## Alcance de puntajes de referencia', '',
        '| Condición | Umbral | Corridas que llegan | Mediana generación entre las que llegan |',
        '|---|---:|---:|---:|']
    for key, row in hit_summary.iterrows():
        method, variant, threshold = key
        report.append(f'| {labels[method + "/" + variant]} | {threshold:.2f} | {int(row.reached)}/20 | '
            f'{row.median_generation_among_reached:.1f} |')
    interaction = final_stats['interaction']
    low, high = interaction['bootstrap_95_ci']
    report += ['', '## Interpretación', '',
        f'Cambiar a inicialización aleatoria modifica el aporte medio del crossover en '
        f'{interaction["mean_delta"]:+.6f} (interacción). IC 95 % [{low:+.6f}, {high:+.6f}]. '
        + ('El intervalo incluye cero: no se demuestra que eliminar los sectores aumente el aporte del cruce.'
           if low <= 0 <= high else
           ('El aporte del crossover es menor con inicialización aleatoria en este escenario; '
            'el intervalo excluye cero. Esto va en sentido contrario a la hipótesis de quitar sectores para potenciar el cruce.'
            if high < 0 else
            'El aporte del crossover es mayor con inicialización aleatoria en este escenario; el intervalo excluye cero.')),
        'La interacción compara el beneficio con−sin de cada método. Una mejora del fitness de una sola '
        'condición no prueba por sí sola que la inicialización potencie el crossover.',
        'El operador competitivo combina recombinación y selección de propuestas. Este diseño no separa '
        'esos componentes; una ventaja a igual generación puede deberse al mayor costo de evaluar alternativas.', '',
        '## Límites y verificación', '',
        '- Bootstrap pareado de 20.000 muestras, semilla fija; prueba exacta de cambio de signos '
        '(2^20 combinaciones), asumiendo simetría/intercambiabilidad bajo la hipótesis nula.',
        '- Interacción a 150 generaciones como contraste principal; demás contrastes exploratorios sin '
        'corrección por multiplicidad. Veinte pares pueden tener potencia insuficiente.',
        '- Presupuestos comunes a las cuatro condiciones: último checkpoint de generación que no supera '
        'el menor conteo final entre las 80 corridas. No son ejecuciones detenidas exactamente al mismo conteo; '
        'los sobrantes varían. Solicitudes incluyen caché; decodificaciones cuentan genotipos sin caché.',
        '- Los umbrales 0,70 y 0,72 son descriptivos y no representan viabilidad real. Medianas sólo entre '
        'corridas que llegan; deben leerse con los conteos de no alcanzados.',
        '- Misma configuración entre las cuatro condiciones, huellas de código iguales y sin cambios '
        'durante la ejecución; capacidad y contigüidad verificadas en todos los candidatos exportados.',
        '- Tiempos de corridas secuenciales, sujetos a carga del equipo y cachés. Datos y pesos del modelo '
        'limitan la generalización; no demuestra óptimo global ni viabilidad eléctrica/económica.', '',
        '![Comparación](comparacion.png)', '', '## Reproducir', '', '```powershell',
        r'.\.venv\Scripts\python.exe -m tasks.compare_initialization --output results/experiments/initialization-crossover-20-pares',
        r'.\.venv\Scripts\python.exe -m tasks.analyze_initialization', '```', '',
        'El directorio de corridas debe ser nuevo; se conservan manifiestos, CSV y GeoJSON por condición.']
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors = ['#166534', '#ca8a04', '#2563eb', '#dc2626']
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), layout='constrained')
    for color, condition in zip(colors, labels):
        frame = histories.loc[histories.condition == condition].pivot(index='generation', columns='seed', values='best_historical_fitness')
        axes[0, 0].plot(frame.index, frame.mean(axis=1), label=labels[condition], color=color)
    axes[0, 0].set_title('Evolución media · 20 semillas por condición')
    axes[0, 0].set_xlabel('Generación'); axes[0, 0].set_ylabel('Mejor fitness histórico medio')
    axes[0, 0].legend(fontsize=9); axes[0, 0].grid(alpha=.2)
    x = np.arange(len(differences))
    axes[0, 1].plot(x, differences.territorial, 'o-', label='Inicialización por sectores', color=colors[0])
    axes[0, 1].plot(x, differences.uniforme, 's-', label='Inicialización aleatoria', color=colors[2])
    axes[0, 1].axhline(0, color='black', linewidth=.8)
    axes[0, 1].set_xticks(x[::2], differences.index.astype(str)[::2])
    axes[0, 1].set_xlabel('Semilla'); axes[0, 1].set_ylabel('Fitness con cruce − sin cruce')
    axes[0, 1].set_title('Aporte pareado del crossover · 150 generaciones')
    axes[0, 1].legend(fontsize=9); axes[0, 1].grid(alpha=.2)
    axes[1, 0].bar(['Por sectores', 'Aleatoria'], diversity_summary.occupied_sectors_50km,
        color=[colors[0], colors[2]])
    axes[1, 0].set_ylim(0, 55); axes[1, 0].set_ylabel('Sectores de 50 km ocupados (media)')
    axes[1, 0].set_title('Cobertura territorial de las 50 semillas iniciales')
    for i, value in enumerate(diversity_summary.occupied_sectors_50km):
        axes[1, 0].text(i, value + 1, f'{value:.1f}', ha='center')
    box_data = [runs.loc[runs.condition == condition, 'best_fitness'].to_numpy() for condition in labels]
    boxes = axes[1, 1].boxplot(box_data, tick_labels=list(labels.values()), patch_artist=True)
    for box, color in zip(boxes['boxes'], colors):
        box.set_facecolor(color); box.set_alpha(.35)
    axes[1, 1].tick_params(axis='x', labelrotation=15)
    axes[1, 1].set_ylabel('Fitness final'); axes[1, 1].set_title('Distribución de resultados finales')
    axes[1, 1].grid(axis='y', alpha=.2)
    fig.savefig(output / 'comparacion.png', dpi=160)
    plt.close(fig)
    (output / 'informe.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    (output / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
