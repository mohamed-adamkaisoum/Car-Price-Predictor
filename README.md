# Auto Market AI

Plateforme d'intelligence automobile pour le marché de l'occasion :

- scraping Avito Maroc ;
- nettoyage et feature engineering ;
- prédiction du prix de marché ;
- analyse good deal / fair price / overpriced ;
- recommandations de voitures similaires.

## Installation

```powershell
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
```

## Scraping

```powershell
python avito_scraper.py --pages 1 --limit 5 --delay-min 1 --delay-max 2
```

Le résultat est sauvegardé en CSV et Excel dans `data/`.

## Pipeline ML

Préparer le dataset :

```powershell
python scripts/prepare_data.py --input data/avito_voitures_30000.csv
```

Entraîner le modèle baseline :

```powershell
python scripts/train_price_model.py
```

Le modèle actif compare plusieurs algorithmes (`RandomForest`, `ExtraTrees`, `XGBoost`,
`LightGBM`, `CatBoost`) et sauvegarde automatiquement le meilleur dans `models/price_model.joblib`.
Les métriques détaillées sont dans `reports/price_model_metrics.json`.

Lancer l'API :

```powershell
uvicorn auto_market_ai.api.main:app --reload
```

Lancer le frontend :

```powershell
cd frontend
npm install
npm run dev -- --port 5173
```

Puis ouvrir :

```text
http://127.0.0.1:5173
```

Endpoints :

- `GET /health`
- `GET /model-metrics`
- `GET /catalog/facets`
- `GET /market-signals`
- `POST /predict`
- `POST /deal-analysis`
- `POST /recommendations`
- `POST /search` (budget + filtres pour acheteurs)
