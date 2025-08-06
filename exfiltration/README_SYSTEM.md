# DoH Exfiltration System - Résumé

## 🎯 Objectif
Système simple de capture et reconstruction de données exfiltrées via DNS-over-HTTPS (DoH) pour la recherche académique.

## 📋 Composants créés

### 1. Client d'exfiltration (`client.py`)
- **But** : Envoie des données via des requêtes DoH
- **Fonctionnalités** :
  - 7 scénarios prédéfinis (basic, stealth, bulk, etc.)
  - Encodage multiple (base64, hex, etc.)
  - Statistiques de transmission
  - Configuration flexible

### 2. Serveur de capture (`simple_server.py`)
- **But** : Capture et reconstruit les données exfiltrées
- **Fonctionnalités** :
  - Interception des paquets DNS via Scapy
  - Détection automatique de l'interface réseau
  - Reconstruction des données segmentées
  - Sauvegarde des fichiers reconstruits

### 3. Intercepteur de trafic (`traffic_interceptor.py`)
- **But** : Capture passive du trafic DNS/DoH
- **Fonctionnalités** :
  - Écoute des paquets réseau
  - Extraction des requêtes DNS
  - Interface avec le serveur de reconstruction

### 4. Configuration Docker
- **Services** :
  - `exfil_interceptor` : Serveur de capture avec permissions réseau
  - `exfil_client` : Client de test pour générer le trafic
- **Capacités** : NET_RAW, NET_ADMIN pour capture de paquets
- **Volumes** : Partage des données capturées

### 5. Scripts utilitaires
- `start_server.sh` : Détection dynamique de l'interface réseau
- `quick_test.py` : Tests d'intégration rapides
- Configuration automatique avec l'infrastructure DoH existante

## 🚀 Utilisation

### Construction
```bash
docker compose build exfil_interceptor exfil_client
```

### Lancement
```bash
# Démarrer le serveur de capture
docker compose up exfil_interceptor

# Dans un autre terminal, lancer les tests
docker compose run exfil_client
```

## 🔧 Configuration

### Variables d'environnement
- `OUTPUT_DIR` : Répertoire de sauvegarde (défaut: `/app/captured`)
- `TARGET_CONTAINER` : Conteneur à surveiller (défaut: `resolver`)
- `DOH_SERVER` : Serveur DoH cible
- `TARGET_DOMAIN` : Domaine d'exfiltration

### Intégration infrastructure existante
- Compatible avec le serveur DoH existant (`doh.local`)
- Utilise le resolver Unbound existant
- Capture passive sans interférer avec le trafic normal

## 📊 Résultats

### Données capturées
- Fichiers `.bin` : Données reconstruites
- Logs : Statistiques de capture
- Métadonnées : Sessions et patterns d'exfiltration

### Scénarios de test
1. **Basic** : Exfiltration simple
2. **Stealth** : Requêtes espacées, petites tailles
3. **Bulk** : Transfert de gros volumes
4. **Fragmented** : Données fragmentées
5. **Encrypted** : Données chiffrées
6. **Adaptive** : Timing variable
7. **Advanced** : Techniques d'évasion

## 🎯 Recherche académique

### Cas d'usage
- Test de détection d'exfiltration
- Analyse de patterns de trafic
- Évaluation de techniques d'évasion
- Développement de contre-mesures

### Métriques collectées
- Volume de données transférées
- Nombre de requêtes
- Timing des transmissions
- Taux de reconstruction réussi
- Détection d'encodage

## ⚠️ Notes importantes
- Utilisation strictement académique/recherche
- Nécessite les privilèges NET_RAW pour la capture
- Compatible avec l'infrastructure Docker existante
- Capture passive sans modification du trafic normal
