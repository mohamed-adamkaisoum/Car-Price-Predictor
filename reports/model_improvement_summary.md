# Auto Market AI - Model Improvement Summary

## Baseline sauvegardée

Le modèle précédent a été archivé dans :

- `models/archive/baseline_price_model_*.joblib`
- `reports/archive/baseline_price_model_metrics_*.json`

## Modèle amélioré

Le modèle actif est sauvegardé dans :

- `models/price_model.joblib`
- `reports/price_model_metrics.json`

Meilleur modèle sélectionné : `lightgbm_log`

Le modèle prédit `log(prix)` puis reconvertit en MAD. Cette approche réduit l'effet des prix extrêmes.

## Améliorations appliquées

- Nettoyage plus strict des annonces douteuses et outliers.
- Traitement séparé des véhicules premium/luxe.
- Features de finition : AMG, S-Line, R-Line, M Sport, GT Line, FR, HSE, etc.
- Flags d'origine : importée, dédouanée, WW Maroc.
- Équipements transformés en colonnes : ABS, airbags, climatisation, GPS, cuir, caméra, radar, jantes, Bluetooth.
- Scores enrichis : `equipment_score`, `luxury_score`, `premium_brand`, `is_luxury_vehicle`.
- Features marché : prix médian par marque/modèle, marque/modèle/année, ville/marque.
- Comparaison de modèles : Random Forest, Extra Trees, XGBoost, LightGBM, CatBoost.
- Évaluation par segment de prix.
- Prédiction API avec fourchette : basse, moyenne, haute.

## Résultats du meilleur modèle

- Lignes propres : 19 814
- MAE global : environ 16 601 MAD
- RMSE global : environ 45 183 MAD
- R2 global : environ 0.926

Segments :

- < 100k MAD : MAE environ 6 603 MAD
- 100k-250k MAD : MAE environ 11 095 MAD
- 250k-500k MAD : MAE environ 27 438 MAD
- > 500k MAD : MAE environ 130 996 MAD

## Note importante

Les features de prix médian marché rendent le modèle beaucoup plus performant pour analyser des annonces présentes dans un catalogue marché structuré. Pour une prédiction utilisateur totalement libre, l'API réutilise les tables de référence sauvegardées dans l'artefact modèle.
