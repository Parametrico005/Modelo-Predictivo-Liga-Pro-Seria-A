"""
Generador de datos ficticios para el modelo predictivo de rendimiento
deportivo en la LigaPro (Serie A de Ecuador).

Sigue la misma organizacion que el repo original (Paul-olulana/
match-outcome-prediction-model): los datos brutos se escriben separados
por categoria en `data/phase1_raw_snapshot/`. La consolidacion final
(`dataset_final.csv`, `train.csv`, `val.csv`, `test.csv`) se realiza
desde `scripts/consolidar_dataset.py`.

Archivos generados en data/phase1_raw_snapshot/:
    1. ligapro_equipos.csv                        - master de clubes
    2. ligapro_presupuestos.csv                   - finanzas por temporada
    3. ligapro_plantilla.csv                      - edad / extranjeros
    4. ligapro_cuerpo_tecnico.csv                 - DT y antiguedad
    5. ligapro_participacion_internacional.csv    - copas
    6. ligapro_rendimiento_ofensivo.csv           - GF, xG, posesion
    7. ligapro_rendimiento_defensivo.csv          - GC
    8. ligapro_posiciones.csv                     - puntos y posicion final

Cuando tengas datos reales, puedes sobrescribir cada CSV por separado
manteniendo el mismo esquema de columnas y luego volver a ejecutar
`consolidar_dataset.py` + `entrenamiento.py`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuracion general
# ---------------------------------------------------------------------------
SEED = 42
TEMPORADAS = [2020, 2021, 2022, 2023, 2024]

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "phase1_raw_snapshot"
RAW_DIR.mkdir(parents=True, exist_ok=True)

EQUIPOS_BASE = [
    {"equipo": "Barcelona SC",              "presupuesto_base": 17.0, "capacidad_estadio": 57267, "ciudad": "Guayaquil"},
    {"equipo": "LDU Quito",                 "presupuesto_base": 14.5, "capacidad_estadio": 41575, "ciudad": "Quito"},
    {"equipo": "Emelec",                    "presupuesto_base": 12.0, "capacidad_estadio": 40000, "ciudad": "Guayaquil"},
    {"equipo": "Independiente del Valle",   "presupuesto_base": 11.0, "capacidad_estadio": 12000, "ciudad": "Sangolqui"},
    {"equipo": "El Nacional",               "presupuesto_base": 5.0,  "capacidad_estadio": 40948, "ciudad": "Quito"},
    {"equipo": "Universidad Catolica",      "presupuesto_base": 4.2,  "capacidad_estadio": 18900, "ciudad": "Quito"},
    {"equipo": "Aucas",                     "presupuesto_base": 4.0,  "capacidad_estadio": 20000, "ciudad": "Quito"},
    {"equipo": "Delfin SC",                 "presupuesto_base": 3.2,  "capacidad_estadio": 18000, "ciudad": "Manta"},
    {"equipo": "Deportivo Cuenca",          "presupuesto_base": 3.0,  "capacidad_estadio": 17500, "ciudad": "Cuenca"},
    {"equipo": "Macara",                    "presupuesto_base": 2.6,  "capacidad_estadio": 18500, "ciudad": "Ambato"},
    {"equipo": "Tecnico Universitario",     "presupuesto_base": 2.2,  "capacidad_estadio": 19695, "ciudad": "Ambato"},
    {"equipo": "Mushuc Runa",               "presupuesto_base": 2.1,  "capacidad_estadio": 8000,  "ciudad": "Ambato"},
    {"equipo": "Orense SC",                 "presupuesto_base": 1.9,  "capacidad_estadio": 16500, "ciudad": "Machala"},
    {"equipo": "Libertad FC",               "presupuesto_base": 1.7,  "capacidad_estadio": 4500,  "ciudad": "Loja"},
    {"equipo": "Cumbaya FC",                "presupuesto_base": 1.6,  "capacidad_estadio": 3500,  "ciudad": "Cumbaya"},
    {"equipo": "Imbabura SC",               "presupuesto_base": 1.5,  "capacidad_estadio": 18084, "ciudad": "Ibarra"},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clip(val: float, lo: float, hi: float) -> float:
    return float(max(lo, min(hi, val)))


def _ruido(rng: np.random.Generator, escala: float) -> float:
    return float(rng.normal(0.0, escala))


# ---------------------------------------------------------------------------
# Simulacion principal
# ---------------------------------------------------------------------------
def generar_tablas(seed: int = SEED) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    # Posicion previa (ficticia) antes de 2020, ordenada por presupuesto
    pos_previa = {
        eq["equipo"]: rank
        for rank, eq in enumerate(
            sorted(EQUIPOS_BASE, key=lambda e: -e["presupuesto_base"]), start=1
        )
    }

    # Acumuladores
    presupuestos, plantilla, cuerpo_tecnico, copas = [], [], [], []
    ofensivo, defensivo, posiciones = [], [], []

    for temporada in TEMPORADAS:
        filas_temp = []
        for eq in EQUIPOS_BASE:
            # Finanzas
            factor_anio = 1.0 + 0.04 * (temporada - 2020)
            presupuesto = _clip(eq["presupuesto_base"] * factor_anio * rng.normal(1.0, 0.08), 0.8, 25.0)
            salario = _clip(1.4 * presupuesto + rng.normal(0, 0.8), 1.5, 45.0)
            refuerzos = _clip(presupuesto * rng.uniform(0.08, 0.30), 0.05, 8.0)

            # Plantilla
            edad = _clip(rng.normal(26.0, 1.6), 22.0, 31.0)
            extranjeros = int(_clip(3 + int(round(presupuesto * 0.35)) + rng.integers(-2, 3), 0, 12))

            # Cuerpo tecnico
            antig_dt = int(_clip(rng.integers(1, 36), 1, 60))

            # Participacion internacional segun posicion del ano anterior
            pos_ant = pos_previa[eq["equipo"]]
            if pos_ant <= 4:
                part_int = int(_clip(rng.integers(8, 14), 0, 16))
            elif pos_ant <= 8:
                part_int = int(_clip(rng.integers(4, 9), 0, 12))
            else:
                part_int = 0

            # Rendimiento deportivo
            xg = _clip(18 + 1.6 * presupuesto + _ruido(rng, 6.0), 15.0, 75.0)
            gf = int(_clip(0.85 * xg + _ruido(rng, 4.0), 10, 80))
            gc = int(_clip(60 - 1.2 * presupuesto + _ruido(rng, 6.0), 15, 85))
            posesion = _clip(45 + 0.7 * presupuesto + _ruido(rng, 3.5), 35.0, 62.0)

            # Score de fortaleza + ruido real
            score = (
                0.42 * presupuesto
                + 0.18 * refuerzos
                + 0.14 * xg / 10.0
                + 0.10 * posesion / 10.0
                + 0.08 * (17 - pos_ant)
                + 0.05 * (part_int / 4.0)
                - 0.04 * (gc / 10.0)
                + _ruido(rng, 2.2)
            )

            filas_temp.append({
                "equipo": eq["equipo"], "temporada": temporada,
                "presupuesto": round(presupuesto, 2), "salario": round(salario, 2),
                "refuerzos": round(refuerzos, 2),
                "edad": round(edad, 2), "extranjeros": extranjeros,
                "antig_dt": antig_dt, "part_int": part_int,
                "xg": round(xg, 2), "gf": gf, "gc": gc,
                "posesion": round(posesion, 2), "pos_ant": pos_ant,
                "score": score,
            })

        # Ranking por score => posicion final
        filas_temp.sort(key=lambda f: -f["score"])
        for posicion_final, fila in enumerate(filas_temp, start=1):
            fila["posicion_final"] = posicion_final
            fila["puntos"] = int(_clip(78 - 2.9 * (posicion_final - 1) + rng.normal(0, 3.5), 18, 85))
            pos_previa[fila["equipo"]] = posicion_final

            presupuestos.append({
                "equipo": fila["equipo"], "temporada": fila["temporada"],
                "presupuesto_musd": fila["presupuesto"],
                "salario_promedio_kusd": fila["salario"],
                "inversion_refuerzos_musd": fila["refuerzos"],
            })
            plantilla.append({
                "equipo": fila["equipo"], "temporada": fila["temporada"],
                "edad_promedio_plantilla": fila["edad"],
                "extranjeros_plantilla": fila["extranjeros"],
            })
            cuerpo_tecnico.append({
                "equipo": fila["equipo"], "temporada": fila["temporada"],
                "antiguedad_dt_meses": fila["antig_dt"],
            })
            copas.append({
                "equipo": fila["equipo"], "temporada": fila["temporada"],
                "participacion_internacional": fila["part_int"],
            })
            ofensivo.append({
                "equipo": fila["equipo"], "temporada": fila["temporada"],
                "goles_favor": fila["gf"],
                "xg_temporada": fila["xg"],
                "posesion_prom_pct": fila["posesion"],
            })
            defensivo.append({
                "equipo": fila["equipo"], "temporada": fila["temporada"],
                "goles_contra": fila["gc"],
            })
            posiciones.append({
                "equipo": fila["equipo"], "temporada": fila["temporada"],
                "puntos_temporada": fila["puntos"],
                "posicion_temporada_anterior": fila["pos_ant"],
                "posicion_final": fila["posicion_final"],
            })

    equipos_df = pd.DataFrame([
        {"equipo": e["equipo"], "ciudad": e["ciudad"], "capacidad_estadio": e["capacidad_estadio"]}
        for e in EQUIPOS_BASE
    ])

    return {
        "ligapro_equipos": equipos_df,
        "ligapro_presupuestos": pd.DataFrame(presupuestos),
        "ligapro_plantilla": pd.DataFrame(plantilla),
        "ligapro_cuerpo_tecnico": pd.DataFrame(cuerpo_tecnico),
        "ligapro_participacion_internacional": pd.DataFrame(copas),
        "ligapro_rendimiento_ofensivo": pd.DataFrame(ofensivo),
        "ligapro_rendimiento_defensivo": pd.DataFrame(defensivo),
        "ligapro_posiciones": pd.DataFrame(posiciones),
    }


def main() -> None:
    tablas = generar_tablas()
    print(f"Escribiendo CSVs en: {RAW_DIR}")
    for nombre, df in tablas.items():
        path = RAW_DIR / f"{nombre}.csv"
        df.to_csv(path, index=False)
        print(f"  - {path.name:45s} filas={len(df):3d}")


if __name__ == "__main__":
    main()
