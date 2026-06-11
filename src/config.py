"""
Configuration centralisée du projet SBVPS
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemins principaux
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = PROJECT_ROOT / "database"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MODELS_DIR = DATA_DIR / "models"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Créer les répertoires s'ils n'existent pas
for path in [DATA_DIR, DATABASE_DIR, MODELS_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/sbvps.db")
DB_PATH = DATABASE_DIR / "sbvps.db"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = PROJECT_ROOT / "logs" / "sbvps.log"

# Football-Data.org API
FOOTBALL_DATA_API_TOKEN = os.getenv("FOOTBALL_DATA_API_TOKEN", "")

# Données fictives (générateur)
FAKE_DATA_CONFIG = {
    "default_league": "Ligue 1",
    "default_season": 2025,
    "teams_per_league": 20,
    "matches_per_season": 380,  # 20 teams * 19 * 2 matchs
    "default_start_date": "2025-08-01",
}

# Feature Engineering
ELO_CONFIG = {
    "initial_elo": 1500,
    "k_factor": 32,
    "home_advantage": 100,
}

HOME_ADVANTAGE_PPG = 0.4  # Points par match en plus

# Modèle ML
MODEL_CONFIG = {
    "test_size": 0.2,
    "random_state": 42,
    "xgb_params": {
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 100,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
    },
}

# Backtesting
BACKTEST_CONFIG = {
    "min_odds": 1.5,  # Cotes minimales pour placer un pari
    "max_odds": 10.0,  # Cotes maximales
    "min_value_threshold": 1.05,  # +5% de value minimum
    "kelly_fraction": 0.25,  # Kelly criterion (fraction conservative)
}

# API
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": True,
}

# Streamlit
STREAMLIT_CONFIG = {
    "page_title": "SBVPS - Sports Betting Value Prediction",
    "layout": "wide",
}
