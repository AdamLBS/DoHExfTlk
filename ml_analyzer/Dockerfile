FROM python:3.9-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpcap-dev \
    tcpdump \
    tshark \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installation de DoHLyzer
WORKDIR /opt
RUN git clone https://github.com/paloaltonetworks/dohlyzer.git || \
    echo "DoHLyzer sera simulé"

# Répertoire de travail
WORKDIR /app

# Copier les requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Créer les répertoires nécessaires
RUN mkdir -p /app/analysis/raw_dohlyzer \
             /app/analysis/ml_ready_csv \
             /app/analysis/predictions \
             /app/models \
             /app/config \
             /app/data/training \
             /app/training_reports \
             /app/training_plots

# Copier les scripts
COPY . .

# Rendre les scripts exécutables
RUN chmod +x *.py init.sh

# Script d'initialisation
COPY init.sh /app/init.sh
RUN chmod +x /app/init.sh

# Exposer le port pour l'API (futur)
EXPOSE 8080

# Point d'entrée
ENTRYPOINT ["/app/init.sh"]
CMD ["python3", "dohlyzer_ml_service.py"]
