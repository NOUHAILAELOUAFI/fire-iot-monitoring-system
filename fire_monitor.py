import json
import time
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

BROKER = "localhost"
SENSORS_TOPIC = "building/fire/sensors"
ALERT_TOPIC = "building/fire/alert"

# Seuils
TH_TEMP = 50.0
TH_SMOKE = 60.0
TH_GAS = 200.0

# Pour éviter les fausses alertes (tu peux remettre 2 plus tard)
CONSECUTIVE_REQUIRED = 1
danger_streak = 0

# InfluxDB (v1)
INFLUX_HOST = "localhost"
INFLUX_PORT = 8086
INFLUX_DB = "fire_iot"

influx = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT)
influx.switch_database(INFLUX_DB)


def is_fire_reading(t: float, s: float, g: float) -> bool:
    return (t >= TH_TEMP) and (s >= TH_SMOKE) and (g >= TH_GAS)


def write_to_influx(temperature: float, smoke: float, gas: float, fire: bool, ts: float):
    """Stocke chaque mesure capteur dans la measurement 'sensors'."""
    point = [
        {
            "measurement": "sensors",
            "tags": {
                "building": "A",
                "floor": "1",
            },
            "time": int(ts),  # secondes
            "fields": {
                "temperature": float(temperature),
                "smoke": float(smoke),
                "gas": float(gas),
                "fire_detected": bool(fire),
                "fire_level": 1 if fire else 0,
            },
        }
    ]
    influx.write_points(point, time_precision="s")


def write_alert_to_influx(temperature: float, smoke: float, gas: float, ts: float):
    """
    Stocke une alerte (événement) dans la measurement 'alerts'.
    C'est pratique pour l'afficher dans Grafana (table, stat, annotations).
    """
    point = [
        {
            "measurement": "alerts",
            "tags": {
                "type": "FIRE",
                "building": "A",
                "floor": "1",
                "source": "fire_monitor",
            },
            "time": int(ts),  # secondes
            "fields": {
                "temperature": float(temperature),
                "smoke": float(smoke),
                "gas": float(gas),
                "message": "Incendie détecté",
                "severity": "HIGH",
            },
        }
    ]
    influx.write_points(point, time_precision="s")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Backend connecté au broker MQTT.")
        client.subscribe(SENSORS_TOPIC)
        print(f"Abonné au topic: {SENSORS_TOPIC}")
    else:
        print(f" Connexion MQTT échouée (code={rc}).")


def on_message(client, userdata, msg):
    global danger_streak
    try:
        data = json.loads(msg.payload.decode("utf-8"))

        temperature = float(data.get("temperature", 0))
        smoke = float(data.get("smoke", 0))
        gas = float(data.get("gas", 0))
        ts = float(data.get("timestamp", time.time()))

        fire_now = is_fire_reading(temperature, smoke, gas)

        # anti faux positifs
        if fire_now:
            danger_streak += 1
        else:
            danger_streak = 0

        # stocker à chaque message
        write_to_influx(temperature, smoke, gas, fire_now, ts)

        print(
            f"📊 Reçu | T={temperature:.2f}°C, Smoke={smoke:.2f}, Gas={gas:.2f} "
            f"| danger={fire_now} | streak={danger_streak}/{CONSECUTIVE_REQUIRED}"
        )

        # publier + stocker alerte si N lectures dangereuses d'affilée
        if danger_streak >= CONSECUTIVE_REQUIRED:
            alert = {
                "type": "FIRE_ALERT",
                "message": "🔥 Incendie détecté !",
                "temperature": temperature,
                "smoke": smoke,
                "gas": gas,
                "timestamp": ts,
                "topic": SENSORS_TOPIC,
            }

            # 1) publier sur MQTT
            client.publish(ALERT_TOPIC, json.dumps(alert, ensure_ascii=False))
            print(f"ALERTE PUBLIÉE sur {ALERT_TOPIC}")

            # 2) stocker l'événement dans InfluxDB
            write_alert_to_influx(temperature, smoke, gas, ts)
            print("ALERTE STOCKÉE dans InfluxDB (measurement=alerts)")

            danger_streak = 0

    except Exception as e:
        print(f"Erreur: {e}")


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, 1883, 60)
    print("Backend incendie + InfluxDB démarré...")
    client.loop_forever()


if __name__ == "__main__":
    main()
