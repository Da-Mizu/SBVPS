"""
Validation Chronologique - Train/Val/Test Split
Évite data leakage en respectant l'ordre temporel
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3
from sklearn.preprocessing import StandardScaler, LabelEncoder
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score
import pickle

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DATABASE_URL, MODELS_DIR
from src.logger import get_logger

logger = get_logger(__name__)

class ChronoValidator:
    """Validation respectant l'ordre chronologique des matchs"""
    
    def __init__(self, train_pct=0.6, val_pct=0.2):
        """
        Args:
            train_pct: % des matchs pour l'entraînement (0.6)
            val_pct: % des matchs pour validation (0.2)
            test_pct: % des matchs pour test (0.2) - calculé auto
        """
        self.train_pct = train_pct
        self.val_pct = val_pct
        self.test_pct = 1.0 - train_pct - val_pct
    
    def load_data(self):
        """Charger tous les matchs avec features"""
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        
        query = """
            SELECT m.match_id, m.result, f.* 
            FROM matches m
            JOIN features f ON m.match_id = f.match_id
            ORDER BY m.match_id
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        logger.info(f"📂 Chargé {len(df)} matchs")
        return df
    
    def split_chronologically(self, df):
        """Split respectant l'ordre temporel"""
        n = len(df)
        
        train_idx = int(n * self.train_pct)
        val_idx = int(n * (self.train_pct + self.val_pct))
        
        train_df = df.iloc[:train_idx]
        val_df = df.iloc[train_idx:val_idx]
        test_df = df.iloc[val_idx:]
        
        logger.info(f"\n📊 Split Chronologique:")
        logger.info(f"   Train: {len(train_df)} matchs ({self.train_pct:.0%})")
        logger.info(f"   Val:   {len(val_df)} matchs ({self.val_pct:.0%})")
        logger.info(f"   Test:  {len(test_df)} matchs ({self.test_pct:.0%})")
        
        return train_df, val_df, test_df
    
    def validate(self):
        """Valider le modèle sur split chrono"""
        logger.info("\n" + "=" * 80)
        logger.info("🔍 VALIDATION CHRONOLOGIQUE")
        logger.info("=" * 80)
        
        # Charger données
        df = self.load_data()
        train_df, val_df, test_df = self.split_chronologically(df)
        
        # Préparer X, y (exclure colonnes non-numériques)
        exclude_cols = ['match_id', 'result', 'feature_id', 'created_at', 'home_team_id', 'away_team_id', 'match_date']
        feature_cols = [col for col in df.columns 
                       if col not in exclude_cols and df[col].dtype in ['float64', 'int64']]
        
        X_train = train_df[feature_cols].values
        y_train = train_df['result'].iloc[:, 0].values if isinstance(train_df['result'], pd.DataFrame) else train_df['result'].values
        
        X_val = val_df[feature_cols].values
        y_val = val_df['result'].iloc[:, 0].values if isinstance(val_df['result'], pd.DataFrame) else val_df['result'].values
        
        X_test = test_df[feature_cols].values
        y_test = test_df['result'].iloc[:, 0].values if isinstance(test_df['result'], pd.DataFrame) else test_df['result'].values
        
        # Scaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        X_test_scaled = scaler.transform(X_test)
        
        # Encoder
        le = LabelEncoder()
        y_train_encoded = le.fit_transform(y_train)
        y_val_encoded = le.transform(y_val)
        y_test_encoded = le.transform(y_test)
        
        # Entraîner
        logger.info("\n🚀 Entraînement...")
        model = XGBClassifier(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X_train_scaled, y_train_encoded)
        
        # Scores
        train_score = model.score(X_train_scaled, y_train_encoded)
        val_score = model.score(X_val_scaled, y_val_encoded)
        test_score = model.score(X_test_scaled, y_test_encoded)
        
        logger.info(f"\n📈 Scores:")
        logger.info(f"   Train Accuracy: {train_score:.4f}")
        logger.info(f"   Val Accuracy:   {val_score:.4f}")
        logger.info(f"   Test Accuracy:  {test_score:.4f}")
        
        # Vérifier overfitting
        overfit = train_score - test_score
        if overfit > 0.10:
            logger.warning(f"⚠️  Possible overfitting: {overfit:.2%}")
        else:
            logger.info(f"✅ Pas d'overfitting évident: {overfit:.2%}")
        
        return {
            'train_score': train_score,
            'val_score': val_score,
            'test_score': test_score,
            'overfit': overfit,
        }

if __name__ == "__main__":
    validator = ChronoValidator(train_pct=0.6, val_pct=0.2)
    results = validator.validate()
