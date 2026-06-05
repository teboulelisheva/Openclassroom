import faiss
import json
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
VECTORSTORE_PATH = os.environ.get("VECTORSTORE_PATH", "./vectorstore/faiss_index")

# Charge l'index
index = faiss.read_index(f"{VECTORSTORE_PATH}/index.faiss")
with open(f"{VECTORSTORE_PATH}/metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

print(f"Nombre de vecteurs : {index.ntotal}")
print(f"Dimension          : {index.d}")
print(f"Nombre de chunks   : {len(metadata)}")

# Stats sur les evenements uniques
uids = set(m["uid"] for m in metadata)
print(f"Evenements uniques : {len(uids)}")

# Exemple de recherche avec score
from dotenv import load_dotenv
import requests, os

def get_embedding(text):
    r = requests.post(
        "https://api.mistral.ai/v1/embeddings",
        headers={"Authorization": f"Bearer {os.environ['MISTRAL_API_KEY']}", "Content-Type": "application/json"},
        json={"model": "mistral-embed", "input": [text]}
    )
    return r.json()["data"][0]["embedding"]

query = "concert Paris"
vec = np.array([get_embedding(query)], dtype=np.float32)
distances, indices = index.search(vec, 5)

print(f"\nRecherche : '{query}'")
print(f"{'Score':<10} {'Titre':<50} {'Date'}")
print("-" * 80)
for dist, idx in zip(distances[0], indices[0]):
    m = metadata[idx]
    print(f"{dist:<10.4f} {m['titre'][:48]:<50} {m['date_debut']}")