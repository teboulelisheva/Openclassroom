"""
Tests unitaires — Endpoints API FastAPI
"""
import pytest
import json
import faiss
import numpy as np
import api.main as main_module
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock index et metadata
MOCK_INDEX = faiss.IndexFlatL2(1024)
MOCK_VECTORS = np.random.rand(3, 1024).astype(np.float32)
MOCK_INDEX.add(MOCK_VECTORS)

MOCK_METADATA = [
    {"uid": "1", "titre": "Concert Jazz", "lieu": "Salle Gaveau", "ville": "Paris",
     "date_debut": "2026-06-01", "date_fin": "2026-06-01", "categories": "Concert",
     "texte": "Concert de jazz au Salle Gaveau Paris.", "url": "https://paris.fr/1"},
    {"uid": "2", "titre": "Exposition Monet", "lieu": "Marmottan", "ville": "Paris",
     "date_debut": "2026-03-01", "date_fin": "2026-09-30", "categories": "Exposition",
     "texte": "Grande exposition Monet au Marmottan.", "url": "https://paris.fr/2"},
    {"uid": "3", "titre": "Spectacle enfants", "lieu": "Theatre", "ville": "Paris",
     "date_debut": "2026-05-15", "date_fin": "2026-05-15", "categories": "Spectacle",
     "texte": "Spectacle pour enfants au Theatre.", "url": "https://paris.fr/3"},
]

# Injection directe dans le module
main_module.index = MOCK_INDEX
main_module.metadata = MOCK_METADATA

from api.main import app
client = TestClient(app)


def mock_embed(*args, **kwargs):
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"data": [{"embedding": [0.1] * 1024}]}
    return mock


def mock_mistral(*args, **kwargs):
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "choices": [{"message": {"content": "Il y a un concert de jazz le 1er juin 2026 a la Salle Gaveau."}}]
    }
    return mock


class TestHealth:
    def test_health_status_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_champs(self):
        r = client.get("/health")
        data = r.json()
        assert "status" in data
        assert "nb_vecteurs" in data
        assert "message" in data

    def test_health_status_ok(self):
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_nb_vecteurs(self):
        r = client.get("/health")
        assert r.json()["nb_vecteurs"] == 3


class TestAsk:
    @patch("api.main.requests.post")
    def test_ask_valide(self, mock_post):
        mock_post.side_effect = [mock_embed(), mock_mistral()]
        r = client.post("/ask", json={"question": "Quels concerts a Paris ?", "k": 2})
        assert r.status_code == 200

    @patch("api.main.requests.post")
    def test_ask_champs_reponse(self, mock_post):
        mock_post.side_effect = [mock_embed(), mock_mistral()]
        r = client.post("/ask", json={"question": "Quels concerts a Paris ?", "k": 2})
        data = r.json()
        assert "question" in data
        assert "reponse" in data
        assert "nb_documents" in data
        assert "sources" in data

    @patch("api.main.requests.post")
    def test_ask_sources_avec_date_fin(self, mock_post):
        mock_post.side_effect = [mock_embed(), mock_mistral()]
        r = client.post("/ask", json={"question": "concerts Paris", "k": 2})
        sources = r.json()["sources"]
        for source in sources:
            assert "date_fin" in source

    def test_ask_question_vide_400(self):
        r = client.post("/ask", json={"question": ""})
        assert r.status_code == 400

    def test_ask_question_trop_courte_400(self):
        r = client.post("/ask", json={"question": "ab"})
        assert r.status_code == 400

    def test_ask_k_trop_grand_400(self):
        r = client.post("/ask", json={"question": "concerts Paris", "k": 15})
        assert r.status_code == 400

    def test_ask_k_zero_400(self):
        r = client.post("/ask", json={"question": "concerts Paris", "k": 0})
        assert r.status_code == 400

    @patch("api.main.requests.post")
    def test_ask_nb_sources_coherent(self, mock_post):
        mock_post.side_effect = [mock_embed(), mock_mistral()]
        r = client.post("/ask", json={"question": "concerts Paris", "k": 2})
        data = r.json()
        assert data["nb_documents"] == len(data["sources"])


class TestRebuild:
    @patch("api.main.load_index")
    def test_rebuild_200(self, mock_load):
        mock_load.return_value = None
        r = client.post("/rebuild")
        assert r.status_code == 200

    @patch("api.main.load_index")
    def test_rebuild_status_ok(self, mock_load):
        mock_load.return_value = None
        r = client.post("/rebuild")
        assert r.json()["status"] == "ok"


class TestFiltreTemporel:
    @patch("api.main.requests.post")
    def test_filtre_ce_mois(self, mock_post):
        mock_post.side_effect = [mock_embed(), mock_mistral()]
        r = client.post("/ask", json={"question": "concerts ce mois a Paris", "k": 3})
        assert r.status_code == 200

    @patch("api.main.requests.post")
    def test_filtre_date_explicite(self, mock_post):
        mock_post.side_effect = [mock_embed(), mock_mistral()]
        r = client.post("/ask", json={"question": "concerts apres le 01/06/2026", "k": 3})
        assert r.status_code == 200