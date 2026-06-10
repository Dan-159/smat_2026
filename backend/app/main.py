from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from .schemas import EstacionCreate, LecturaCreate, LoginPayload
from . import crud, models
from .database import engine, get_db
from .auth import crear_token_acceso, obtener_identidad_actual
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
title="SMAT - Sistema de Monitoreo de Alerta Temprana",
description="""
API robusta para la gestión y monitoreo de desastres naturales.
Permite la telemetría de sensores en tiempo real y el cálculo de niveles de riesgo.
**Entidades principales:**
* **Estaciones:** Puntos de monitoreo físico.
* **Lecturas:** Datos capturados por sensores.
* **Riesgos:** Análisis de criticidad basado en umbrales.
""",
version="1.0.0",
terms_of_service="http://unmsm.edu.pe/terms/",
contact={
    "name": "Soporte Técnico SMAT - FISI",
    "url": "http://fisi.unmsm.edu.pe",
    "email": "desarrollo.smat@unmsm.edu.pe",
    },
license_info={
    "name": "Apache 2.0",
    "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Inicio"], summary="Bienvenida", description="Mensaje de bienvenida a la API SMAT")
def read_root():
    return {"message": "Bienvenido a la API de SMAT - Sistema de Monitoreo de Alerta Temprana"}

#--------------Endpoint para autenticación (generación de token) con OAuth2PasswordRequestForm--------------
@app.post("/token", tags=["Seguridad"])
async def login_para_obtener_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if (form_data.username == "admin" and form_data.password == "12345") or crud.consultar_usuario(db, form_data.username, form_data.password):
        token = crear_token_acceso({"sub": form_data.username})
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

@app.post("/usuarios/", status_code=201, tags=["Seguridad"])
def crear_usuario(datos_usuario: LoginPayload, db: Session = Depends(get_db)):
    return crud.crear_usuario(db, datos_usuario)

#--------------Endpoints para estaciones--------------
@app.post("/estaciones/",status_code=201,
tags=["Gestión de Infraestructura"],
summary="Registrar una nueva estación de monitoreo",
description="Inserta una estación física (ej. río, volcán, zona sísmica) en la base de datos relacional."
)
def crear_estacion(estacion: EstacionCreate, db: Session = Depends(get_db), usuario: str = Depends(obtener_identidad_actual)):
    return crud.crear_estacion(db, estacion)

@app.get("/estaciones/", response_model=list[EstacionCreate], 
tags=["Gestión de Infraestructura"],
summary="Listar estaciones de monitoreo",
description="Obtiene una lista de todas las estaciones registradas en la base de datos relacional.")
def mostrar_estaciones(db: Session = Depends(get_db)):
    return crud.mostrar_estaciones(db)

@app.put("/estaciones/{id}",status_code=200, response_model=EstacionCreate,
tags=["Gestión de Infraestructura"], 
summary="Actualizar una estación de monitoreo", 
description="Actualiza los detalles de una estación existente en la base de datos relacional.")
def actualizar_estacion(id: int, estacion: EstacionCreate, db: Session = Depends(get_db), usuario: str = Depends(obtener_identidad_actual)):
    return crud.actualizar_estacion(db, id, estacion)

@app.delete("/estaciones/{id}", status_code=204,
tags=["Gestión de Infraestructura"], 
summary="Eliminar una estación de monitoreo", 
description="Elimina una estación existente de la base de datos relacional.")
def eliminar_estacion(id: int, db: Session = Depends(get_db), usuario: str = Depends(obtener_identidad_actual)):
    crud.eliminar_estacion(db, id)
    return {"detail": "Estación eliminada exitosamente"}


#--------------Endpoints para lecturas--------------
@app.post(
"/lecturas/",
status_code=201,
tags=["Telemetría de Sensores"],
summary="Recibir datos de telemetría",
description="Recibe el valor capturado por un sensor y lo vincula a una estación existente mediante suID.")
def registrar_lectura(lectura: LecturaCreate, db: Session = Depends(get_db), usuario: str = Depends(obtener_identidad_actual)):
    return crud.registrar_lectura(db, lectura)

@app.get("/lecturas/{id}/historial", response_model=list[LecturaCreate],
tags=["Telemetría de Sensores"],
summary="Mostrar historial de lecturas",
description="Obtiene el historial de lecturas para una estación específica.")
def mostrar_lecturas_de_estacion(id: int, db: Session = Depends(get_db)):
    return crud.mostrar_lecturas_de_estacion(db, id)

@app.get("/lecturas/{id}/ultima", response_model=LecturaCreate,
tags=["Telemetría de Sensores"],
summary="Mostrar última lectura",
description="Obtiene la última lectura registrada para una estación específica.")
def ultima_lectura_de_estacion(id: int, db: Session = Depends(get_db)):
    return crud.ultima_lectura_de_estacion(db, id)

#--------------Endpoints para Reportes--------------
@app.get("/estaciones/{id}/historial",
tags=["Reportes Históricos"],
summary="Reporte histórico de estaciones",
description="Muestra el conteo total de lecturas y el valor promedio para cada estación registrada en la base de datos.",
response_model=dict
)
def mostrar_reporte_historico_por_estacion(id: int, db: Session = Depends(get_db)):
    return crud.mostrar_reporte_historico_por_estacion(db, id)

#--------------Endpoint para análisis de riesgo--------------
# Endpoint para evaluar el nivel de riesgo actual basado en la última lectura de una estación
@app.get(
"/estaciones/{id}/riesgo",
tags=["Análisis de Riesgo"],
summary="Evaluar nivel de peligro actual",
description="Analiza la última lectura recibida de una estación y determina si el estado es NORMAL,ALERTA o PELIGRO."
)
def obtener_riesgo(id: int, db: Session = Depends(get_db)):
    # El nivel de riesgo se determina por los siguientes umbrales:
    """
    - NORMAL: valor < 10
    - ALERTA: 10 <= valor < 20
    - PELIGRO: valor >= 20
    """
    return crud.obtener_riesgo(db, id)

#--------------Endpoint stats--------------
@app.get(
"/estaciones/stats",
tags=["Estadísticas"],
summary="Mostrar estadísticas generales",
description="Muestra estadísticas generales sobre las estaciones y lecturas registradas."
)
def mostrar_estadisticas(db: Session = Depends(get_db)):
    return crud.mostrar_estadisticas(db)