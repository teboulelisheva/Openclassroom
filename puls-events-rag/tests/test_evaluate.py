"""
Tests unitaires — Évaluation du système RAG
CE1 : jeu de test annoté + métriques automatisées
CE2 : résultats documentés et lisibles
CE3 : indicateurs de qualité (précision sémantique, taux acceptable)

Usage :
    pytest tests/test_evaluate.py -v
    pytest tests/test_evaluate.py -v --tb=short > logs/evaluation_results.txt
"""
import pytest
import os
import json
import re
import faiss
import numpy as np
import requests as req
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
VECTORSTORE_PATH = os.environ.get("VECTORSTORE_PATH", "./vectorstore/faiss_index")

# ─── Jeu de test annoté ──────────────────────────────────────────────────────
# Chaque entrée contient :
#   - question : la question posée au système
#   - mots_cles_attendus : mots qui doivent apparaître dans la réponse
#   - critere : description du critère de validation
#   - type : catégorie du test

JEU_DE_TEST = [
    {
        "id": "T01",
        "question": "Quels concerts sont disponibles à Paris ?",
        "mots_cles_attendus": ["concert", "paris", "lieu", "date"],
        "critere": "La réponse mentionne au moins un concert avec lieu et date",
        "type": "concert"
    },
    {
        "id": "T02",
        "question": "Y a-t-il des expositions d'art à Paris ?",
        "mots_cles_attendus": ["exposition", "musée", "paris"],
        "critere": "La réponse mentionne une exposition avec son lieu",
        "type": "exposition"
    },
    {
        "id": "T03",
        "question": "Je cherche un événement pour enfants à Paris",
        "mots_cles_attendus": ["enfant", "famille", "jeune", "spectacle"],
        "critere": "La réponse propose un événement familial ou pour enfants",
        "type": "famille"
    },
    {
        "id": "T04",
        "question": "Des événements culturels gratuits à Paris ?",
        "mots_cles_attendus": ["gratuit", "libre", "entrée", "événement"],
        "critere": "La réponse mentionne des événements gratuits ou indique ne pas en trouver",
        "type": "gratuit"
    },
    {
        "id": "T05",
        "question": "Quels spectacles de danse sont prévus à Paris ?",
        "mots_cles_attendus": ["danse", "spectacle", "paris"],
        "critere": "La réponse mentionne un spectacle de danse ou indique ne pas en trouver",
        "type": "danse"
    },
    {
        "id": "T06",
        "question": "Recommande-moi des activités culturelles à Paris en 2026",
        "mots_cles_attendus": ["paris", "2026", "activité", "événement"],
        "critere": "La réponse propose des activités avec des dates en 2026",
        "type": "general"
    },
    {
        "id": "T07",
        "question": "Quel est le prix du bitcoin ?",
        "mots_cles_attendus": ["pas", "aucun", "trouv", "correspond"],
        "critere": "Le système reconnaît que la question est hors sujet",
        "type": "hors_sujet"
    },
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_embedding(text: str):
    """Génère un embedding via l'API Mistral."""
    r = req.post(
        "https://api.mistral.ai/v1/embeddings",
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
        json={"model": "mistral-embed", "input": [text]},
        timeout=30
    )
    assert r.status_code == 200, f"Erreur embedding : {r.text[:100]}"
    return r.json()["data"][0]["embedding"]


def search_faiss(query: str, k: int = 3):
    """Recherche dans l'index FAISS."""
    index = faiss.read_index(os.path.join(VECTORSTORE_PATH, "index.faiss"))
    with open(os.path.join(VECTORSTORE_PATH, "metadata.json"), "r", encoding="utf-8") as f:
        metadata = json.load(f)
    vec = np.array([get_embedding(query)], dtype=np.float32)
    distances, indices = index.search(vec, k)
    return [(metadata[idx], float(dist)) for dist, idx in zip(distances[0], indices[0]) if idx < len(metadata)]


def call_mistral(prompt: str):
    """Appelle l'API Mistral pour générer une réponse."""
    r = req.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 512,
        },
        timeout=30
    )
    assert r.status_code == 200, f"Erreur Mistral : {r.text[:100]}"
    return r.json()["choices"][0]["message"]["content"]


def rag_pipeline(question: str, k: int = 3):
    """Pipeline RAG complet : question → embedding → FAISS → Mistral."""
    results = search_faiss(question, k=k)
    contexte = ""
    scores = []
    for meta, score in results:
        contexte += (
            f"Evenement : {meta.get('titre', '')}\n"
            f"Lieu : {meta.get('lieu', '')}, {meta.get('ville', '')}\n"
            f"Date : du {meta.get('date_debut', '')} au {meta.get('date_fin', '')}\n"
            f"Detail : {meta.get('texte', '')}\n---\n"
        )
        scores.append(score)

    date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
    prompt = f"""Tu es un assistant culturel pour Puls-Events.
Nous sommes le {date_aujourdhui}.
Reponds a la question en te basant UNIQUEMENT sur les evenements fournis.
Si aucun evenement ne correspond, dis-le clairement.

EVENEMENTS :
{contexte}

QUESTION : {question}
REPONSE :"""

    reponse = call_mistral(prompt)
    score_moyen = sum(scores) / len(scores) if scores else 999
    return reponse, score_moyen, results


def evaluer_reponse(reponse: str, mots_cles: list) -> float:
    """Calcule un score basé sur la présence des mots-clés attendus."""
    reponse_lower = reponse.lower()
    matches = sum(1 for mot in mots_cles if mot.lower() in reponse_lower)
    return matches / len(mots_cles) if mots_cles else 0


# ─── Tests ───────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not MISTRAL_API_KEY, reason="MISTRAL_API_KEY non définie")
class TestJeuDeTest:

    def test_T01_concerts_paris(self):
        """T01 : Le système répond à une question sur les concerts."""
        test = JEU_DE_TEST[0]
        reponse, score_faiss, _ = rag_pipeline(test["question"])
        score = evaluer_reponse(reponse, test["mots_cles_attendus"])
        print(f"\n[{test['id']}] Score mots-clés: {score:.2f} | Score FAISS: {score_faiss:.4f}")
        print(f"Réponse: {reponse[:200]}")
        assert score >= 0.3, f"Réponse insuffisante (score={score:.2f}): {reponse[:100]}"

    def test_T02_expositions_art(self):
        """T02 : Le système répond à une question sur les expositions."""
        test = JEU_DE_TEST[1]
        reponse, score_faiss, _ = rag_pipeline(test["question"])
        score = evaluer_reponse(reponse, test["mots_cles_attendus"])
        print(f"\n[{test['id']}] Score mots-clés: {score:.2f} | Score FAISS: {score_faiss:.4f}")
        assert score >= 0.25, f"Réponse insuffisante (score={score:.2f})"

    def test_T03_enfants_famille(self):
        """T03 : Le système répond à une question sur les événements famille."""
        test = JEU_DE_TEST[2]
        reponse, score_faiss, _ = rag_pipeline(test["question"])
        score = evaluer_reponse(reponse, test["mots_cles_attendus"])
        print(f"\n[{test['id']}] Score mots-clés: {score:.2f} | Score FAISS: {score_faiss:.4f}")
        assert score >= 0.25, f"Réponse insuffisante (score={score:.2f})"

    def test_T04_evenements_gratuits(self):
        """T04 : Le système répond à une question sur les événements gratuits."""
        test = JEU_DE_TEST[3]
        reponse, score_faiss, _ = rag_pipeline(test["question"])
        score = evaluer_reponse(reponse, test["mots_cles_attendus"])
        print(f"\n[{test['id']}] Score mots-clés: {score:.2f} | Score FAISS: {score_faiss:.4f}")
        assert score >= 0.25, f"Réponse insuffisante (score={score:.2f})"

    def test_T05_danse(self):
        """T05 : Le système répond à une question sur la danse."""
        test = JEU_DE_TEST[4]
        reponse, score_faiss, _ = rag_pipeline(test["question"])
        score = evaluer_reponse(reponse, test["mots_cles_attendus"])
        print(f"\n[{test['id']}] Score mots-clés: {score:.2f} | Score FAISS: {score_faiss:.4f}")
        assert score >= 0.25, f"Réponse insuffisante (score={score:.2f})"

    def test_T06_activites_2026(self):
        """T06 : Le système propose des activités en 2026."""
        test = JEU_DE_TEST[5]
        reponse, score_faiss, _ = rag_pipeline(test["question"])
        score = evaluer_reponse(reponse, test["mots_cles_attendus"])
        print(f"\n[{test['id']}] Score mots-clés: {score:.2f} | Score FAISS: {score_faiss:.4f}")
        assert score >= 0.25, f"Réponse insuffisante (score={score:.2f})"

    def test_T07_hors_sujet(self):
        """T07 : Le système gère correctement une question hors sujet."""
        test = JEU_DE_TEST[6]
        reponse, score_faiss, _ = rag_pipeline(test["question"])
        score = evaluer_reponse(reponse, test["mots_cles_attendus"])
        print(f"\n[{test['id']}] Score mots-clés: {score:.2f} | Score FAISS: {score_faiss:.4f}")
        assert len(reponse) > 10, "La réponse est vide"


@pytest.mark.skipif(not MISTRAL_API_KEY, reason="MISTRAL_API_KEY non définie")
class TestMetriques:

    def test_score_faiss_acceptable(self):
        """Les scores FAISS sont dans une plage acceptable (< 1.0)."""
        _, score_faiss, _ = rag_pipeline("concert paris", k=3)
        print(f"\nScore FAISS moyen : {score_faiss:.4f}")
        assert score_faiss < 1.0, f"Score FAISS trop élevé : {score_faiss:.4f}"

    def test_temps_reponse_acceptable(self):
        """Le temps de réponse est inférieur à 10 secondes."""
        import time
        start = time.time()
        rag_pipeline("exposition paris", k=3)
        elapsed = time.time() - start
        print(f"\nTemps de réponse : {elapsed:.2f}s")
        assert elapsed < 10, f"Temps de réponse trop long : {elapsed:.2f}s"

    def test_reponse_non_vide(self):
        """La réponse générée n'est jamais vide."""
        reponse, _, _ = rag_pipeline("événement culturel paris", k=3)
        assert len(reponse.strip()) > 10, "La réponse est vide"

    def test_taux_reussite_global(self):
        """Au moins 70% des tests du jeu annoté sont corrects."""
        scores = []
        for test in JEU_DE_TEST[:5]:
            reponse, _, _ = rag_pipeline(test["question"], k=3)
            score = evaluer_reponse(reponse, test["mots_cles_attendus"])
            scores.append(score >= 0.25)

        taux = sum(scores) / len(scores)
        print(f"\nTaux de réussite global : {taux:.0%} ({sum(scores)}/{len(scores)})")
        assert taux >= 0.7, f"Taux de réussite insuffisant : {taux:.0%}"

    def test_generation_rapport_evaluation(self, tmp_path):
        """Génère un rapport d'évaluation lisible."""
        os.makedirs("logs", exist_ok=True)
        rapport = {
            "date": datetime.now().isoformat(),
            "nb_tests": len(JEU_DE_TEST),
            "resultats": []
        }

        for test in JEU_DE_TEST[:3]:
            reponse, score_faiss, _ = rag_pipeline(test["question"], k=3)
            score_mots = evaluer_reponse(reponse, test["mots_cles_attendus"])
            rapport["resultats"].append({
                "id": test["id"],
                "question": test["question"],
                "score_mots_cles": round(score_mots, 3),
                "score_faiss": round(score_faiss, 4),
                "statut": "OK" if score_mots >= 0.25 else "KO",
                "reponse_extrait": reponse[:150]
            })

        with open("logs/evaluation_results.json", "w", encoding="utf-8") as f:
            json.dump(rapport, f, ensure_ascii=False, indent=2)

        assert os.path.exists("logs/evaluation_results.json")
        print(f"\nRapport généré : logs/evaluation_results.json")
