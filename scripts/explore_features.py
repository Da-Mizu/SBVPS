"""
Script pour explorer et analyser les features en base de données
"""
import sys
from pathlib import Path
import pandas as pd

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage import Database
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    print("=" * 80)
    print("FEATURES ANALYSIS & EXPLORATION - SBVPS")
    print("=" * 80)
    
    try:
        with Database() as db:
            # Charger les features
            features_df = db.get_features(league="Ligue 1", season=2025)
            
            if len(features_df) == 0:
                print("\nERROR: No features found!")
                sys.exit(1)
            
            print(f"\n[GENERAL INFO]")
            print(f"  Total Matches:  {len(features_df)}")
            print(f"  Total Features: {len(features_df.columns)}")
            print(f"  Date Range:     {features_df['match_date'].min()} to {features_df['match_date'].max()}")
            
            # Résultats
            print(f"\n[RESULTS DISTRIBUTION]")
            result_counts = features_df['result'].value_counts()
            for result, count in result_counts.items():
                pct = (count / len(features_df)) * 100
                label = "Home Win (1)" if result == "1" else "Draw (X)" if result == "X" else "Away Win (2)"
                print(f"  {label:20} : {count:3d} ({pct:5.1f}%)")
            
            # Elo Ratings
            print(f"\n[ELO RATINGS STATISTICS]")
            print(f"  Home Elo - Mean: {features_df['home_elo'].mean():.0f}, Std: {features_df['home_elo'].std():.0f}")
            print(f"            Min:  {features_df['home_elo'].min():.0f}, Max: {features_df['home_elo'].max():.0f}")
            print(f"  Away Elo - Mean: {features_df['away_elo'].mean():.0f}, Std: {features_df['away_elo'].std():.0f}")
            print(f"            Min:  {features_df['away_elo'].min():.0f}, Max: {features_df['away_elo'].max():.0f}")
            print(f"  Elo Diff - Mean: {features_df['elo_diff'].mean():.0f}, Std: {features_df['elo_diff'].std():.0f}")
            print(f"            Min:  {features_df['elo_diff'].min():.0f}, Max: {features_df['elo_diff'].max():.0f}")
            
            # Expected Win Probabilities
            print(f"\n[EXPECTED WIN PROBABILITIES]")
            print(f"  Home Exp Win - Mean: {features_df['home_exp_win_prob'].mean():.3f}")
            print(f"  Away Exp Win - Mean: {features_df['away_exp_win_prob'].mean():.3f}")
            
            # Form Scores
            print(f"\n[FORM SCORES (Last 5 Matches)]")
            print(f"  Home Form 5 - Mean: {features_df['home_form_5'].mean():.3f}, Std: {features_df['home_form_5'].std():.3f}")
            print(f"  Away Form 5 - Mean: {features_df['away_form_5'].mean():.3f}, Std: {features_df['away_form_5'].std():.3f}")
            print(f"  Home Wins 5 - Mean: {features_df['home_wins_5'].mean():.3f}")
            print(f"  Away Wins 5 - Mean: {features_df['away_wins_5'].mean():.3f}")
            
            # Home Advantage
            print(f"\n[HOME ADVANTAGE]")
            print(f"  Mean: {features_df['home_advantage'].mean():.3f}")
            print(f"  Std:  {features_df['home_advantage'].std():.3f}")
            print(f"  Min:  {features_df['home_advantage'].min():.3f}")
            print(f"  Max:  {features_df['home_advantage'].max():.3f}")
            
            # Rest & Fatigue
            print(f"\n[REST & FATIGUE]")
            print(f"  Home Days Rest - Mean: {features_df['home_days_rest'].mean():.1f}, Std: {features_df['home_days_rest'].std():.1f}")
            print(f"  Away Days Rest - Mean: {features_df['away_days_rest'].mean():.1f}, Std: {features_df['away_days_rest'].std():.1f}")
            print(f"  Home Matches 7d - Mean: {features_df['home_matches_7'].mean():.2f}")
            print(f"  Away Matches 7d - Mean: {features_df['away_matches_7'].mean():.2f}")
            
            # PPG (Points Per Game)
            print(f"\n[POINTS PER GAME (PPG)]")
            print(f"  Home PPG All - Mean: {features_df['home_ppg_all'].mean():.3f}, Std: {features_df['home_ppg_all'].std():.3f}")
            print(f"  Away PPG All - Mean: {features_df['away_ppg_all'].mean():.3f}, Std: {features_df['away_ppg_all'].std():.3f}")
            
            # Home/Away Split
            print(f"\n[HOME/AWAY PPG SPLIT]")
            print(f"  Home - At Home PPG: {features_df['home_home_ppg'].mean():.3f}")
            print(f"  Home - Away PPG:    {features_df['home_away_ppg'].mean():.3f}")
            print(f"  Away - At Home PPG: {features_df['away_home_ppg'].mean():.3f}")
            print(f"  Away - Away PPG:    {features_df['away_away_ppg'].mean():.3f}")
            
            # Buts
            print(f"\n[GOALS STATISTICS]")
            print(f"  Home Goals - Mean: {features_df['home_goals'].mean():.2f}, Std: {features_df['home_goals'].std():.2f}")
            print(f"  Away Goals - Mean: {features_df['away_goals'].mean():.2f}, Std: {features_df['away_goals'].std():.2f}")
            print(f"  Total Goals:       {features_df['home_goals'].sum() + features_df['away_goals'].sum()}")
            
            # Corrélations intéressantes
            print(f"\n[FEATURE CORRELATIONS WITH RESULT]")
            
            # Créer une colonne numérique pour le résultat
            features_df['result_num'] = features_df['result'].map({'1': 1, 'X': 0, '2': -1})
            
            correlations = {
                'home_elo': features_df[['home_elo', 'result_num']].corr().iloc[0, 1],
                'away_elo': features_df[['away_elo', 'result_num']].corr().iloc[0, 1],
                'elo_diff': features_df[['elo_diff', 'result_num']].corr().iloc[0, 1],
                'home_form_5': features_df[['home_form_5', 'result_num']].corr().iloc[0, 1],
                'away_form_5': features_df[['away_form_5', 'result_num']].corr().iloc[0, 1],
                'home_advantage': features_df[['home_advantage', 'result_num']].corr().iloc[0, 1],
                'home_days_rest': features_df[['home_days_rest', 'result_num']].corr().iloc[0, 1],
                'away_days_rest': features_df[['away_days_rest', 'result_num']].corr().iloc[0, 1],
                'home_ppg_all': features_df[['home_ppg_all', 'result_num']].corr().iloc[0, 1],
                'away_ppg_all': features_df[['away_ppg_all', 'result_num']].corr().iloc[0, 1],
            }
            
            # Trier par abs correlation
            sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
            for feature, corr in sorted_corr:
                sign = "+" if corr > 0 else ""
                print(f"  {feature:25} : {sign}{corr:.4f}")
            
            # Top 5 matches avec les plus hauts Elo diffs
            print(f"\n[TOP 5 MATCHES BY ELO DIFFERENCE]")
            top_elo = features_df.nlargest(5, 'elo_diff')[['match_date', 'home_team_id', 'away_team_id', 'elo_diff', 'home_goals', 'away_goals', 'result']]
            for idx, (_, row) in enumerate(top_elo.iterrows(), 1):
                print(f"  {idx}. Date: {row['match_date']} | Elo Diff: {row['elo_diff']:.0f} | Score: {row['home_goals']:.0f}-{row['away_goals']:.0f} ({row['result']})")
            
            # Matches avec plus de repos
            print(f"\n[MATCHES WITH MOST REST (HOME TEAM)]")
            max_rest = features_df.nlargest(5, 'home_days_rest')[['match_date', 'home_days_rest', 'away_days_rest', 'home_goals', 'away_goals', 'result']]
            for idx, (_, row) in enumerate(max_rest.iterrows(), 1):
                print(f"  {idx}. Date: {row['match_date']} | Home Rest: {row['home_days_rest']:.0f}d | Away Rest: {row['away_days_rest']:.0f}d | Result: {row['home_goals']:.0f}-{row['away_goals']:.0f} ({row['result']})")
            
            print(f"\n" + "=" * 80)
            print("EXPLORATION COMPLETE - Features are ready for ML training!")
            print("=" * 80)
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
