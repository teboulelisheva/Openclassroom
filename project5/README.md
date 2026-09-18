
# Prédiction de la consommation énergétique des bâtiments de Seattle

## Contexte du projet

Des relevés minutieux ont été effectués par les agents de la ville de Seattle en 2016 afin de mesurer la consommation énergétique et les émissions de CO₂ des bâtiments non résidentiels.

Ces relevés étant coûteux à obtenir, la ville souhaite désormais prédire ces informations pour les bâtiments qui n'ont pas encore été mesurés.

L'objectif est donc de développer un modèle de machine learning capable de prédire :

- la consommation totale d'énergie
- les émissions de CO₂

à partir de caractéristiques structurelles des bâtiments telles que :

- la surface
- l'année de construction
- le type d'utilisation
- la localisation
- les caractéristiques techniques du bâtiment

Ces prédictions permettront à la ville de mieux piloter sa politique énergétique et environnementale.

---

# Objectifs du projet

## 1. Analyse exploratoire des données

Réaliser une analyse exploratoire (EDA) afin de :

- comprendre la structure du dataset
- identifier les variables importantes
- détecter les valeurs aberrantes
- analyser les corrélations

---

## 2. Modélisation

Tester plusieurs modèles supervisés afin de prédire la consommation énergétique.

Modèles testés :

- Random Forest
- Régression linéaire
- Support Vector Regression

L'objectif est de sélectionner le modèle le plus performant.

---

## 3. Interprétabilité

Identifier les facteurs ayant le plus d'impact sur la prédiction, notamment :

- la surface du bâtiment
- le type d'utilisation
- l'année de construction
- l'intensité énergétique

---

# Architecture du projet

Dataset
↓
Notebook d’analyse
↓
Entraînement du modèle ML
↓
Fonction Python predict()
↓
API FastAPI
↓
Interface Gradio
↓
Déploiement Hugging Face Spaces

---

# Environnements du projet

## Développement (DEV)

Environnement local utilisé pour :

- l'analyse exploratoire
- l'entraînement des modèles
- l'expérimentation

Outils :

- Python
- Jupyter Notebook
- PyCharm
- Pandas
- Scikit-learn

---

## Intégration Continue (CI)

Un pipeline CI est configuré avec GitHub Actions.

À chaque push ou pull request :

1. installation des dépendances
2. exécution des tests
3. validation du code

---

## Production (PROD)

Le modèle est déployé sur Hugging Face Spaces afin de permettre l'utilisation du modèle via une interface web.

---

# Pipeline CI/CD

Le pipeline automatisé suit les étapes suivantes :

1. Push sur GitHub
2. Déclenchement du pipeline GitHub Actions
3. Installation des dépendances
4. Lancement des tests automatiques
5. Validation du code
6. Déploiement du modèle

---

# API de prédiction

Une API REST a été développée avec FastAPI.

## Endpoints

GET /health  
Vérifie que l'API fonctionne.

POST /predict  
Retourne une prédiction du modèle.

Les données sont validées avec Pydantic.

---

# Base de données et traçabilité

Une base PostgreSQL est utilisée afin d'enregistrer :

- les entrées envoyées au modèle
- les prédictions produites

Cela permet de garantir une traçabilité complète.

Schéma simplifié :

buildings
- id
- building_id
- primary_property
- gross_floor_area
- year_built
- site_energy_use

ml_inputs
- id
- timestamp
- feature1
- feature2

ml_predictions
- id
- input_id
- prediction
- timestamp

Relation :
ml_inputs.id → ml_predictions.input_id

---

# Interface utilisateur

Une interface web a été développée avec Gradio permettant :

- d'entrer les caractéristiques d’un bâtiment
- d'obtenir une prédiction instantanément

---

# Déploiement

Le projet est déployé sur Hugging Face Spaces.

Architecture :

Modèle ML  
↓  
Fonction predict()  
↓  
Gradio  
↓  
Hugging Face Space

---

# Tests et fiabilité

Une suite de tests a été développée avec Pytest.

## Tests unitaires

- chargement des données
- entraînement du modèle
- cohérence des prédictions
- validation des données

## Tests fonctionnels

- fonctionnement de l’API FastAPI
- intégration avec PostgreSQL
- enregistrement des prédictions

## Couverture de tests

La couverture est mesurée avec pytest-cov et un rapport HTML est généré.

---

# Technologies utilisées

- Python
- Pandas
- Scikit-learn
- FastAPI
- PostgreSQL
- Pytest
- GitHub Actions
- Gradio
- Hugging Face Spaces

---

# Améliorations possibles

- ajout de métriques supplémentaires
- monitoring du modèle
- automatisation complète du déploiement
- amélioration de l'interface utilisateur
