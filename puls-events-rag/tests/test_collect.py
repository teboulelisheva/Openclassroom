"""
Tests unitaires — Récupération des données
CE1 : valide que l'API Paris retourne des données exploitables
"""
import pytest
import requests
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records"


def test_api_paris_accessible():
    """L'API Paris répond avec un status 200."""
    r = requests.get(BASE_URL, params={"limit": 1}, timeout=10)
    assert r.status_code == 200, f"API inaccessible : {r.status_code}"


def test_api_retourne_des_resultats():
    """L'API retourne au moins un événement."""
    r = requests.get(BASE_URL, params={"limit": 5}, timeout=10)
    data = r.json()
    results = data.get("results", [])
    assert len(results) > 0, "Aucun événement retourné"


def test_api_champs_obligatoires():
    """Chaque événement contient les champs attendus."""
    r = requests.get(BASE_URL, params={"limit": 5}, timeout=10)
    results = r.json().get("results", [])
    champs = ["title", "date_start", "date_end"]
    for event in results:
        for champ in champs:
            assert champ in event, f"Champ manquant : {champ}"


def test_api_filtre_date():
    """Le filtre sur les dates fonctionne."""
    from datetime import datetime, timedelta
    date_debut = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
    date_fin = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
    params = {
        "limit": 5,
        "where": f'date_start >= "{date_debut}" AND date_start <= "{date_fin}"',
    }
    r = requests.get(BASE_URL, params=params, timeout=10)
    assert r.status_code == 200
    results = r.json().get("results", [])
    assert len(results) > 0, "Aucun événement dans la période demandée"


def test_api_pagination():
    """La pagination fonctionne correctement."""
    r1 = requests.get(BASE_URL, params={"limit": 5, "offset": 0}, timeout=10)
    r2 = requests.get(BASE_URL, params={"limit": 5, "offset": 5}, timeout=10)
    ids1 = [e.get("id") for e in r1.json().get("results", [])]
    ids2 = [e.get("id") for e in r2.json().get("results", [])]
    assert set(ids1).isdisjoint(set(ids2)), "La pagination retourne des doublons"
