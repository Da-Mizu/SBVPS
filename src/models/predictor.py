"""
Prédictions avec le modèle entraîné
"""
import numpy as np
import pandas as pd
from src.logger import get_logger
from src.models.trainer import ModelTrainer
from src.config import MODELS_DIR

logger = get_logger(__name__)


class Predictor:
    """Utilise le modèle entraîné pour faire des prédictions"""

    def __init__(self, model_filepath=None):
        """
        Initialize Predictor
        
        Args:
            model_filepath: Chemin du modèle sauvegardé
        """
        self.model_dict = None
        self.trainer = None
        
        if model_filepath:
            self.load_model(model_filepath)

    def load_model(self, filepath):
        """
        Charge un modèle depuis un fichier
        
        Args:
            filepath: Chemin du fichier
        """
        try:
            self.model_dict = ModelTrainer.load_model(filepath)
            logger.info(f"Model loaded for prediction")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise

    def predict_matches(self, features_df):
        """
        Fait des prédictions pour une liste de matchs
        
        Args:
            features_df: DataFrame avec les features des matchs
            
        Returns:
            DataFrame avec les prédictions
        """
        if self.model_dict is None:
            logger.error("No model loaded")
            return None
        
        logger.info(f"Prediction pour {len(features_df)} matchs...")
        
        # Récupérer les éléments du modèle
        model = self.model_dict['model']
        scaler = self.model_dict['scaler']
        label_encoder = self.model_dict['label_encoder']
        feature_names = self.model_dict['feature_names']
        
        # Préparer les features
        X = features_df[feature_names].copy()
        X_filled = X.fillna(X.median())
        X_scaled = scaler.transform(X_filled)
        
        # Prédictions
        predictions = model.predict(X_scaled)
        probabilities = model.predict_proba(X_scaled)
        
        # Décoder
        predicted_results = label_encoder.inverse_transform(predictions)
        
        # Map classes to their indices (classes may not be in order 1, X, 2)
        class_to_idx = {cls: idx for idx, cls in enumerate(label_encoder.classes_)}
        idx_1 = class_to_idx.get('1', 0)
        idx_x = class_to_idx.get('X', 1)
        idx_2 = class_to_idx.get('2', 2)
        
        # Créer résultats (avec ou sans match_id)
        has_match_id = 'match_id' in features_df.columns
        
        if has_match_id:
            results_df = pd.DataFrame({
                'match_id': features_df['match_id'].values,
                'predicted_result': predicted_results,
                'confidence': np.max(probabilities, axis=1),
                'prob_1': probabilities[:, idx_1],
                'prob_x': probabilities[:, idx_x],
                'prob_2': probabilities[:, idx_2],
            })
        else:
            results_df = pd.DataFrame({
                'predicted_result': predicted_results,
                'confidence': np.max(probabilities, axis=1),
                'prob_1': probabilities[:, idx_1],
                'prob_x': probabilities[:, idx_x],
                'prob_2': probabilities[:, idx_2],
            })
        
        logger.info(f"  Prédictions générées")
        
        return results_df

    def check_value_bets(self, predictions_df, odds_df, min_value_threshold=1.05):
        """
        Identifie les paris "Value" (probabilité > cote attendue)
        
        Args:
            predictions_df: DataFrame avec prédictions
            odds_df: DataFrame avec les cotes des bookmakers
            min_value_threshold: Ratio minimum de value (défaut: 1.05 = +5%)
            
        Returns:
            DataFrame avec paris value identifiés
        """
        logger.info(f"\nIdentification des paris Value (threshold: {min_value_threshold}x)...")
        
        value_bets = []
        
        for _, pred in predictions_df.iterrows():
            match_id = pred['match_id']
            predicted_result = pred['predicted_result']
            prob = pred[f'prob_{predicted_result.lower() if predicted_result in ["X"] else "1" if predicted_result == "1" else "2"}']
            
            # Chercher les cotes pour ce match
            match_odds = odds_df[odds_df['match_id'] == match_id]
            
            if len(match_odds) > 0:
                # Prendre la meilleure cote (Pinnacle généralement)
                best_odd = None
                if predicted_result == '1':
                    best_odd = match_odds['odd_1'].max()
                elif predicted_result == 'X':
                    best_odd = match_odds['odd_x'].max()
                else:  # '2'
                    best_odd = match_odds['odd_2'].max()
                
                if best_odd:
                    # Cote attendue (1 / probabilité)
                    expected_odd = 1 / prob
                    
                    # Value ratio
                    value_ratio = best_odd / expected_odd
                    
                    if value_ratio >= min_value_threshold:
                        value_bets.append({
                            'match_id': match_id,
                            'predicted_result': predicted_result,
                            'probability': prob,
                            'best_odd': best_odd,
                            'expected_odd': expected_odd,
                            'value_ratio': value_ratio,
                            'value_pct': (value_ratio - 1) * 100
                        })
        
        value_df = pd.DataFrame(value_bets)
        
        if len(value_df) > 0:
            logger.info(f"  Value bets trouvés: {len(value_df)}")
            logger.info(f"  Value moyen: {value_df['value_pct'].mean():.1f}%")
        else:
            logger.info(f"  Aucun pari value trouvé")
        
        return value_df
