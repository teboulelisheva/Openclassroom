# Version Python figée pour garantir la reproductibilité
FROM python:3.12-slim

# Bonnes pratiques : pas de .pyc, sortie non bufferisée (logs immédiats)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# On installe les dépendances d'abord pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis le code applicatif
COPY ./app ./app

EXPOSE 8000

# --reload est pratique en dev ; à retirer en production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
