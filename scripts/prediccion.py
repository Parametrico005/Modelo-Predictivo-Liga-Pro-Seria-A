"""
Inferencia con el mejor modelo entrenado.

Uso:
    python scripts/prediccion.py --csv_entrada data/datasets/test.csv \
        --csv_salida prediccion_nueva_temporada.csv

El CSV de entrada debe tener las columnas definidas en FEATURES
(ver scripts/preprocesamiento.py) ademas de 'temporada' y 'equipo'.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from preprocesamiento import FEATURES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = ROOT / "output" / "models" / "mejor_modelo.joblib"


def rankear(predicciones: np.ndarray) -> np.ndarray:
    order = np.argsort(predicciones, kind="stable")
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(order) + 1)
    return ranks


def predecir(csv_entrada: Path, csv_salida: Path, modelo_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_entrada)
    faltantes = [c for c in FEATURES if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en {csv_entrada.name}: {faltantes}")

    pipeline = joblib.load(modelo_path)
    pred = pipeline.predict(df[FEATURES])
    ranking = rankear(pred)

    salida = df[["temporada", "equipo"]].copy() if "equipo" in df.columns else df.copy()
    salida["posicion_predicha_continua"] = np.round(pred, 2)
    salida["posicion_predicha_ranking"] = ranking
    salida = salida.sort_values("posicion_predicha_ranking")
    salida.to_csv(csv_salida, index=False)
    return salida


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv_entrada", type=Path, required=True)
    parser.add_argument("--csv_salida", type=Path, required=True)
    parser.add_argument("--modelo", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()

    salida = predecir(args.csv_entrada, args.csv_salida, args.modelo)
    print(salida.to_string(index=False))
    print(f"\nPredicciones guardadas en: {args.csv_salida}")


if __name__ == "__main__":
    main()
