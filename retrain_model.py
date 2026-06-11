"""
Générer un dataset d'entraînement COHÉRENT et réentraîner le modèle
Où Elo_diff → Résultat en relations claires
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold
import pickle

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import MODELS_DIR
from src.logger import get_logger

logger = get_logger(__name__)

# Générer un VRAI dataset cohérent
logger.info("🎲 Générant un dataset cohérent...")

np.random.seed(42)
n_samples = 1000

# Générer les Elo
home_elo = np.random.normal(1550, 150, n_samples)
away_elo = np.random.normal(1550, 150, n_samples)

# Limiter entre 1200 et 1900
home_elo = np.clip(home_elo, 1200, 1900)
away_elo = np.clip(away_elo, 1200, 1900)

# Elo diff et prob Elo
elo_diff = home_elo - away_elo
home_exp_win = 1 / (1 + 10 ** (-elo_diff / 400))
away_exp_win = 1 - home_exp_win

# Générer les résultats en fonction de Elo + hasard
results = []
for hw, aw in zip(home_exp_win, away_exp_win):
    # Draw plus rare
    rand = np.random.random()
    if rand < hw * 0.85:
        results.append('1')  # Home win (85% du home_exp)
    elif rand < (hw * 0.85 + aw * 0.85):
        results.append('2')  # Away win (85% du away_exp)
    else:
        results.append('X')  # Draw (30% + reste)

# Créer les autres features (fixes pour test)
data = pd.DataFrame({
    'home_elo': home_elo,
    'away_elo': away_elo,
    'elo_diff': elo_diff,
    'home_exp_win_prob': home_exp_win,
    'away_exp_win_prob': away_exp_win,
    'home_form_5': np.random.normal(1.4, 0.3, n_samples),
    'away_form_5': np.random.normal(1.4, 0.3, n_samples),
    'home_wins_5': np.random.normal(2.3, 1.0, n_samples),
    'away_wins_5': np.random.normal(2.3, 1.0, n_samples),
    'home_draws_5': np.random.normal(0.5, 0.3, n_samples),
    'away_draws_5': np.random.normal(0.5, 0.3, n_samples),
    'home_advantage': np.random.normal(0.2, 0.1, n_samples),
    'home_days_rest': np.random.normal(5.0, 2.0, n_samples),
    'away_days_rest': np.random.normal(5.0, 2.0, n_samples),
    'home_matches_7': np.random.normal(0.5, 0.5, n_samples),
    'away_matches_7': np.random.normal(0.5, 0.5, n_samples),
    'home_ppg_all': np.random.normal(1.5, 0.4, n_samples),
    'away_ppg_all': np.random.normal(1.5, 0.4, n_samples),
    'home_home_ppg': np.random.normal(1.6, 0.4, n_samples),
    'home_away_ppg': np.random.normal(1.4, 0.4, n_samples),
    'away_home_ppg': np.random.normal(1.4, 0.4, n_samples),
    'away_away_ppg': np.random.normal(1.6, 0.4, n_samples),
    'result': results,
})

logger.info(f"Dataset shape: {data.shape}")
logger.info(f"Result distribution:\n{data['result'].value_counts()}")

# Préparer les données
X = data.drop('result', axis=1)
y = data['result']

feature_names = list(X.columns)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

le = LabelEncoder()
y_encoded = le.fit_transform(y)

logger.info(f"Classes: {le.classes_}")

# Entraîner avec config OPTIMISÉE
logger.info("\n🚀 Entraînement du modèle...")

model = XGBClassifier(
    n_estimators=300,      # Plus d'estimateurs
    max_depth=7,           # Profondeur modérée
    learning_rate=0.05,    # Learning rate plus faible
    subsample=0.9,
    colsample_bytree=0.9,
    min_child_weight=2,
    random_state=42,
    objective='multi:softprob',
    eval_metric='mlogloss',
    verbosity=0
)

# Validation croisée
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = []

for fold, (train_idx, val_idx) in enumerate(cv.split(X_scaled, y_encoded), 1):
    X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
    y_train, y_val = y_encoded[train_idx], y_encoded[val_idx]
    
    model.fit(X_train, y_train, verbose=0)
    score = model.score(X_val, y_val)
    cv_scores.append(score)
    logger.info(f"   Fold {fold}: {score:.4f}")

logger.info(f"   CV Mean: {np.mean(cv_scores):.4f} ± {np.std(cv_scores):.4f}")

# Réentraîner sur toutes les données
model.fit(X_scaled, y_encoded)

# Feature importances
importances = model.feature_importances_
feature_importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': importances
}).sort_values('importance', ascending=False)

logger.info("\n📊 TOP 10 FEATURES:")
print(feature_importance_df.head(10).to_string())

# Sauvegarder
model_dict = {
    'model': model,
    'scaler': scaler,
    'label_encoder': le,
    'feature_names': feature_names,
}

model_path = MODELS_DIR / "model_v1.1.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(model_dict, f)

logger.info(f"\n✅ Modèle sauvegardé: {model_path}")

# TEST: France vs Cambodge
logger.info("\n" + "=" * 80)
logger.info("🧪 TEST: France (1705) vs Cambodge (1500)")
logger.info("=" * 80)

test_features = pd.DataFrame({
    'home_elo': [1705],
    'away_elo': [1500],
    'elo_diff': [205],
    'home_exp_win_prob': [0.765],
    'away_exp_win_prob': [0.235],
    'home_form_5': [1.4],
    'away_form_5': [1.4],
    'home_wins_5': [2.33],
    'away_wins_5': [2.33],
    'home_draws_5': [0.5],
    'away_draws_5': [0.5],
    'home_advantage': [0.0],
    'home_days_rest': [5.0],
    'away_days_rest': [5.0],
    'home_matches_7': [0.0],
    'away_matches_7': [0.0],
    'home_ppg_all': [1.5],
    'away_ppg_all': [1.5],
    'home_home_ppg': [1.6],
    'home_away_ppg': [1.4],
    'away_home_ppg': [1.4],
    'away_away_ppg': [1.6],
})

test_features_scaled = scaler.transform(test_features)
probs = model.predict_proba(test_features_scaled)

# Map classes
class_to_idx = {cls: idx for idx, cls in enumerate(le.classes_)}
idx_1 = class_to_idx.get('1', 0)
idx_x = class_to_idx.get('X', 1)
idx_2 = class_to_idx.get('2', 2)

logger.info(f"\nClasses: {le.classes_}")
logger.info(f"France (Home): {probs[0][idx_1]:.1%} ✅")
logger.info(f"Draw (X): {probs[0][idx_x]:.1%}")
logger.info(f"Cambodge (Away): {probs[0][idx_2]:.1%}")

if probs[0][idx_1] > 0.6:
    logger.info("\n✅ RÉSULTAT CORRECT: France favorisée!")
else:
    logger.error("\n❌ RÉSULTAT MAUVAIS: France pas assez favorisée")
