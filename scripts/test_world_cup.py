#!/usr/bin/env python3
"""
Test World Cup 2026 predictions with model probabilities
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import get_logger
from src.data.api_fetcher import FootballDataFetcher
from src.models.predictor import Predictor
from src.models.value_analyzer import ValueAnalyzer

logger = get_logger(__name__)

def create_feature_row(home_team: str, away_team: str, home_stats: dict, away_stats: dict) -> pd.DataFrame:
    """Create feature row from team stats"""
    
    elo_diff = home_stats['elo'] - away_stats['elo']
    exp_win_prob = 1 / (1 + 10 ** (-elo_diff / 400))
    
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
        'home_advantage': [0.0],  # World Cup = neutral ground (no home advantage)
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

# World Cup 2026 Group Stage Simulations
WORLD_CUP_MATCHES = [
    # Group A
    {'home': 'France', 'away': 'Angleterre', 'odds_1': 1.95, 'odds_x': 3.50, 'odds_2': 4.00},
    {'home': 'France', 'away': 'Allemagne', 'odds_1': 1.85, 'odds_x': 3.60, 'odds_2': 4.20},
    {'home': 'Allemagne', 'away': 'Angleterre', 'odds_1': 2.10, 'odds_x': 3.40, 'odds_2': 3.80},
    
    # Group B
    {'home': 'Brésil', 'away': 'Argentine', 'odds_1': 2.00, 'odds_x': 3.30, 'odds_2': 3.50},
    {'home': 'Brésil', 'away': 'Belgique', 'odds_1': 1.80, 'odds_x': 3.50, 'odds_2': 4.50},
    {'home': 'Argentine', 'away': 'Belgique', 'odds_1': 1.95, 'odds_x': 3.40, 'odds_2': 4.10},
    
    # Group C
    {'home': 'Espagne', 'away': 'Pays-Bas', 'odds_1': 2.05, 'odds_x': 3.50, 'odds_2': 3.70},
    {'home': 'Espagne', 'away': 'Portugal', 'odds_1': 1.90, 'odds_x': 3.60, 'odds_2': 4.00},
    {'home': 'Pays-Bas', 'away': 'Portugal', 'odds_1': 2.25, 'odds_x': 3.40, 'odds_2': 3.30},
    
    # Group D
    {'home': 'Uruguay', 'away': 'Pologne', 'odds_1': 1.75, 'odds_x': 3.60, 'odds_2': 4.80},
    {'home': 'Uruguay', 'away': 'Mexique', 'odds_1': 1.70, 'odds_x': 3.70, 'odds_2': 5.00},
    {'home': 'Pologne', 'away': 'Mexique', 'odds_1': 2.30, 'odds_x': 3.30, 'odds_2': 3.10},
    
    # KO Stage
    {'home': 'France', 'away': 'Brésil', 'odds_1': 2.35, 'odds_x': 3.50, 'odds_2': 3.00},
    {'home': 'Allemagne', 'away': 'Espagne', 'odds_1': 2.45, 'odds_x': 3.40, 'odds_2': 2.90},
]

def test_world_cup_predictions(model_version: str = 'v1.0'):
    """Test model predictions on World Cup matches"""
    
    logger.info("🏆 WORLD CUP 2026 PREDICTIONS 🏆")
    logger.info("=" * 80)
    
    # Load model
    predictor = Predictor()
    predictor.load_model(f'data/models/model_{model_version}.pkl')
    
    fetcher = FootballDataFetcher()
    analyzer = ValueAnalyzer()
    
    results = []
    
    for i, match in enumerate(WORLD_CUP_MATCHES, 1):
        logger.info(f"\n[Match {i:2d}] {match['home']} vs {match['away']}")
        logger.info("-" * 80)
        
        try:
            # Get team stats
            home_stats = fetcher.estimate_team_stats(match['home'])
            away_stats = fetcher.estimate_team_stats(match['away'])
            
            # Create feature row
            feature_row = create_feature_row(
                match['home'], match['away'],
                home_stats, away_stats
            )
            
            # Predict
            predictions = predictor.predict_matches(feature_row)
            
            if predictions is not None and len(predictions) > 0:
                pred = predictions.iloc[0]
                
                # Log predictions
                logger.info(f"  Model Probabilities:")
                logger.info(f"    {match['home']} (1): {pred['prob_1']*100:.1f}%")
                logger.info(f"    Draw (X):      {pred['prob_x']*100:.1f}%")
                logger.info(f"    {match['away']} (2): {pred['prob_2']*100:.1f}%")
                logger.info(f"    Confidence: {pred['confidence']*100:.1f}%")
                
                # Analyze value
                ev_1 = analyzer.calculate_expected_value(pred['prob_1'], match['odds_1'])
                ev_x = analyzer.calculate_expected_value(pred['prob_x'], match['odds_x'])
                ev_2 = analyzer.calculate_expected_value(pred['prob_2'], match['odds_2'])
                
                # Find best value
                best_ev = max(
                    ('1', ev_1['ev_pct']) if ev_1['is_value'] else ('1', -999),
                    ('X', ev_x['ev_pct']) if ev_x['is_value'] else ('X', -999),
                    ('2', ev_2['ev_pct']) if ev_2['is_value'] else ('2', -999),
                    key=lambda x: x[1]
                )
                
                if best_ev[1] > -999:
                    logger.info(f"  💡 VALUE: {best_ev[0]} @ {best_ev[1]:+.1f}% EV")
                else:
                    logger.info(f"  ❌ NO VALUE")
                
                results.append({
                    'match': f"{match['home']} vs {match['away']}",
                    'prob_1': pred['prob_1'],
                    'prob_x': pred['prob_x'],
                    'prob_2': pred['prob_2'],
                    'confidence': pred['confidence'],
                    'best_value': best_ev[0],
                    'ev_pct': best_ev[1] if best_ev[1] > -999 else 0
                })
            
        except Exception as e:
            logger.error(f"  Error: {e}")
            continue
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 SUMMARY")
    logger.info("=" * 80)
    
    df_results = pd.DataFrame(results)
    
    if len(df_results) > 0:
        # Value opportunities
        value_opportunities = df_results[df_results['ev_pct'] > 0]
        if len(value_opportunities) > 0:
            logger.info(f"\n✅ Found {len(value_opportunities)} value opportunities:")
            for _, row in value_opportunities.iterrows():
                logger.info(f"   {row['match']}: {row['best_value']} @ {row['ev_pct']:+.1f}%")
        else:
            logger.info("\n❌ No value opportunities found in these odds")
        
        # Model stats
        logger.info(f"\n📈 Model Statistics:")
        logger.info(f"   Average Confidence: {df_results['confidence'].mean()*100:.1f}%")
        logger.info(f"   Matches Analyzed: {len(df_results)}")
    
    logger.info("\n" + "=" * 80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-version', default='v1.0', help='Model version to use')
    args = parser.parse_args()
    
    test_world_cup_predictions(args.model_version)
