#!/bin/bash
DOMAIN="doh.local"
CERT_DIR="./certs"
mkdir -p $CERT_DIR
openssl genrsa -out $CERT_DIR/$DOMAIN.key 2048
openssl req -new -x509 -key $CERT_DIR/$DOMAIN.key -out $CERT_DIR/$DOMAIN.crt -days 365 -subj "/C=FR/ST=Local/L=Local/O=DoH Test/CN=$DOMAIN"
openssl x509 -in $CERT_DIR/$DOMAIN.crt -text -noout | grep -A 1 "Subject:"