"""
Puls-Events RAG API
API FastAPI exposant le systeme RAG
"""
import os
import re
import json
import faiss
import numpy as np
import requests
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Tuple
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
VECTORSTORE_PATH = os.environ.get("VECTORSTORE_PATH", "./vectorstore/faiss_index")

app = FastAPI(
    title="Puls-Events RAG API",
    description="API de recommandation d evenements culturels basee sur un systeme RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Chargement de l'index au demarrage ---
index = None
metadata = []

def load_index():
    global index, metadata
    index_path = os.path.join(VECTORSTORE_PATH, "index.faiss")
    meta_path = os.path.join(VECTORSTORE_PATH, "metadata.json")
    if not os.path.exists(index_path):
        raise FileNotFoundError(
            f"Index FAISS introuvable : {index_path}. "
            "Lance d'abord : python scripts/build_index.py"
        )
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    print(f"Index charge : {index.ntotal} vecteurs")

@app.on_event("startup")
def startup():
    load_index()


# --- Extraction temporelle ---

def extract_temporal_filter(question: str) -> Optional[Tuple[str, str]]:
    """
    Extrait une contrainte temporelle de la question.
    Retourne un tuple (date_debut, date_fin) au format YYYY-MM-DD
    ou None si pas de contrainte temporelle detectee.
    """
    now = datetime.now()
    q = question.lower()

    # --- Date explicite JJ/MM/AAAA ---
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', question)
    if match:
        date_str = f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
        if "avant" in q:
            return ("0000-01-01", date_str)
        else:  # apres le, a partir du, depuis le
            return (date_str, "9999-12-31")

    # --- Date explicite YYYY-MM-DD ---
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', question)
    if match:
        date_str = match.group(0)
        if "avant" in q:
            return ("0000-01-01", date_str)
        else:
            return (date_str, "9999-12-31")

    # --- Ce weekend ---
    if "ce weekend" in q or "ce week-end" in q:
        # Prochain samedi et dimanche
        days_until_saturday = (5 - now.weekday()) % 7
        saturday = now + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)
        return (saturday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d"))

    # --- Cette semaine ---
    if "cette semaine" in q:
        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=7 - now.weekday())).strftime("%Y-%m-%d")
        return (start, end)

    # --- Ce mois-ci / en mai / en juin etc. ---
    mois_map = {
        "janvier": 1, "fevrier": 2, "février": 2, "mars": 3,
        "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
        "aout": 8, "août": 8, "septembre": 9, "octobre": 10,
        "novembre": 11, "decembre": 12, "décembre": 12
    }

    if "ce mois" in q:
        debut = now.replace(day=1).strftime("%Y-%m-%d")
        # Dernier jour du mois
        next_month = now.replace(day=28) + timedelta(days=4)
        fin = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")
        return (debut, fin)

    for mois_str, mois_num in mois_map.items():
        if mois_str in q:
            annee = now.year
            # Si le mois est passe cette annee, on prend l'annee prochaine
            if mois_num < now.month:
                annee += 1
            debut = f"{annee}-{mois_num:02d}-01"
            next_month = datetime(annee, mois_num, 28) + timedelta(days=4)
            fin = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")
            return (debut, fin)

    # --- Aujourd'hui ---
    if "aujourd" in q or "ce soir" in q:
        today = now.strftime("%Y-%m-%d")
        return (today, today)

    # --- Bientot / prochainement / a venir ---
    if any(mot in q for mot in ["bientot", "bientôt", "prochainement", "a venir", "à venir"]):
        start = now.strftime("%Y-%m-%d")
        end = (now + timedelta(days=30)).strftime("%Y-%m-%d")
        return (start, end)

    # --- Pas de contrainte temporelle detectee ---
    return None


def filter_by_date(results, question: str, k: int):
    """Applique le filtre temporel extrait de la question."""
    temporal = extract_temporal_filter(question)

    if temporal:
        date_debut_filtre, date_fin_filtre = temporal
        print(f"Filtre temporel detecte : {date_debut_filtre} -> {date_fin_filtre}")
        filtres = [
            (meta, score) for meta, score in results
            if meta.get("date_debut", "") <= date_fin_filtre   # commence avant la fin de la periode
            and meta.get("date_fin", "") >= date_debut_filtre  # finit apres le debut de la periode
        ]
        results = filtres if filtres else results

    return results[:k]


# --- Helpers ---
def get_embedding(text: str) -> List[float]:
    r = requests.post(
        "https://api.mistral.ai/v1/embeddings",
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
        json={"model": "mistral-embed", "input": [text]}
    )
    if r.status_code != 200:
        raise Exception(f"Erreur Mistral embeddings : {r.text[:100]}")
    return r.json()["data"][0]["embedding"]


def search_faiss(query: str, k: int = 3):
    vec = np.array([get_embedding(query)], dtype=np.float32)
    distances, indices = index.search(vec, k)
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(metadata):
            results.append((metadata[idx], float(dist)))
    return results


# --- Modeles ---
class QuestionRequest(BaseModel):
    question: str
    k: Optional[int] = 3

class AnswerResponse(BaseModel):
    question: str
    reponse: str
    nb_documents: int
    sources: list


# --- Endpoints ---
@app.get("/health", tags=["Monitoring"])
def health_check():
    """Verifie que l API et l index FAISS sont operationnels."""
    return {
        "status": "ok",
        "nb_vecteurs": index.ntotal if index else 0,
        "message": "API operationnelle"
    }


@app.post("/ask", response_model=AnswerResponse, tags=["Chatbot"])
def ask(request: QuestionRequest):
    """Pose une question au chatbot RAG."""
    if not request.question or len(request.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question trop courte ou vide")
    if request.k < 1 or request.k > 10:
        raise HTTPException(status_code=400, detail="k doit etre entre 1 et 10")

    try:
        # Recupere plus de resultats pour compenser le filtre date
        raw_results = search_faiss(request.question, k=request.k * 3)

        # Filtre temporel intelligent
        results = filter_by_date(raw_results, request.question, k=request.k)

        # Construction du contexte
        contexte = ""
        sources = []
        for meta, score in results:
            contexte += (
                f"Evenement : {meta.get('titre', '')}\n"
                f"Lieu : {meta.get('lieu', '')}, {meta.get('ville', '')}\n"
                f"Date : du {meta.get('date_debut', '')} au {meta.get('date_fin', '')}\n"
                f"Categories : {meta.get('categories', '')}\n"
                f"Detail : {meta.get('texte', '')}\n---\n"
            )
            sources.append({
                "titre": meta.get("titre", ""),
                "lieu": meta.get("lieu", ""),
                "date_debut": meta.get("date_debut", ""),
                "date_fin": meta.get("date_fin", ""),
                "score": round(score, 4),
                "url": meta.get("url", "")
            })

        # Prompt avec date courante
        date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
        temporal = extract_temporal_filter(request.question)
        contexte_temporel = ""
        if temporal:
            contexte_temporel = f"La question porte sur la periode du {temporal[0]} au {temporal[1]}.\n"

        prompt = f"""Tu es un assistant culturel pour Puls-Events, specialise dans les evenements a Paris.
Nous sommes le {date_aujourdhui}.
{contexte_temporel}Reponds a la question en te basant UNIQUEMENT sur les evenements fournis ci-dessous.
Si aucun evenement ne correspond a la periode demandee, dis-le clairement.
Sois precis, friendly et donne les informations pratiques (lieu, date, lien si disponible).

EVENEMENTS :
{contexte}

QUESTION : {request.question}
REPONSE :"""

        r = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "mistral-small-latest",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 512,
            }
        )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Erreur Mistral : {r.text[:100]}")

        reponse = r.json()["choices"][0]["message"]["content"]
        return {
            "question": request.question,
            "reponse": reponse,
            "nb_documents": len(results),
            "sources": sources
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rebuild", tags=["Admin"])
def rebuild():
    """Recharge l index FAISS depuis le disque."""
    try:
        load_index()
        return {"status": "ok", "message": f"Index recharge : {index.ntotal} vecteurs"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))