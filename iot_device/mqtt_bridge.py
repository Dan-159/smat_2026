import paho.mqtt.client as mqtt
import requests
import json
# CONFIGURACIÓN
BROKER = "broker.hivemq.com"
TOPIC = "fisi/smat/estaciones/#" # Escucha todas las estaciones
API_URL = "http://localhost:8000/lecturas/"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhcnJveiIsImV4cCI6MTc4MTA1MTk2NX0.q2JCEkx6T9ZdDAzM--F8rP7PrDNHELMDJ3xAJQC0VEM" # Token de un usuario con permisos
def on_message(client, userdata, msg):
    try:
        # 1. Decodificar el mensaje MQTT
        payload = json.loads(msg.payload.decode())
        print(f"📩 Mensaje recibido en {msg.topic}: {payload}")
        # 2. Extraer el ID de la estación desde el tópico
        # Ejemplo: fisi/smat/estaciones/1 -> ID = 1
        estacion_id = msg.topic.split('/')[-1]
        # 3. Preparar los datos para el Backend
        data_to_send = {
        "valor": payload["valor"],
        "estacion_id": int(estacion_id)
        }
        # 4. Enviar a la API mediante HTTP POST
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = requests.post(API_URL, json=data_to_send, headers=headers)
        if response.status_code == 200:
            print(f"✅ Dato persistido en DB para estación {estacion_id}")
        else:
            print(f"⚠️ Error API ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")
# Configuración del Cliente MQTT
client = mqtt.Client()
client.on_message = on_message
print("🚀 Bridge SMAT iniciado. Esperando datos...")
client.connect(BROKER, 1883)
client.subscribe(TOPIC)
client.loop_forever()