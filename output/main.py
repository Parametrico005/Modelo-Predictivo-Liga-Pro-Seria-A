from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import joblib
import json
import pandas as pd
from pydantic import BaseModel

app = FastAPI()

# Configuración para permitir la conexión con el HTML
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Rutas absolutas (para que funcione sin importar desde dónde se lance)
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

# 1. Cargar todos los modelos al iniciar el servidor
modelos = {
    "ridge": joblib.load(MODELS_DIR / "ridge.joblib"),
    "rf": joblib.load(MODELS_DIR / "randomforest.joblib"),
    "xgb": joblib.load(MODELS_DIR / "xgboost.joblib"),
    "mejor": joblib.load(MODELS_DIR / "mejor_modelo.joblib")
}

# 2. Cargar las métricas del JSON
with open(MODELS_DIR / "model_card.json", "r", encoding="utf-8") as f:
    metricas = json.load(f)

class DatosEntrada(BaseModel):
    modelo_seleccionado: str
    presupuesto_musd: float
    salario_promedio_kusd: float
    inversion_refuerzos_musd: float
    edad_promedio_plantilla: float
    extranjeros_plantilla: int
    antiguedad_dt_meses: int
    participacion_internacional: int
    capacidad_estadio: int
    posicion_temporada_anterior: int
    goles_favor_ant: int
    goles_contra_ant: int
    diferencia_goles_ant: int
    xg_ant: float
    posesion_ant: float

@app.post("/predecir")
def predecir_puntos(datos: DatosEntrada):
    # Extraer el nombre del modelo y los datos
    nombre_mod = datos.modelo_seleccionado
    dict_datos = datos.dict()
    del dict_datos["modelo_seleccionado"] # Eliminar campo que no es del modelo
    
    # Seleccionar el modelo y predecir
    modelo_act = modelos.get(nombre_mod, modelos["mejor"])
    df = pd.DataFrame([dict_datos])
    prediccion = modelo_act.predict(df)[0]
    
    # Obtener métricas específicas de ese modelo desde el JSON
    info_metrica = metricas["modelos"].get(nombre_mod.capitalize(), {})
    
    return {
        "puntos": round(float(prediccion), 2),
        "modelo_usado": nombre_mod.upper(),
        "metricas": info_metrica.get("val", {}) # Enviamos el MAE, R2, etc. de validación
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)