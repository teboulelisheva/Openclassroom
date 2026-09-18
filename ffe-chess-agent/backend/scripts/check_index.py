"""Vérifie la présence de l'index Milvus.

Code de sortie 0 si la collection existe déjà, 1 sinon. Utilisé par
l'entrypoint pour ne (re)construire l'index qu'au premier démarrage.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.milvus_service import get_milvus_service  # noqa: E402

svc = get_milvus_service()
try:
    exists = svc.get_client().has_collection(svc.collection)
except Exception as exc:  # noqa: BLE001
    print(f"Vérification de l'index impossible : {exc}")
    exists = False

sys.exit(0 if exists else 1)
