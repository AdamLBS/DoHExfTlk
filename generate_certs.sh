#!/bin/bash

# Script pour générer des certificats auto-signés pour le serveur DoH local

DOMAIN="doh.local"
CERT_DIR="./certs"

# Créer le répertoire s'il n'existe pas
mkdir -p $CERT_DIR

# Générer la clé privée
openssl genrsa -out $CERT_DIR/$DOMAIN.key 2048

# Générer le certificat auto-signé
openssl req -new -x509 -key $CERT_DIR/$DOMAIN.key -out $CERT_DIR/$DOMAIN.crt -days 365 -subj "/C=FR/ST=Local/L=Local/O=DoH Test/CN=$DOMAIN"

# Afficher les informations du certificat
echo "Certificat généré pour $DOMAIN"
openssl x509 -in $CERT_DIR/$DOMAIN.crt -text -noout | grep -A 1 "Subject:"

echo ""
echo "Pour utiliser ce serveur DoH, ajoutez cette ligne à votre /etc/hosts :"
echo "127.0.0.1    $DOMAIN"
