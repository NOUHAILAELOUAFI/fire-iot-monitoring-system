import paho.mqtt.client as mqtt
import time
import random
import json

BROKER = "localhost"
TOPIC = "building/fire/sensors"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)

print("📡 Simulateur de capteurs démarré...")

while True:
    data = {
        "temperature": round(random.uniform(20, 80), 2),
        "smoke": round(random.uniform(0, 100), 2),
        "gas": round(random.uniform(0, 300), 2),
        "timestamp": time.time()
    }

    client.publish(TOPIC, json.dumps(data))
    print("Données envoyées :", data)

    time.sleep(5)
