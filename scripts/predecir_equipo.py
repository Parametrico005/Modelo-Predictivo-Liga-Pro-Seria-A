"""
Prediccion de puntos para UN equipo en una temporada futura.

Uso interactivo:
    python scripts/predecir_equipo.py

Uso con argumentos (para automatizar):
    python scripts/predecir_equipo.py \
        --equipo "Barcelona SC" \
        --temporada 2027 \
        --presupuesto 19.5 \
        --salario 27.0 \
        --refuerzos 4.2 \
        --edad 26.5 \
        --extranjeros 8 \
        --dt_meses 14 \
        --copas 10 \
        --estadio 57267 \
        --pos_anterior 1 \
        --gf_anterior 42 \
        --gc_anterior 28 \
        --xg_anterior 51.0 \
        --posesion_anterior 55.0
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from preprocesamiento import FEATURES  # noqa: E402

MODEL_PATH = ROOT / "output" / "models" / "mejor_modelo.joblib"


def _pedir(prompt: str, tipo=float, default=None):
    sufijo = f" [{default}]" if default is not None else ""
    while True:
        val = input(f"  {prompt}{sufijo}: ").strip()
        if val == "" and default is not None:
            return tipo(default)
        try:
            return tipo(val)
        except ValueError:
            print(f"    -> Ingresa un valor numerico valido.")


def pedir_datos_interactivo() -> dict:
    print("\n" + "="*55)
    print("  PREDICCION DE PUNTOS — LigaPro")
    print("="*55)
    equipo    = input("  Nombre del equipo (ej: Barcelona SC): ").strip() or "Mi Equipo"
    temporada = _pedir("Temporada a predecir (ej: 2027)", int, 2027)

    print("\n--- ECONOMICAS ---")
    presupuesto = _pedir("Presupuesto total (millones USD, ej: 19.5)", float)
    salario     = _pedir("Salario promedio plantilla (miles USD/mes, ej: 27.0)", float)
    refuerzos   = _pedir("Inversion en refuerzos (millones USD, ej: 4.2)", float)

    print("\n--- PLANTILLA ---")
    edad        = _pedir("Edad promedio plantilla (ej: 26.5)", float)
    extranjeros = _pedir("Numero de extranjeros (ej: 8)", int)

    print("\n--- CUERPO TECNICO ---")
    dt_meses    = _pedir("Meses del DT en el cargo al inicio de temporada (ej: 14)", int)

    print("\n--- CONTEXTO ---")
    copas       = _pedir("Partidos internacionales esperados (ej: 10, o 0 si no clasifica)", int)
    estadio     = _pedir("Capacidad del estadio (ej: 57267)", int)

    print("\n--- TEMPORADA ANTERIOR ---")
    pos_ant     = _pedir("Posicion final temporada anterior (1=campeon, 16=ultimo, ej: 2)", int)
    gf_ant      = _pedir("Goles a favor temporada anterior (ej: 42)", int)
    gc_ant      = _pedir("Goles en contra temporada anterior (ej: 28)", int)
    xg_ant      = _pedir("xG (expected goals) temporada anterior (ej: 51.0)", float)
    pos_ant_pct = _pedir("Posesion promedio % temporada anterior (ej: 55.0)", float)

    return dict(
        equipo=equipo, temporada=temporada,
        presupuesto_musd=presupuesto,
        salario_promedio_kusd=salario,
        inversion_refuerzos_musd=refuerzos,
        edad_promedio_plantilla=edad,
        extranjeros_plantilla=extranjeros,
        antiguedad_dt_meses=dt_meses,
        participacion_internacional=copas,
        capacidad_estadio=estadio,
        posicion_temporada_anterior=pos_ant,
        goles_favor_ant=gf_ant,
        goles_contra_ant=gc_ant,
        diferencia_goles_ant=gf_ant - gc_ant,
        xg_ant=xg_ant,
        posesion_ant=pos_ant_pct,
    )


def predecir(datos: dict) -> float:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "No se encontro el modelo entrenado. Ejecuta primero:\n"
            "  python scripts/entrenamiento.py"
        )
    modelo = joblib.load(MODEL_PATH)
    X = pd.DataFrame([{f: datos[f] for f in FEATURES}])
    puntos = float(modelo.predict(X)[0])
    return round(puntos, 1)


def mostrar_resultado(datos: dict, puntos: float):
    print("\n" + "="*55)
    print(f"  PREDICCION: {datos['equipo']} — Temporada {datos['temporada']}")
    print("="*55)
    print(f"\n  Puntos estimados : {puntos:.1f} puntos")

    if puntos >= 70:
        zona = "CAMPEON o zona de titulo"
    elif puntos >= 55:
        zona = "Clasificacion a Copa Libertadores / Sudamericana"
    elif puntos >= 40:
        zona = "Zona media de la tabla"
    else:
        zona = "Zona de descenso o lucha por la permanencia"
    print(f"  Zona proyectada  : {zona}")

    print("\n  Datos usados:")
    print(f"    Presupuesto      : USD {datos['presupuesto_musd']:.1f}M")
    print(f"    Salario prom.    : USD {datos['salario_promedio_kusd']:.1f}k/mes")
    print(f"    Inversion fichajes: USD {datos['inversion_refuerzos_musd']:.1f}M")
    print(f"    Posicion anterior: {datos['posicion_temporada_anterior']}")
    print(f"    Goles ant.       : {datos['goles_favor_ant']} GF / {datos['goles_contra_ant']} GC")
    print("="*55 + "\n")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--equipo",      default=None)
    parser.add_argument("--temporada",   type=int,   default=None)
    parser.add_argument("--presupuesto", type=float, default=None)
    parser.add_argument("--salario",     type=float, default=None)
    parser.add_argument("--refuerzos",   type=float, default=None)
    parser.add_argument("--edad",        type=float, default=None)
    parser.add_argument("--extranjeros", type=int,   default=None)
    parser.add_argument("--dt_meses",    type=int,   default=None)
    parser.add_argument("--copas",       type=int,   default=None)
    parser.add_argument("--estadio",     type=int,   default=None)
    parser.add_argument("--pos_anterior",type=int,   default=None)
    parser.add_argument("--gf_anterior", type=int,   default=None)
    parser.add_argument("--gc_anterior", type=int,   default=None)
    parser.add_argument("--xg_anterior", type=float, default=None)
    parser.add_argument("--posesion_anterior", type=float, default=None)
    args, _ = parser.parse_known_args()

    # Si se pasan todos los argumentos por CLI, los usamos directamente
    if all(v is not None for v in [args.equipo, args.temporada, args.presupuesto,
                                    args.salario, args.refuerzos, args.edad,
                                    args.extranjeros, args.dt_meses, args.copas,
                                    args.estadio, args.pos_anterior, args.gf_anterior,
                                    args.gc_anterior, args.xg_anterior, args.posesion_anterior]):
        datos = dict(
            equipo=args.equipo, temporada=args.temporada,
            presupuesto_musd=args.presupuesto,
            salario_promedio_kusd=args.salario,
            inversion_refuerzos_musd=args.refuerzos,
            edad_promedio_plantilla=args.edad,
            extranjeros_plantilla=args.extranjeros,
            antiguedad_dt_meses=args.dt_meses,
            participacion_internacional=args.copas,
            capacidad_estadio=args.estadio,
            posicion_temporada_anterior=args.pos_anterior,
            goles_favor_ant=args.gf_anterior,
            goles_contra_ant=args.gc_anterior,
            diferencia_goles_ant=args.gf_anterior - args.gc_anterior,
            xg_ant=args.xg_anterior,
            posesion_ant=args.posesion_anterior,
        )
    else:
        datos = pedir_datos_interactivo()

    puntos = predecir(datos)
    mostrar_resultado(datos, puntos)


if __name__ == "__main__":
    main()
