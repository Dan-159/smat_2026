import paho.mqtt.client as mqtt
import requests
import json
import sys
import time

# CONFIGURACIÓN DEL ENTORNO SMAT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "fisi/smat/estaciones/+/lecturas"
API_URL = "http://localhost:8000/lecturas/"

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhcnJveiIsImV4cCI6MTc4MTExMjExNX0.pSCYvGnP2n04DC_NZ0NGq80G__RXYviw88oq8dwwkoA"

# -------------------------------
# MEMORIA CACHÉ LOCAL
# -------------------------------
last_values = {}   # {estacion_id: ultimo_valor}
last_times = {}    # {estacion_id: timestamp}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("🟢 Conectado exitosamente al Broker MQTT")
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Escuchando: {MQTT_TOPIC}")
    else:
        print(f"🔴 Error conexión MQTT: {rc}")
        sys.exit(1)

def should_send(estacion_id, new_value):
    now = time.time()

    last_value = last_values.get(estacion_id)
    last_time = last_times.get(estacion_id)

    # Si nunca se ha enviado → enviar
    if last_value is None:
        return True

    # Cambio porcentual
    change = abs(new_value - last_value) / last_value * 100

    # Condición 1: cambio mayor al 5%
    if change > 5:
        return True

    # Condición 2: más de 60 segundos sin envío
    if last_time is None or (now - last_time) > 60:
        return True

    return False

def on_message(client, userdata, msg):
    try:
        payload_raw = msg.payload.decode("utf-8")
        data_json = json.loads(payload_raw)

        topic_parts = msg.topic.split('/')
        estacion_id = int(topic_parts[3])

        valor = float(data_json["valor"])

        print(f"📩 Recibido estación {estacion_id}: {valor}")

        # -------------------------------
        # FILTRO DE CAMBIO (DEADBAND)
        # -------------------------------
        if not should_send(estacion_id, valor):
            print(f"⛔ BLOQUEADO por filtro (sin cambio significativo)")
            return

        # actualizar caché
        last_values[estacion_id] = valor
        last_times[estacion_id] = time.time()

        api_payload = {
            "valor": valor,
            "estacion_id": estacion_id
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT_TOKEN}"
        }

        response = requests.post(API_URL, json=api_payload, headers=headers)

        if response.status_code in [200, 201]:
            print(f"💾 ENVIADO a DB: estación {estacion_id} valor {valor}")
        else:
            print(f"⚠️ ERROR API: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error Bridge: {e}")

bridge_client = mqtt.Client()
bridge_client.on_connect = on_connect
bridge_client.on_message = on_message

try:
    print("🚀 Bridge con Deadband Filter iniciado...")
    bridge_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    bridge_client.loop_forever()

except KeyboardInterrupt:
    print("\n🛑 Bridge detenido")