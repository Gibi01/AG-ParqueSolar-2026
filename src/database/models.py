"""Modelos SQLAlchemy: el almacén relacional del que lee el AG.

Las operaciones pesadas de geometría (distancia, intersección, buffer)
suceden en GeoPandas contra archivos GeoPackage (ver RawLayerCache en
src/data/cache.py y data/raw/layers/*.gpkg) — esa es la herramienta
apropiada para geometrías. Esta base SQLite es la capa de "datos
procesados" consultable y portable descripta en la arquitectura
(RAW -> ETL -> procesamiento geoespacial -> DB local -> AG -> resultados);
las geometrías también se replican acá como texto WKT para
referencia/trazabilidad, pero el AG y la función de fitness solo leen de
acá columnas numéricas simples — nunca geometrías, y nunca la red.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GridCell(Base):
    __tablename__ = "grid_cells"

    cell_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    region_name: Mapped[str] = mapped_column(String, nullable=False)
    resolution_km: Mapped[float] = mapped_column(Float, nullable=False)
    projected_crs: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_x_m: Mapped[float] = mapped_column(Float, nullable=False)
    centroid_y_m: Mapped[float] = mapped_column(Float, nullable=False)
    cell_area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    geometry_wkt: Mapped[str] = mapped_column(Text, nullable=False)


class UrbanArea(Base):
    __tablename__ = "urban_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bahra_id: Mapped[int] = mapped_column(Integer, nullable=True)
    nom_prov: Mapped[str] = mapped_column(String, nullable=True)
    nom_depto: Mapped[str] = mapped_column(String, nullable=True)
    nombre: Mapped[str] = mapped_column(String, nullable=True)
    tipo: Mapped[str] = mapped_column(String, nullable=True)
    fuente: Mapped[str] = mapped_column(String, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geometry_wkt: Mapped[str] = mapped_column(Text, nullable=False)
    used_for_exclusion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PowerLine(Base):
    __tablename__ = "power_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_line_id: Mapped[int] = mapped_column(Integer, nullable=True)
    tension_v: Mapped[float] = mapped_column(Float, nullable=True)
    geometry_wkt: Mapped[str] = mapped_column(Text, nullable=False)


class Transformer(Base):
    __tablename__ = "transformers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String, nullable=True)
    propiedad: Mapped[str] = mapped_column(String, nullable=True)
    concesion: Mapped[str] = mapped_column(String, nullable=True)
    potencia_instalada_mv: Mapped[float] = mapped_column(Float, nullable=True)
    fecha_puesta_servicio: Mapped[str] = mapped_column(String, nullable=True)
    tension_entrada: Mapped[str] = mapped_column(String, nullable=True)
    tension_salida: Mapped[str] = mapped_column(String, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geometry_wkt: Mapped[str] = mapped_column(Text, nullable=False)


class SolarRadiation(Base):
    __tablename__ = "solar_radiation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grid_cell_id: Mapped[int] = mapped_column(ForeignKey("grid_cells.cell_id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    era5_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    era5_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radiation_kwh_m2: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    download_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CandidateLocation(Base):
    __tablename__ = "candidate_locations"

    grid_cell_id: Mapped[int] = mapped_column(ForeignKey("grid_cells.cell_id"), primary_key=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    solar_score: Mapped[float] = mapped_column(Float, nullable=True)
    distance_to_power_line_km: Mapped[float] = mapped_column(Float, nullable=True)
    grid_proximity_score: Mapped[float] = mapped_column(Float, nullable=True)
    distance_to_transformer_km: Mapped[float] = mapped_column(Float, nullable=True)
    transformer_proximity_score: Mapped[float] = mapped_column(Float, nullable=True)
    valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    invalid_reason: Mapped[str] = mapped_column(String, nullable=True)


class OptimizationResult(Base):
    # Tabla nueva para permitir métricas ausentes sin alterar resultados
    # históricos ni intentar una migración destructiva de SQLite.
    __tablename__ = "optimization_results_flexible"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    grid_cell_id: Mapped[int] = mapped_column(ForeignKey("grid_cells.cell_id"), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    solar_score: Mapped[float] = mapped_column(Float, nullable=True)
    distance_to_power_line_km: Mapped[float] = mapped_column(Float, nullable=True)
    distance_to_transformer_km: Mapped[float] = mapped_column(Float, nullable=True)
    grid_proximity_score: Mapped[float] = mapped_column(Float, nullable=True)
    transformer_proximity_score: Mapped[float] = mapped_column(Float, nullable=True)
    fitness: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
