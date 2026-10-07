"""Compare fixed competitive crossover against the old operator and no crossover."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tasks.analyze_crossover import common_budget_scores, difference_statistics


ROOT = Path('results/experiments')
STAGES = {
    'desarrollo': (ROOT / 'crossover-20261006-10-pares', ROOT / 'crossover-competitivo-desarrollo'),
    'validacion': (ROOT / 'crossover-anterior-validacion', ROOT / 'crossover-competitivo-validacion'),
}


def collect(old_path, new_path):
    old_manifest = json.loads((old_path / 'manifest.json').read_text(encoding='utf-8'))
    new_manifest = json.loads((new_path / 'manifest.json').read_text(encoding='utf-8'))
    if old_manifest['status'] != 'complete' or new_manifest['status'] != 'complete':
        raise ValueError('Incomplete experiment.')
    if old_manifest['dataset_id'] != new_manifest['dataset_id'] or old_manifest['seeds'] != new_manifest['seeds']:
        raise ValueError('Different datasets or seeds.')
    old, new = pd.read_csv(old_path / 'runs.csv'), pd.read_csv(new_path / 'runs.csv')
    old_zero = old.loc[old.variant == 'sin_cruce'].set_index('seed')
    new_zero = new.loc[new.variant == 'sin_cruce'].set_index('seed')
    if not np.allclose(old_zero.best_fitness, new_zero.best_fitness, rtol=0, atol=1e-14):
        raise ValueError('No-crossover control is not reproducible.')
    if not old_zero.initial_population_sha256.equals(new_zero.initial_population_sha256):
        raise ValueError('Different initial populations.')
    def merge_frames(old_frame, new_frame):
        return pd.concat([old_frame.loc[old_frame.variant == 'con_cruce'].assign(variant='anterior'),
                          new_frame.loc[new_frame.variant == 'con_cruce'].assign(variant='nuevo'),
                          new_frame.loc[new_frame.variant == 'sin_cruce']], ignore_index=True)
    runs = merge_frames(old, new)
    histories = merge_frames(pd.read_csv(old_path / 'histories.csv'), pd.read_csv(new_path / 'histories.csv'))
    return runs, histories


def comparisons(rows):
    pairs = rows.pivot(index='seed', columns='variant', values='best_fitness')
    if pairs.isna().any().any():
        raise ValueError('Missing seed/variant.')
    return {baseline: difference_statistics(pairs.nuevo - pairs[baseline]) for baseline in ('anterior', 'sin_cruce')}


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    output = ROOT / 'crossover-mejora'
    output.mkdir(parents=True, exist_ok=True)
    result, all_runs = {}, []
    report = ['# Validación del crossover competitivo', '',
        'Se sustituyó el cruce de cortes independientes por un cruce de punto común con competencia por fitness. Se probaron 10 semillas conocidas y 10 semillas nuevas (301–310), fijadas antes de ver los resultados de validación.', '',
        '## Qué cambia', '',
        '1. Se descartan instrucciones que el decodificador saltó o no procesó; el parque del padre se conserva.',
        '2. Se prueban hasta tres cortes comunes distintos. Cada hijo conserva su semilla y combina un prefijo propio con un sufijo del otro padre.',
        '3. Se evalúa cada propuesta y compite con su padre. Se conserva una mejora de fitness, o un empate con un parque diferente.',
        'La garantía es local y anterior a mutación/reemplazo de duplicados: el crossover no entrega un hijo de menor fitness que su padre correspondiente. No garantiza una mejora estricta, mejora poblacional ni óptimo global.', '',
        '## Diseño', '',
        '- Mismo dataset guardado, fitness, población 50, 200 generaciones, crossover 0,75, mutación 0,20, elitismo 2 y torneo 3.',
        '- Tres condiciones: operador anterior, nuevo operador, sin crossover. Las poblaciones iniciales coinciden por semilla.',
        '- El diseño se fijó en tasks/crossover-improvement/plan.md. El operador no se ajustó después de observar las semillas 301–310.',
        '- El nuevo operador evalúa alternativas: comparar sólo generaciones puede darle mayor presupuesto. Se analizan solicitudes y decodificaciones comunes por separado.',
        '- Los controles sin cruce se reprodujeron exactamente. Se reutiliza una sola copia por semilla.',
        '- Los tiempos de las fases que coincidieron en ejecución no sirven como comparación precisa de rendimiento; se priorizan conteos de evaluaciones.', '']
    colors = {'nuevo': '#247b45', 'anterior': '#2367a3', 'sin_cruce': '#d46c22'}
    labels = {'nuevo': 'Nuevo crossover', 'anterior': 'Crossover anterior', 'sin_cruce': 'Sin crossover'}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout='constrained')
    for ax, (stage, paths) in zip(axes, STAGES.items()):
        runs, histories = collect(*paths)
        runs.to_csv(output / f'{stage}_runs.csv', index=False)
        all_runs.append(runs.assign(stage=stage))
        summary = runs.groupby('variant').agg(mean=('best_fitness', 'mean'), std=('best_fitness', 'std'),
            best=('best_fitness', 'max'), requests=('evaluation_requests', 'mean'), decoded=('decoded_individuals', 'mean'))
        summary.to_csv(output / f'{stage}_summary.csv')
        values = dict(final=comparisons(runs), summary=summary.to_dict(orient='index'))
        for metric in ('evaluation_requests', 'decoded_individuals'):
            budget, scores = common_budget_scores(histories, metric)
            scores.to_csv(output / f'{stage}_{metric}.csv', index=False)
            values[metric] = dict(budget=budget, comparisons=comparisons(scores))
        result[stage] = values
        report += [f'## {stage.capitalize()}', '', '| Variante | Fitness medio ± desvío | Mejor | Solicitudes medias | Decodificaciones medias |', '|---|---:|---:|---:|---:|']
        for variant in ('anterior', 'sin_cruce', 'nuevo'):
            row = summary.loc[variant]
            report.append(f'| {labels[variant]} | {row["mean"]:.6f} ± {row["std"]:.6f} | {row.best:.6f} | {row.requests:.0f} | {row.decoded:.0f} |')
        report.append('')
        for mode, comparison in [('200 generaciones', values['final'])] + [
            (f"Presupuesto común de {values[m]['budget']} {m}", values[m]['comparisons']) for m in ('evaluation_requests', 'decoded_individuals')]:
            report += [f'### {mode}', '', '| Comparación | Diferencia media nuevo − referencia | IC bootstrap 95 % | Victorias nuevo | p bilateral |', '|---|---:|---:|---:|---:|']
            for baseline, stats in comparison.items():
                low, high = stats['bootstrap_95_ci']
                report.append(f"| Nuevo vs {labels[baseline]} | {stats['mean_delta']:.6f} | [{low:.6f}, {high:.6f}] | {stats['crossover_wins']}/10 | {stats['sign_flip_p_two_sided']:.4f} |")
            report.append('')
        for variant in ('anterior', 'sin_cruce', 'nuevo'):
            frame = histories.loc[histories.variant == variant].pivot(index='generation', columns='seed', values='best_historical_fitness')
            ax.plot(frame.index, frame.mean(axis=1), color=colors[variant], label=labels[variant])
        ax.set_title(stage.capitalize() + ' · 10 semillas'); ax.set_xlabel('Generación')
        ax.set_ylabel('Mejor fitness histórico promedio'); ax.legend(); ax.grid(alpha=.2)
    fig.savefig(output / 'comparacion_tres_variantes.png', dpi=160)
    plt.close(fig)
    pd.concat(all_runs, ignore_index=True).to_csv(output / 'all_runs.csv', index=False)
    (output / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    validation = result['validacion']['final']
    report += ['## Conclusión', '',
        f"En las semillas nuevas, el crossover competitivo cambia el fitness medio respecto del anterior en {validation['anterior']['mean_delta']:.6f} y respecto de la variante sin cruce en {validation['sin_cruce']['mean_delta']:.6f}.",
        'La mejora media a 200 generaciones se repite en desarrollo y validación, pero los intervalos de validación incluyen cero: no se demuestra superioridad estadística concluyente en las diez semillas nuevas.',
        'El nuevo operador consume aproximadamente el doble de solicitudes y más decodificaciones. Con presupuestos comunes no muestra una ventaja concluyente y, en validación, las diferencias medias son negativas. Por tanto, no se presenta como una mejora demostrada de eficiencia.',
        'La mejora observada debe interpretarse junto con los intervalos y los presupuestos comunes. La garantía de aceptación por hijo no convierte una diferencia experimental en una garantía universal.',
        'Los cortes múltiples y la evaluación selectiva son parte del nuevo operador: este experimento evalúa el paquete completo, sin atribuir causalidad a cada componente individual.',
        'El presupuesto común se aproxima tomando el último registro por generación que no supera el límite. Las solicitudes incluyen caché; las decodificaciones son genotipos evaluados sin caché, no parques únicos ni una medida exacta de tiempo.',
        'Pruebas bilaterales pareadas por cambio de signos, asumiendo intercambiabilidad/simetría bajo la hipótesis nula; bootstrap de 20.000 muestras con semilla fija. Los múltiples contrastes son exploratorios; no se aplica corrección por multiplicidad.',
        'La zona recurrente y el fitness siguen dependiendo de los datos y pesos del modelo; no demuestran viabilidad eléctrica o económica.', '',
        '![Comparación de tres variantes](comparacion_tres_variantes.png)', '',
        '## Reproducir', '', '```powershell',
        r'.\.venv\Scripts\python.exe -m tasks.compare_crossover --operator sequence --output results/experiments/crossover-20261006-10-pares',
        r'.\.venv\Scripts\python.exe -m tasks.compare_crossover --operator competitive --output results/experiments/crossover-competitivo-desarrollo',
        r'.\.venv\Scripts\python.exe -m tasks.compare_crossover --operator sequence --seeds 301 302 303 304 305 306 307 308 309 310 --output results/experiments/crossover-anterior-validacion',
        r'.\.venv\Scripts\python.exe -m tasks.compare_crossover --operator competitive --seeds 301 302 303 304 305 306 307 308 309 310 --output results/experiments/crossover-competitivo-validacion',
        r'.\.venv\Scripts\python.exe -m tasks.validate_crossover', '```', '',
        'Los directorios de corridas deben ser nuevos; no se sobrescriben los existentes. Los manifiestos y los CSV de historias conservan todos los resultados, incluidas las parejas donde el nuevo cruce pierde.']
    (output / 'informe.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
