from __future__ import annotations

from pathlib import Path

import sqlite3
from shapely import wkt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from current_run import RUN


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
    bounds = draw.multiline_textbbox((0, 0), text, font=fnt, align="center", spacing=spacing)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.multiline_text(((x1 + x2 - width) / 2, (y1 + y2 - height) / 2), text,
                        font=fnt, fill=fill, align="center", spacing=spacing)


def arrow(draw, start, end, color="#222222", width=3):
    draw.line([start, end], fill=color, width=width)
    vector = np.array([end[0] - start[0], end[1] - start[1]], dtype=float)
    unit = vector / np.linalg.norm(vector)
    normal = np.array([-unit[1], unit[0]])
    tip = np.array(end)
    draw.polygon([tuple(tip), tuple(tip - unit * 14 + normal * 7), tuple(tip - unit * 14 - normal * 7)], fill=color)


def architecture():
    image, draw = canvas(1800, 720)
    draw.text((55, 35), "Del problema territorial a configuraciones de parque comparables", font=font(32, bold=True), fill="#222222")
    labels = ["Fuentes\ngeoespaciales", "Grilla de\n500 m", "Restricciones\ny métricas", "Parques\ncontiguos", "Búsqueda\ngenética"]
    boxes = []
    for index, label in enumerate(labels):
        x1 = 55 + index * 345
        box = (x1, 185, x1 + 280, 335)
        boxes.append(box)
        draw.rounded_rectangle(box, radius=18, fill="#ececec", outline="#222222", width=3)
        centered(draw, box, label, font(29, bold=True))
        if index:
            arrow(draw, (boxes[index - 1][2] + 12, 260), (box[0] - 12, 260))
    lower = [(1090, 455, 1370, 610), (1435, 455, 1715, 610)]
    for box, label in zip(lower, ("TOP 5 general\npuede solaparse", "TOP 5 territorial\nsin solapamiento")):
        draw.rounded_rectangle(box, radius=18, fill="#ececec", outline="#222222", width=3)
        centered(draw, box, label, font(27, bold=True))
    arrow(draw, (1575, 345), (1575, 440))
    arrow(draw, (1420, 532), (1385, 532))
    draw.text((55, 655), "El sistema apoya la preselección; no acredita disponibilidad del suelo ni conexión eléctrica.",
              font=font(27, italic=True), fill="#333333")
    image.save(OUT / "figura_arquitectura.png", dpi=(240, 240))


def territorial_map(ranking=None, province=None, output=None):
    ranking = RUN["territorial"] if ranking is None else ranking
    if province is None:
        with sqlite3.connect(RUN['configuration']['paths']['database']) as connection:
            geometry, = connection.execute(
                'SELECT geometry_wkt FROM layer_region WHERE dataset_id = ?',
                (RUN['metadata']['dataset_id'],),
            ).fetchone()
        province = wkt.loads(geometry)
    minx, miny, maxx, maxy = province.bounds
    minx, maxx = minx - .12, maxx + .12
    miny, maxy = miny - .12, maxy + .12
    image, draw = canvas(1200, 1420)
    draw.text((55, 35), "Cinco configuraciones territoriales sin superposición", font=font(34, bold=True), fill="#222222")
    plot = (100, 125, 1100, 1260)
    scale = min((plot[2] - plot[0]) / (maxx - minx), (plot[3] - plot[1]) / (maxy - miny))
    xoff = (plot[0] + plot[2] - (maxx - minx) * scale) / 2
    yoff = (plot[1] + plot[3] - (maxy - miny) * scale) / 2

    def xy(x, y):
        return xoff + (x - minx) * scale, plot[3] - (yoff - plot[1]) - (y - miny) * scale

    draw.rounded_rectangle(plot, radius=15, fill="#f2f2f2", outline="#555555", width=2)
    polygons = [province] if province.geom_type == "Polygon" else list(province.geoms)
    for polygon in polygons:
        draw.polygon([xy(x, y) for x, y in polygon.exterior.coords], fill="#e8ece8")
        for interior in polygon.interiors:
            draw.polygon([xy(x, y) for x, y in interior.coords], fill="#f2f2f2")
    for latitude in range(int(np.ceil(miny)), int(np.floor(maxy)) + 1):
        _, y = xy(minx, latitude)
        draw.line((plot[0], y, plot[2], y), fill="#dddddd", width=1)
        draw.text((plot[0] + 8, y + 4), f"{latitude}°", font=font(18), fill="#777777")
    for longitude in range(int(np.ceil(minx)), int(np.floor(maxx)) + 1):
        x, _ = xy(longitude, miny)
        draw.line((x, plot[1], x, plot[3]), fill="#dddddd", width=1)
        draw.text((x + 4, plot[3] - 26), f"{longitude}°", font=font(18), fill="#777777")
    for polygon in polygons:
        draw.line([xy(x, y) for x, y in polygon.exterior.coords], fill="#555555", width=5, joint="curve")
        for interior in polygon.interiors:
            draw.line([xy(x, y) for x, y in interior.coords], fill="#777777", width=3, joint="curve")
    colors = ["#111111", "#555555", "#777777", "#999999", "#bbbbbb"]
    for row, color in zip(ranking.itertuples(), colors):
        x, y = xy(row.longitude, row.latitude)
        draw.ellipse((x - 22, y - 22, x + 22, y + 22), fill=color, outline="white", width=3)
        centered(draw, (x - 22, y - 22, x + 22, y + 22), str(int(row.rank)), font(18, bold=True), fill="white")
        label_offsets = {3: (-115, -70), 4: (35, -8), 5: (-125, 42)}
        dx, dy = label_offsets.get(int(row.rank), (28, -14))
        draw.text((x + dx, y + dy), f"#{int(row.rank)} · {row.station_id}", font=font(20, bold=True), fill="#222222")
    draw.text((100, 1290), "Parques contiguos de área variable; grilla de 500 m y límite de 80 MW.", font=font(24), fill="#222222")
    draw.text((100, 1335), "La separación configurada es 0 km: se evita el solapamiento, no la cercanía.", font=font(22, italic=True), fill="#444444")
    image.save(output or OUT / "figura_mapa_territorial.png", dpi=(240, 240))


def fitness_components():
    ranking = RUN["territorial"]
    weights = RUN["configuration"]["fitness"]
    components = [
        ("Radiación", "weight_solar", weights["weight_solar"] * ranking.solar_score.to_numpy(), "#222222"),
        ("Líneas", "weight_grid_distance", weights["weight_grid_distance"] * ranking.grid_proximity_score.to_numpy(), "#666666"),
        ("Transformadores", "weight_transformer_distance", weights["weight_transformer_distance"] * ranking.transformer_proximity_score.to_numpy(), "#aaaaaa"),
        ("Potencia", "weight_installed_power", weights["weight_installed_power"] * ranking.installed_power_score.to_numpy(), "#dddddd"),
        ("Forma", "weight_compactness", weights["weight_compactness"] * ranking.compactness_score.to_numpy(), "#b0b0b0"),
    ]
    image, draw = canvas(1800, 900)
    draw.text((65, 35), "Aportes al fitness del TOP 5 territorial", font=font(34, bold=True), fill="#222222")
    plot = (120, 160, 1720, 720)
    ymax = 0.8
    for tick in np.arange(0, 0.81, 0.2):
        y = plot[3] - tick / ymax * (plot[3] - plot[1])
        draw.line((plot[0], y, plot[2], y), fill="#dedede", width=2)
        draw.text((45, y - 14), f"{tick:.1f}", font=font(22), fill="#333333")
    slot = (plot[2] - plot[0]) / len(ranking)
    for index, row in enumerate(ranking.itertuples()):
        x1, x2 = plot[0] + index * slot + slot * .18, plot[0] + (index + 1) * slot - slot * .18
        bottom = plot[3]
        for _, _, values, color in components:
            height = values[index] / ymax * (plot[3] - plot[1])
            draw.rectangle((x1, bottom - height, x2, bottom), fill=color, outline="#444444")
            bottom -= height
        centered(draw, (x1, 735, x2, 795), f"#{int(row.rank)}\n{row.station_id}", font(20))
    x = 125
    for label, key, _, color in components:
        draw.rectangle((x, 835, x + 30, 860), fill=color, outline="#333333")
        draw.text((x + 42, 831), f"{label} × {weights[key]:.2f}", font=font(21), fill="#222222")
        x += 330
    image.save(OUT / "figura_componentes_fitness.png", dpi=(240, 240))


def convergence():
    history = RUN["history"]
    image, draw = canvas(1800, 850)
    draw.text((65, 35), "Evolución observada en la corrida vigente", font=font(34, bold=True), fill="#222222")
    plot = (130, 145, 1710, 695)
    ymin, ymax = 0.48, 0.74
    for tick in np.arange(0.48, 0.741, 0.04):
        y = plot[3] - (tick - ymin) / (ymax - ymin) * (plot[3] - plot[1])
        draw.line((plot[0], y, plot[2], y), fill="#dedede", width=2)
        draw.text((50, y - 14), f"{tick:.2f}", font=font(22), fill="#333333")
    generations = int(history.generation.max())

    def points(column):
        return [(plot[0] + row.generation / generations * (plot[2] - plot[0]),
                 plot[3] - (getattr(row, column) - ymin) / (ymax - ymin) * (plot[3] - plot[1]))
                for row in history.itertuples()]

    draw.line(points("best_historical_fitness"), fill="#111111", width=5)
    draw.line(points("mean_fitness"), fill="#888888", width=4)
    for tick in (0, 50, 100, 150, 200):
        x = plot[0] + tick / generations * (plot[2] - plot[0])
        draw.text((x - 12, plot[3] + 15), str(tick), font=font(21), fill="#333333")
    draw.text((785, 755), "Generación", font=font(24), fill="#222222")
    draw.line((1110, 780, 1170, 780), fill="#111111", width=5)
    draw.text((1185, 765), "Mejor visto", font=font(22), fill="#222222")
    draw.line((1410, 780, 1470, 780), fill="#888888", width=5)
    draw.text((1485, 765), "Media", font=font(22), fill="#222222")
    image.save(OUT / "figura_convergencia.png", dpi=(240, 240))


if __name__ == "__main__":
    architecture()
    territorial_map()
    fitness_components()
    convergence()
    print(f"Figuras actualizadas desde {RUN['metadata']['run_id']}: {OUT}")
