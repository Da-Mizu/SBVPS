"""
Script pour générer les prédictions avec le modèle entraîné
"""
import argparse
import sys
from pathlib import Path

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage import Database
from src.models.predictor import Predictor
from src.config import MODELS_DIR
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generer les predictions avec le modele entraîne"
    )
    parser.add_argument(
        "--league",
        type=str,
        default="Ligue 1",
        choices=["Ligue 1", "Premier League", "La Liga", "Serie A"],
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
        "--save-db",
        action="store_true",
        help="Sauvegarder les predictions en BD"
    )

    args = parser.parse_args()

    try:
        logger.info("=" * 70)
        logger.info("PREDICTIONS - SBVPS")
        logger.info("=" * 70)

        # Charger le modèle
        logger.info(f"\n[1] Chargement du modele {args.version}...")
        model_path = MODELS_DIR / f"model_{args.version}.pkl"
        
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            logger.info(f"Please train the model first: python scripts/train_model.py --version {args.version}")
            sys.exit(1)
        
        predictor = Predictor(model_filepath=model_path)
        
        with Database() as db:
            # Charger les features
            logger.info(f"\n[2] Chargement des features...")
            features_df = db.get_features(league=args.league, season=args.season)
            
            if len(features_df) == 0:
                logger.warning(f"Aucun feature trouve pour {args.league} {args.season}")
                sys.exit(1)
            
            logger.info(f"  Features charges: {len(features_df)} matchs")
            
            # Faire les prédictions
            logger.info(f"\n[3] Generation des predictions...")
            predictions_df = predictor.predict_matches(features_df)
            
            # Afficher un aperçu
            logger.info(f"\n[4] Apercu des predictions:")
            logger.info(f"  Total predictions: {len(predictions_df)}")
            
            for result in ['1', 'X', '2']:
                count = len(predictions_df[predictions_df['predicted_result'] == result])
                pct = (count / len(predictions_df)) * 100
                label = "Home Win" if result == '1' else "Draw" if result == 'X' else "Away Win"
                logger.info(f"  {label:15} : {count:3d} ({pct:5.1f}%)")
            
            logger.info(f"\n  Confidence - Mean: {predictions_df['confidence'].mean():.3f}")
            logger.info(f"  Confidence - Min:  {predictions_df['confidence'].min():.3f}")
            logger.info(f"  Confidence - Max:  {predictions_df['confidence'].max():.3f}")
            
            # Afficher les top prédictions (plus confiantes)
            logger.info(f"\n[5] Top 5 predictions (par confidence):")
            top_preds = predictions_df.nlargest(5, 'confidence')[
                ['match_id', 'predicted_result', 'confidence', 'prob_1', 'prob_x', 'prob_2']
            ]
            for idx, (_, row) in enumerate(top_preds.iterrows(), 1):
                logger.info(f"  {idx}. Match {int(row['match_id']):3d} : {row['predicted_result']} " +
                           f"(conf: {row['confidence']:.1%}, prob: 1={row['prob_1']:.1%} X={row['prob_x']:.1%} 2={row['prob_2']:.1%})")
            
            # Sauvegarder en BD
            if args.save_db:
                logger.info(f"\n[6] Sauvegarde des predictions en BD...")
                db.insert_predictions(predictions_df, model_version=args.version)
                
                # Stats finales
                stats = db.get_stats()
                logger.info(f"\n[7] STATISTIQUES FINALES:")
                logger.info(f"  Teams:        {stats['teams_count']}")
                logger.info(f"  Matches:      {stats['matches_count']}")
                logger.info(f"  Features:     {stats['features_count']}")
                logger.info(f"  Predictions:  {stats['predictions_count']}")
            
            logger.info(f"\n" + "=" * 70)
            logger.info("SUCCESS - Predictions generees!")
            if not args.save_db:
                logger.info(f"Prochaine etape: ajouter --save-db pour sauvegarder en BD")
            logger.info("=" * 70)

    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
