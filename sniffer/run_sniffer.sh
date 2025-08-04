#!/bin/bash

set -e
# 🧪 Active le venv
echo "[🐍] Activation de l'environnement virtuel..."
source .venv/bin/activate

echo "[🔍] Détection de l'interface veth liée à 'resolver'..."

# Étape 1 : récupérer le iflink du conteneur
IFLINK=$(docker exec resolver cat /sys/class/net/eth0/iflink)
echo "[ℹ️ ] iflink depuis 'resolver': $IFLINK"

# Étape 2 : trouver l'interface correspondante sur l'hôte
MATCH_LINE=$(ip link | grep -B1 "^ *$IFLINK:")
VETH_LINE=$(echo "$MATCH_LINE" | head -n 1)
IFACE=$(echo "$VETH_LINE" | awk -F': ' '{print $2}' | awk -F'@' '{print $1}')
echo "[✅] Interface détectée : $IFACE"

# Étape 3 : lancer le sniffer Python avec l'interface détectée
echo "[🚀] Lancement du sniffer sur l'interface $IFACE..."
python3 decode_live.py --iface "$IFACE"
