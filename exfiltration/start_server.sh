#!/bin/bash

set -e

echo "[🔍] Démarrage du serveur d'exfiltration DoH..."

# Méthode 1: Essayer de détecter l'interface veth du conteneur resolver
echo "[ℹ️] Tentative de détection de l'interface réseau du conteneur resolver..."

if command -v docker &> /dev/null; then
    # Récupérer l'iflink du conteneur resolver
    IFLINK=$(docker exec resolver cat /sys/class/net/eth0/iflink 2>/dev/null || echo "")
    
    if [ -n "$IFLINK" ]; then
        echo "[ℹ️] iflink du resolver: $IFLINK"
        # Trouver l'interface correspondante sur l'hôte
        MATCH_LINE=$(ip link | grep -B1 "^ *$IFLINK:" 2>/dev/null || echo "")
        if [ -n "$MATCH_LINE" ]; then
            VETH_LINE=$(echo "$MATCH_LINE" | tail -n 1)
            IFACE=$(echo "$VETH_LINE" | awk '{print $2}' | awk -F'@' '{print $1}' | sed 's/:$//')
            echo "[✅] Interface veth détectée : $IFACE"
        else
            echo "[⚠️] Interface veth non trouvée, utilisation de eth0"
            IFACE="eth0"
        fi
    else
        echo "[⚠️] Impossible de récupérer l'iflink, utilisation de eth0"
        IFACE="eth0"
    fi
else
    echo "[⚠️] Docker CLI non disponible, utilisation de eth0"
    IFACE="eth0"
fi

echo "[🚀] Lancement du serveur d'exfiltration sur interface $IFACE..."
echo "[ℹ️] Répertoire de sortie: ${OUTPUT_DIR:-/app/captured}"

# Créer le répertoire de sortie
mkdir -p "${OUTPUT_DIR:-/app/captured}"

# Lancer le serveur d'exfiltration avec détection d'interface dynamique
export INTERFACE="$IFACE"
python3 -u /app/simple_server.py
