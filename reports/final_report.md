# Rapport de projet — Auto Market AI

## Page de garde
- Titre : Auto Market AI
- Auteur : [Nom de l’étudiant]
- Enseignant : [Nom du professeur]
- Date : Juin 2026
- Filière : Data Science / Intelligence Artificielle

---

## 1. Résumé
Ce projet consiste à construire une plateforme d’intelligence automobile pour le marché de l’occasion au Maroc. L’objectif principal est de récupérer des annonces Avito, de nettoyer et préparer les données, de prédire le prix de marché et de proposer des analyses de deal ainsi que des recommandations de véhicules similaires.

---

## 2. Contexte et objectifs
- Contexte : marché automobile d’occasion au Maroc.
- Enjeux : aider acheteurs et vendeurs à évaluer correctement un prix, détecter les bonnes affaires et comparer les annonces.
- Objectifs :
  - Scraper les annonces Avito
  - Nettoyer et transformer les données
  - Entraîner un modèle de prédiction de prix
  - Développer une API backend
  - Créer un frontend interactif pour l’utilisateur

---

## 3. Technologies et outils
- Langage principal : Python
- Frontend : React + Vite + TypeScript
- Backend : FastAPI + Uvicorn
- Data science : pandas, scikit-learn, XGBoost, LightGBM, CatBoost, joblib
- Formats de données : CSV, JSON
- Package management : `requirements.txt`

---

## 4. Organisation du dépôt
Arborescence principale :
- `avito_scraper.py` : scraper Avito
- `README.md` : mode d’emploi et commandes
- `requirements.txt` : dépendances Python
- `data/` : données brutes et nettoyées
- `frontend/` : application web React
- `models/` : modèles entraînés
- `reports/` : métriques et rapports
- `scripts/` : préparation de données et entraînement
- `src/auto_market_ai/` : code backend et ML

---

## 5. Description des composants

### 5.1 Scraping
- `avito_scraper.py`
- Récupère des annonces Avito Maroc
- Enregistre les résultats en CSV et Excel dans `data/`

### 5.2 Préparation des données
- `scripts/prepare_data.py`
- Nettoyage des valeurs, gestion des formats et transformation des caractéristiques
- Sortie : `data/processed/avito_voitures_clean.csv`

### 5.3 Entraînement du modèle
- `scripts/train_price_model.py`
- Compare plusieurs algorithmes : RandomForest, ExtraTrees, XGBoost, LightGBM, CatBoost
- Sauvegarde le meilleur modèle dans `models/price_model.joblib`
- Génère les métriques dans `reports/price_model_metrics.json`

### 5.4 Backend
- `src/auto_market_ai/api/main.py`
- Endpoints :
  - `GET /health`
  - `GET /model-metrics`
  - `GET /catalog/facets`
  - `GET /market-signals`
  - `POST /predict`
  - `POST /deal-analysis`
  - `POST /recommendations`
  - `POST /search`

- Services :
  - `catalog.py` : facettes et signaux marché
  - `deal_finder.py` : classification des deals
  - `recommendation.py` : recommandations de voitures
  - `ml/predict.py` : prédictions de prix
  - `config.py` : chemins de fichiers et constantes
  - `preprocessing/` : nettoyage et pipeline

### 5.5 Frontend
- `frontend/src/App.tsx`
- Pages :
  - `HomePage` : page d’accueil
  - `SearchPage` : recherche par budget et filtres
  - `DealPage` : analyse d’annonce
  - `MarketPage` : signaux marché
- Composants réutilisables pour affichage et navigation

---

## 6. Méthodologie
1. Collecte des données par scraping
2. Inspection et nettoyage
3. Feature engineering
4. Entraînement et sélection du meilleur modèle
5. Déploiement API backend
6. Connexion frontend / backend
7. Tests fonctionnels et validation

---

## 7. Tests réalisés
### Backend
- Serveur démarré avec la commande :
  - `python -m uvicorn auto_market_ai.api.main:app --host 127.0.0.1 --port 8000`
- Commande exécutée avec `PYTHONPATH=src` pour permettre l’import du package.
- Vérification des endpoints :
  - `GET http://127.0.0.1:8000/health` => `{"status":"ok"}`
  - `GET http://127.0.0.1:8000/catalog/facets` => réponse JSON avec marques, villes, carburants, transmissions, prix, nombre d’annonces.

### Frontend
- Serveur frontend démarré avec :
  - `npm run dev -- --port 5173`
- Pages vérifiées :
  - `http://127.0.0.1:5173/` (Accueil)
  - `http://127.0.0.1:5173/recherche`
  - `http://127.0.0.1:5173/analyse`
  - `http://127.0.0.1:5173/marche`

### Captures d’écran
- Pages capturées pour le rapport :
  - Accueil
  - Recherche
  - Analyse de deal
  - Signaux marché

---

## 8. Résultats et validation
- Le backend est fonctionnel et expose les données nécessaires au frontend.
- Le frontend charge les pages et les interfaces attendues.
- Les tests montrent que l’application est opérationnelle dans sa configuration locale.

---

## 9. Points forts
- Architecture claire backend / frontend
- Pipeline ML complet et automatisé
- Interface web simple et orientée utilisateur
- Utilisation de données réelles du marché marocain

---

## 10. Limites et améliorations possibles
- Améliorer le scraping pour couvrir plus de pages et plus de champs
- Ajouter des tests automatisés pour l’API et le frontend
- Enrichir les signaux marché (graphique, tendance par marque)
- Ajouter un composant d’historique d’annonces

---

## 11. Conclusion
Ce projet montre une chaîne complète de création d’une application d’aide à la décision pour le marché de l’occasion. La solution couvre le scraping, le traitement de données, l’entraînement ML, la mise en service d’une API et une interface utilisateur. Le résultat est un prototype fonctionnel prêt à être présenté et amélioré.

---

## 12. Annexes
- Commandes d’installation :
  - `python -m pip install -r requirements.txt`
  - `cd frontend && npm install`
- Commandes d’exécution :
  - `python -m uvicorn auto_market_ai.api.main:app --host 127.0.0.1 --port 8000`
  - `cd frontend && npm run dev -- --port 5173`
- Captures d’écran des pages principales
- Endpoints API testés et résultats obtenus
