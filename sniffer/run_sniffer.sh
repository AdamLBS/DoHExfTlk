#!/bin/bash

set -e

echo "[🔍] Démarrage du sniffer pour intercepter le trafic du resolver..."

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

echo "[🚀] Lancement du sniffer Python sur $IFACE avec filtre DNS..."
python3 /app/decode_live.py --iface "$IFACE"
