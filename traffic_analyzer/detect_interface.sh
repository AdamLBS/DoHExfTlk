#!/bin/bash

set -e
if command -v docker &> /dev/null; then
    IFLINK=$(docker exec traefik cat /sys/class/net/eth0/iflink 2>/dev/null || echo "")
    
    if [ -n "$IFLINK" ]; then
        MATCH_LINE=$(ip link | grep -B1 "^ *$IFLINK:" 2>/dev/null || echo "")
        if [ -n "$MATCH_LINE" ]; then
            VETH_LINE=$(echo "$MATCH_LINE" | tail -n 1)
            IFACE=$(echo "$VETH_LINE" | awk '{print $2}' | awk -F'@' '{print $1}' | sed 's/:$//')
            echo "veth interface detected: $IFACE"
        else
            echo "veth interface not found, using eth0"
            IFACE="eth0"
        fi
    else
        echo "Cannot retrieve iflink, using eth0"
        IFACE="eth0"
    fi
else
    echo "Docker CLI not available, using eth0"
    IFACE="eth0"
fi

mkdir -p "${OUTPUT_DIR:-/app/captured}"
export INTERFACE="$IFACE"
chown 1000:1000 "${OUTPUT_DIR:-/app/captured}"
chmod 755 "${OUTPUT_DIR:-/app/captured}"
cd DoHLyzer
python3 -m meter.dohlyzer --interface "$IFACE" -c ./../output/output.csv
