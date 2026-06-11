"""
Script de validation et exploration des données en base de données
"""
import sys
from pathlib import Path

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage import Database


def main():
    print("=" * 70)
    print("DATA VALIDATION - SBVPS Database Explorer")
    print("=" * 70)
    
    try:
        with Database() as db:
            # Obtenir les stats
            stats = db.get_stats()
            
            print("\n[DATABASE STATISTICS]")
            print(f"  Teams:              {stats['teams_count']}")
            print(f"  Matches:            {stats['matches_count']}")
            print(f"  Matches Played:     {stats['matches_played']}")
            print(f"  Bookmaker Odds:     {stats['odds_count']}")
            print(f"  Predictions:        {stats['predictions_count']}")
            
            # Récupérer quelques matchs
            matches_df = db.get_matches(league="Ligue 1", season=2025)
            
            print(f"\n[FIRST 5 MATCHES]")
            print(f"  Loaded: {len(matches_df)} matches\n")
            
            for idx, row in matches_df.head(5).iterrows():
                print(f"  Match {idx + 1}:")
                print(f"    Date:    {row['match_date']}")
                print(f"    Home:    ID {row['home_team_id']} vs Away: ID {row['away_team_id']}")
                print(f"    Score:   {row['home_goals']}-{row['away_goals']}")
                print(f"    Result:  {row['result']}")
                print()
            
            # Statistiques de résultats
            print("[MATCH RESULTS DISTRIBUTION]")
            result_counts = matches_df['result'].value_counts()
            for result, count in result_counts.items():
                pct = (count / len(matches_df)) * 100
                label = "Home Win" if result == "1" else "Draw" if result == "X" else "Away Win"
                print(f"  {label:10} ({result}): {count:3d} matches ({pct:5.1f}%)")
            
            # Statistiques de buts
            print("\n[GOALS STATISTICS]")
            avg_home_goals = matches_df['home_goals'].mean()
            avg_away_goals = matches_df['away_goals'].mean()
            print(f"  Avg Home Goals:     {avg_home_goals:.2f}")
            print(f"  Avg Away Goals:     {avg_away_goals:.2f}")
            print(f"  Total Goals:        {matches_df['home_goals'].sum() + matches_df['away_goals'].sum()}")
            
            print("\n" + "=" * 70)
            print("SUCCESS - Database validation complete")
            print("=" * 70)
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
