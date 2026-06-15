"""
Script pour générer les données de la Coupe du Monde 2026
Récupère depuis l'API en priorité, utilise la BD comme fallback
"""
import sys
import argparse
import random
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.api_football_data import FootballDataAPIFetcher
from src.data.collector import FakeDataCollector
from src.data.storage import Database
from src.logger import get_logger

logger = get_logger(__name__)


def generate_world_cup_data(use_api=True, save_db=False):
    """
    Générer les données de la Coupe du Monde 2026
    
    Priorité: 
    1. API football-data.org (si disponible et use_api=True)
    2. Données fictives générées localement
    """
    
    logger.info("="*70)
    logger.info("🌍 GÉNÉRATEUR DE DONNÉES - COUPE DU MONDE 2026")
    logger.info("="*70)
    
    matches_df = None
    standings_df = None
    api_used = False
    
    # Étape 1: Essayer l'API
    if use_api:
        logger.info("\n[1] Tentative de récupération depuis l'API football-data.org...")
        fetcher = FootballDataAPIFetcher()
        
        if fetcher.api_is_available():
            matches_df = fetcher.get_world_cup_2026_matches()
            standings_df = fetcher.get_world_cup_standings()
            
            if matches_df is not None:
                api_used = True
                logger.info(f"✅ API utilisée avec succès!")
                logger.info(f"   → {len(matches_df)} matchs récupérés")
                if standings_df is not None:
                    logger.info(f"   → Classement: {len(standings_df)} équipes")
        else:
            logger.info("⚠️  API non disponible. Utilisation des données fictives...")
    
    # Étape 2: Fallback sur données fictives
    if matches_df is None:
        logger.info("\n[2] Génération de données fictives (fallback)...")
        
        collector = FakeDataCollector()
        
        # Générer équipes World Cup
        logger.info("   📋 Génération de 32 équipes pour la Coupe du Monde...")
        teams = collector.generate_world_cup_teams()
        logger.info(f"   ✅ {len(teams)} équipes générées")
        
        # Générer matchs
        logger.info("   ⚽ Génération des matchs de groupe (64 matchs)...")
        matches = collector.generate_world_cup_matches(teams)
        matches_df = collector.matches_to_dataframe(matches)
        logger.info(f"   ✅ {len(matches_df)} matchs générés")
        
        # Générer standings
        logger.info("   🏆 Génération du classement...")
        standings = []
        for rank, team in enumerate(teams[:32], 1):
            standings.append({
                "rank": rank,
                "team_name": team["name"],
                "team_id": team["id"],
                "played": 0,
                "won": 0,
                "draw": 0,
                "lost": 0,
                "points": 0,
                "goals_for": 0,
            })
        
        import pandas as pd
        standings_df = pd.DataFrame(standings)
        logger.info(f"   ✅ Classement généré")
    
    # Étape 3: Afficher résumé
    logger.info(f"\n📊 RÉSUMÉ GÉNÉRÉ:")
    logger.info(f"   • Source: {'API football-data.org' if api_used else 'Données fictives'}")
    logger.info(f"   • Équipes: {len(standings_df) if standings_df is not None else 'N/A'}")
    logger.info(f"   • Matchs: {len(matches_df)}")
    logger.info(f"   • Ligue: World Cup 2026")
    
    # Étape 4: Générer cotes
    logger.info(f"\n[3] Génération des cotes des bookmakers...")
    collector = FakeDataCollector()
    
    # Convertir matches_df en liste de dicts si nécessaire
    matches_list = matches_df.to_dict('records') if hasattr(matches_df, 'to_dict') else matches_df
    odds_list = collector.generate_odds(matches_list)
    logger.info(f"   ✅ {len(odds_list)} cotes générées")
    
    # Étape 5: Sauvegarder en BD (optionnel)
    if save_db:
        logger.info(f"\n[4] 💾 Sauvegarde en base de données...")
        
        with Database() as db:
            db.create_tables()
            
            # Insérer les équipes
            teams_for_db = []
            if standings_df is not None:
                for _, row in standings_df.iterrows():
                    teams_for_db.append({
                        "team_id": int(row["team_id"]) if row["team_id"] else None,
                        "name": row["team_name"],
                        "league": "World Cup 2026",
                        "country": row["team_name"],
                        "founded_year": random.randint(1880, 1950),
                        "elo": 1500,
                    })
            
            if teams_for_db:
                db.insert_teams(teams_for_db)
                logger.info(f"   → Insertion des équipes...")
            
            # Insérer les matchs
            logger.info(f"   → Insertion des matchs...")
            db.insert_matches(matches_df.to_dict('records'))
            
            # Insérer les cotes
            logger.info(f"   → Insertion des cotes...")
            db.insert_odds(odds_list)
        
        logger.info(f"\n✅ BASE DE DONNÉES:")
        logger.info(f"   • Équipes: {len(teams_for_db) if teams_for_db else 'N/A'}")
        logger.info(f"   • Matchs: {len(matches_df)}")
        logger.info(f"   • Cotes: {len(odds_list)}")
        logger.info(f"   • Localisation: database/sbvps.db")
    
    logger.info(f"\n{'='*70}")
    logger.info("✅ SUCCÈS ! Données World Cup générées")
    logger.info(f"{'='*70}\n")
    
    return matches_df, standings_df, odds_list if save_db else None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Générer les données de la Coupe du Monde 2026"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Ne pas utiliser l'API (données fictives uniquement)"
    )
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="Sauvegarder les données en base de données"
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Token API football-data.org"
    )
    
    args = parser.parse_args()
    
    try:
        matches_df, standings_df, _ = generate_world_cup_data(
            use_api=not args.no_api,
            save_db=args.save_db
        )
    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        sys.exit(1)
