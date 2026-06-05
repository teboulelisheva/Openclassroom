"""
Tests unitaires — Nettoyage des données
CE1 : valide que le prétraitement produit des données exploitables
"""
import pytest
import re
import pandas as pd


def clean_html(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_event_fields(event):
    return {
        "uid": str(event.get("id", "")),
        "titre": clean_html(event.get("title", "") or ""),
        "description": clean_html(event.get("description", "") or event.get("lead_text", "") or ""),
        "lieu": event.get("address_name", "") or "",
        "ville": "Paris",
        "date_debut": (event.get("date_start", "") or "")[:10],
        "date_fin": (event.get("date_end", "") or "")[:10],
        "categories": event.get("category", "") or "",
        "url": event.get("url", "") or "",
    }


SAMPLE_EVENTS = [
    {"id": "1", "title": "<b>Concert Jazz</b>", "description": "Un beau concert.", "address_name": "Salle Gaveau", "date_start": "2026-06-01T20:00:00", "date_end": "2026-06-01T23:00:00", "category": "Concert", "url": "https://paris.fr/1"},
    {"id": "2", "title": "Exposition Monet", "description": "Grande expo.", "address_name": "Marmottan", "date_start": "2026-03-01T00:00:00", "date_end": "2026-09-30T00:00:00", "category": "Exposition", "url": ""},
    {"id": "2", "title": "Exposition Monet", "description": "Grande expo.", "address_name": "Marmottan", "date_start": "2026-03-01T00:00:00", "date_end": "2026-09-30T00:00:00", "category": "Exposition", "url": ""},
    {"id": "3", "title": "X", "description": "", "address_name": "", "date_start": "", "date_end": "", "category": "", "url": ""},
]


def build_df(events):
    rows = [extract_event_fields(e) for e in events]
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset="uid")
    df = df[df["description"].str.len() > 20]
    df = df[df["titre"].str.len() > 2]
    df["texte_complet"] = (
        "Evenement : " + df["titre"] + ". "
        + "Lieu : " + df["lieu"] + ", " + df["ville"] + ". "
        + "Du " + df["date_debut"] + " au " + df["date_fin"] + ". "
        + "Description : " + df["description"].str[:500]
    )
    return df


def test_clean_html_supprime_balises():
    """Les balises HTML sont supprimées."""
    assert clean_html("<b>Concert</b>") == "Concert"
    assert clean_html("<p>Hello <br/> world</p>") == "Hello world"


def test_clean_html_gere_none():
    """La fonction gère les valeurs None."""
    assert clean_html(None) == ""
    assert clean_html(123) == ""


def test_clean_html_espaces():
    """Les espaces multiples sont normalisés."""
    assert clean_html("hello   world") == "hello world"


def test_extraction_champs():
    """L'extraction des champs fonctionne correctement."""
    event = SAMPLE_EVENTS[0]
    row = extract_event_fields(event)
    assert row["uid"] == "1"
    assert row["titre"] == "Concert Jazz"
    assert row["ville"] == "Paris"
    assert row["date_debut"] == "2026-06-01"


def test_deduplication():
    """Les doublons sont supprimés."""
    df = build_df(SAMPLE_EVENTS)
    assert df["uid"].nunique() == len(df), "Des doublons sont présents"


def test_filtre_description_vide():
    """Les événements sans description sont écartés."""
    df = build_df(SAMPLE_EVENTS)
    assert all(df["description"].str.len() > 20)


def test_filtre_titre_court():
    """Les événements avec un titre trop court sont écartés."""
    df = build_df(SAMPLE_EVENTS)
    assert all(df["titre"].str.len() > 2)


def test_texte_complet_cree():
    """Le champ texte_complet est bien créé."""
    df = build_df(SAMPLE_EVENTS)
    assert "texte_complet" in df.columns
    assert all(df["texte_complet"].str.len() > 50)


def test_dataset_non_vide():
    """Le dataset final contient des données."""
    df = build_df(SAMPLE_EVENTS)
    assert len(df) > 0
