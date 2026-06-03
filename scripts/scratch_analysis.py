import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from auto_market_ai.config import CLEAN_DATA_PATH, RAW_DATA_PATH
from auto_market_ai.data.schema import ML_FEATURES, TARGET
from auto_market_ai.ml.train import CATEGORICAL_FEATURES, NUMERIC_FEATURES, build_candidates

def evaluate_ensemble():
    print("Loading data...", flush=True)
    raw = pd.read_csv(RAW_DATA_PATH)
    
    from auto_market_ai.preprocessing.cleaning import clean_dataset
    print("Running initial cleaning...", flush=True)
    data = clean_dataset(raw)
    
    X = data.drop(columns=[TARGET])
    y = data[TARGET]
    
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=data["price_segment"]
    )
    
    print("Computing non-leaked market reference medians on train set...", flush=True)
    train_df = X_train_raw.copy()
    train_df["prix"] = y_train
    
    global_median = train_df["prix"].median()
    brand_model_median = train_df.groupby("brand_model")["prix"].median()
    brand_model_year_median = train_df.groupby(["brand_model", "annee"])["prix"].median()
    city_brand_median = train_df.groupby(["ville", "marque"])["prix"].median()
    
    def apply_medians(df):
        df = df.copy()
        df["brand_model_median_price"] = df["brand_model"].map(brand_model_median).fillna(global_median)
        df["brand_model_year_median_price"] = df.set_index(["brand_model", "annee"]).index.map(
            brand_model_year_median
        )
        df["brand_model_year_median_price"] = pd.Series(
            df["brand_model_year_median_price"], index=df.index
        ).fillna(df["brand_model_median_price"])
        
        df["city_brand_median_price"] = df.set_index(["ville", "marque"]).index.map(city_brand_median)
        df["city_brand_median_price"] = pd.Series(
            df["city_brand_median_price"], index=df.index
        ).fillna(global_median)
        return df

    print("Applying reference medians...", flush=True)
    X_train = apply_medians(X_train_raw)[ML_FEATURES]
    X_test = apply_medians(X_test_raw)[ML_FEATURES]
    
    candidates = build_candidates()
    boosting_candidates = {
        name: model for name, model in candidates.items() 
        if "lightgbm" in name or "xgboost" in name or "catboost" in name
    }
    
    predictions_dict = {}
    maes = {}
    
    for name, model in boosting_candidates.items():
        print(f"Training model: {name}...", flush=True)
        model.fit(X_train, y_train)
        preds = np.maximum(model.predict(X_test), 0)
        predictions_dict[name] = preds
        mae = np.mean(np.abs(y_test - preds))
        maes[name] = mae
        print(f"Model: {name:<20} | Test MAE: {mae:.2f} MAD", flush=True)
        
    # Let's test different ensembles
    # 1. Simple average of all three
    avg_preds = np.mean(list(predictions_dict.values()), axis=0)
    avg_mae = np.mean(np.abs(y_test - avg_preds))
    print(f"Ensemble (LGB + XGB + CatBoost)   | Test MAE: {avg_mae:.2f} MAD", flush=True)
    
    # 2. Weighted average: 0.5 * LightGBM + 0.3 * CatBoost + 0.2 * XGBoost
    weighted_preds = (
        0.5 * predictions_dict["lightgbm_log"] + 
        0.3 * predictions_dict["catboost_log"] + 
        0.2 * predictions_dict["xgboost_log"]
    )
    weighted_mae = np.mean(np.abs(y_test - weighted_preds))
    print(f"Weighted Ensemble (0.5/0.3/0.2)   | Test MAE: {weighted_mae:.2f} MAD", flush=True)

if __name__ == "__main__":
    evaluate_ensemble()
