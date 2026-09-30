"""Self-contained static SVG plots: no new dependency, CDN or network required."""
from html import escape
import numpy as np


def write_search_charts(history, output):
    plots = [
        ('Fitness', 'Puntaje', [('best_historical_fitness', 'Mejor histórico'), ('mean_fitness', 'Media'), ('median_fitness', 'Mediana')]),
        ('Diversidad', 'Parques', [('unique_parks', 'Distintos'), ('population_size', 'Población')]),
        ('Mutaciones efectivas', 'Porcentaje', [('mutation_effective_percent', 'Eventos que cambiaron las celdas')]),
        ('Genes por individuo', 'Promedio', [('mean_accepted_genes', 'Aceptados'), ('mean_skipped_genes', 'Rechazados'), ('mean_unprocessed_genes', 'No procesados')]),
    ]
    colors = ['#0072b2', '#d55e00', '#009e73']
    x = history.generation.to_numpy(float)
    sections = []
    for number, (title, unit, series) in enumerate(plots):
        values = history[[key for key, _ in series]].to_numpy(float)
        finite = values[np.isfinite(values)]
        low, high = (float(finite.min()), float(finite.max())) if len(finite) else (0., 1.)
        if title in ('Diversidad', 'Mutaciones efectivas', 'Genes por individuo'):
            low = 0.
        high = max(high, low + .01)
        high += (high-low)*.05
        px = lambda value: 70 + 500*(value-x.min())/max(1., x.max()-x.min())
        py = lambda value: 210 - 160*(value-low)/(high-low)
        elements = [f'<svg viewBox="0 0 600 260" role="img" aria-labelledby="chart{number}">',
                    f'<title id="chart{number}">{escape(title)} por generación</title>',
                    '<rect x="70" y="50" width="500" height="160" fill="none" stroke="#bbb"/>',
                    f'<text x="12" y="30">{escape(unit)}</text>', '<text x="270" y="250">Generación</text>']
        for step in range(5):
            y = low + step*(high-low)/4
            xv = x.min() + step*(x.max()-x.min())/4
            elements.extend([f'<text x="62" y="{py(y)+4:.2f}" text-anchor="end">{y:.3g}</text>',
                             f'<text x="{px(xv):.2f}" y="230" text-anchor="middle">{xv:.0f}</text>'])
        legend = []
        for color, (key, label) in zip(colors, series):
            segments, points = [], []
            for xv, yv in zip(x, history[key]):
                if np.isfinite(yv):
                    points.append(f'{px(xv):.2f},{py(yv):.2f}')
                elif points:
                    segments.append(points)
                    points = []
            if points:
                segments.append(points)
            for segment in segments:
                elements.append(f'<polyline points="{" ".join(segment)}" fill="none" stroke="{color}" stroke-width="2"/>')
                if len(segment) == 1:
                    cx, cy = segment[0].split(',')
                    elements.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="{color}"/>')
            legend.append(f'<span style="color:{color}">● {escape(label)}</span>')
        sections.append(f'<section><h2>{escape(title)}</h2>{" ".join(legend)}' + ''.join(elements) + '</svg></section>')
    html = ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>Evolución del AG</title><style>body{font:16px system-ui;margin:24px;color:#222;background:#fff}'
            'main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,500px),1fr));gap:24px}'
            'svg{width:100%;height:auto}svg text{font:13px system-ui;fill:#333}span{display:inline-block;margin-right:16px}'
            'h2{font-size:20px}</style><h1>Evolución del algoritmo genético</h1>'
            '<p>Sin reinicios parciales ni rectángulos. Las generaciones sin eventos de mutación no tienen porcentaje; no se representan como cero.</p>'
            '<p><a href="history.csv">Descargar métricas completas</a></p><main>' + ''.join(sections) + '</main></html>')
    output.write_text(html, encoding='utf-8')
    return output
