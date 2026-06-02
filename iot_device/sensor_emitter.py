import requests
import time
import random

# CONFIGURACIÓN
API_URL = "http://localhost:8000/lecturas/"
ESTACION_ID = 1  # ID de la estación registrada en la DB

# Configuración para obtener el token de autenticación
LOGIN_URL = "http://localhost:8000/token" 
form_data = {"username": "admin", "password": "12345"}  #Usuario y contraseña del admin creado en el endpoint token
token_recibido = requests.post(LOGIN_URL, data=form_data)
TOKEN = token_recibido.json().get("access_token") # Obtenido del login
#Recordar que el token tiene una duración limitada (30 min)

def leer_sensor_emulado():
    # Simulamos una lectura de nivel de río (0 a 100 cm)
    return round(random.uniform(10.5, 85.0), 2)

def enviar_telemetria():
    print(f"--- Iniciando Emisor IoT para Estación {ESTACION_ID} ---")
    
    while True:
        valor = leer_sensor_emulado()
        payload = {
            "estacion_id": ESTACION_ID,
            "valor": valor
        }
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            if response.status_code == 201:
                if(valor > 70):
                    print(f"[ALERTA] Umbral de inundación superado: {valor} cm")
                else:
                    print(f"[OK] Lectura enviada: {valor} cm")
            else:
                print(f"[ERROR] Código: {response.status_code}")
        except Exception as e:
            print(f"[CRÍTICO] No hay conexión con el servidor: {e}")

        # Tiempo entre cada lectura 
        if(valor > 70):
            time.sleep(2)
        else:
            time.sleep(10)

if __name__ == "__main__":
    enviar_telemetria()