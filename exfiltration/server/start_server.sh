#!/bin/bash

set -e

echo "Starting DoH exfiltration server..."

# Method 1: Try to detect the resolver container's veth interface
echo "Attempting to detect resolver container network interface..."

if command -v docker &> /dev/null; then
    # Get resolver container iflink
    IFLINK=$(docker exec resolver cat /sys/class/net/eth0/iflink 2>/dev/null || echo "")
    
    if [ -n "$IFLINK" ]; then
        # Find corresponding interface on host
        MATCH_LINE=$(ip link | grep -B1 "^ *$IFLINK:" 2>/dev/null || echo "")
        if [ -n "$MATCH_LINE" ]; then
            VETH_LINE=$(echo "$MATCH_LINE" | tail -n 1)
            IFACE=$(echo "$VETH_LINE" | awk '{print $2}' | awk -F'@' '{print $1}' | sed 's/:$//')
            echo "veth interface detected: $IFACE"
        else
            echo "Error: veth interface not found"
            exit 1
        fi
    else
        echo "Error: Cannot retrieve iflink from resolver container"
        exit 1
    fi
else
    echo "Error: Docker CLI not available"
    exit 1
fi

echo "Starting exfiltration server on interface $IFACE..."

# Create output directory
mkdir -p "${OUTPUT_DIR:-/app/captured}"

# Launch exfiltration server with dynamic interface detection
export INTERFACE="$IFACE"
python3 -u /app/server.py
