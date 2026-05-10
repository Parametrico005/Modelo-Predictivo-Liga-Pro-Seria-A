"""
Exporta los modelos .joblib entrenados a JSON para uso en la web (index.html).

Uso:
    python scripts/exportar_modelos_json.py

Genera en output/models/:
    ridge_model.json   → parámetros del scaler + Ridge (embebidos en JS)
    rf_model.json      → árboles del Random Forest (cargado bajo demanda)
    xgb_model.json     → árboles del XGBoost (cargado bajo demanda)

Correr este script cada vez que se reentrene el modelo.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "output" / "models"


def export_ridge(pipeline) -> dict:
    scaler = pipeline.named_steps["scaler"]
    model = pipeline.named_steps["model"]
    return {
        "mean":      scaler.mean_.tolist(),
        "scale":     scaler.scale_.tolist(),
        "coef":      model.coef_.tolist(),
        "intercept": float(model.intercept_),
    }


def export_rf(pipeline) -> dict:
    scaler = pipeline.named_steps["scaler"]
    rf = pipeline.named_steps["model"]

    def tree_to_dict(estimator):
        t = estimator.tree_
        return {
            "f": t.feature.tolist(),
            "t": [round(v, 5) for v in t.threshold.tolist()],
            "v": [round(v, 4) for v in t.value[:, 0, 0].tolist()],
            "l": t.children_left.tolist(),
            "r": t.children_right.tolist(),
        }

    return {
        "scaler": {
            "mean":  scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
        },
        "trees": [tree_to_dict(e) for e in rf.estimators_],
    }


def export_xgb(pipeline) -> dict:
    import pandas as pd

    scaler = pipeline.named_steps["scaler"]
    xgb_step = pipeline.named_steps["model"]
    booster = xgb_step.get_booster()

    config = json.loads(booster.save_config())
    bs_raw = config["learner"]["learner_model_param"]["base_score"]
    base_score = float(re.sub(r"[\[\]]", "", bs_raw))

    df = booster.trees_to_dataframe()
    trees = []
    for tree_id in range(xgb_step.n_estimators):
        tree_df = df[df["Tree"] == tree_id].set_index("Node")
        nodes = []
        for node_idx in sorted(tree_df.index):
            row = tree_df.loc[node_idx]
            if row["Feature"] == "Leaf":
                nodes.append({"leaf": round(float(row["Gain"]), 6)})
            else:
                nodes.append({
                    "f": int(row["Feature"][1:]),
                    "t": round(float(row["Split"]), 6),
                    "y": int(row["Yes"].split("-")[1]),
                    "n": int(row["No"].split("-")[1]),
                })
        trees.append(nodes)

    return {
        "scaler": {
            "mean":  scaler.mean_.tolist(),
            "scale": scaler.scale_.tolist(),
        },
        "base_score": base_score,
        "trees": trees,
    }


def main():
    try:
        import joblib
    except ImportError:
        sys.exit("Instala joblib: pip install joblib")

    print("Cargando modelos...")
    ridge_pipe = joblib.load(MODELS_DIR / "ridge.joblib")
    rf_pipe    = joblib.load(MODELS_DIR / "randomforest.joblib")
    xgb_pipe   = joblib.load(MODELS_DIR / "xgboost.joblib")

    print("Exportando Ridge...", end=" ")
    ridge_data = export_ridge(ridge_pipe)
    out = MODELS_DIR / "ridge_model.json"
    out.write_text(json.dumps(ridge_data))
    print(f"OK ({out.stat().st_size // 1024 + 1} KB)")

    print("Exportando Random Forest...", end=" ")
    rf_data = export_rf(rf_pipe)
    out = MODELS_DIR / "rf_model.json"
    out.write_text(json.dumps(rf_data))
    print(f"OK ({out.stat().st_size // 1024} KB)")

    print("Exportando XGBoost...", end=" ")
    xgb_data = export_xgb(xgb_pipe)
    out = MODELS_DIR / "xgb_model.json"
    out.write_text(json.dumps(xgb_data))
    print(f"OK ({out.stat().st_size // 1024} KB)")

    print("\nTodos los modelos exportados en output/models/")
    print("Haz commit y push a main para actualizar la web.")


if __name__ == "__main__":
    main()
