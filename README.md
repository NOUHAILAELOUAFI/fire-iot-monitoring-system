# Fire IoT Monitoring System

Système intelligent de surveillance et de prévention des incendies basé sur l’IoT.

## Description
Ce projet permet de surveiller en temps réel la température, la fumée et le gaz
afin de détecter automatiquement les risques d’incendie dans un bâtiment.

## Technologies utilisées
- Python
- MQTT (Mosquitto)
- InfluxDB
- Grafana
- WSL (Ubuntu)

## Architecture
Capteurs simulés → MQTT → Backend Python → InfluxDB → Grafana → Email d’alerte

## Fonctionnalités
- Simulation des capteurs IoT
- Communication MQTT
- Détection d’incendie
- Stockage des données
- Dashboard Grafana
- Alertes par email

## Lancement du projet
```bash
python sensor_simulator.py
python fire_monitor.py
