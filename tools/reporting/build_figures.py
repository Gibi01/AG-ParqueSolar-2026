from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tmp" / "report_assets"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False, italic: bool = False):
    name = "ariali.ttf" if italic else "arialbd.ttf" if bold else "arial.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def canvas(width: int, height: int):
    image = Image.new("RGB", (width, height), "white")
    return image, ImageDraw.Draw(image)


def centered(draw, box, text, fnt, fill="#222222", spacing=5):
    x1, y1, x2, y2 = box
    b = draw.multiline_textbbox((0, 0), text, font=fnt, align="center", spacing=spacing)
    w, h = b[2] - b[0], b[3] - b[1]
    draw.multiline_text(((x1 + x2 - w) / 2, (y1 + y2 - h) / 2), text, font=fnt, fill=fill, align="center", spacing=spacing)


def arrow(draw, start, end, color="#222222", width=3):
    draw.line([start, end], fill=color, width=width)
    x2, y2 = end
    x1, y1 = start
    v = np.array([x2 - x1, y2 - y1], dtype=float)
    n = np.linalg.norm(v)
    if n == 0:
        return
    u = v / n
    p = np.array([-u[1], u[0]])
    tip = np.array([x2, y2])
    a = tip - u * 14 + p * 7
    b = tip - u * 14 - p * 7
    draw.polygon([tuple(tip), tuple(a), tuple(b)], fill=color)


def architecture():
    image, d = canvas(1800, 700)
    d.text((55, 35), "IGN · BAHRA · Secretaría de Energía · Copernicus ERA5-Land ARCO", font=font(30), fill="#222222")
    labels = ["Fuentes\noficiales", "Ingesta\ny caché", "Procesamiento\ngeoespacial", "Base local\nSQLite", "Algoritmo\ngenético"]
    boxes = []
    for i, label in enumerate(labels):
        x1 = 55 + i * 345
        box = (x1, 190, x1 + 280, 340)
        boxes.append(box)
        d.rounded_rectangle(box, radius=18, fill="#ececec", outline="#222222", width=3)
        centered(d, box, label, font(30, bold=True))
        if i:
            arrow(d, (boxes[i - 1][2] + 12, 265), (box[0] - 12, 265))
    lower1 = (1090, 470, 1370, 620)
    lower2 = (1435, 470, 1715, 620)
    for box, label in ((lower1, "CSV y JSON\ntrazables"), (lower2, "Mapa HTML\ny ranking")):
        d.rounded_rectangle(box, radius=18, fill="#ececec", outline="#222222", width=3)
        centered(d, box, label, font(30, bold=True))
    arrow(d, (1575, 350), (1575, 455))
    arrow(d, (1420, 545), (1385, 545))
    d.text((55, 650), "El algoritmo genético opera únicamente sobre métricas precalculadas en la base local.", font=font(27, italic=True), fill="#333333")
    image.save(OUT / "figura_arquitectura.png", dpi=(240, 240))


def candidate_map():
    c = pd.read_csv(ROOT / "results" / "candidate_locations.csv")
    r = pd.read_csv(ROOT / "results" / "ranking.csv")
    image, d = canvas(1200, 1380)
    d.text((60, 35), "Celdas analizadas y diez ubicaciones mejor clasificadas", font=font(34, bold=True), fill="#222222")
    plot = (110, 130, 1090, 1230)
    d.rectangle(plot, outline="#333333", width=2)
    lon_min, lon_max = c.longitude.min(), c.longitude.max()
    lat_min, lat_max = c.latitude.min(), c.latitude.max()

    def xy(lon, lat):
        x = plot[0] + (lon - lon_min) / (lon_max - lon_min) * (plot[2] - plot[0])
        y = plot[3] - (lat - lat_min) / (lat_max - lat_min) * (plot[3] - plot[1])
        return x, y

    for row in c.itertuples():
        x, y = xy(row.longitude, row.latitude)
        valid = bool(row.valid)
        fill = "#707070" if valid else "#d8d8d8"
        radius = 8 if valid else 6
        d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline="#555555")
    for row in r.itertuples():
        x, y = xy(row.longitude, row.latitude)
        radius = 20
        d.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#111111", outline="white", width=2)
        centered(d, (x - radius, y - radius, x + radius, y + radius), str(int(row.rank)), font(16, bold=True), fill="white")
    d.text((110, 1255), "Gris oscuro: válida   Gris claro: excluida   Negro: TOP 10", font=font(26), fill="#222222")
    d.text((110, 1300), "Coordenadas geográficas de los centroides; representación esquemática.", font=font(23, italic=True), fill="#444444")
    image.save(OUT / "figura_mapa_candidatos.png", dpi=(240, 240))


def fitness_components():
    r = pd.read_csv(ROOT / "results" / "ranking.csv").sort_values("rank")
    solar = 0.5 * r.solar_score.to_numpy()
    lines = 0.2 * r.grid_proximity_score.to_numpy()
    trafo = 0.3 * r.transformer_proximity_score.to_numpy()
    image, d = canvas(1800, 900)
    d.text((65, 35), "Contribución ponderada de cada criterio al fitness", font=font(34, bold=True), fill="#222222")
    plot = (120, 170, 1720, 730)
    ymax = 0.86
    for tick in np.arange(0, 0.81, 0.2):
        y = plot[3] - tick / ymax * (plot[3] - plot[1])
        d.line((plot[0], y, plot[2], y), fill="#dedede", width=2)
        d.text((45, y - 14), f"{tick:.1f}", font=font(22), fill="#333333")
    d.line((plot[0], plot[1], plot[0], plot[3]), fill="#222222", width=3)
    d.line((plot[0], plot[3], plot[2], plot[3]), fill="#222222", width=3)
    slot = (plot[2] - plot[0]) / len(r)
    bw = slot * 0.62
    for i, row in enumerate(r.itertuples()):
        x1 = plot[0] + i * slot + (slot - bw) / 2
        x2 = x1 + bw
        bottom = plot[3]
        for value, fill in ((solar[i], "#222222"), (lines[i], "#777777"), (trafo[i], "#c5c5c5")):
            h = value / ymax * (plot[3] - plot[1])
            d.rectangle((x1, bottom - h, x2, bottom), fill=fill, outline="#444444")
            bottom -= h
        centered(d, (x1 - 8, plot[3] + 10, x2 + 8, plot[3] + 82), f"#{int(row.rank)}\n{int(row.grid_cell_id)}", font(19), spacing=2)
    legends = [("#222222", "Radiación × 0,50"), ("#777777", "Líneas × 0,20"), ("#c5c5c5", "Transformadores × 0,30")]
    x = 220
    for fill, label in legends:
        d.rectangle((x, 820, x + 35, 850), fill=fill, outline="#333333")
        d.text((x + 48, 819), label, font=font(23), fill="#222222")
        x += 510
    image.save(OUT / "figura_componentes_fitness.png", dpi=(240, 240))


def convergence():
    c = pd.read_csv(ROOT / "results" / "candidate_locations.csv")
    c = c[c.valid.astype(bool)].reset_index(drop=True)
    lookup = (0.5 * c.solar_score + 0.2 * c.grid_proximity_score + 0.3 * c.transformer_proximity_score).to_numpy()
    rng = np.random.default_rng(42)
    pop_size, generations, elitism, tournament, pc, pm = 50, 100, 2, 3, .75, .05
    population = rng.integers(0, len(c), size=pop_size)
    best, mean = [], []
    for _ in range(generations):
        fit = lookup[population]
        best.append(float(fit.max()))
        mean.append(float(fit.mean()))
        elite = population[np.argsort(-fit)[:elitism]]
        n = pop_size - elitism
        parents = np.empty(n, dtype=population.dtype)
        for i in range(n):
            pos = rng.integers(0, pop_size, size=tournament)
            contenders = population[pos]
            parents[i] = contenders[np.argmax(lookup[contenders])]
        children = parents.copy()
        for i in range(0, n - 1, 2):
            if rng.random() < pc:
                alpha = rng.random()
                a, b = int(parents[i]), int(parents[i + 1])
                children[i] = min(max(int(round(alpha * a + (1 - alpha) * b)), 0), len(c) - 1)
                children[i + 1] = min(max(int(round(alpha * b + (1 - alpha) * a)), 0), len(c) - 1)
        mask = rng.random(n) < pm
        if mask.sum():
            children[mask] = rng.integers(0, len(c), size=int(mask.sum()))
        population = np.concatenate([elite, children])
    fit = lookup[population]
    best.append(float(fit.max()))
    mean.append(float(fit.mean()))

    image, d = canvas(1800, 850)
    d.text((65, 35), "Evolución del mejor fitness y del fitness medio", font=font(34, bold=True), fill="#222222")
    plot = (130, 150, 1710, 700)
    ymin, ymax = 0.0, 0.86
    for tick in np.arange(0, .81, .2):
        y = plot[3] - (tick - ymin) / (ymax - ymin) * (plot[3] - plot[1])
        d.line((plot[0], y, plot[2], y), fill="#dedede", width=2)
        d.text((50, y - 14), f"{tick:.1f}", font=font(22), fill="#333333")
    d.line((plot[0], plot[1], plot[0], plot[3]), fill="#222222", width=3)
    d.line((plot[0], plot[3], plot[2], plot[3]), fill="#222222", width=3)

    def point(i, value):
        x = plot[0] + i / generations * (plot[2] - plot[0])
        y = plot[3] - (value - ymin) / (ymax - ymin) * (plot[3] - plot[1])
        return x, y

    d.line([point(i, v) for i, v in enumerate(best)], fill="#111111", width=5)
    d.line([point(i, v) for i, v in enumerate(mean)], fill="#888888", width=4)
    for tick in (0, 20, 40, 60, 80, 100):
        x, _ = point(tick, 0)
        d.text((x - 12, plot[3] + 15), str(tick), font=font(21), fill="#333333")
    d.text((780, 760), "Generación", font=font(24), fill="#222222")
    d.line((1130, 780, 1190, 780), fill="#111111", width=5)
    d.text((1205, 765), "Mejor fitness", font=font(22), fill="#222222")
    d.line((1430, 780, 1490, 780), fill="#888888", width=5)
    d.text((1505, 765), "Fitness medio", font=font(22), fill="#222222")
    image.save(OUT / "figura_convergencia.png", dpi=(240, 240))


if __name__ == "__main__":
    architecture()
    candidate_map()
    fitness_components()
    convergence()
    print(OUT)
