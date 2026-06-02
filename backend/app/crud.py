from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
import models  
from schemas import EstacionCreate, LecturaCreate, LoginPayload
#-----Funciones CRUD para usuarios-----
def crear_usuario(db: Session, datos_usuario: LoginPayload):
    nuevo_usuario = models.UsuariosDB(nombre=datos_usuario.username, contraseña=datos_usuario.password)
    if db.query(models.UsuariosDB).filter(models.UsuariosDB.nombre == datos_usuario.username).first():
        raise HTTPException(status_code=400, detail="Nombre de usuario ya existe")
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

def consultar_usuario(db: Session, nombre: str , contraseña: str):
    if not db.query(models.UsuariosDB).filter(models.UsuariosDB.nombre == nombre).first():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db.query(models.UsuariosDB).filter(models.UsuariosDB.nombre == nombre, models.UsuariosDB.contraseña == contraseña).first()   

#-----Funciones CRUD para estaciones-----
def crear_estacion(db: Session, estacion: EstacionCreate):
    nueva_estacion = models.EstacionDB(id=estacion.id, nombre=estacion.nombre,ubicacion=estacion.ubicacion)
    if db.query(models.EstacionDB).filter(models.EstacionDB.id == estacion.id).first():
        raise HTTPException(status_code=400, detail="ID de estación ya existe")
    db.add(nueva_estacion)
    db.commit()
    db.refresh(nueva_estacion)
    return nueva_estacion

def mostrar_estaciones(db: Session):
    return db.query(models.EstacionDB).all()

def actualizar_estacion(db: Session, id: int, estacion: EstacionCreate):
    estacion_db = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion_db:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    estacion_db.nombre = estacion.nombre
    estacion_db.ubicacion = estacion.ubicacion
    db.commit()
    db.refresh(estacion_db)
    return estacion_db

def eliminar_estacion(db: Session, id: int):
    estacion_db = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion_db:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    db.delete(estacion_db)
    db.commit()

#-----Funciones CRUD para lecturas-----
def registrar_lectura(db: Session, lectura: LecturaCreate):
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == lectura.estacion_id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no existe")
    nueva_lectura = models.LecturaDB(valor=lectura.valor,estacion_id=lectura.estacion_id)
    db.add(nueva_lectura)
    db.commit()
    return {"status": "Lectura guardada en DB"}

def mostrar_lecturas_de_estacion(db: Session, id: int):
    if not db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first():
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    lecturas=db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    if not lecturas:
        raise HTTPException(status_code=404, detail="No hay lecturas de esta estación")
    return lecturas

def ultima_lectura_de_estacion(db: Session, id: int):
    if not db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first():
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    ultima_lectura=db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).order_by(models.LecturaDB.id.desc()).first()
    if not ultima_lectura:
        raise HTTPException(status_code=404, detail="No hay lecturas de esta estación")
    return ultima_lectura

#-----Funciones para reportes-----     
def mostrar_reporte_historico_por_estacion(db: Session, id: int):
    reporte = {}
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    
    lecturas = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    conteo = len(lecturas)
    promedio = sum(l.valor for l in lecturas) / conteo if conteo > 0 else 0.0
    reporte.update({
        "estacion_id": id,
        "nombre": estacion.nombre,
        "ubicacion": estacion.ubicacion,
        "lecturas": [{"lectura registrada #": i, "valor": lecturas[i-1].valor} for i in range(1, conteo + 1)],
        "conteo de lecturas": conteo,
        "promedio de lecturas": round(promedio, 2)
    })
    return reporte

#-----Funciones para análisis de riesgo-----
def obtener_riesgo(db: Session, id: int):
    # Validar existencia de la estación
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    
    # Obtener la última lectura de la estación
    ultima_lectura = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).order_by(models.LecturaDB.id.desc()).first()
    
    if not ultima_lectura:
        return {"id": id, "nivel": "SIN DATOS", "valor": 0}
    
    valor = ultima_lectura.valor
    if valor < 10:
        nivel = "NORMAL"
    elif 10 <= valor < 20:
        nivel = "ALERTA"
    else:
        nivel = "PELIGRO"
    
    return {"id": id, "nivel": nivel, "valor": valor}

#-----Funciones stats-----
def mostrar_estadisticas(db: Session):
    conteo_estaciones = db.query(func.count(models.EstacionDB.id)).scalar()
    conteo_lecturas = db.query(func.count(models.LecturaDB.id)).scalar()
    valor_maximo = db.query(func.max(models.LecturaDB.valor)).scalar()
    
    datos_de_la_lectura_mas_alta = {
        "estacion_id": None,
        "nombre de la estación": None,
        "ubicacion de la estación": None,
        "valor": 0
    }
    
    if valor_maximo is not None:
        lectura_alta = db.query(models.LecturaDB).filter(models.LecturaDB.valor == valor_maximo).first()
        if lectura_alta and lectura_alta.estacion:
            datos_de_la_lectura_mas_alta = {
                "estacion_id": lectura_alta.estacion_id,
                "nombre de la estación": lectura_alta.estacion.nombre,
                "ubicacion de la estación": lectura_alta.estacion.ubicacion,
                "valor": lectura_alta.valor
            }
            
    return {
        "Total de estaciones registradas": conteo_estaciones,
        "Total de lecturas registradas": conteo_lecturas,
        "Datos de la lectura más alta": datos_de_la_lectura_mas_alta
    }