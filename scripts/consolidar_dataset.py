"""Consolida los CSV organizados por categoria y agrega variables rezagadas."""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT       = Path(__file__).resolve().parents[1]
CAT_DIR    = ROOT / "data" / "categorias"
PRESUP_DIR = CAT_DIR / "presupuestarias"
COMPET_DIR = CAT_DIR / "competitivas"
PROC_DIR   = ROOT / "data" / "datasets"
PROC_DIR.mkdir(parents=True, exist_ok=True)

TEMPORADAS_TRAIN = [2019, 2020, 2021, 2022, 2023]
TEMPORADAS_VAL   = [2024]
TEMPORADAS_TEST  = [2025]

# Mapa nombre logico -> (subcarpeta categoria, nombre archivo sin extension)
ARCHIVOS = {
    "ligapro_equipos":                      COMPET_DIR,
    "ligapro_presupuestos":                 PRESUP_DIR,
    "ligapro_plantilla":                    COMPET_DIR,
    "ligapro_cuerpo_tecnico":               COMPET_DIR,
    "ligapro_participacion_internacional":  COMPET_DIR,
    "ligapro_rendimiento_ofensivo":         COMPET_DIR,
    "ligapro_rendimiento_defensivo":        COMPET_DIR,
    "ligapro_posiciones":                   COMPET_DIR,
}


def _leer(nombre):
    path = ARCHIVOS[nombre] / f"{nombre}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontro {path}. Ejecuta primero "
            f"`python scripts/organizar_dataset_por_categoria.py` "
            f"para regenerar la estructura categorizada."
        )
    return pd.read_csv(path)


def _agregar_rezagados(df):
    """Agrega stats de la temporada ANTERIOR por equipo (shift de 1 periodo)."""
    df = df.sort_values(["equipo", "temporada"]).copy()
    mapa = {
        "goles_favor":      "goles_favor_ant",
        "goles_contra":     "goles_contra_ant",
        "diferencia_goles": "diferencia_goles_ant",
        "xg_temporada":     "xg_ant",
        "posesion_prom_pct":"posesion_ant",
    }
    for orig, nuevo in mapa.items():
        df[nuevo] = df.groupby("equipo")[orig].shift(1)
    cols_ant = list(mapa.values())
    for col in cols_ant:
        df[col] = df[col].fillna(df[col].median())
    return df


def consolidar():
    equipos      = _leer("ligapro_equipos")
    presupuestos = _leer("ligapro_presupuestos")
    plantilla    = _leer("ligapro_plantilla")
    cuerpo_tec   = _leer("ligapro_cuerpo_tecnico")
    copas        = _leer("ligapro_participacion_internacional")
    ofensivo     = _leer("ligapro_rendimiento_ofensivo")
    defensivo    = _leer("ligapro_rendimiento_defensivo")
    posiciones   = _leer("ligapro_posiciones")

    df = posiciones.copy()
    for otro in (presupuestos, plantilla, cuerpo_tec, copas, ofensivo, defensivo):
        df = df.merge(otro, on=["equipo", "temporada"], how="left")
    df = df.merge(equipos, on="equipo", how="left")

    df["diferencia_goles"] = df["goles_favor"] - df["goles_contra"]
    df = _agregar_rezagados(df)

    columnas = [
        "temporada", "equipo", "ciudad",
        # Variables pre-temporada (predictores)
        "presupuesto_musd", "salario_promedio_kusd", "inversion_refuerzos_musd",
        "edad_promedio_plantilla", "extranjeros_plantilla",
        "antiguedad_dt_meses", "participacion_internacional", "capacidad_estadio",
        "posicion_temporada_anterior",
        # Rendimiento rezagado (de la temporada anterior)
        "goles_favor_ant", "goles_contra_ant", "diferencia_goles_ant",
        "xg_ant", "posesion_ant",
        # Stats de la temporada en curso (referencia, NO predictores)
        "goles_favor", "goles_contra", "diferencia_goles",
        "xg_temporada", "posesion_prom_pct",
        # Targets
        "puntos_temporada", "posicion_final",
    ]
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas faltantes: {faltantes}")
    return df[columnas].sort_values(["temporada", "posicion_final"]).reset_index(drop=True)


def main():
    df = consolidar()
    df.to_csv(PROC_DIR / "dataset_final.csv", index=False)
    df[df["temporada"].isin(TEMPORADAS_TRAIN)].to_csv(PROC_DIR / "train.csv", index=False)
    df[df["temporada"].isin(TEMPORADAS_VAL)].to_csv(PROC_DIR  / "val.csv",   index=False)
    df[df["temporada"].isin(TEMPORADAS_TEST)].to_csv(PROC_DIR  / "test.csv",  index=False)
    n_train = df["temporada"].isin(TEMPORADAS_TRAIN).sum()
    n_val   = df["temporada"].isin(TEMPORADAS_VAL).sum()
    n_test  = df["temporada"].isin(TEMPORADAS_TEST).sum()
    print(f"Dataset: {len(df)} filas  |  Train={n_train}  Val={n_val}  Test={n_test}")


if __name__ == "__main__":
    main()
