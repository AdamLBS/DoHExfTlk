#!/bin/bash

# Script pour tester le serveur DoH local depuis le conteneur client

echo "=== Test du serveur DoH local ==="

# Test 1: Requête DoH simple pour google.com
echo "Test 1: Requête DoH pour google.com"
curl -k --insecure --ssl-no-revoke \
     -H "Accept: application/dns-json" \
     -H "User-Agent: DoH-Test-Client/1.0" \
     "https://doh.local/dns-query?name=google.com&type=A" \
     -v 2>&1 | grep -E "(HTTP|dns|Answer|Status)" || echo "Erreur de connexion"

echo ""

# Test 1bis: Test avec affichage des erreurs
echo "Test 1bis: Requête DoH avec debug"
curl -k --insecure --connect-timeout 10 \
     -H "Accept: application/dns-json" \
     "https://doh.local/dns-query?name=google.com&type=A" \
     2>&1

echo ""

# Test 2: Requête DoH en POST  
echo "Test 2: Requête DoH en POST pour cloudflare.com"
curl -k --insecure --connect-timeout 10 \
     -X POST \
     -H "Content-Type: application/dns-message" \
     -H "Accept: application/dns-json" \
     -H "User-Agent: DoH-Test-Client/1.0" \
     --data-binary @<(echo -n "cloudflare.com" | base64) \
     "https://doh.local/dns-query" \
     2>&1

echo ""

# Test 3: Vérification du certificat (attendu: auto-signé)
echo "Test 3: Informations du certificat du serveur"
echo | openssl s_client -connect doh.local:443 -servername doh.local -verify_return_error 2>/dev/null | openssl x509 -noout -subject -issuer 2>/dev/null || echo "Certificat auto-signé détecté (normal)"

echo ""

# Test 3bis: Test de connectivité directe
echo "Test 3bis: Test de connectivité réseau"
ping -c 2 traefik || echo "Ping vers traefik échoué"
nc -zv traefik 443 2>&1 || echo "Port 443 non accessible"

echo ""

# Test 4: Test direct du serveur DoH (sans HTTPS)
echo "Test 4: Test direct du serveur DoH"
curl -H "Accept: application/dns-json" \
     "http://doh_server:8053/dns-query?name=google.com&type=A" \
     2>&1

echo ""

# Test 5: Vérification de la résolution DNS classique via le resolver
echo "Test 5: Test DNS classique via resolver"
nslookup google.com resolver

echo ""
echo "=== Tests terminés ==="
