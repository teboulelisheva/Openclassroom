#!/bin/sh
# Démarrage du backend :
#  1) construit l'index Milvus s'il n'existe pas encore (persiste ensuite) ;
#  2) lance l'API FastAPI.
# L'index n'est reconstruit qu'au premier démarrage grâce au volume vectorstore.

echo "== FFE Chess Agent : démarrage du backend =="

if python scripts/check_index.py; then
  echo "Index Milvus déjà présent : pas de reconstruction."
else
  echo "Index Milvus absent -> construction (télécharge le modèle au 1er lancement)..."
  python scripts/build_index.py || echo "AVERTISSEMENT: build_index a échoué, l'API démarre quand même."
fi

echo "Lancement de l'API FastAPI sur le port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
