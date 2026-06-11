"""
Entraînement du modèle de Machine Learning pour SBVPS
Utilise XGBoost pour prédire les résultats (1, X, 2)
"""
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from xgboost import XGBClassifier
from src.logger import get_logger
from src.config import MODELS_DIR, MODEL_CONFIG

logger = get_logger(__name__)


class ModelTrainer:
    """Entraîne et valide le modèle XGBoost"""

    def __init__(self, model_version="v1.0"):
        """
        Initialize Model Trainer
        
        Args:
            model_version: Version du modèle
        """
        self.model_version = model_version
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = None
        self.feature_indices = None

    def prepare_data(self, features_df):
        """
        Prépare les données pour l'entraînement
        
        Args:
            features_df: DataFrame avec les features
            
        Returns:
            X (features), y (target encoded)
        """
        logger.info("Preparation des donnees...")
        
        # Sélectionner les features à utiliser (exclure identifiants et résultats)
        exclude_cols = ['match_id', 'home_team_id', 'away_team_id', 'match_date', 
                       'home_goals', 'away_goals', 'result', 'feature_id', 'created_at']
        
        feature_cols = [col for col in features_df.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        
        logger.info(f"  Features sélectionnés: {len(feature_cols)}")
        logger.info(f"  Features: {', '.join(feature_cols[:5])}...")
        
        # Préparer X et y
        X = features_df[feature_cols].copy()
        y = features_df['result'].copy()
        
        # Encoder les résultats (1 -> 0, X -> 1, 2 -> 2)
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Gérer les NaN (remplir avec la médiane)
        X_filled = X.fillna(X.median())
        
        logger.info(f"  X shape: {X_filled.shape}")
        logger.info(f"  y distribution: {np.bincount(y_encoded)}")
        logger.info(f"  y classes: {self.label_encoder.classes_}")
        
        # Scaler les features
        X_scaled = self.scaler.fit_transform(X_filled)
        
        return X_scaled, y_encoded, X_filled

    def train_model(self, X, y, cv_folds=5):
        """
        Entraîne le modèle XGBoost
        
        Args:
            X: Features (scaled)
            y: Target (encoded)
            cv_folds: Nombre de folds pour cross-validation
            
        Returns:
            Modèle entraîné + scores de CV
        """
        logger.info(f"\nEntraînement du modele XGBoost (v{self.model_version})...")
        
        # Créer le modèle
        self.model = XGBClassifier(
            n_estimators=MODEL_CONFIG['xgb_params']['n_estimators'],
            max_depth=MODEL_CONFIG['xgb_params']['max_depth'],
            learning_rate=MODEL_CONFIG['xgb_params']['learning_rate'],
            subsample=MODEL_CONFIG['xgb_params']['subsample'],
            colsample_bytree=MODEL_CONFIG['xgb_params']['colsample_bytree'],
            objective='multi:softprob',
            num_class=3,  # 3 classes: 1, X, 2
            random_state=MODEL_CONFIG['random_state'],
            verbosity=0
        )
        
        # Entraîner le modèle
        self.model.fit(X, y, verbose=False)
        
        logger.info("  Model entraîné sur 100% des données")
        
        # Cross-validation
        logger.info(f"\nCross-validation ({cv_folds}-fold)...")
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=MODEL_CONFIG['random_state'])
        cv_scores = cross_val_score(self.model, X, y, cv=cv, scoring='accuracy')
        
        logger.info(f"  CV Scores: {cv_scores}")
        logger.info(f"  CV Mean Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        return cv_scores

    def get_feature_importance(self, top_n=10):
        """
        Retourne l'importance des features
        
        Args:
            top_n: Nombre de top features à retourner
            
        Returns:
            DataFrame avec importances
        """
        if self.model is None:
            logger.warning("Model not trained yet")
            return None
        
        importances = self.model.feature_importances_
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return importance_df.head(top_n)

    def save_model(self, filename=None):
        """
        Sauvegarde le modèle en fichier
        
        Args:
            filename: Nom du fichier (défaut: model_{version}.pkl)
        """
        if self.model is None:
            logger.error("No model to save")
            return None
        
        if filename is None:
            filename = f"model_{self.model_version}.pkl"
        
        filepath = MODELS_DIR / filename
        
        # Créer un dict avec tous les éléments nécessaires
        model_dict = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'feature_names': self.feature_names,
            'model_version': self.model_version
        }
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(model_dict, f)
            logger.info(f"Model saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise

    @staticmethod
    def load_model(filepath):
        """
        Charge un modèle depuis un fichier
        
        Args:
            filepath: Chemin du fichier
            
        Returns:
            Dictionnaire avec model, scaler, encodeur
        """
        try:
            with open(filepath, 'rb') as f:
                model_dict = pickle.load(f)
            logger.info(f"Model loaded: {filepath}")
            return model_dict
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def predict(self, X_features):
        """
        Fait des prédictions sur de nouvelles données
        
        Args:
            X_features: DataFrame de features (raw, non-scaled)
            
        Returns:
            DataFrame avec prédictions
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None
        
        # Remplir les NaN
        X_filled = X_features.fillna(X_features.median())
        
        # Scaler
        X_scaled = self.scaler.transform(X_filled)
        
        # Prédictions
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        # Décoder les résultats
        predicted_results = self.label_encoder.inverse_transform(predictions)
        
        # Créer un DataFrame avec les résultats
        results_df = pd.DataFrame({
            'predicted_result': predicted_results,
            'confidence': np.max(probabilities, axis=1),
            'prob_1': probabilities[:, 0],      # Home win
            'prob_x': probabilities[:, 1],      # Draw
            'prob_2': probabilities[:, 2],      # Away win
        })
        
        return results_df
