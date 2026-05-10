"""
Entrenamiento comparativo de tres modelos para predecir la posicion final
de cada club en la LigaPro:

    1. Regresion lineal regularizada (Ridge)  -> linea base interpretable
    2. Random Forest Regressor                -> modelo no lineal robusto
    3. Gradient Boosting (XGBoost si esta     -> mejor rendimiento esperado
       instalado, sklearn como fallback)

Metricas reportadas:
    - MAE (error absoluto medio, en puestos)
    - RMSE (error cuadratico medio, en puestos)
    - R2 (coeficiente de determinacion)
    - Spearman (correlacion de ranking)

Ejecucion:
    python scripts/entrenamiento.py
"""

from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Permite importar preprocesamiento.py cuando se ejecuta como script
sys.path.append(str(Path(__file__).resolve().parent))
from preprocesamiento import (  # noqa: E402
    FEATURES, TARGET, cargar_dataset, construir_xy, particion_temporal,
)

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / "data" / "datasets" / "dataset_final.csv"
MODELS_DIR = ROOT / "output" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Particion temporal por defecto (facil de ajustar con datos reales)
TEMPORADAS_TRAIN = [2019, 2020, 2021, 2022, 2023]
TEMPORADAS_VAL = [2024]
TEMPORADAS_TEST = [2025]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _get_xgboost_or_fallback():
    """Devuelve (modelo, nombre). Usa XGBoost si esta disponible."""
    try:
        from xgboost import XGBRegressor  # type: ignore

        modelo = XGBRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            n_jobs=-1,
        )
        return modelo, "XGBoost"
    except Exception:
        modelo = GradientBoostingRegressor(
            n_estimators=400,
            learning_rate=0.05,
            max_depth=3,
            random_state=42,
        )
        return modelo, "GradientBoosting (sklearn)"


def construir_modelos() -> dict:
    """Define los tres pipelines a comparar."""
    ridge = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0, random_state=42)),
        ]
    )

    rf = Pipeline(
        [
            ("scaler", StandardScaler(with_mean=False)),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=500,
                    max_depth=None,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    boosting_model, boosting_name = _get_xgboost_or_fallback()
    boosting = Pipeline(
        [
            ("scaler", StandardScaler(with_mean=False)),
            ("model", boosting_model),
        ]
    )

    return {
        "ridge": ridge,
        "randomforest": rf,
        "xgboost": boosting,
    }, boosting_name


def _spearman(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Correlacion de Spearman implementada con numpy (evita scipy)."""
    rt = pd.Series(y_true).rank().to_numpy()
    rp = pd.Series(y_pred).rank().to_numpy()
    if np.std(rt) == 0 or np.std(rp) == 0:
        return float("nan")
    return float(np.corrcoef(rt, rp)[0, 1])


def evaluar(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Calcula metricas principales."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = r2_score(y_true, y_pred)
    rho = _spearman(np.asarray(y_true), np.asarray(y_pred))
    return {
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "R2": round(float(r2), 4),
        "Spearman": round(float(rho), 4),
    }


# ---------------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"Cargando dataset desde: {DATA_CSV}")
    df = cargar_dataset(DATA_CSV)

    train, val, test = particion_temporal(
        df, TEMPORADAS_TRAIN, TEMPORADAS_VAL, TEMPORADAS_TEST
    )
    X_train, y_train, _ = construir_xy(train)
    X_val, y_val, _ = construir_xy(val)
    X_test, y_test, _ = construir_xy(test)

    print(f"Filas Train / Val / Test: {len(X_train)} / {len(X_val)} / {len(X_test)}")

    modelos, boosting_name = construir_modelos()
    print(f"Modelos a comparar: Ridge, Random Forest, {boosting_name}\n")

    resultados: dict = {}
    mejor_nombre = None
    mejor_mae = float("inf")

    for nombre, pipeline in modelos.items():
        pipeline.fit(X_train, y_train)
        pred_val = pipeline.predict(X_val)
        pred_test = pipeline.predict(X_test)

        metricas_val = evaluar(y_val.to_numpy(), pred_val)
        metricas_test = evaluar(y_test.to_numpy(), pred_test)

        resultados[nombre] = {
            "validacion": metricas_val,
            "test": metricas_test,
        }

        print(f"[{nombre}]")
        print(f"  Val  -> {metricas_val}")
        print(f"  Test -> {metricas_test}")

        # Guardar cada modelo
        joblib.dump(pipeline, MODELS_DIR / f"{nombre}.joblib")

        if metricas_val["MAE"] < mejor_mae:
            mejor_mae = metricas_val["MAE"]
            mejor_nombre = nombre

    print(f"\nMejor modelo (por MAE en validacion): {mejor_nombre}")
    joblib.dump(modelos[mejor_nombre], MODELS_DIR / "mejor_modelo.joblib")

    # Guardar resumen completo
    resumen = {
        "modelos": resultados,
        "mejor_modelo": mejor_nombre,
        "features": FEATURES,
        "target": TARGET,
        "particion": {
            "train": TEMPORADAS_TRAIN,
            "val": TEMPORADAS_VAL,
            "test": TEMPORADAS_TEST,
        },
        "n_filas": {
            "train": int(len(X_train)),
            "val": int(len(X_val)),
            "test": int(len(X_test)),
        },
    }
    with open(MODELS_DIR / "model_card.json", "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print(f"Resumen guardado en: {MODELS_DIR / 'model_card.json'}")


if __name__ == "__main__":
    main()
