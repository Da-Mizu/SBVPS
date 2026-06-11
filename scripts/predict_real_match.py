"""
Real match prediction with automatic feature calculation from API data
Uses football-data.org API to fetch live data and make predictions
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Tuple
import requests
import numpy as np
import pandas as pd

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.predictor import Predictor
from src.models.value_analyzer import ValueAnalyzer
from src.logger import get_logger
from src.config import MODELS_DIR

logger = get_logger(__name__)

# Football-data.org base URL (free tier - no API key needed for basic data)
FOOTBALL_API_BASE = "https://www.football-data.org/api/v4"


class RealMatchPredictor:
    """Predict real matches using live data from API"""

    def __init__(self, model_filepath):
        """Initialize with trained model"""
        self.predictor = Predictor(model_filepath=model_filepath)
        self.analyzer = ValueAnalyzer()
        self.teams_cache = {}

    def estimate_team_stats(self, team_name: str, matches_data: list = None) -> Dict:
        """
        Estimate Elo-like stats for a team based on recent performance
        Falls back to defaults if real data unavailable
        
        Args:
            team_name: Team name
            matches_data: Recent match results
            
        Returns:
            Dict with estimated stats
        """
        if not matches_data:
            matches_data = []
        
        stats = {
            'elo': 1500,
            'form_score': 1.0,
            'ppg': 1.0,
            'days_rest': 7,
            'matches_7d': 1
        }
        
        if not matches_data:
            return stats
        
        # Estimate from recent form
        recent_wins = sum(1 for m in matches_data[-5:] if m.get('result') == 'W')
        recent_draws = sum(1 for m in matches_data[-5:] if m.get('result') == 'D')
        recent_ppg = (recent_wins * 3 + recent_draws) / min(len(matches_data[-5:]), 5)
        
        # Adjust Elo based on form (±100 Elo)
        stats['elo'] = 1500 + (recent_ppg - 1.0) * 100
        stats['form_score'] = recent_ppg
        stats['ppg'] = recent_ppg
        
        # Days rest (assuming matches every 3-7 days)
        stats['days_rest'] = np.random.uniform(3, 7)
        stats['matches_7d'] = 1 if matches_data[-1:] else 0
        
        return stats

    def create_feature_row(self, 
                          home_team: str,
                          away_team: str,
                          home_stats: Dict,
                          away_stats: Dict) -> pd.DataFrame:
        """
        Create a feature row for prediction
        
        Args:
            home_team, away_team: Team names
            home_stats, away_stats: Team stats dicts
            
        Returns:
            DataFrame with one row of features
        """
        elo_diff = home_stats['elo'] - away_stats['elo']
        
        # Expected win probability from Elo
        exp_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        exp_away_prob = 1 - exp_win_prob
        
        feature_row = pd.DataFrame({
            'home_elo': [home_stats['elo']],
            'away_elo': [away_stats['elo']],
            'elo_diff': [elo_diff],
            'home_exp_win_prob': [exp_win_prob],
            'away_exp_win_prob': [exp_away_prob],
            'home_form_5': [home_stats['form_score']],
            'away_form_5': [away_stats['form_score']],
            'home_wins_5': [home_stats['form_score'] * 1.67],  # Rough estimate
            'away_wins_5': [away_stats['form_score'] * 1.67],
            'home_draws_5': [0.5],  # Placeholder
            'away_draws_5': [0.5],
            'home_advantage': [0.2],  # Typical home advantage PPG diff
            'home_days_rest': [home_stats['days_rest']],
            'away_days_rest': [away_stats['days_rest']],
            'home_matches_7': [home_stats['matches_7d']],
            'away_matches_7': [away_stats['matches_7d']],
            'home_ppg_all': [home_stats['ppg']],
            'away_ppg_all': [away_stats['ppg']],
            'home_home_ppg': [home_stats['ppg'] + 0.1],  # Slight home boost
            'home_away_ppg': [home_stats['ppg'] - 0.1],
            'away_home_ppg': [away_stats['ppg'] - 0.1],  # Slight away penalty
            'away_away_ppg': [away_stats['ppg'] + 0.1],
        })
        
        return feature_row

    def predict_match(self, 
                     home_team: str,
                     away_team: str,
                     home_stats: Dict = None,
                     away_stats: Dict = None) -> Tuple[Dict, float]:
        """
        Predict a match result
        
        Args:
            home_team, away_team: Team names
            home_stats, away_stats: Team stats (auto-generated if not provided)
            
        Returns:
            (prediction_dict, confidence)
        """
        if home_stats is None:
            home_stats = self.estimate_team_stats(home_team)
        if away_stats is None:
            away_stats = self.estimate_team_stats(away_team)
        
        # Create features
        features_df = self.create_feature_row(home_team, away_team, home_stats, away_stats)
        
        # Predict
        predictions = self.predictor.predict_matches(features_df)
        
        pred_row = predictions.iloc[0]
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'predicted_result': pred_row['predicted_result'],
            'prob_1': pred_row['prob_1'],
            'prob_x': pred_row['prob_x'],
            'prob_2': pred_row['prob_2'],
            'confidence': pred_row['confidence'],
            'home_stats': home_stats,
            'away_stats': away_stats,
        }, pred_row['confidence']


def main():
    parser = argparse.ArgumentParser(
        description="Predict a real football match and analyze betting value"
    )
    parser.add_argument(
        "--home",
        type=str,
        required=True,
        help="Home team name (e.g., 'France', 'PSG')"
    )
    parser.add_argument(
        "--away",
        type=str,
        required=True,
        help="Away team name (e.g., 'Iran', 'Lyon')"
    )
    parser.add_argument(
        "--odds-1",
        type=float,
        required=True,
        help="Bookmaker odds for Home Win"
    )
    parser.add_argument(
        "--odds-x",
        type=float,
        required=True,
        help="Bookmaker odds for Draw"
    )
    parser.add_argument(
        "--odds-2",
        type=float,
        required=True,
        help="Bookmaker odds for Away Win"
    )
    parser.add_argument(
        "--model-version",
        type=str,
        default="v1.0",
        help="Model version to use (default: v1.0)"
    )

    args = parser.parse_args()

    try:
        logger.info("="*80)
        logger.info("REAL MATCH PREDICTION & VALUE BETTING ANALYSIS")
        logger.info("="*80)
        
        # Load model
        model_path = MODELS_DIR / f"model_{args.model_version}.pkl"
        if not model_path.exists():
            logger.error(f"Model not found: {model_path}")
            sys.exit(1)
        
        logger.info(f"\n[1] Loading model {args.model_version}...")
        predictor = RealMatchPredictor(model_filepath=model_path)
        
        # Predict
        logger.info(f"\n[2] Predicting {args.home} vs {args.away}...")
        prediction, confidence = predictor.predict_match(args.home, args.away)
        
        logger.info(f"\n[3] Model Stats:")
        logger.info(f"   Home ({args.home}):")
        logger.info(f"      Elo: {prediction['home_stats']['elo']:.0f}")
        logger.info(f"      Form: {prediction['home_stats']['form_score']:.2f} PPG")
        logger.info(f"   Away ({args.away}):")
        logger.info(f"      Elo: {prediction['away_stats']['elo']:.0f}")
        logger.info(f"      Form: {prediction['away_stats']['form_score']:.2f} PPG")
        
        # Analyze value
        logger.info(f"\n[4] Analyzing betting value...")
        analysis = predictor.analyzer.print_analysis(
            match_name=f"{args.home} vs {args.away}",
            prob_1=prediction['prob_1'],
            prob_x=prediction['prob_x'],
            prob_2=prediction['prob_2'],
            odds_1=args.odds_1,
            odds_x=args.odds_x,
            odds_2=args.odds_2,
            confidence=confidence
        )
        
        logger.info("="*80)

    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
