"""
Script de build de l'index vectoriel FAISS
Recupere les evenements depuis l'API Ville de Paris
et construit l'index vectoriel avec les embeddings Mistral

Usage :
    python scripts/build_index.py

Variables d'environnement requises :
    MISTRAL_API_KEY : cle API Mistral
"""
import os
import re
import requests
import pandas as pd
import faiss
import numpy as np
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
VECTORSTORE_PATH = os.environ.get("VECTORSTORE_PATH", "./vectorstore/faiss_index")
BASE_URL_PARIS = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records"
DATE_DEBUT = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
DATE_FIN = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")


def clean_html(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_events(limit=100, max_records=500):
    print("Recuperation des evenements depuis l'API Paris...")
    all_records = []
    offset = 0
    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "where": f'date_start >= "{DATE_DEBUT}" AND date_start <= "{DATE_FIN}"',
            "order_by": "date_start ASC",
            "lang": "fr",
        }
        r = requests.get(BASE_URL_PARIS, params=params, timeout=30)
        if r.status_code != 200:
            print(f"Erreur {r.status_code}: {r.text[:100]}")
            break
        records = r.json().get("results", [])
        if not records:
            break
        all_records.extend(records)
        print(f"  {len(all_records)} evenements recuperes...")
        offset += limit
        if len(all_records) >= max_records:
            break
    print(f"Total : {len(all_records)} evenements")
    return all_records


def build_dataframe(raw_events):
    rows = []
    for e in raw_events:
        rows.append({
            "uid": str(e.get("id", "")),
            "titre": clean_html(e.get("title", "") or ""),
            "description": clean_html(e.get("description", "") or e.get("lead_text", "") or ""),
            "lieu": e.get("address_name", "") or "",
            "adresse": e.get("address_street", "") or "",
            "ville": "Paris",
            "code_postal": e.get("address_zipcode", "") or "",
            "date_debut": (e.get("date_start", "") or "")[:10],
            "date_fin": (e.get("date_end", "") or "")[:10],
            "categories": e.get("category", "") or "",
            "url": e.get("url", "") or "",
        })
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset="uid")
    df = df[df["description"].str.len() > 20]
    df = df[df["titre"].str.len() > 2]
    df["texte_complet"] = (
        "Evenement : " + df["titre"] + ". "
        + "Lieu : " + df["lieu"] + ", " + df["ville"] + ". "
        + "Du " + df["date_debut"] + " au " + df["date_fin"] + ". "
        + "Categories : " + df["categories"] + ". "
        + "Description : " + df["description"].str[:500]
    )
    print(f"Dataset : {len(df)} evenements apres nettoyage")
    return df


def get_embeddings(texts):
    """Embeddings via API Mistral par batch de 50"""
    all_embeddings = []
    batch_size = 50
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        r = requests.post(
            "https://api.mistral.ai/v1/embeddings",
            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
            json={"model": "mistral-embed", "input": batch}
        )
        if r.status_code != 200:
            raise Exception(f"Erreur Mistral embeddings : {r.text[:100]}")
        all_embeddings.extend([item["embedding"] for item in r.json()["data"]])
        print(f"  Embeddings batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
    return all_embeddings


def chunk_texts(df, chunk_size=500, overlap=50):
    """Decoupage simple des textes en chunks"""
    chunks = []
    for _, row in df.iterrows():
        text = row["texte_complet"]
        # Decoupage par phrases si trop long
        if len(text) <= chunk_size:
            chunks.append({
                "texte": text,
                **{k: row[k] for k in ["uid", "titre", "lieu", "ville", "date_debut", "date_fin", "categories", "url"]}
            })
        else:
            # Decoupage avec overlap
            start = 0
            while start < len(text):
                end = min(start + chunk_size, len(text))
                chunks.append({
                    "texte": text[start:end],
                    **{k: row[k] for k in ["uid", "titre", "lieu", "ville", "date_debut", "date_fin", "categories", "url"]}
                })
                start += chunk_size - overlap
    return chunks


def build_index(df):
    print("Chunking des textes...")
    chunks = chunk_texts(df)
    print(f"{len(chunks)} chunks crees")

    print("Generation des embeddings via Mistral...")
    texts = [c["texte"] for c in chunks]
    embeddings = get_embeddings(texts)

    # Construction index FAISS
    print("Construction de l'index FAISS...")
    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    vectors = np.array(embeddings, dtype=np.float32)
    index.add(vectors)
    print(f"Index FAISS : {index.ntotal} vecteurs (dim={dim})")

    # Sauvegarde index + metadonnees
    os.makedirs(VECTORSTORE_PATH, exist_ok=True)
    faiss.write_index(index, os.path.join(VECTORSTORE_PATH, "index.faiss"))

    # Sauvegarder les metadonnees separement
    metadata = [{"texte": c["texte"], "uid": c["uid"], "titre": c["titre"],
                 "lieu": c["lieu"], "ville": c["ville"], "date_debut": c["date_debut"],
                 "date_fin": c["date_fin"], "categories": c["categories"], "url": c["url"]}
                for c in chunks]
    with open(os.path.join(VECTORSTORE_PATH, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Index sauvegarde dans {VECTORSTORE_PATH}/")
    return index, metadata


if __name__ == "__main__":
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY non definie ! Copie .env.example en .env et remplis la cle.")
    raw = fetch_events()
    df = build_dataframe(raw)
    build_index(df)
    print("\nBuild termine ! Lance maintenant : docker build -t puls-events-rag . && docker run -p 8000:8000 --env-file .env puls-events-rag")
