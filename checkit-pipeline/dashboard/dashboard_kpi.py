"""
dashboard/dashboard_kpi.py — Tableau de bord KPI du pipeline ETL CheckIt.AI.

Trois familles d'indicateurs (recommandation de la mission) :
  1. PRÉCISION : % d'entrées valides après transformation, causes de rejet ;
  2. RAPIDITÉ  : durée de chaque tâche Airflow, évolution sur les runs ;
  3. COÛT      : volume stocké (images + base), appels API consommés.

Conçu pour un public NON TECHNIQUE : gros chiffres (st.metric), libellés
en français, code couleur simple (vert = OK, rouge = seuil dépassé).
Les seuils affichés sont ceux du plan de monitoring (docs/plan_monitoring.md).

Lancement :
    streamlit run dashboard/dashboard_kpi.py
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration (mêmes conventions que le pipeline)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

RAW_JSONL = PROJECT_ROOT / "data" / "publications.jsonl"
CLEAN_JSONL = PROJECT_ROOT / "data" / "dataset_clean.jsonl"
IMAGES_DIR = PROJECT_ROOT / "data" / "images"
PIPELINE_LOG = PROJECT_ROOT / "pipeline.log"
AIRFLOW_DB = Path(os.getenv("AIRFLOW_HOME", Path.home() / "airflow")) / "airflow.db"
DAG_ID = "etl_checkit_multimodal"

# Seuils d'alerte (alignés sur le plan de monitoring)
SEUIL_VALIDITE_MIN = 70.0      # % minimum d'entrées valides
SEUIL_DUREE_EXTRACT_MIN = 15   # minutes max pour la tâche d'extraction


# ---------------------------------------------------------------------------
# Collecte des métriques (chaque fonction échoue proprement si la
# source manque : le dashboard reste utilisable partiellement)
# ---------------------------------------------------------------------------
def compte_jsonl(path: Path) -> int:
    """Nombre d'entrées d'un fichier JSON Lines (0 si absent)."""
    if not path.exists():
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for ligne in f if ligne.strip())


def charge_dataset_clean() -> pd.DataFrame:
    """Charge le dataset propre pour les graphiques (vide si absent)."""
    if not CLEAN_JSONL.exists():
        return pd.DataFrame()
    return pd.read_json(CLEAN_JSONL, lines=True)


def rejets_depuis_logs() -> dict:
    """Compte les causes de rejet dans pipeline.log (WARNING typés)."""
    causes = {"Image invalide": 0, "Texte trop court": 0, "Doublons": 0}
    if not PIPELINE_LOG.exists():
        return causes
    with open(PIPELINE_LOG, "r", encoding="utf-8") as f:
        for ligne in f:
            if "image invalide" in ligne.lower() or "Image inaccessible" in ligne:
                causes["Image invalide"] += 1
            elif "Texte trop court" in ligne:
                causes["Texte trop court"] += 1
            elif "Doublon ignoré" in ligne:
                causes["Doublons"] += 1
    return causes


def durees_taches_airflow() -> pd.DataFrame:
    """Durées des tâches depuis la base de métadonnées Airflow (SQLite).

    En mode 'standalone', Airflow stocke chaque exécution de tâche dans
    la table task_instance : on y lit début, fin et état pour calculer
    la durée réelle de chaque tâche, run par run.
    """
    if not AIRFLOW_DB.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(f"file:{AIRFLOW_DB}?mode=ro", uri=True)
        df = pd.read_sql_query(
            """SELECT task_id, run_id, state, start_date, end_date
               FROM task_instance
               WHERE dag_id = ? AND start_date IS NOT NULL
               ORDER BY start_date""",
            conn, params=(DAG_ID,),
        )
        conn.close()
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df
    df["start_date"] = pd.to_datetime(df["start_date"], format="ISO8601")
    df["end_date"] = pd.to_datetime(df["end_date"], format="ISO8601")
    df["duree_s"] = (df["end_date"] - df["start_date"]).dt.total_seconds()
    return df


def taille_dossier_mo(path: Path) -> float:
    """Taille d'un dossier en Mo (proxy du coût de stockage)."""
    if not path.exists():
        return 0.0
    octets = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(octets / 1_048_576, 2)


def stats_base_postgres() -> dict | None:
    """Volumétrie de la table publications (None si base inaccessible)."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "checkit"),
            user=os.getenv("POSTGRES_USER", "etl_checkit"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
        )
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM publications;")
        total = cur.fetchone()[0]
        cur.execute("""SELECT source, count(*) FROM publications
                       GROUP BY source ORDER BY 2 DESC;""")
        par_source = dict(cur.fetchall())
        cur.execute("SELECT pg_total_relation_size('publications');")
        taille_mo = round(cur.fetchone()[0] / 1_048_576, 2)
        conn.close()
        return {"total": total, "par_source": par_source, "taille_mo": taille_mo}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
st.set_page_config(page_title="KPI Pipeline CheckIt.AI", page_icon="📊",
                   layout="wide")
st.title("📊 Pipeline de collecte CheckIt.AI — tableau de bord")
st.caption(f"Actualisé le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')} "
           "— pipeline planifié toutes les 6 heures")

# ===== 1. PRÉCISION ========================================================
st.header("1. Qualité des données")

nb_brut = compte_jsonl(RAW_JSONL)
nb_valide = compte_jsonl(CLEAN_JSONL)
pct_valide = round(100 * nb_valide / nb_brut, 1) if nb_brut else 0.0
alerte_qualite = nb_brut > 0 and pct_valide < SEUIL_VALIDITE_MIN

c1, c2, c3 = st.columns(3)
c1.metric("Publications collectées (brut)", nb_brut)
c2.metric("Publications valides (texte + image)", nb_valide)
c3.metric("Taux de validité", f"{pct_valide} %",
          delta=f"objectif ≥ {SEUIL_VALIDITE_MIN} %",
          delta_color="normal" if not alerte_qualite else "inverse")

if alerte_qualite:
    st.error(f"⚠️ Taux de validité sous le seuil de {SEUIL_VALIDITE_MIN} % : "
             "vérifier les causes de rejet ci-dessous et les logs.")
elif nb_brut == 0:
    st.info("Aucune donnée brute trouvée : lancez d'abord le pipeline "
            "(DAG etl_checkit_multimodal).")
else:
    st.success("✅ Qualité des données conforme à l'objectif.")

rejets = rejets_depuis_logs()
if sum(rejets.values()) > 0:
    st.subheader("Pourquoi des publications sont-elles écartées ?")
    st.bar_chart(pd.Series(rejets, name="Nombre de rejets"))

# ===== 2. RAPIDITÉ =========================================================
st.header("2. Rapidité d'exécution")

df_taches = durees_taches_airflow()
if df_taches.empty:
    st.info("Base Airflow introuvable : les durées s'afficheront après une "
            "exécution du DAG sur cette machine.")
else:
    derniers = df_taches.groupby("task_id").last()
    c1, c2, c3 = st.columns(3)
    noms = {"extract_publications": "Extraction",
            "transform_dataset": "Transformation",
            "load_to_postgres": "Chargement"}
    for col, (task, label) in zip((c1, c2, c3), noms.items()):
        if task in derniers.index:
            duree = derniers.loc[task, "duree_s"]
            col.metric(f"{label} (dernier run)", f"{duree:.1f} s")

    duree_extract = derniers.loc["extract_publications", "duree_s"] \
        if "extract_publications" in derniers.index else 0
    if duree_extract > SEUIL_DUREE_EXTRACT_MIN * 60:
        st.error(f"⚠️ Extraction anormalement longue "
                 f"(> {SEUIL_DUREE_EXTRACT_MIN} min) : source lente ou bloquée ?")

    st.subheader("Évolution des durées sur les derniers runs")
    pivot = df_taches.pivot_table(index="run_id", columns="task_id",
                                  values="duree_s", aggfunc="last")
    st.bar_chart(pivot.tail(10).rename(columns=noms))

    echecs = int((df_taches["state"] == "failed").sum())
    reussites = int((df_taches["state"] == "success").sum())
    st.caption(f"Historique : {reussites} tâche(s) en succès, "
               f"{echecs} en échec.")

# ===== 3. COÛT (RESSOURCES) ================================================
st.header("3. Coût et ressources")

stats_db = stats_base_postgres()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stockage images", f"{taille_dossier_mo(IMAGES_DIR)} Mo")
c2.metric("Stockage base de données",
          f"{stats_db['taille_mo']} Mo" if stats_db else "n/d")
c3.metric("Lignes en base", stats_db["total"] if stats_db else "n/d")
# 4 runs/jour x pages max x 1 appel : estimation du quota API consommé
c4.metric("Appels API / jour (max)", "12 / 200",
          help="4 exécutions par jour × 3 pages NewsData maximum ; "
               "le plan gratuit autorise 200 crédits/jour.")

if stats_db is None:
    st.info("Base PostgreSQL inaccessible : vérifier que le service est "
            "démarré et que le .env contient les identifiants.")

# ===== 4. CONTENU COLLECTÉ =================================================
st.header("4. Contenu du dataset")

df_clean = charge_dataset_clean()
if not df_clean.empty:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Répartition par source")
        st.bar_chart(df_clean["source"].value_counts())
    with c2:
        st.subheader("Principaux domaines")
        st.bar_chart(df_clean["domain"].value_counts().head(8))

    st.subheader("Aperçu des dernières publications")
    colonnes = ["published_at", "source", "domain", "title", "word_count"]
    st.dataframe(df_clean[colonnes].tail(10), width="stretch")
else:
    st.info("Dataset propre introuvable : exécuter le pipeline pour "
            "alimenter cette section.")

st.divider()
st.caption("Seuils et procédures d'alerte : voir docs/plan_monitoring.md")
