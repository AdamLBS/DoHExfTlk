#!/bin/bash
set -e

echo "Démarrage du sniffer..."

# Lancer le script Python qui sniffe directement sur l'interface eth0
bash /app/run_sniffer.sh &

# Garder le conteneur en vie
wait
