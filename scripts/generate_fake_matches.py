"""
Script pour générer des données fictives et les stocker en base de données
"""
import argparse
import sys
from pathlib import Path

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.collector import FakeDataCollector
from src.data.storage import Database
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Générer des données fictives de matchs de football"
    )
    parser.add_argument(
        "--n", "--num-matches",
        type=int,
        default=380,
        help="Nombre de matchs à générer (défaut: 380)"
    )
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="Année de la saison (défaut: 2025)"
    )
    parser.add_argument(
        "--league",
        type=str,
        default="Ligue 1",
        choices=["Ligue 1", "Premier League", "La Liga", "Serie A"],
        help="Ligue à simuler (défaut: Ligue 1)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2025-08-01",
        help="Date de début de la saison (format: YYYY-MM-DD, défaut: 2025-08-01)"
    )
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Sauvegarder les données en base de données"
    )
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Vider la base avant d'insérer (développement)"
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 60)
        logger.info("🚀 GÉNÉRATEUR DE DONNÉES FICTIVES - SBVPS")
        logger.info("=" * 60)

        # Initialiser le collecteur
        collector = FakeDataCollector()

        # Générer les équipes
        logger.info(f"\n📋 Génération des équipes {args.league}...")
        teams = collector.generate_teams(league=args.league)

        # Générer les matchs
        logger.info(f"\n⚽ Génération de {args.n} matchs pour la saison {args.season}...")
        matches = collector.generate_matches(
            league=args.league,
            season=args.season,
            start_date=args.start_date,
            num_matches=args.n
        )

        # Générer les cotes
        logger.info(f"\n💰 Génération des cotes des bookmakers...")
        odds = collector.generate_odds(matches)

        # Afficher les stats
        logger.info(f"\n📊 RÉSUMÉ GÉNÉRÉ:")
        logger.info(f"   • Équipes: {len(teams)}")
        logger.info(f"   • Matchs: {len(matches)}")
        logger.info(f"   • Cotes (par bookmaker): {len(odds) // len(matches) * 4}")
        logger.info(f"   • Ligue: {args.league}")
        logger.info(f"   • Saison: {args.season}")
        logger.info(f"   • Période: {args.start_date} à ...")

        # Afficher un exemple
        logger.info(f"\n📌 EXEMPLE DE MATCH:")
        ex_match = matches[0]
        logger.info(f"   {ex_match['home_team']} {ex_match['home_goals']}-{ex_match['away_goals']} {ex_match['away_team']}")
        logger.info(f"   Date: {ex_match['match_date']} {ex_match['match_time']}")
        logger.info(f"   Résultat: {ex_match['result']}")

        ex_odds = [o for o in odds if o['match_id'] == 1][0]
        logger.info(f"\n📌 EXEMPLE DE COTES ({ex_odds['bookmaker']}):")
        logger.info(f"   Victoire domicile: {ex_odds['odd_1']:.2f}")
        logger.info(f"   Nul: {ex_odds['odd_x']:.2f}")
        logger.info(f"   Victoire extérieur: {ex_odds['odd_2']:.2f}")

        # Sauvegarder en base de données
        if args.save_db:
            logger.info(f"\n💾 Sauvegarde en base de données...")

            with Database() as db:
                # Créer les tables
                db.create_tables()

                # Optionnel: vider la base
                if args.clear_db:
                    logger.warning("   ⚠️ Suppression des données existantes...")
                    db.clear_all()

                # Insérer les données
                logger.info(f"   → Insertion des équipes...")
                db.insert_teams(teams)

                # Convertir les matchs au format DB
                matches_db = []
                for idx, match in enumerate(matches, 1):
                    home_team_id = db.get_team_id(match['home_team'])
                    away_team_id = db.get_team_id(match['away_team'])

                    matches_db.append({
                        'league': match['league'],
                        'season': match['season'],
                        'match_date': match['match_date'],
                        'home_team_id': home_team_id,
                        'away_team_id': away_team_id,
                        'home_goals': match['home_goals'],
                        'away_goals': match['away_goals'],
                        'result': match['result'],
                        'status': match['status']
                    })

                logger.info(f"   → Insertion des matchs...")
                db.insert_matches(matches_db)

                logger.info(f"   → Insertion des cotes...")
                db.insert_odds(odds)

                # Afficher les stats finales
                stats = db.get_stats()
                logger.info(f"\n✅ BASE DE DONNÉES:")
                logger.info(f"   • Équipes: {stats['teams_count']}")
                logger.info(f"   • Matchs: {stats['matches_count']}")
                logger.info(f"   • Matchs joués: {stats['matches_played']}")
                logger.info(f"   • Cotes: {stats['odds_count']}")
                logger.info(f"   • Localisation: database/sbvps.db")

        logger.info(f"\n" + "=" * 60)
        logger.info("✅ SUCCÈS ! Données générées et sauvegardées")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ ERREUR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
