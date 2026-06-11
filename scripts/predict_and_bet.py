"""
Automated Match Prediction & Betting Value Analysis
Fetches team data automatically and recommends bets
"""
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.api_fetcher import FootballDataFetcher, create_interactive_match_predictor
from src.models.predictor import Predictor
from src.models.value_analyzer import ValueAnalyzer
from src.config import MODELS_DIR
from src.logger import get_logger

logger = get_logger(__name__)


class AutomatedMatchPredictor:
    """Automatically predict matches with API data + model"""

    def __init__(self, model_filepath):
        """Initialize predictor"""
        self.predictor = Predictor(model_filepath=model_filepath)
        self.analyzer = ValueAnalyzer()

    def create_feature_row(self, 
                          home_team: str,
                          away_team: str,
                          home_stats: dict,
                          away_stats: dict,
                          neutral_ground: bool = False) -> pd.DataFrame:
        """Create feature row from team stats"""
        
        elo_diff = home_stats['elo'] - away_stats['elo']
        exp_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # No home advantage on neutral ground (e.g., World Cup)
        home_advantage = 0.0 if neutral_ground else 0.2
        
        feature_row = pd.DataFrame({
            'home_elo': [home_stats['elo']],
            'away_elo': [away_stats['elo']],
            'elo_diff': [elo_diff],
            'home_exp_win_prob': [exp_win_prob],
            'away_exp_win_prob': [1 - exp_win_prob],
            'home_form_5': [home_stats['form_score']],
            'away_form_5': [away_stats['form_score']],
            'home_wins_5': [home_stats['form_score'] * 1.67],
            'away_wins_5': [away_stats['form_score'] * 1.67],
            'home_draws_5': [0.5],
            'away_draws_5': [0.5],
            'home_advantage': [home_advantage],
            'home_days_rest': [home_stats['days_rest']],
            'away_days_rest': [away_stats['days_rest']],
            'home_matches_7': [home_stats['matches_7d']],
            'away_matches_7': [away_stats['matches_7d']],
            'home_ppg_all': [home_stats['ppg']],
            'away_ppg_all': [away_stats['ppg']],
            'home_home_ppg': [home_stats['ppg'] + 0.1],
            'home_away_ppg': [home_stats['ppg'] - 0.1],
            'away_home_ppg': [away_stats['ppg'] - 0.1],
            'away_away_ppg': [away_stats['ppg'] + 0.1],
        })
        
        return feature_row

    def predict(self, 
               home_team: str,
               away_team: str,
               home_stats: dict,
               away_stats: dict,
               neutral_ground: bool = False) -> dict:
        """Predict match"""
        
        features_df = self.create_feature_row(home_team, away_team, home_stats, away_stats, neutral_ground)
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
        }

    def analyze_and_recommend(self,
                             prediction: dict,
                             odds_1: float,
                             odds_x: float,
                             odds_2: float):
        """Analyze value and make recommendation"""
        
        self.analyzer.print_analysis(
            match_name=f"{prediction['home_team']} vs {prediction['away_team']}",
            prob_1=prediction['prob_1'],
            prob_x=prediction['prob_x'],
            prob_2=prediction['prob_2'],
            odds_1=odds_1,
            odds_x=odds_x,
            odds_2=odds_2,
            confidence=prediction['confidence']
        )


def main():
    parser = argparse.ArgumentParser(
        description="Automated match prediction with value betting analysis"
    )
    parser.add_argument(
        "--home",
        type=str,
        help="Home team name"
    )
    parser.add_argument(
        "--away",
        type=str,
        help="Away team name"
    )
    parser.add_argument(
        "--odds-1",
        type=float,
        help="Odds for Home Win"
    )
    parser.add_argument(
        "--odds-x",
        type=float,
        help="Odds for Draw"
    )
    parser.add_argument(
        "--odds-2",
        type=float,
        help="Odds for Away Win"
    )
    parser.add_argument(
        "--model-version",
        type=str,
        default="v1.1",
        help="Model version to use"
    )
    parser.add_argument(
        "--neutral-ground",
        action="store_true",
        help="Match on neutral ground (e.g., World Cup)"
    )

    args = parser.parse_args()

    try:
        # Load model
        model_path = MODELS_DIR / f"model_{args.model_version}.pkl"
        if not model_path.exists():
            logger.error(f"Model not found: {model_path}")
            sys.exit(1)
        
        predictor = AutomatedMatchPredictor(model_filepath=model_path)
        
        # Get match info (interactive or command-line)
        if args.home and args.away and args.odds_1 and args.odds_x and args.odds_2:
            # Command-line mode
            match_info = {
                'home_name': args.home,
                'away_name': args.away,
                'home_stats': FootballDataFetcher.estimate_team_stats(args.home),
                'away_stats': FootballDataFetcher.estimate_team_stats(args.away),
                'odds_1': args.odds_1,
                'odds_x': args.odds_x,
                'odds_2': args.odds_2
            }
        else:
            # Interactive mode
            match_info = create_interactive_match_predictor()
            if not match_info:
                sys.exit(1)
        
        # Predict
        logger.info(f"\n[4] Predicting...")
        prediction = predictor.predict(
            home_team=match_info['home_name'],
            away_team=match_info['away_name'],
            home_stats=match_info['home_stats'],
            away_stats=match_info['away_stats'],
            neutral_ground=args.neutral_ground
        )
        
        logger.info(f"\n[5] Model Prediction:")
        logger.info(f"   {match_info['home_name']} Win (1): {prediction['prob_1']*100:.1f}%")
        logger.info(f"   Draw (X):     {prediction['prob_x']*100:.1f}%")
        logger.info(f"   {match_info['away_name']} Win (2): {prediction['prob_2']*100:.1f}%")
        logger.info(f"   Confidence: {prediction['confidence']*100:.1f}%")
        
        # Analyze value
        logger.info(f"\n[6] Analyzing betting value...")
        predictor.analyze_and_recommend(
            prediction=prediction,
            odds_1=match_info['odds_1'],
            odds_x=match_info['odds_x'],
            odds_2=match_info['odds_2']
        )
        
    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
