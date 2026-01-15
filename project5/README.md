Des relevés minutieux ont été effectués par les agents de la ville en 2016. Voici les données et leur source. Ces relevés sont coûteux à obtenir, et à partir de ceux déjà réalisés, vous voulez tenter de prédire les émissions de CO2 et la consommation totale d’énergie de bâtiments non destinés à l’habitation pour lesquels elles n’ont pas encore été mesurées.

 

Votre prédiction se basera sur les données structurelles des bâtiments (taille et usage des bâtiments, date de construction, situation géographique, ...).

 

Le Project Lead Douglas vous convie par message à une réunion de kick-off :

 

Comme tu le sais, ce genre de projet est mené en général par ta collègue Data Scientist Léa. Sauf qu’elle va partir en congé maternité à partir de la semaine prochaine. Ce projet a une très haute visibilité en ce moment auprès de la mairie de Seattle et nous ne pouvons pas attendre son retour pour commencer à travailler dessus. 

 

Afin de t’aider, je me suis coordonné avec Léa pour qu’elle te facilite le travail en te préparant un notebook avec un template de la démarche à suivre et des conseils pour éviter certains pièges. Dans l’ensemble, j’attends de toi :

une courte analyse exploratoire pour faire ressortir des insights clés sur les différents bâtiments ;
des tests des différents modèles supervisés visant à prédire la consommation en énergie des bâtiments ;
la détermination des facteurs principaux impactant le plus le modèle que tu auras sélectionné.

# Projet 5 – Mise en place d’un pipeline CI/CD pour un modèle de ML

## 1. Contexte du projet
Ce projet a pour objectif de mettre en place une infrastructure
d’intégration continue (CI) et de déploiement continu (CD) pour un
projet de machine learning.

---

## 2. Environnements

### Développement (dev)
- Environnement local (PyCharm)
- Utilisé pour l’exploration et l’entraînement
- Notebook Jupyter

### Test (ci)
- Environnement GitHub Actions
- Lancement automatique des tests à chaque push ou pull request
- Validation du code avant fusion

### Production (prod)
- Déploiement sur Hugging Face Spaces
- Modèle prêt à être utilisé via une interface ou une API

---

## 3. Pipeline CI/CD

Le pipeline CI/CD suit les étapes suivantes :

1. Push ou Pull Request sur le dépôt GitHub
2. Lancement automatique du pipeline CI via GitHub Actions
3. Installation des dépendances
4. Exécution des tests automatiques
5. Validation du code
6. (Optionnel) Déploiement du modèle en production

---

## 4. Tests automatisés

Les tests automatisés permettent de vérifier :
- Le chargement des données
- L’entraînement du modèle sur un échantillon réduit
- La capacité du modèle à produire des prédictions

Les tests sont exécutés automatiquement à chaque push et pull request.

---

## 5. Gestion des branches et validation

- La branche `main` est protégée
- Toute modification doit passer par une Pull Request
- La fusion est conditionnée au succès du pipeline CI

---

## 6. Gestion des secrets

Les secrets (tokens, clés API) sont stockés dans les GitHub Secrets.
Ils ne sont jamais présents en clair dans le code source.

---

## 7. Outils utilisés

- GitHub Actions pour la CI/CD
- Hugging Face Spaces pour le déploiement
- Python, scikit-learn, pandas

---

## 8. Limites et améliorations possibles

- Les tests n’incluent pas l’entraînement complet pour limiter
  le temps d’exécution
- Le pipeline peut être étendu avec des métriques avancées


Ton modèle ML
     ↓
Fonction Python (predict)
     ↓
Gradio (UI web)
     ↓
Hugging Face Space (serveur + URL)
