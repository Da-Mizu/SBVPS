import pickle
import pandas as pd
from pathlib import Path

# Charger le modèle
model_path = Path("data/models/model_v1.0.pkl")
with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

model = model_data['model']
scaler = model_data['scaler']
le = model_data['label_encoder']
feature_names = model_data['feature_names']

print("=" * 80)
print("🔍 MODEL DIAGNOSTICS")
print("=" * 80)

print(f"\nModel Type: {type(model)}")
print(f"Number of features: {len(feature_names)}")
print(f"Feature names:\n{feature_names}")

# Feature importances
if hasattr(model, 'feature_importances_'):
    importances = model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print("\n📊 TOP 10 MOST IMPORTANT FEATURES:")
    print(feature_importance_df.head(10))
    
# Test avec données de test
print("\n" + "=" * 80)
print("🧪 TEST: France vs Cambodge")
print("=" * 80)

# Créer un row de test
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

print(f"\nInput features (raw):\n{test_features}")

# Scale
test_features_scaled = scaler.transform(test_features)
print(f"\nInput features (scaled):\n{pd.DataFrame(test_features_scaled, columns=feature_names)}")

# Prédire
raw_probs = model.predict_proba(test_features_scaled)
predictions = model.predict(test_features_scaled)

print(f"\nRaw probabilities:\n{raw_probs}")
print(f"\nClasses: {le.classes_}")
print(f"\nProbabilities for each class:")
for i, cls in enumerate(le.classes_):
    print(f"  {cls}: {raw_probs[0][i]:.1%}")

print(f"\nPredicted class: {predictions[0]}")
print(f"Predicted class name: {le.inverse_transform(predictions)[0]}")
