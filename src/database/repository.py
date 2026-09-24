"""Repositorio: el único lugar que habla con la base de datos SQLite.

El algoritmo genético (src/optimization/*) nunca debe consultar una API —
lee las ubicaciones candidatas exclusivamente a través de este
repositorio, que a su vez solo lee del archivo SQLite local. Este módulo
es el punto donde se hace cumplir esa regla arquitectónica.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from src.climate.records import SolarRadiationRecord
from src.database.models import (
    Base,
    CandidateLocation,
    GridCell,
    OptimizationResult,
    PowerLine,
    SolarRadiation,
    Transformer,
    UrbanArea,
)


class Repository:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)

    def _replace_table(self, model, df: pd.DataFrame) -> None:
        table = model.__table__
        with self.engine.begin() as conn:
            conn.execute(delete(table))
            if len(df) > 0:
                df.to_sql(table.name, conn, if_exists="append", index=False)

    # --- escrituras -----------------------------------------------------

    def replace_grid_cells(self, grid_gdf: gpd.GeoDataFrame, region_name: str, resolution_km: float, projected_crs: str) -> None:
        df = pd.DataFrame(
            {
                "cell_id": grid_gdf["cell_id"],
                "region_name": region_name,
                "resolution_km": resolution_km,
                "projected_crs": projected_crs,
                "latitude": grid_gdf["latitude"],
                "longitude": grid_gdf["longitude"],
                "centroid_x_m": grid_gdf["centroid_x_m"],
                "centroid_y_m": grid_gdf["centroid_y_m"],
                "cell_area_m2": grid_gdf["cell_area_m2"],
                "geometry_wkt": grid_gdf.geometry.to_wkt(),
            }
        )
        self._replace_table(GridCell, df)

    def replace_urban_areas(self, urban_gdf: gpd.GeoDataFrame, excluded_types: set[str]) -> None:
        df = pd.DataFrame(
            {
                "bahra_id": urban_gdf["bahra_id"],
                "nom_prov": urban_gdf["nom_prov"],
                "nom_depto": urban_gdf["nom_depto"],
                "nombre": urban_gdf["nombre"],
                "tipo": urban_gdf["tipo"],
                "fuente": urban_gdf["fuente"],
                "latitude": urban_gdf.geometry.y,
                "longitude": urban_gdf.geometry.x,
                "geometry_wkt": urban_gdf.geometry.to_wkt(),
                "used_for_exclusion": urban_gdf["tipo"].isin(excluded_types),
            }
        )
        self._replace_table(UrbanArea, df)

    def replace_power_lines(self, lines_gdf: gpd.GeoDataFrame) -> None:
        df = pd.DataFrame(
            {
                "source_line_id": lines_gdf["line_id"],
                "tension_v": lines_gdf["tension_v"],
                "geometry_wkt": lines_gdf.geometry.to_wkt(),
            }
        )
        self._replace_table(PowerLine, df)

    def clear_power_lines(self) -> None:
        self._replace_table(PowerLine, pd.DataFrame())

    def replace_transformers(self, transformers_gdf: gpd.GeoDataFrame) -> None:
        df = pd.DataFrame(
            {
                "nombre": transformers_gdf.get("nombre"),
                "propiedad": transformers_gdf.get("propiedad"),
                "concesion": transformers_gdf.get("concesion"),
                "potencia_instalada_mv": transformers_gdf.get("potencia_instalada_mv"),
                "fecha_puesta_servicio": transformers_gdf.get("fecha_puesta_servicio"),
                "tension_entrada": transformers_gdf.get("tension_entrada"),
                "tension_salida": transformers_gdf.get("tension_salida"),
                "latitude": transformers_gdf.geometry.y,
                "longitude": transformers_gdf.geometry.x,
                "geometry_wkt": transformers_gdf.geometry.to_wkt(),
            }
        )
        self._replace_table(Transformer, df)

    def clear_transformers(self) -> None:
        self._replace_table(Transformer, pd.DataFrame())

    def replace_solar_radiation(self, records: Iterable[SolarRadiationRecord]) -> None:
        df = pd.DataFrame(
            [
                {
                    "grid_cell_id": r.grid_cell_id,
                    "year": r.year,
                    "month": r.month,
                    "era5_latitude": r.era5_latitude,
                    "era5_longitude": r.era5_longitude,
                    "radiation_kwh_m2": r.radiation_kwh_m2,
                    "source": r.source,
                    "download_timestamp": r.download_timestamp,
                }
                for r in records
            ]
        )
        self._replace_table(SolarRadiation, df)

    def replace_candidate_locations(self, df: pd.DataFrame) -> None:
        self._replace_table(CandidateLocation, df)

    def save_optimization_results(self, run_id: str, ranked_df: pd.DataFrame) -> None:
        df = ranked_df.copy()
        df.insert(0, "run_id", run_id)
        df["created_at"] = datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            df.to_sql(OptimizationResult.__tablename__, conn, if_exists="append", index=False)

    # --- lecturas --------------------------------------------------------

    def get_grid_cells_df(self) -> pd.DataFrame:
        return pd.read_sql("SELECT * FROM grid_cells", self.engine)

    def get_solar_radiation_df(self) -> pd.DataFrame:
        return pd.read_sql("SELECT * FROM solar_radiation", self.engine)

    def get_candidate_locations_df(self, valid_only: bool = True) -> pd.DataFrame:
        query = "SELECT * FROM candidate_locations"
        if valid_only:
            query += " WHERE valid = 1"
        return pd.read_sql(query, self.engine)

    def get_power_lines_gdf(self) -> gpd.GeoDataFrame:
        df = pd.read_sql("SELECT * FROM power_lines", self.engine)
        return gpd.GeoDataFrame(
            df.drop(columns=["geometry_wkt"]),
            geometry=gpd.GeoSeries.from_wkt(df["geometry_wkt"]),
            crs="EPSG:4326",
        )

    def get_transformers_gdf(self) -> gpd.GeoDataFrame:
        df = pd.read_sql("SELECT * FROM transformers", self.engine)
        return gpd.GeoDataFrame(
            df.drop(columns=["geometry_wkt"]),
            geometry=gpd.GeoSeries.from_wkt(df["geometry_wkt"]),
            crs="EPSG:4326",
        )

    def get_urban_areas_gdf(self) -> gpd.GeoDataFrame:
        df = pd.read_sql("SELECT * FROM urban_areas", self.engine)
        return gpd.GeoDataFrame(
            df.drop(columns=["geometry_wkt"]),
            geometry=gpd.GeoSeries.from_wkt(df["geometry_wkt"]),
            crs="EPSG:4326",
        )

    def get_grid_cells_gdf(self) -> gpd.GeoDataFrame:
        df = pd.read_sql("SELECT * FROM grid_cells", self.engine)
        return gpd.GeoDataFrame(
            df.drop(columns=["geometry_wkt"]),
            geometry=gpd.GeoSeries.from_wkt(df["geometry_wkt"]),
            crs="EPSG:4326",
        )

    def session(self) -> Session:
        return Session(self.engine)
