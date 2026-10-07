"""Analyze completed paired runs and create Spanish report, figures and geographic map."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from tasks.compare_crossover import paired_results


def difference_statistics(delta):
    delta = np.asarray(delta, dtype=float)
    if not len(delta) or not np.isfinite(delta).all():
        raise ValueError('Finite paired differences required.')
    rng = np.random.default_rng(90210)
    boot = rng.choice(delta, size=(20000, len(delta)), replace=True).mean(axis=1)
    observed = abs(delta.mean())
    null = np.array([abs(np.mean(delta * signs)) for signs in itertools.product((-1, 1), repeat=len(delta))])
    return dict(mean_delta=float(delta.mean()), median_delta=float(np.median(delta)),
                bootstrap_95_ci=np.quantile(boot, [.025, .975]).tolist(),
                sign_flip_p_two_sided=float(np.mean(null >= observed - 1e-14)),
                crossover_wins=int((delta > 1e-12).sum()),
                no_crossover_wins=int((delta < -1e-12).sum()), ties=int((abs(delta) <= 1e-12).sum()))


def common_budget_scores(histories, metric='evaluation_requests'):
    budget = int(histories.groupby(['variant', 'seed'])[metric].max().min())
    scores = (histories.loc[histories[metric] <= budget]
              .sort_values(metric).groupby(['variant', 'seed']).tail(1)
              [['variant', 'seed', 'best_historical_fitness', metric]]
              .rename(columns={'best_historical_fitness': 'best_fitness'}))
    return budget, scores


def geographic_statistics(winners, alternatives):
    coordinates = winners[['centroid_x_m', 'centroid_y_m']].to_numpy(dtype=float) / 1000
    distances = np.linalg.norm(coordinates[:, None, :] - coordinates[None, :, :], axis=2)
    medoid_index = int(np.argmin(distances.sum(axis=1)))
    medoid = winners.iloc[medoid_index]
    output = dict(medoid=dict(latitude=float(medoid.latitude), longitude=float(medoid.longitude),
                              station_name=str(medoid.station_name)), variants={})
    cells = [set(json.loads(value)) for value in winners.cell_ids]
    overlap = []
    for i in range(len(winners)):
        for j in range(i + 1, len(winners)):
            overlap.append(dict(variant_a=winners.iloc[i].variant, seed_a=int(winners.iloc[i].seed),
                                variant_b=winners.iloc[j].variant, seed_b=int(winners.iloc[j].seed),
                                distance_km=float(distances[i, j]),
                                same_park=cells[i] == cells[j], jaccard=len(cells[i] & cells[j]) / len(cells[i] | cells[j])))
    for variant, frame in winners.groupby('variant'):
        indices = np.flatnonzero(winners.variant.to_numpy() == variant)
        local_distances = distances[np.ix_(indices, indices)]
        nearest_to_medoid = distances[indices, medoid_index]
        off_diagonal = local_distances[np.triu_indices(len(indices), 1)]
        output['variants'][variant] = dict(
            median_pair_distance_km=float(np.median(off_diagonal)),
            max_pair_distance_km=float(off_diagonal.max()),
            winners_within_10km_medoid=int((nearest_to_medoid <= 10).sum()),
            winners_within_25km_medoid=int((nearest_to_medoid <= 25).sum()),
            winners_within_50km_medoid=int((nearest_to_medoid <= 50).sum()),
            nearest_station_counts={str(k): int(v) for k, v in frame.station_name.value_counts().items()},
            distinct_winner_parks=len({tuple(sorted(json.loads(c))) for c in frame.cell_ids}),
            territorial_top5_station_presence={str(station): int(group.seed.nunique())
                for station, group in alternatives.loc[alternatives.variant == variant].groupby('station_name')})
    return output, pd.DataFrame(overlap)


def figures(output, runs, histories, budget, projected_crs):
    import geopandas as gpd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    colors = {'con_cruce': '#2367a3', 'sin_cruce': '#d46c22'}
    labels = {'con_cruce': 'Con crossover (75 %)', 'sin_cruce': 'Sin crossover (0 %)'}
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
    pairs = paired_results(runs)
    fig, ax = plt.subplots(figsize=(9, 4.5), layout='constrained')
    positions = np.arange(len(pairs))
    ax.plot(positions, pairs.con_cruce, 'o-', color=colors['con_cruce'], label=labels['con_cruce'])
    ax.plot(positions, pairs.sin_cruce, 's-', color=colors['sin_cruce'], label=labels['sin_cruce'])
    ax.set_xticks(positions, pairs.seed.astype(str)); ax.set_xlabel('Semilla aleatoria')
    ax.set_ylabel('Mejor fitness final (puntaje)'); ax.set_title(f'Comparación pareada · {int(histories.generation.max())} generaciones')
    ax.legend(); ax.grid(axis='y', alpha=.2)
    fig.savefig(output / 'fitness_por_semilla.png', dpi=160); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout='constrained')
    for variant, frame in histories.groupby('variant'):
        pivot = frame.pivot(index='generation', columns='seed', values='best_historical_fitness')
        axes[0].plot(pivot.index, pivot.mean(axis=1), color=colors[variant], label=labels[variant])
        axes[0].fill_between(pivot.index, pivot.min(axis=1), pivot.max(axis=1), color=colors[variant], alpha=.13)
        x = np.linspace(50, budget, 150).astype(int)
        values = []
        for _, run in frame.groupby('seed'):
            run = run.sort_values('evaluation_requests')
            indices = np.searchsorted(run.evaluation_requests.to_numpy(), x, side='right') - 1
            values.append(run.best_historical_fitness.to_numpy()[indices])
        values = np.asarray(values)
        axes[1].plot(x, values.mean(axis=0), color=colors[variant], label=labels[variant])
        axes[1].fill_between(x, values.min(axis=0), values.max(axis=0), color=colors[variant], alpha=.13)
    for ax in axes:
        ax.set_ylabel('Mejor fitness histórico (puntaje)'); ax.grid(alpha=.2); ax.legend()
    axes[0].set_xlabel('Generación'); axes[0].set_title(f'Promedio y rango entre {runs.seed.nunique()} semillas')
    axes[1].set_xlabel('Solicitudes de evaluación acumuladas'); axes[1].set_title('Presupuesto común · último registro disponible')
    fig.savefig(output / 'evolucion_comparada.png', dpi=160); plt.close(fig)

    boundary = gpd.read_file(output / 'region.geojson').to_crs(projected_crs)
    stations = gpd.read_file(output / 'transformers.geojson').to_crs(projected_crs)
    lines = gpd.read_file(output / 'lines.geojson').to_crs(projected_crs)
    points = gpd.GeoDataFrame(runs.copy(), geometry=gpd.points_from_xy(runs.centroid_x_m, runs.centroid_y_m), crs=projected_crs)
    fig, axes = plt.subplots(1, 2, figsize=(10, 10), sharex=True, sharey=True, layout='constrained')
    for ax, variant in zip(axes, ('con_cruce', 'sin_cruce')):
        boundary.plot(ax=ax, color='#f5f5f5', edgecolor='#444444', linewidth=.8)
        if len(lines): lines.plot(ax=ax, color='#b0b0b0', linewidth=.45, alpha=.6)
        stations.plot(ax=ax, color='#555555', marker='^', markersize=35)
        points.loc[points.variant == variant].plot(ax=ax, color=colors[variant], markersize=50, alpha=.7)
        for station in stations.itertuples():
            name=str(getattr(station, 'nombre', getattr(station, 'station_id', 'ET')))
            ax.annotate(name, (station.geometry.x, station.geometry.y), xytext=(5, 5), textcoords='offset points', fontsize=8)
        ax.set_title(labels[variant] + '\n10 ganadores; algunos puntos se superponen')
        ax.set_xlabel('Este UTM (m)'); ax.set_ylabel('Norte UTM (m)'); ax.ticklabel_format(style='plain', axis='both')
        ax.tick_params(axis='x', labelrotation=30)
    fig.savefig(output / 'zonas_ganadoras.png', dpi=160); plt.close(fig)


def interactive_map(output, runs):
    import folium
    import geopandas as gpd
    boundary = gpd.read_file(output / 'region.geojson').to_crs(4326)
    west, south, east, north = boundary.total_bounds
    m = folium.Map(location=[float(runs.latitude.mean()), float(runs.longitude.mean())], zoom_start=8)
    m.fit_bounds([[south, west], [north, east]])
    folium.GeoJson(str(output / 'region.geojson'), name='Santa Fe', style_function=lambda _: dict(color='#555555', weight=1, fillOpacity=0)).add_to(m)
    for variant, color in [('con_cruce', '#2367a3'), ('sin_cruce', '#d46c22')]:
        group = folium.FeatureGroup(name=variant.replace('_', ' '), show=True)
        for row in runs.loc[runs.variant == variant].itertuples():
            folium.CircleMarker([row.latitude, row.longitude], radius=6, color=color, fill=True, fill_opacity=.7,
                tooltip=f'Semilla {row.seed} · {variant} · fitness {row.best_fitness:.6f} · ET cercana: {row.station_name}').add_to(group)
        group.add_to(m)
    alternatives = json.loads((output / 'alternatives.geojson').read_text(encoding='utf-8'))
    for variant, color in [('con_cruce', '#2367a3'), ('sin_cruce', '#d46c22')]:
        subset = dict(type='FeatureCollection', features=[f for f in alternatives['features'] if f['properties']['variant'] == variant])
        folium.GeoJson(subset, name='TOP 5 territorial · ' + variant.replace('_', ' '), show=False,
            style_function=lambda _, c=color: dict(color=c, weight=2, fillOpacity=.25),
            tooltip=folium.GeoJsonTooltip(fields=['seed', 'rank', 'fitness'], aliases=['Semilla', 'Puesto territorial', 'Fitness'])).add_to(m)
    folium.GeoJson(str(output / 'transformers.geojson'), name='Estaciones de referencia').add_to(m)
    folium.LayerControl().add_to(m)
    m.save(output / 'mapa_interactivo.html')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    output = args.output
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['status'] != 'complete':
        raise ValueError('The experiment is incomplete.')
    runs = pd.read_csv(output / 'runs.csv')
    histories = pd.read_csv(output / 'histories.csv')
    winners = pd.read_csv(output / 'winners.csv')
    alternatives = pd.read_csv(output / 'alternatives.csv')
    sample_size = len(manifest['seeds'])
    operator = manifest.get('crossover_operator', 'sequence')
    pairs = paired_results(runs)
    stats = difference_statistics(pairs.delta)
    budget, common = common_budget_scores(histories)
    common.to_csv(output / 'common_budget.csv', index=False)
    common_pairs = paired_results(common)
    common_pairs.to_csv(output / 'paired_common_budget.csv', index=False)
    geo, overlap = geographic_statistics(winners, alternatives)
    overlap.to_csv(output / 'winner_similarity.csv', index=False)
    overview = runs.groupby('variant').agg(fitness_mean=('best_fitness', 'mean'), fitness_std=('best_fitness', 'std'),
        fitness_min=('best_fitness', 'min'), fitness_max=('best_fitness', 'max'),
        requests_mean=('evaluation_requests', 'mean'), seconds_mean=('seconds', 'mean'),
        unique_parks_mean=('unique_parks_seen', 'mean')).reset_index()
    overview.to_csv(output / 'summary.csv', index=False)
    analysis = dict(paired_final=stats, common_budget=budget,
                    paired_common_budget=difference_statistics(common_pairs.delta), geography=geo,
                    analyst_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output / 'analysis.json').write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding='utf-8')
    figures(output, runs, histories, budget, manifest['projected_crs'])
    interactive_map(output, runs)
    ci = stats['bootstrap_95_ci']
    near_count = sum(v['winners_within_25km_medoid'] for v in geo['variants'].values())
    distinct_parks = len({tuple(sorted(json.loads(c))) for c in winners.cell_ids})
    lines = ['# Experimento: estabilidad territorial y aporte del crossover', '',
        f'Se ejecutaron {len(runs)} corridas: {sample_size} semillas y dos variantes, con el mismo dataset y la misma población inicial por pareja.',
        f'Operador evaluado: **{operator}**. La variante sin crossover mantiene selección por torneo, elitismo, mutación y reemplazo de duplicados.', '',
        f'**Hallazgo geográfico:** {near_count} de {len(runs)} ganadores están a menos de 25 km del centro representativo. Hay {distinct_parks} configuraciones distintas entre los ganadores.',
        f"**Hallazgo sobre crossover:** gana {stats['crossover_wins']} de {sample_size} parejas; la diferencia media con − sin es {stats['mean_delta']:.6f}. El intervalo y el control de presupuesto se detallan abajo.", '',
        '## Diseño y trazabilidad', '',
        f"- Dataset: `{manifest['dataset_id']}`; referencia: `{manifest['reference']}`.",
        f"- Semillas fijadas antes de ejecutar: {manifest['seeds']}.",
        f"- Población {manifest['configuration']['genetic_algorithm']['population_size']}; generaciones {manifest['generations']} (más generación 0); mutación 0,20; elitismo 2; torneo 3.",
        '- Crossover: 0,75 frente a 0. Igualar generaciones no iguala solicitudes ni decodificaciones; ambos contadores se conservan.',
        '- Se comprobó identidad de poblaciones iniciales, integridad de historias, capacidad y contigüidad de todos los candidatos archivados.',
        '- Manifiesto con configuración sin credenciales, hashes del código ejecutado, identificación del dataset y tiempos.', '',
        '## Calidad y costo', '',
        '| Variante | Fitness medio ± desvío | Mínimo | Máximo | Solicitudes medias | Tiempo medio del AG |',
        '|---|---:|---:|---:|---:|---:|']
    for row in overview.itertuples():
        lines.append(f'| {row.variant} | {row.fitness_mean:.6f} ± {row.fitness_std:.6f} | {row.fitness_min:.6f} | {row.fitness_max:.6f} | {row.requests_mean:.0f} | {row.seconds_mean:.2f} s |')
    lines += ['', f"Crossover gana en {stats['crossover_wins']}/{sample_size} parejas; sin crossover gana en {stats['no_crossover_wins']}/{sample_size}; empates: {stats['ties']}.",
        f"Diferencia media **con − sin**: {stats['mean_delta']:.6f} puntos de fitness. IC bootstrap exploratorio del 95 %: [{ci[0]:.6f}, {ci[1]:.6f}].",
        f"Prueba pareada bilateral de cambio de signos: p = {stats['sign_flip_p_two_sided']:.4f}. Supone intercambiabilidad/simetría bajo la hipótesis nula; el tamaño de muestra limita la generalización.", '',
        f"Presupuesto común observado: {budget} solicitudes. Se toma el último registro poblacional que no supera ese límite, sin interpolar ni inventar evaluaciones intermedias.",
        f"A ese presupuesto la diferencia media con − sin es {analysis['paired_common_budget']['mean_delta']:.6f}; victorias con cruce: {analysis['paired_common_budget']['crossover_wins']}/{sample_size}.",
        'Es un control aproximado: cada historia sólo registra al terminar una generación y se comparan solicitudes, no costos idénticos ni decodificaciones iguales.', '',
        '![Fitness por semilla](fitness_por_semilla.png)', '', '![Evolución](evolucion_comparada.png)', '',
        '## Recurrencia geográfica', '',
        'Se cuentan ganadores por sectores proyectados de 10, 25 y 50 km, usando el origen territorial del AG. Los límites de los sectores pueden separar ubicaciones próximas.',
        'El TOP 5 territorial se analiza por separado: un sector presente varias veces en una corrida cuenta una sola vez. Frecuencia significa recurrencia del algoritmo bajo este modelo, no probabilidad física de viabilidad.', '',
        f"Centro representativo (ganador medoid entre las 20 corridas): {geo['medoid']['latitude']:.5f}, {geo['medoid']['longitude']:.5f}; ET cercana: {geo['medoid']['station_name']}."]
    for variant, values in geo['variants'].items():
        sectors = pd.read_csv(output / 'winners_frequency_50km.csv')
        sector = sectors.loc[sectors.variant == variant].iloc[0]
        lines += ['', f'### {variant}', '',
            f"- Sector de 50 km más repetido: ({int(sector.sector_x)}, {int(sector.sector_y)}), {int(sector.runs)}/{sample_size} ganadores.",
            f"- Ganadores a menos de 10/25/50 km del centro representativo común: {values['winners_within_10km_medoid']}/{sample_size}, {values['winners_within_25km_medoid']}/{sample_size} y {values['winners_within_50km_medoid']}/{sample_size}.",
            f"- Distancia mediana entre pares de ganadores: {values['median_pair_distance_km']:.2f} km; máxima: {values['max_pair_distance_km']:.2f} km.",
            f"- Parques ganadores distintos: {values['distinct_winner_parks']}/{sample_size}.",
            f"- ET más cercana a los ganadores: {values['nearest_station_counts']}.",
            f"- Presencia de cada ET cercana en el TOP 5 territorial (corridas, máximo {sample_size}): {values['territorial_top5_station_presence']}."]
    conclusion = ('En estas corridas, el crossover no muestra una ventaja media de fitness.' if stats['mean_delta'] <= 0 else
                  'En estas corridas, el crossover muestra una ventaja media de fitness; su estabilidad debe juzgarse con el intervalo y las parejas.')
    lines += ['', '![Ganadores por ubicación](zonas_ganadoras.png)', '', '[Mapa interactivo de las 20 corridas](mapa_interactivo.html)', '',
        '## Interpretación y límites', '', conclusion,
        'El resultado compara el crossover actual con su desactivación. No compara AG contra búsqueda aleatoria u otro optimizador, por lo que no establece si el AG completo es superior o innecesario.',
        f"Incertidumbre: IC 95 % [{ci[0]:.6f}, {ci[1]:.6f}], p = {stats['sign_flip_p_two_sided']:.4f}. Interpretar junto con los presupuestos y las semillas usadas.",
        'Una explicación posible es que un sufijo de genes cambie su significado espacial al combinarse con otro prefijo. Este experimento no demuestra ese mecanismo causal.',
        'Las mismas semillas sincronizan el inicio, pero las variantes consumen números aleatorios diferentes después del primer cruce: no son trayectorias idénticas con una sola operación quitada.',
        'La proximidad a una ET no demuestra conexión ni capacidad disponible. El límite de 80 MW sigue siendo experimental. La irradiación se estima a partir de cuatro meses representativos.',
        'El fitness usa pesos provisionales; una zona recurrente es prometedora bajo esos pesos y datos, sin acreditar óptimo global, viabilidad predial o rentabilidad.', '',
        '## Reproducir', '', '```powershell',
        r'.\.venv\Scripts\python.exe -m tasks.compare_crossover --operator ' + operator + ' --output results/experiments/nueva-comparacion',
        r'.\.venv\Scripts\python.exe -m tasks.analyze_crossover results/experiments/nueva-comparacion', '```', '',
        'El analizador requiere Matplotlib. Las corridas no requieren descargar nuevos datos ni Matplotlib.',
        'Archivos principales: runs.csv, paired.csv, histories.csv, summary.csv, analysis.json, winner_similarity.csv, winners_frequency_*km.csv y alternatives_frequency_*km.csv.']
    (output / 'informe.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(analysis, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
