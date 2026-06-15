"""
Script pour entraîner le modèle de Machine Learning
"""
import argparse
import sys
from pathlib import Path

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage import Database
from src.models.trainer import ModelTrainer
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Entraîner le modèle XGBoost pour prédire les résultats"
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
        "--version",
        type=str,
        default="v1.0",
        help="Version du modele (defaut: v1.0)"
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Nombre de folds pour cross-validation (defaut: 5)"
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 70)
        logger.info("ML TRAINING - SBVPS (XGBoost)")
        logger.info("=" * 70)

        with Database() as db:
            # Charger les features
            logger.info(f"\n[1] Chargement des features...")
            features_df = db.get_features(league=args.league, season=args.season)
            
            if len(features_df) == 0:
                logger.warning(f"Aucun feature trouve pour {args.league} {args.season}")
                sys.exit(1)
            
            logger.info(f"  Features charges: {len(features_df)} matchs")
            
            # Initialiser le trainer
            logger.info(f"\n[2] Initialisation du trainer (model {args.version})...")
            trainer = ModelTrainer(model_version=args.version)
            
            # Préparer les données
            logger.info(f"\n[3] Preparation des donnees...")
            X, y, X_raw = trainer.prepare_data(features_df)
            
            # Entraîner le modèle
            logger.info(f"\n[4] Entrainement du modele...")
            cv_scores = trainer.train_model(X, y, cv_folds=args.cv_folds)
            
            # Afficher l'importance des features
            logger.info(f"\n[5] Top 10 features par importance:")
            top_features = trainer.get_feature_importance(top_n=10)
            for idx, row in top_features.iterrows():
                logger.info(f"  {idx+1:2d}. {row['feature']:25s} : {row['importance']:.4f}")
            
            # Sauvegarder le modèle
            logger.info(f"\n[6] Sauvegarde du modele...")
            model_path = trainer.save_model()
            
            # Résumé
            logger.info(f"\n[7] RESUMÉ:")
            logger.info(f"  Modele:          {args.version}")
            logger.info(f"  Ligue:           {args.league}")
            logger.info(f"  Saison:          {args.season}")
            logger.info(f"  Matchs traites:  {len(features_df)}")
            logger.info(f"  Features:        {len(trainer.feature_names)}")
            logger.info(f"  CV Mean Acc:     {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            logger.info(f"  Model saved:     {model_path}")
            
            logger.info(f"\n" + "=" * 70)
            logger.info("SUCCESS - Modele entraîne et sauvegarde!")
            logger.info(f"Prochaine etape: python scripts/predict_matches.py --version {args.version}")
            logger.info("=" * 70)

    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
