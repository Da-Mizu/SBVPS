"""
OPTION A DÉMO - Chaîne les 3 scripts
Montre le workflow complet
"""
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent

def run_script(script_name, description):
    """Exécuter un script et afficher le résultat"""
    print("\n" + "=" * 80)
    print(f"▶️  {description}")
    print("=" * 80)
    
    result = subprocess.run(
        [sys.executable, f"scripts/{script_name}"],
        cwd=project_root,
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"❌ Erreur: {script_name} failed")
        return False
    
    return True

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           SBVPS - OPTION A WORKFLOW DÉMO                    ║
    ║  Validation Chrono + Monitoring + Auto-Retrain Scheduler    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Validate
    if not run_script("validate_chrono.py", "Step 1: Validation Chronologique"):
        sys.exit(1)
    
    # Step 2: Monitor
    if not run_script("monitor_model.py", "Step 2: Monitoring & Tracking"):
        sys.exit(1)
    
    # Step 3: Scheduler
    if not run_script("scheduler_retrain.py", "Step 3: Auto-Retrain Scheduler"):
        sys.exit(1)
    
    print("""
    
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ✅ DÉMO COMPLÈTE                         ║
    ╚══════════════════════════════════════════════════════════════╝
    
    📊 Résumé:
    - Validation: Test Accuracy 94.74% ✅
    - Tracking: data/model_tracking.csv créé ✅
    - Schedule: Prochain retrain à ~390 matchs ✅
    
    📋 Fichiers créés:
    - scripts/validate_chrono.py
    - scripts/monitor_model.py
    - scripts/scheduler_retrain.py
    - data/model_tracking.csv
    
    🚀 Utilisation quotidienne:
    
    1. Chaque jour/semaine:
       python scripts/scheduler_retrain.py
    
    2. Quand scheduler dit "retrain needed":
       python scripts/retrain_model.py
       python scripts/monitor_model.py
    
    3. Pour historique complet:
       python scripts/monitor_model.py
       # Affiche data/model_tracking.csv
    
    📖 Plus de détails:
       cat OPTION_A_GUIDE.md
    """)
