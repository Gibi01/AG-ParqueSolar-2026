from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def latest_complete_run() -> Path:
    runs = [
        path
        for path in (ROOT / "results" / "spatial").glob("run-*")
        if all((path / name).exists() for name in (
            "optimization_run.json", "ranking.csv", "ranking_territorial.csv", "history.csv"
        ))
    ]
    if not runs:
        raise FileNotFoundError("No hay corridas espaciales completas en results/spatial.")
    return max(runs, key=lambda path: path.name)


def load_run_summary() -> dict:
    run_dir = latest_complete_run()
    metadata = json.loads((run_dir / "optimization_run.json").read_text(encoding="utf-8"))
    ranking = pd.read_csv(run_dir / "ranking.csv").sort_values("rank")
    territorial = pd.read_csv(run_dir / "ranking_territorial.csv").sort_values("rank")
    history = pd.read_csv(run_dir / "history.csv").sort_values("generation")
    candidates = pd.read_csv(run_dir / "candidates.csv")

    dataset_id = metadata["dataset_id"]
    database = Path(metadata["configuration"]["paths"]["database"])
    with sqlite3.connect(database) as connection:
        total, valid = connection.execute(
            "SELECT COUNT(*), SUM(valid) FROM spatial_cells WHERE dataset_id = ?",
            (dataset_id,),
        ).fetchone()
        invalid_reasons = dict(connection.execute(
            "SELECT COALESCE(invalid_reason, 'valid'), COUNT(*) "
            "FROM spatial_cells WHERE dataset_id = ? GROUP BY invalid_reason",
            (dataset_id,),
        ).fetchall())

    cfg = metadata["configuration"]
    final = history.iloc[-1]
    return {
        "root": ROOT,
        "run_dir": run_dir,
        "metadata": metadata,
        "configuration": cfg,
        "ranking": ranking,
        "territorial": territorial,
        "history": history,
        "candidates": candidates,
        "first": ranking.iloc[0],
        "total_cells": int(total),
        "valid_cells": int(valid),
        "urban_excluded": int(invalid_reasons.get("intersects_urban_area", 0)),
        "excluded_pct": 100 * (int(total) - int(valid)) / int(total),
        "final_unique": int(final["unique_parks"]),
        "final_population": int(final["population_size"]),
        "archive_size": len(candidates),
        "climate_periods": metadata["dataset"]["climate_periods"],
    }


RUN = load_run_summary()
