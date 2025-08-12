#!/bin/bash

set -e

# Method 1: Try to detect resolver container's veth interface

if command -v docker &> /dev/null; then
    # Get resolver container iflink
    IFLINK=$(docker exec traefik cat /sys/class/net/eth0/iflink 2>/dev/null || echo "")
    
    if [ -n "$IFLINK" ]; then
        # Find corresponding interface on host
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

# Create output directory
mkdir -p "${OUTPUT_DIR:-/app/captured}"

# Launch traffic analyzer with dynamic interface detection
export INTERFACE="$IFACE"
chown 1000:1000 "${OUTPUT_DIR:-/app/captured}"
# Make it so that each new file created belongs to the user with UID 1000
chmod 755 "${OUTPUT_DIR:-/app/captured}"
# Ensure the output directory is accessible
cd DoHLyzer
python3 -m meter.dohlyzer --interface "$IFACE" -c ./../output/output.csv
