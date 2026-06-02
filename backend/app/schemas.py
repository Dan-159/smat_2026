from pydantic import BaseModel
from typing import Optional
from datetime import datetime

#Estaciones
class EstacionCreate(BaseModel):
    id: int
    nombre: str
    ubicacion: str


#Lecturas
class LecturaCreate(BaseModel):
    estacion_id: int
    valor: float
    fecha: Optional[datetime] = None
  
  
# Inicio de Sesión  
class LoginPayload(BaseModel):
    username: str
    password: str