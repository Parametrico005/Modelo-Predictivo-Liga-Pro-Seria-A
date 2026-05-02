# Modelo Predictivo del Rendimiento Deportivo en el Futbol Ecuatoriano (LigaPro)

Proyecto de titulacion que desarrolla un modelo de Inteligencia Artificial
para predecir los **puntos finales** de cada club de la LigaPro Serie A a
partir del **presupuesto institucional** y un conjunto de variables
competitivas conocidas antes del inicio de la temporada.

El proyecto entrega:

- Dataset real de 16 equipos x 8 temporadas (2019-2026), organizado en CSV
  por tipo de variable (presupuestaria / competitiva).
- Tres modelos comparados: Ridge, Random Forest y XGBoost. Se selecciona
  automaticamente el mejor por MAE en validacion.
- Backend FastAPI + interfaz web moderna para inferencia interactiva.
- Documento academico en Word (`docs/Informe_Final_LigaPro.docx`).

---

## Estructura del repositorio

```
LigaPro Serie A/
├── README.md
├── cover.pdf                                   <- portada institucional
│
├── data/
│   ├── categorias/                             <- FUENTE CANONICA (CSV)
│   │   ├── presupuestarias/
│   │   │   └── ligapro_presupuestos.csv        (presupuesto, salario,
│   │   │                                        refuerzos, valor plantel,
│   │   │                                        cantidad fichajes, etc.)
│   │   └── competitivas/
│   │       ├── ligapro_equipos.csv             (master de clubes)
│   │       ├── ligapro_plantilla.csv           (edad / extranjeros)
│   │       ├── ligapro_cuerpo_tecnico.csv      (DT)
│   │       ├── ligapro_participacion_internacional.csv
│   │       ├── ligapro_rendimiento_ofensivo.csv
│   │       ├── ligapro_rendimiento_defensivo.csv
│   │       ├── ligapro_posiciones.csv
│   │       └── ligapro_eficiencia.csv          (puntos / posibles)
│   │
│   └── datasets/                               <- INPUT DEL MODELO
│       ├── dataset_final.csv                   (128 filas, 24 cols)
│       ├── train.csv                           (2019-2023)
│       ├── val.csv                             (2024)
│       └── test.csv                            (2025)
│
├── scripts/
│   ├── consolidar_dataset.py                   (categorias -> dataset_final)
│   ├── preprocesamiento.py                     (FEATURES, TARGET, splits)
│   ├── entrenamiento.py                        (entrena los 3 modelos)
│   ├── prediccion.py                           (inferencia batch desde CSV)
│   └── predecir_equipo.py                      (inferencia interactiva)
│
├── output/                                     <- API + UI + MODELOS
│   ├── main.py                                 (backend FastAPI)
│   ├── index.html                              (UI moderna)
│   ├── requirements.txt
│   └── models/
│       ├── ridge.joblib
│       ├── randomforest.joblib
│       ├── xgboost.joblib
│       ├── mejor_modelo.joblib                 (copia del mejor por MAE)
│       └── model_card.json                     (metricas + features + splits)
│
├── notebooks/
│   └── 01_ligapro_COLAB.ipynb                  (EDA + modelado)
│
└── docs/
    └── Informe_Final_LigaPro.docx              (documento academico)
```

---




## Modelos comparados

Los tres modelos se entrenan **por separado** sobre el mismo conjunto de
features pre-temporada. El script elige automaticamente el mejor por MAE
en validacion (2024).

| Modelo | Principio | Hiperparametros |
|---|---|---|
| **Ridge** | Regresion lineal con penalizacion L2 | alpha=1.0, StandardScaler |
| **Random Forest** | Ensemble de 500 arboles aleatorios | min_samples_leaf=2, max_depth=None |
| **XGBoost** | Boosting secuencial de arboles | 400 estimadores, lr=0.05, depth=4 |

### Resultados actuales (re-entrenamiento mas reciente)

| Modelo | MAE val | RMSE val | R2 val | Spearman val | Spearman test |
|---|---|---|---|---|---|
| **Ridge (mejor)** | 6.65 | 7.83 | 0.626 | 0.724 | 0.577 |
| Random Forest | 9.28 | 10.94 | 0.271 | 0.466 | 0.627 |
| XGBoost | 11.39 | 13.25 | -0.070 | 0.274 | 0.506 |

Ridge gana porque con 80 filas de entrenamiento los modelos no lineales
sobreajustan. La metrica mas relevante es **Spearman** (correlacion de
ranking), porque lo que interesa es predecir el orden de la tabla.

---

## Variables (features) usadas por el modelo

```
Recursos:        presupuesto_musd, salario_promedio_kusd, inversion_refuerzos_musd
Plantilla:       edad_promedio_plantilla, extranjeros_plantilla
Cuerpo tecnico:  antiguedad_dt_meses
Contexto:        participacion_internacional, capacidad_estadio
Inercia:         posicion_temporada_anterior
Lag deportivo:   goles_favor_ant, goles_contra_ant, diferencia_goles_ant,
                 xg_ant, posesion_ant
TARGET:          puntos_temporada
```

Todas las variables son **conocidas antes del primer partido** de la
temporada que se quiere predecir, por lo que el modelo es valido como
herramienta de planificacion pre-temporada.
