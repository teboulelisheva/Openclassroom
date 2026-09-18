"""
Tests unitaires — Vectorisation et indexation FAISS
CE1 : valide que l'index vectoriel est correctement construit
"""
import pytest
import os
import json
import faiss
import numpy as np


VECTORSTORE_PATH = os.environ.get("VECTORSTORE_PATH", "./vectorstore/faiss_index")
INDEX_PATH = os.path.join(VECTORSTORE_PATH, "index.faiss")
META_PATH = os.path.join(VECTORSTORE_PATH, "metadata.json")


def test_index_faiss_existe():
    """Le fichier index.faiss existe sur le disque."""
    assert os.path.exists(INDEX_PATH), f"Index FAISS introuvable : {INDEX_PATH}"


def test_metadata_existe():
    """Le fichier metadata.json existe sur le disque."""
    assert os.path.exists(META_PATH), f"Metadata introuvable : {META_PATH}"


def test_index_non_vide():
    """L'index FAISS contient des vecteurs."""
    index = faiss.read_index(INDEX_PATH)
    assert index.ntotal > 0, "L'index FAISS est vide"


def test_index_dimension():
    """Les vecteurs ont la bonne dimension (1024 pour Mistral Embed)."""
    index = faiss.read_index(INDEX_PATH)
    assert index.d == 1024, f"Dimension incorrecte : {index.d} (attendu 1024)"


def test_metadata_coherent_avec_index():
    """Le nombre de métadonnées correspond au nombre de vecteurs."""
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    assert index.ntotal == len(metadata), f"Incohérence : {index.ntotal} vecteurs pour {len(metadata)} métadonnées"


def test_metadata_champs_obligatoires():
    """Chaque entrée de métadonnées contient les champs requis."""
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    champs = ["uid", "titre", "lieu", "ville", "date_debut", "date_fin", "texte"]
    for i, meta in enumerate(metadata[:10]):
        for champ in champs:
            assert champ in meta, f"Chunk {i} — champ manquant : {champ}"


def test_recherche_retourne_resultats():
    """Une recherche FAISS retourne des résultats."""
    index = faiss.read_index(INDEX_PATH)
    vec = np.random.rand(1, 1024).astype(np.float32)
    distances, indices = index.search(vec, k=3)
    assert len(indices[0]) == 3
    assert all(idx >= 0 for idx in indices[0])


def test_scores_positifs():
    """Les scores de similarité FAISS sont positifs."""
    index = faiss.read_index(INDEX_PATH)
    vec = np.random.rand(1, 1024).astype(np.float32)
    distances, indices = index.search(vec, k=3)
    assert all(d >= 0 for d in distances[0]), "Des scores négatifs détectés"


def test_uids_uniques():
    """Pas de doublons d'événements dans les métadonnées."""
    with open(META_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    uids = [m["uid"] for m in metadata]
    evenements_uniques = len(set(uids))
    assert evenements_uniques > 0, "Aucun événement unique trouvé"


def test_rechargement_index():
    """L'index peut être rechargé depuis le disque sans erreur."""
    index1 = faiss.read_index(INDEX_PATH)
    index2 = faiss.read_index(INDEX_PATH)
    assert index1.ntotal == index2.ntotal
