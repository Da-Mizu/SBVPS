"""
Quick Start Guide - SBVPS
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("\n" + "=" * 70)
print("SBVPS - Sports Betting Value Prediction System")
print("=" * 70)
print("\n[1] INSTALLATION DES DÉPENDANCES")
print("    pip install -r requirements.txt")

print("\n[2] GÉNÉRER LES DONNÉES FICTIVES")
print("    python scripts/generate_fake_matches.py --n 380 --season 2025 --league 'Ligue 1' --save-db")

print("\n[3] VALIDER LES DONNÉES")
print("    python scripts/validate_data.py")

print("\n[4] (PROCHAINEMENT) FEATURE ENGINEERING")
print("    python scripts/engineer_features.py")

print("\n[5] (PROCHAINEMENT) ENTRAÎNER LE MODÈLE ML")
print("    python scripts/train_model.py")

print("\n[6] (PROCHAINEMENT) BACKTESTING")
print("    python scripts/run_backtest.py")

print("\n[7] (PROCHAINEMENT) LANCER LE DASHBOARD")
print("    streamlit run dashboard/streamlit_app.py")

print("\n" + "=" * 70)
print("Localisation des données:")
print(f"    Database: {project_root}/database/sbvps.db")
print(f"    Logs:     {project_root}/logs/sbvps.log")
print(f"    Models:   {project_root}/data/models/")
print("\n" + "=" * 70 + "\n")
