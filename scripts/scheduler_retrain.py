"""
Auto-Retrain Scheduler
Décide si modèle doit être réentraîné basé sur:
- Nombre de nouveaux matchs
- Performance dégradation
"""
import sys
from pathlib import Path
import pandas as pd
import sqlite3
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DATABASE_URL, MODELS_DIR
from src.logger import get_logger
from scripts.monitor_model import ModelMonitor

logger = get_logger(__name__)

class RetainScheduler:
    """Décide quand réentraîner le modèle"""
    
    # Configuration
    RETRAIN_AFTER_N_MATCHES = 200  # Retrain après 200 nouveaux matchs
    MIN_ACCURACY_THRESHOLD = 0.55   # Alerte si test_acc < 55%
    
    def __init__(self):
        self.monitor = ModelMonitor()
    
    def get_last_retrain_match_count(self):
        """Récupérer le nombre de matchs au dernier retrain"""
        df = pd.read_csv(self.monitor.tracking_file)
        if len(df) == 0:
            return 0
        
        latest = df.iloc[-1]
        return int(latest['num_matches'])
    
    def get_current_match_count(self):
        """Nombre total de matchs en base"""
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM matches")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def check_retrain_needed(self):
        """Vérifier si retrain est nécessaire"""
        
        logger.info("\n" + "=" * 80)
        logger.info("🔍 VÉRIFICATION RETRAIN")
        logger.info("=" * 80)
        
        last_count = self.get_last_retrain_match_count()
        current_count = self.get_current_match_count()
        new_matches = current_count - last_count
        
        logger.info(f"\n📊 Status:")
        logger.info(f"   Matchs au retrain: {last_count}")
        logger.info(f"   Matchs actuels: {current_count}")
        logger.info(f"   Nouveaux matchs: {new_matches}")
        logger.info(f"   Seuil retrain: {self.RETRAIN_AFTER_N_MATCHES}")
        
        # Vérifier performance
        latest_stats = self.monitor.get_latest_stats()
        if latest_stats:
            logger.info(f"\n📈 Dernière performance:")
            logger.info(f"   Version: {latest_stats['version']}")
            logger.info(f"   Test Accuracy: {latest_stats['test_acc']:.2%}")
            logger.info(f"   Seuil min: {self.MIN_ACCURACY_THRESHOLD:.0%}")
            
            if latest_stats['test_acc'] < self.MIN_ACCURACY_THRESHOLD:
                logger.warning(f"⚠️  Performance dégradée!")
                return True, "performance_degradation"
        
        # Vérifier nb matchs
        if new_matches >= self.RETRAIN_AFTER_N_MATCHES:
            logger.info(f"\n✅ Retrain recommandé: {new_matches} nouveaux matchs")
            return True, "new_matches_threshold"
        else:
            remaining = self.RETRAIN_AFTER_N_MATCHES - new_matches
            logger.info(f"\nℹ️  Pas encore retrain: {remaining} matchs avant seuil")
            return False, "no_retrain_needed"
    
    def print_schedule(self):
        """Afficher le planning de retrain"""
        current = self.get_current_match_count()
        next_retrain = current + (self.RETRAIN_AFTER_N_MATCHES - 
                                  (current - self.get_last_retrain_match_count()))
        
        logger.info(f"\n📅 Schedule:")
        logger.info(f"   Prochain retrain à: ~{next_retrain} matchs")
        logger.info(f"   Prochaine version: v1.2")

if __name__ == "__main__":
    scheduler = RetainScheduler()
    
    # Vérifier si retrain needed
    needs_retrain, reason = scheduler.check_retrain_needed()
    
    if needs_retrain:
        logger.warning(f"\n🔴 ACTION REQUISE: {reason}")
        logger.info("Exécute: python scripts/retrain_model.py")
    else:
        logger.info(f"\n✅ Modèle courant suffisant")
    
    # Afficher schedule
    scheduler.print_schedule()
