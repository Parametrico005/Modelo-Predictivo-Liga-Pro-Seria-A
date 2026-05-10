"""
Preprocesamiento para el modelo predictivo LigaPro.
TARGET: puntos_temporada (puntos al final de la temporada).
FEATURES: solo variables conocidas ANTES de que empiece la temporada.
"""

from __future__ import annotations
from pathlib import Path
from typing import Tuple
import pandas as pd

# Variables pre-temporada (no hay datos del partido en curso)
FEATURES: list[str] = [
    # Economicas
    "presupuesto_musd",
    "salario_promedio_kusd",
    "inversion_refuerzos_musd",
    # Plantilla
    "edad_promedio_plantilla",
    "extranjeros_plantilla",
    # Cuerpo tecnico
    "antiguedad_dt_meses",
    # Contexto
    "participacion_internacional",
    "capacidad_estadio",
    # Temporada anterior
    "posicion_temporada_anterior",
    # Rendimiento deportivo de la temporada ANTERIOR (rezagado)
    "goles_favor_ant",
    "goles_contra_ant",
    "diferencia_goles_ant",
    "xg_ant",
    "posesion_ant",
]

TARGET: str = "puntos_temporada"
ID_COLS: list[str] = ["temporada", "equipo"]


def cargar_dataset(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    faltantes = [c for c in FEATURES + [TARGET] + ID_COLS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas faltantes en {csv_path.name}: {faltantes}")
    return df


def construir_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    X    = df[FEATURES].copy()
    y    = df[TARGET].astype(float)
    meta = df[ID_COLS].copy()
    return X, y, meta


def particion_temporal(
    df: pd.DataFrame,
    temporadas_train: list[int],
    temporadas_val: list[int],
    temporadas_test: list[int],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["temporada"].isin(temporadas_train)].copy()
    val   = df[df["temporada"].isin(temporadas_val)].copy()
    test  = df[df["temporada"].isin(temporadas_test)].copy()
    return train, val, test
