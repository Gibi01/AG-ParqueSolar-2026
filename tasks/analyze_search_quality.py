"""Summarize completed independent search baselines; no new optimization."""
import argparse
import base64
import hashlib
import html
import json
import sqlite3
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
import pandas as pd
import shapely

LABEL = {'ag':'AG', 'random':'Aleatoria', 'random_local':'Aleatoria + local', 'rectangles':'Rectángulos'}
COLOR = {'ag':'#267682', 'random':'#999DA1', 'random_local':'#D6982B', 'rectangles':'#31583C'}


def table(frame):
    def value(x):
        if isinstance(x, (float, np.floating)):
            return f'{x:.6f}'
        return str(x)
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |',
                     '| '+' | '.join(['---']*len(frame.columns))+' |',
                     *['| '+' | '.join(value(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None)]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    out = args.output
    manifest = json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['status']=='complete'
    for name,digest in manifest['code_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest, name
    runs = pd.read_csv(out/'runs.csv')
    assert len(runs)==3*len(manifest['seeds'])
    assert runs.groupby('seed').objective_evaluations.nunique().eq(1).all()
    rects = pd.read_csv(out/'rectangles/ranking_territorial.csv')
    ref = pd.read_csv(out/'reference_rankings.csv')
    ref_rect = pd.read_csv(out/'reference_rectangles_comparison.csv')
    ref_top = ref.loc[ref.ranking_type=='ranking_territorial'].copy()
    ref_best = float(ref.fitness.max())
    rect_best = float(rects.fitness.max())
    summary = runs.groupby('method').agg(mean_best=('best_fitness','mean'), median_best=('best_fitness','median'),
                                         worst=('best_fitness','min'),best=('best_fitness','max'),std=('best_fitness','std'),
                                         mean_seconds=('seconds','mean'),mean_evaluations=('objective_evaluations','mean'),
                                         mean_unique_parks=('unique_parks_seen','mean'),
                                         mean_territorial_fitness=('territorial_mean','mean'))
    summary.to_csv(out/'summary.csv')
    pairs = runs.pivot(index='seed',columns='method',values='best_fitness')
    pairs['local_minus_ag'],pairs['random_minus_ag'] = pairs.random_local-pairs.ag,pairs.random-pairs.ag
    pairs['rectangles_minus_ag'] = rect_best-pairs.ag
    pairs.to_csv(out/'paired.csv')
    rng = np.random.default_rng(20261006)
    statistics = {}
    for name in ('local_minus_ag','random_minus_ag'):
        delta = pairs[name].to_numpy()
        ci = np.quantile(rng.choice(delta,size=(20000,len(delta)),replace=True).mean(axis=1),[.025,.975])
        statistics[name] = dict(mean=float(delta.mean()),ci95=ci.tolist(),
                                wins=int((delta>1e-7).sum()),losses=int((delta < -1e-7).sum()),ties=int((abs(delta)<=1e-7).sum()))
    random_draws = np.concatenate([np.load(out/'random'/f'seed-{seed}'/'random_draw_fitness.npy') for seed in manifest['seeds']])
    ref_rect['random_draws_better'] = [int((random_draws>f+1e-7).sum()) for f in ref_rect.fitness]
    ref_rect['random_percentile'] = 100*(1-ref_rect.random_draws_better/len(random_draws))
    ref_rect.to_csv(out/'reference_percentiles.csv',index=False)
    winner_rows = []
    best_rows = {}
    for method in ('ag','random','random_local'):
        for seed in manifest['seeds']:
            winner = pd.read_csv(out/method/f'seed-{seed}'/'ranking.csv').iloc[0]
            winner_rows.append(dict(winner,method=method,seed=seed))
        best_seed = int(runs.loc[runs.method==method].sort_values('best_fitness',ascending=False).iloc[0].seed)
        best_rows[method] = dict(pd.read_csv(out/method/f'seed-{best_seed}'/'ranking.csv').iloc[0],seed=best_seed)
    best_rows['rectangles'] = dict(rects.iloc[0],seed=0)
    pd.DataFrame(winner_rows).to_csv(out/'winners.csv',index=False)
    observed_best = max(float(x['fitness']) for x in best_rows.values())
    analysis = dict(reference_best=ref_best,rectangle_best=rect_best,best_observed=observed_best,
                    reference_observed_gap=observed_best-ref_best,
                    reference_observed_gap_percent=100*(observed_best/ref_best-1),
                    rectangle_count=manifest['rectangles']['evaluations'],random_draws=len(random_draws),paired=statistics)
    (out/'analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    methods = ['ag','random','random_local']
    fig, ax = plt.subplots(figsize=(10,5.2))
    ax.boxplot([runs.loc[runs.method==m,'best_fitness'] for m in methods],tick_labels=[LABEL[m] for m in methods],showmeans=True)
    for i,m in enumerate(methods,1):
        v = runs.loc[runs.method==m,'best_fitness'].to_numpy()
        ax.scatter(i+np.linspace(-.09,.09,len(v)),v,c=COLOR[m],zorder=3,s=30)
    ax.axhline(rect_best,color=COLOR['rectangles'],ls='--',label=f'Mejor rectángulo: {rect_best:.6f}')
    ax.axhline(ref_best,color='#A54040',ls=':',label=f'AG de referencia: {ref_best:.6f}')
    ax.set_ylabel('Mejor fitness por corrida');ax.set_title('Diez semillas · mismo presupuesto de evaluaciones por pareja')
    ax.legend(loc='lower right');ax.grid(axis='y',alpha=.18);fig.tight_layout();fig.savefig(out/'fitness_metodos.png',dpi=180);plt.close(fig)
    fig,ax = plt.subplots(figsize=(10,5.2))
    fractions = np.linspace(0,1,501)
    for m in methods:
        curves = []
        for seed in manifest['seeds']:
            row = runs.loc[(runs.seed==seed)&(runs.method==m)].iloc[0]
            curve = pd.read_csv(out/m/f'seed-{seed}'/'curve.csv')
            assert int(curve.evaluations.iloc[-1])==int(row.objective_evaluations)
            positions = np.searchsorted(curve.evaluations.to_numpy(),fractions*row.objective_evaluations,side='right')-1
            curves.append(np.where(positions>=0,curve.best_fitness.to_numpy()[np.maximum(positions,0)],np.nan))
        values = np.array(curves)
        ax.plot(fractions[1:]*100,np.nanmedian(values[:,1:],axis=0),c=COLOR[m],label=LABEL[m],lw=2)
        ax.fill_between(fractions[1:]*100,np.nanquantile(values[:,1:],.25,axis=0),np.nanquantile(values[:,1:],.75,axis=0),color=COLOR[m],alpha=.13)
    ax.axhline(rect_best,color=COLOR['rectangles'],ls='--',label='Mejor rectángulo (presupuesto distinto)')
    ax.axvline(40,color='#AAAAAA',ls=':',alpha=.6)
    ax.set_xlabel('Porcentaje del presupuesto de evaluaciones de cada pareja');ax.set_ylabel('Mediana del mejor fitness observado')
    ax.set_title('Progreso: mediana y rango intercuartílico entre semillas');ax.grid(alpha=.15);ax.legend(loc='lower right')
    fig.tight_layout();fig.savefig(out/'progreso_metodos.png',dpi=180);plt.close(fig)
    shapes = [('Referencia',dict(ref.loc[ref.ranking_type=='ranking'].iloc[0]),'#A54040'),
              *[(LABEL[m],best_rows[m],COLOR[m]) for m in ('ag','random_local','rectangles')]]
    fig,axes = plt.subplots(1,4,figsize=(14,4))
    for ax,(name,row,color) in zip(axes,shapes):
        geom = shapely.from_wkt(row['geometry_wkt']);cx,cy=geom.centroid.x,geom.centroid.y
        polygons = list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
        for p in polygons:
            exterior = np.asarray(p.exterior.coords)-[cx,cy]
            ax.add_patch(Polygon(exterior/1000,fc=color,ec='#172F3E',lw=1.2))
            for hole in p.interiors:
                ax.add_patch(Polygon((np.asarray(hole.coords)-[cx,cy])/1000,fc='white',ec='#172F3E',lw=1))
        ax.set_xlim(-2.5,2.5);ax.set_ylim(-2.5,2.5);ax.set_aspect('equal');ax.grid(alpha=.15)
        ax.set_title(f"{name}\nF={row['fitness']:.6f} · C={row['compactness_score']:.4f}\n{row['installed_power_mw']:.2f} MW",fontsize=10)
        ax.set_xlabel('Distancia local (km)')
    axes[0].set_ylabel('Distancia local (km)');fig.suptitle('Geometrías reales · misma escala · cada parque centrado en su propio centroide')
    fig.tight_layout();fig.savefig(out/'formas_ganadoras.png',dpi=180,bbox_inches='tight');plt.close(fig)
    # Geographic map: exact IGN contour and actual exported candidate polygons.
    source = json.loads(Path(manifest['reference']).read_text(encoding='utf-8'))
    connection = sqlite3.connect(Path(source['configuration']['paths']['database']).resolve().as_uri()+'?mode=ro',uri=True)
    region = pd.read_sql_query('SELECT geometry_wkt FROM layer_region WHERE dataset_id=?',connection,params=[manifest['dataset_id']])
    stations = pd.read_sql_query('SELECT * FROM layer_transformers WHERE dataset_id=?',connection,params=[manifest['dataset_id']])
    connection.close()
    region = gpd.GeoDataFrame(geometry=gpd.GeoSeries.from_wkt(region.geometry_wkt),crs=4326)
    fmap = folium.Map(location=[-31,-61],zoom_start=7)
    folium.GeoJson(region.to_json(),name='Santa Fe · IGN',style_function=lambda _:dict(color='#172F3E',weight=1.5,fillOpacity=0)).add_to(fmap)
    for method in methods:
        layer = folium.FeatureGroup(name=LABEL[method]+' · 10 ganadores',show=method!='random')
        for row in [r for r in winner_rows if r['method']==method]:
            geo = gpd.GeoSeries([shapely.from_wkt(row['geometry_wkt'])],crs=manifest['projected_crs']).to_crs(4326)
            popup = f"{LABEL[method]} · semilla {row['seed']}<br>Fitness {row['fitness']:.6f}<br>Compactación {row['compactness_score']:.4f}<br>Potencia {row['installed_power_mw']:.3f} MW"
            folium.GeoJson(geo.to_json(),style_function=lambda _,m=method:dict(color=COLOR[m],weight=2,fillOpacity=.35),tooltip=popup).add_to(layer)
            folium.CircleMarker([row['latitude'],row['longitude']],radius=4,color=COLOR[method],fill=True,popup=popup).add_to(layer)
        layer.add_to(fmap)
    for method,frame in [('rectangles',rects),('reference',ref_top)]:
        layer = folium.FeatureGroup(name='Rectángulos · top 5' if method=='rectangles' else 'AG de referencia · top 5',show=method=='rectangles')
        color = COLOR['rectangles'] if method=='rectangles' else '#A54040'
        for row in frame.itertuples():
            geo=gpd.GeoSeries([shapely.from_wkt(row.geometry_wkt)],crs=manifest['projected_crs']).to_crs(4326)
            folium.GeoJson(geo.to_json(),style_function=lambda _,c=color:dict(color=c,weight=3,fillOpacity=.2),tooltip=f'{method} #{row.rank} · F={row.fitness:.6f}').add_to(layer)
        layer.add_to(fmap)
    layer=folium.FeatureGroup(name='ET de referencia',show=False)
    for row in stations.itertuples():
        point=shapely.from_wkt(row.geometry_wkt)
        folium.Marker([point.y,point.x],tooltip=str(row.station_id)).add_to(layer)
    layer.add_to(fmap);folium.LayerControl(collapsed=False).add_to(fmap)
    fmap.save(out/'mapa_comparacion.html')
    baseline_best = max(rect_best,float(runs.loc[runs.method!='ag','best_fitness'].max()))
    if baseline_best > ref_best+1e-7:
        verdict = f'El ganador de referencia es mejorable: un método sin AG obtuvo {baseline_best:.6f}, frente a {ref_best:.6f}.'
    else:
        verdict = f'Los métodos sin AG no superaron al ganador de referencia ({ref_best:.6f}) en estos presupuestos.'
    if statistics['local_minus_ag']['wins'] > statistics['local_minus_ag']['losses']:
        verdict += ' La búsqueda aleatoria con mejora local superó al AG en más parejas de las que perdió.'
    else:
        verdict += ' La búsqueda aleatoria con mejora local no mostró una ventaja consistente frente al AG.'
    rectangle_wins = int((pairs.ag < rect_best-1e-7).sum())
    verdict += f' El AG superó a los métodos aleatorios en promedio, pero {rectangle_wins}/10 semillas quedaron por debajo del mejor rectángulo.'
    if (out/'audit_archive/analysis.json').exists():
        verdict += ' El ganador actual es competitivo; el top 5 territorial contiene alternativas mejorables y pierde propuestas ya evaluadas.'
    comparable = pd.read_csv(out/'ag/seed-42/ranking_territorial.csv')[['rank','fitness']].rename(columns={'fitness':'AG referencia'})
    comparable = comparable.merge(rects[['rank','fitness']].rename(columns={'fitness':'Rectángulos'}),on='rank',how='outer')
    local42 = pd.read_csv(out/'random_local/seed-42/ranking_territorial.csv')[['rank','fitness']].rename(columns={'fitness':'Aleatoria + local, semilla 42'})
    comparable = comparable.merge(local42,on='rank',how='outer')
    comparable.to_csv(out/'top5_comparison_seed42.csv',index=False)
    physical = pd.DataFrame([dict(metodo=LABEL[m],semilla=r['seed'],fitness=r['fitness'],MW=r['installed_power_mw'],
                                  compactacion=r['compactness_score'],perimetro_m=r['park_perimeter_m'],
                                  irradiacion=r['solar_annual_kwh_m2'],distancia_ET_km=r['distance_to_transformer_km']) for m,r in best_rows.items()])
    physical.to_csv(out/'best_physical_metrics.csv',index=False)
    lines = ['# Calidad de búsqueda del AG con compactación','',verdict,'',
             '## Condiciones de comparación','',
             f"Dataset `{manifest['dataset_id']}`. Referencia `{source['run_id']}`.",
             'Grilla 500 m; capacidad experimental 80 MW; densidad 31,3 MW/km². Pesos: solar 0,35; líneas 0,10; ET 0,35; potencia 0,10; compactación 0,10.',
             'AG: 50 individuos, 200 generaciones, cruce competitivo 0,75, mutación 0,20, torneo 3, dos élites. Semillas: '+', '.join(map(str,manifest['seeds']))+'.',
             'Cada método aleatorio recibió exactamente las evaluaciones efectivas del objetivo (fallos de caché) del AG de su pareja. Los presupuestos varían entre semillas. Los tiempos excluyen la carga y preparación comunes del dataset y la exportación.',
             'La comparación aleatoria usa sectores balanceados de 50 km y crecimiento conectado directo; no muestrea uniformemente todos los parques. El híbrido usa 40% del presupuesto para muestreo y 60% para mejora local con reinicios: agregar/quitar/intercambiar una celda, mejor mejora estricta, conexión y capacidad conservadas.',
             'Las semillas identifican parejas de presupuesto; no aseguran las mismas poblaciones iniciales ni trayectorias pseudoaleatorias entre métodos. Distintos cromosomas del AG pueden evaluar el mismo parque; se registran también solicitudes y parques únicos.',
             '## Resultados de las diez semillas','',table(summary.reset_index()),'',table(pairs.reset_index()),'',
             '![Fitness por método](fitness_metodos.png)','',
             'Cada punto es una corrida. La caja muestra el rango intercuartílico; línea naranja: mediana; triángulo verde: media. Las líneas horizontales indican referencias, no resultados con presupuesto igual al de cada pareja.', '',
             '## Diferencias pareadas','']
    for name,s in statistics.items():
        lines += [f"{name}: media {s['mean']:.6f}; IC bootstrap exploratorio 95% [{s['ci95'][0]:.6f}, {s['ci95'][1]:.6f}]; victorias/pérdidas/empates {s['wins']}/{s['losses']}/{s['ties']}."]
    lines += ['', 'Diez semillas constituyen una exploración; estos intervalos no prueban superioridad universal. Diferencias menores a 1e-7 se consideran empates.','',
              '![Progreso](progreso_metodos.png)','',
              '## Rectángulos y calidad del ranking actual','',
              f"Se evaluaron **{manifest['rectangles']['evaluations']:,}** colocaciones de rectángulos de celdas completas válidas, todas las dimensiones h×w con h*w≤10 y ambas orientaciones. Mejor fitness: **{rect_best:.6f}**. Tiempo de evaluación: {manifest['rectangles']['seconds']:.1f} s.",
              'El conteo es completo para esa familia. No incluye parques con celdas recortadas, once o más fragmentos ni formas no rectangulares. Un ganador que aprovecha recortes puede superar a todos los rectángulos completos sin ser un óptimo global.',
              'Se retuvieron suficientes finalistas para calcular el top 5 sin superposición de la familia rectangular. Los métodos estocásticos retienen hasta 10 parques por sector; sus top 5 dependen también del archivo. Esta diferencia impide atribuir toda diferencia territorial sólo al mecanismo de búsqueda.',
              'Los percentiles aleatorios son respecto del muestreo definido y contienen repeticiones; los rectangulares son respecto de la familia enumerada. No son percentiles de todo el dominio.','',
              table(ref_rect[['ranking_type','rank','fitness','rectangles_better','rectangle_percentile','random_draws_better','random_percentile']]),'',
              'Comparación por posición de ranking territorial (semilla 42):','',table(comparable),'',
              'Estos rankings aplican selección voraz sin superposición y separación adicional 0 km. Los puestos no corresponden a los mismos terrenos; no prueban el óptimo de un conjunto de cinco parques.','',
              '## Métricas físicas y geometrías','',table(physical),'',
              '![Geometrías](formas_ganadoras.png)','',
              '[Mapa interactivo de ganadores y alternativas](mapa_comparacion.html)','',
              '## Interpretación y límites','',
              f"El mejor fitness observado entre todos los métodos fue {observed_best:.6f}. El ganador de referencia queda {observed_best-ref_best:.6f} puntos por debajo ({100*(observed_best/ref_best-1):.3f}% relativo al fitness). Esta es una brecha observada, no una brecha certificada respecto del óptimo global.",
              'No se debe convertir una diferencia porcentual de fitness en energía, rentabilidad o eficiencia. Tampoco la cercanía geométrica demuestra capacidad disponible de red. La compactación es una aproximación geométrica al diseño, no un costo de construcción.',
              'La función objetivo y los datos describen sólo el escenario del proyecto: ponderaciones experimentales, irradiación estacional estimada y restricciones territoriales parciales. Un buen resultado de optimización no demuestra viabilidad física del proyecto.',
              '## Reproducir','', '```powershell',
              r'.\.venv\Scripts\python.exe -m tasks.compare_search_quality --output results/experiments/nueva-validacion-compactacion',
              r'.\.venv\Scripts\python.exe -m tasks.analyze_search_quality results/experiments/nueva-validacion-compactacion','```','',
              'No se modificó el AG, su configuración ni sus resultados previos para esta comparación. Manifiesto, hashes, resultados por semilla, geometrías y curvas quedan en esta carpeta.']
    audit_path = out/'audit_archive/analysis.json'
    if audit_path.exists():
        audit = json.loads(audit_path.read_text(encoding='utf-8'))
        audit_comparison = pd.read_csv(out/'audit_archive/comparison.csv')
        lines += ['', '## Auditoría de retención: misma corrida, sin cambiar la búsqueda','',
                  f"Se reprodujo exactamente la semilla 42: mismo ranking general y mismo presupuesto. Se registraron {audit['evaluated_distinct_parks']} parques distintos evaluados, frente a {audit['retained_parks']} retenidos al final.",
                  'El registro incluye propuestas internas de cruce y mutación, aunque no ingresen a la población. No se agregaron movimientos de búsqueda ni se cambiaron números aleatorios.',
                  'Comparación del ranking territorial al conservar todas las propuestas evaluadas y al agregar los rectángulos enumerados:', '',table(audit_comparison),'',
                  f"Media del top 5 publicado: {audit['original_top5_mean']:.6f}; media usando todos los parques ya evaluados por el mismo AG: {audit['all_evaluated_top5_mean']:.6f}; media del archivo AG más rectángulos: {audit['ag_plus_rectangles_top5_mean']:.6f}.",
                  'Si el ranking mejora sin nuevas evaluaciones del territorio, el problema incluye retención y selección de alternativas; no puede atribuirse sólo a que el AG no haya explorado candidatos mejores. El límite de 10 por sector y la política de ingreso de propuestas pueden excluir opciones útiles sin superposición.',
                  '[Alternativas de todos los parques ya evaluados](audit_archive/all_evaluated/ranking_territorial.csv) · [AG más rectángulos](audit_archive/ag_plus_rectangles/ranking_territorial.csv)']
        analysis['archive_audit'] = audit
        (out/'analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'informe.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    embeds=[]
    for name in ('fitness_metodos.png','progreso_metodos.png','formas_ganadoras.png'):
        data=base64.b64encode((out/name).read_bytes()).decode()
        embeds.append(f'<img style="width:100%;height:auto" src="data:image/png;base64,{data}"/>')
    body='<h1>Calidad de búsqueda del AG con compactación</h1><p>'+html.escape(verdict)+'</p>'
    body+='<p>Mismo dataset, restricciones y fitness. Diez semillas; mismo presupuesto de evaluaciones por pareja. Rectángulos: familia completa, presupuesto distinto.</p>'
    body+=summary.reset_index().to_html(index=False,float_format=lambda v:f'{v:.6f}')+''.join(embeds)
    body+='<h2>Ranking territorial · semilla 42</h2>'+comparable.to_html(index=False,float_format=lambda v:f'{v:.6f}')
    if audit_path.exists():
        body+='<h2>Auditoría de retención · misma corrida</h2>'+audit_comparison.to_html(index=False,float_format=lambda v:f'{v:.6f}')
        body+='<p>Registrar todas las propuestas evaluadas permite separar la calidad de búsqueda de la retención y selección del ranking. La trayectoria del AG se reprodujo sin cambios.</p>'
    body+='<p><a href="informe.md">Informe completo y límites</a> · <a href="mapa_comparacion.html">Mapa interactivo</a> · <a href="runs.csv">Corridas CSV</a></p>'
    (out/'resumen.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Calidad de búsqueda</title><style>body{font:17px Arial;background:#f5f7f8;color:#172F3E;max-width:1200px;margin:40px auto;padding:24px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:9px;border-bottom:1px solid #ccd6dc;text-align:right}h1,h2{font-family:Georgia}img{margin:24px 0}</style>'+body+'</html>',encoding='utf-8')
    print(json.dumps(analysis,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
