"""
Script pour calculer et stocker les features en base de données
"""
import argparse
import sys
from pathlib import Path

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage import Database
from src.features.engineer import FeatureEngineer
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Calculer et stocker les features pour le ML"
    )
    parser.add_argument(
        "--league",
        type=str,
        default="Ligue 1",
        choices=["Ligue 1", "Premier League", "La Liga", "Serie A", "World Cup"],
        help="Ligue a traiter (defaut: Ligue 1)"
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Annee de la saison (defaut: 2025)"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Effacer les features existantes avant de recalculer"
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 70)
        logger.info("FEATURE ENGINEERING - SBVPS")
        logger.info("=" * 70)

        with Database() as db:
            # Créer les tables (si elles n'existent pas)
            logger.info("\n[1] Creation de la table features...")
            db.create_tables()
            
            # Initialiser le Feature Engineer
            logger.info(f"\n[2] Initialisation du Feature Engineer...")
            engineer = FeatureEngineer(db)
            
            # Calculer tous les features
            logger.info(f"\n[3] Calcul des features pour {args.league} {args.season}...")
            features_df = engineer.calculate_all_features(
                league=args.league,
                season=args.season
            )
            
            if len(features_df) == 0:
                logger.warning(f"Aucun match trouve pour {args.league} {args.season}")
                sys.exit(1)
            
            # Afficher un aperçu
            logger.info(f"\n[4] Apercu des features calculees:")
            logger.info(f"    Nombre de matchs: {len(features_df)}")
            logger.info(f"    Nombre de colonnes: {len(features_df.columns)}")
            
            # Afficher les 3 premiers matchs
            logger.info(f"\n    Exemple - Match 1:")
            first_match = features_df.iloc[0]
            logger.info(f"      Match ID: {first_match['match_id']}")
            logger.info(f"      Date: {first_match['match_date']}")
            logger.info(f"      Elo: Home {first_match['home_elo']:.0f} vs Away {first_match['away_elo']:.0f}")
            logger.info(f"      Elo Diff: {first_match['elo_diff']:.0f}")
            logger.info(f"      Win Prob: Home {first_match['home_exp_win_prob']:.1%} vs Away {first_match['away_exp_win_prob']:.1%}")
            logger.info(f"      Form 5: Home {first_match['home_form_5']:.2f} vs Away {first_match['away_form_5']:.2f}")
            logger.info(f"      Rest: Home {first_match['home_days_rest']:.0f}j vs Away {first_match['away_days_rest']:.0f}j")
            logger.info(f"      PPG All: Home {first_match['home_ppg_all']:.2f} vs Away {first_match['away_ppg_all']:.2f}")
            logger.info(f"      Resultat: {first_match['home_goals']:.0f}-{first_match['away_goals']:.0f} ({first_match['result']})")
            
            # Sauvegarder en base de données
            logger.info(f"\n[5] Sauvegarde des features en BD...")
            db.insert_features(features_df)
            
            # Afficher les stats finales
            stats = db.get_stats()
            logger.info(f"\n[6] STATISTIQUES FINALES:")
            logger.info(f"    Teams:        {stats['teams_count']}")
            logger.info(f"    Matches:      {stats['matches_count']}")
            logger.info(f"    Odds:         {stats['odds_count']}")
            logger.info(f"    Features:     {stats['features_count']}")
            logger.info(f"    Predictions:  {stats['predictions_count']}")
            
            # Statistiques des features
            logger.info(f"\n[7] DISTRIBUTION DES FEATURES:")
            logger.info(f"    Elo Diff - Mean: {features_df['elo_diff'].mean():.0f}, Std: {features_df['elo_diff'].std():.0f}")
            logger.info(f"    Home Advantage - Mean: {features_df['home_advantage'].mean():.3f}, Min: {features_df['home_advantage'].min():.3f}, Max: {features_df['home_advantage'].max():.3f}")
            logger.info(f"    Home Form 5 - Mean: {features_df['home_form_5'].mean():.2f}")
            logger.info(f"    Away Form 5 - Mean: {features_df['away_form_5'].mean():.2f}")
            logger.info(f"    Days Rest (Home) - Mean: {features_df['home_days_rest'].mean():.1f}")
            logger.info(f"    Days Rest (Away) - Mean: {features_df['away_days_rest'].mean():.1f}")
            
            logger.info(f"\n" + "=" * 70)
            logger.info("SUCCESS - Features calcules et stockes")
            logger.info("=" * 70)

    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
