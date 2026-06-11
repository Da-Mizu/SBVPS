"""
Backtest simplifié - Diagnostic
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DATABASE_URL, MODELS_DIR
from src.logger import get_logger
from src.models.predictor import Predictor

logger = get_logger(__name__)

# Charger le modèle
logger.info("Loading model...")
model_path = MODELS_DIR / "model_v1.1.pkl"
predictor = Predictor(model_filepath=model_path)

# Charger les données
logger.info("Loading data...")
db_path = DATABASE_URL.replace("sqlite:///", "")
conn = sqlite3.connect(db_path)

query = """
    SELECT m.match_id, m.result, f.* 
    FROM matches m
    JOIN features f ON m.match_id = f.match_id
    LIMIT 10
"""

df = pd.read_sql_query(query, conn)
conn.close()

logger.info(f"Loaded {len(df)} matches")

# Prédictions
feature_cols = [col for col in df.columns 
               if col not in ['match_id', 'result', 'feature_id', 'created_at']]

X = df[feature_cols].copy()
logger.info(f"Features: {len(X.columns)} columns")

logger.info("Making predictions...")
predictions = predictor.predict_matches(X)

logger.info(f"Predictions shape: {predictions.shape}")
logger.info(f"\nFirst 5 predictions:\n{predictions.head()}")

logger.info(f"\nActual results: {df['result'].values[:5]}")
logger.info("✅ SUCCESS")
