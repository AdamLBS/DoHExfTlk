# Configuration DoH Local Environment

Ce projet configure un environnement DoH (DNS over HTTPS) local pour les tests et l'analyse.

## Architecture

- **Traefik**: Reverse proxy avec certificats auto-signés
- **DoH Server**: Serveur DNS over HTTPS
- **Resolver**: Serveur DNS Unbound en backend
- **Sniffer**: Conteneur pour capturer le trafic réseau
- **Client Test**: Conteneur Ubuntu pour effectuer des tests DoH

## Installation et démarrage

1. Générer les certificats auto-signés :
```bash
chmod +x generate_certs.sh
./generate_certs.sh
```

2. Démarrer l'environnement :
```bash
docker-compose up -d
```

**Note**: Aucune modification du système hôte n'est nécessaire. Tout est configuré automatiquement dans les conteneurs.

## Tests

### Test basique du serveur DoH
```bash
docker exec -it client_test bash /scripts/test_doh.sh
```

### Test d'exfiltration continue
```bash
docker exec -it client_test bash /scripts/exfiltrate_doh.sh
```

### Test depuis l'hôte (nécessite configuration hosts)
Si vous voulez tester depuis l'hôte, ajoutez d'abord cette ligne à votre `/etc/hosts` :
```bash
echo "127.0.0.1    doh.local" | sudo tee -a /etc/hosts
```

Puis testez :
```bash
curl -k -H "Accept: application/dns-json" \
     "https://doh.local/dns-query?name=google.com&type=A"
```

## Accès aux services

- **Serveur DoH**: https://doh.local/dns-query
- **Dashboard Traefik**: http://localhost:8080
- **Résolveur DNS classique**: localhost:53 (via le conteneur resolver)

## Capture de trafic

Le conteneur `sniffer_exfil` capture automatiquement le trafic réseau et sauvegarde les données dans `./sniffer/output/`.

## Remarques

- Les certificats sont auto-signés, votre navigateur affichera un avertissement de sécurité
- Utilisez l'option `-k` avec curl pour ignorer les erreurs de certificat
- L'environnement est entièrement local et ne nécessite pas de connexion internet pour le DoH
