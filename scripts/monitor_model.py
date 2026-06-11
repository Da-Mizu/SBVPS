"""
Model Monitoring - Tracker performance du modèle
Sauvegarde les stats à chaque retrain
"""
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import sqlite3

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DATABASE_URL
from src.logger import get_logger

logger = get_logger(__name__)

class ModelMonitor:
    """Track model performance over time"""
    
    def __init__(self):
        self.tracking_file = Path("data/model_tracking.csv")
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Créer le fichier de tracking s'il existe pas"""
        if not self.tracking_file.exists():
            self.tracking_file.parent.mkdir(exist_ok=True)
            
            # Header
            header = pd.DataFrame(columns=[
                'timestamp', 'model_version', 'train_accuracy', 
                'val_accuracy', 'test_accuracy', 'overfit_ratio',
                'num_matches', 'last_match_id', 'notes'
            ])
            header.to_csv(self.tracking_file, index=False)
            logger.info(f"✅ Fichier tracking créé: {self.tracking_file}")
    
    def log_retrain(self, model_version, train_acc, val_acc, test_acc, num_matches, notes=""):
        """Enregistrer une session d'entraînement"""
        
        # Charger existing
        df = pd.read_csv(self.tracking_file)
        
        # Calculer overfit
        overfit = train_acc - test_acc
        
        # Dernier match ID
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(match_id) FROM matches")
        last_match_id = cursor.fetchone()[0]
        conn.close()
        
        # Nouveau row
        new_row = pd.DataFrame({
            'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'model_version': [model_version],
            'train_accuracy': [f"{train_acc:.4f}"],
            'val_accuracy': [f"{val_acc:.4f}"],
            'test_accuracy': [f"{test_acc:.4f}"],
            'overfit_ratio': [f"{overfit:.4f}"],
            'num_matches': [num_matches],
            'last_match_id': [last_match_id],
            'notes': [notes],
        })
        
        # Append
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.tracking_file, index=False)
        
        logger.info(f"✅ Enregistré: {model_version} (Test Acc: {test_acc:.2%})")
    
    def get_latest_stats(self):
        """Récupérer les stats du dernier modèle"""
        df = pd.read_csv(self.tracking_file)
        if len(df) == 0:
            return None
        
        latest = df.iloc[-1]
        return {
            'version': latest['model_version'],
            'test_acc': float(latest['test_accuracy']),
            'num_matches': int(latest['num_matches']),
            'timestamp': latest['timestamp'],
        }
    
    def print_history(self, n=5):
        """Afficher historique des n derniers modèles"""
        df = pd.read_csv(self.tracking_file)
        
        if len(df) == 0:
            logger.info("Aucun historique")
            return
        
        logger.info(f"\n📊 Historique ({min(n, len(df))} derniers):")
        print(df.tail(n).to_string(index=False))

if __name__ == "__main__":
    monitor = ModelMonitor()
    
    # Test: enregistrer une session
    monitor.log_retrain(
        model_version="v1.1",
        train_acc=0.6234,
        val_acc=0.5847,
        test_acc=0.5812,
        num_matches=190,
        notes="Synthetic data training"
    )
    
    # Afficher historique
    monitor.print_history(n=10)
    
    # Stats actuels
    latest = monitor.get_latest_stats()
    if latest:
        logger.info(f"\n✅ Modèle courant: {latest['version']} ({latest['test_acc']:.2%})")
