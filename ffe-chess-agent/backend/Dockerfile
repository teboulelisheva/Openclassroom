# Version Python figée pour garantir la reproductibilité
FROM python:3.12-slim

# Bonnes pratiques : pas de .pyc, sortie non bufferisée (logs immédiats)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Binaire Stockfish (moteur d'analyse) — installé à /usr/games/stockfish
RUN apt-get update \
    && apt-get install -y --no-install-recommends stockfish \
    && rm -rf /var/lib/apt/lists/*

# On installe les dépendances Python ensuite pour profiter du cache Docker
COPY requirements.txt .
# torch en version CPU d'abord : évite ~5 Go de paquets CUDA/nvidia inutiles
# sans GPU (image beaucoup plus légère et build plus rapide).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

# Puis le code applicatif
COPY ./app ./app
COPY ./scripts ./scripts
COPY ./data ./data
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8000

# Construit l'index Milvus si absent, puis lance l'API (voir entrypoint.sh).
CMD ["./entrypoint.sh"]
