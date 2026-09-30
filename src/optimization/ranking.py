"""Greedy top-five alternatives using actual polygon edges, in projected metres."""
import shapely


def territorial_top5(candidates, separation_km=0):
    if separation_km < 0:
        raise ValueError('La separación no puede ser negativa.')
    selected, geometries = [], []
    for index, row in candidates.sort_values(['fitness', 'rank'], ascending=[False, True]).iterrows():
        polygon = shapely.from_wkt(row.geometry_wkt)
        if any(polygon.intersection(other).area > 0 or polygon.distance(other) < separation_km * 1000
               for other in geometries):
            continue
        selected.append(index)
        geometries.append(polygon)
        if len(selected) == 5:
            break
    result = candidates.loc[selected].copy()
    result['general_rank'] = result['rank']
    result['rank'] = range(1, len(result) + 1)
    return result
