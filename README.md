# SBVPS - Sports Betting Value Prediction System

Système de prédiction de résultats de paris sportifs basé sur le "Value Betting".

## 🎯 Objectif

Créer un système modulaire Python capable de :
- Ingérer des données (matchs, cotes, historiques)
- Calculer des indicateurs (features : ELO, forme, fatigue, etc.)
- Entraîner un modèle prédictif (probabilités victoire/nul/défaite)
- Backtester contre les cotes historiques
- Identifier les opportunités "Value" sur un dashboard

## 🛠 Stack Technique

- **Langage** : Python 3.11+
- **Data/ML** : Pandas, NumPy, Scikit-Learn, XGBoost, LightGBM
- **Base de données** : SQLite
- **API Backend** : FastAPI
- **Frontend** : Streamlit
- **ML Ops** : Joblib, Pickle

## 📋 Plan de Développement

- [ ] **Étape 1** : Architecture & Collecte de Données
- [ ] **Étape 2** : Feature Engineering
- [ ] **Étape 3** : Entraînement du Modèle ML
- [ ] **Étape 4** : Système de Backtesting
- [ ] **Étape 5** : API FastAPI & Dashboard Streamlit

## 📁 Structure du Projet

```
SBVPS/
├── data/                   # Données brutes, traitées, modèles
├── database/              # Base SQLite
├── src/                   # Code source (data, features, models, backtesting, API)
├── scripts/              # Scripts d'exécution
├── dashboard/            # Streamlit app
├── tests/                # Tests unitaires
└── notebooks/            # Exploration et analyse
```

## 🚀 Quick Start

### 1. Installation

```bash
python -m venv venv
venv\Scripts\activate  # Sur Windows
pip install -r requirements.txt
```

### 2. Générer des données fictives

```bash
python scripts/generate_fake_matches.py --n 380 --season 2025 --league "Ligue 1"
```

### 3. Entraîner le modèle

```bash
python scripts/train_model.py
```

### 4. Backtesting

```bash
python scripts/run_backtest.py
```

### 5. Lancer le dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

## 📊 Données

Les données sont stockées dans `database/sbvps.db` (SQLite).

### Tables principales
- `matches` : Résultats des matchs
- `odds` : Cotes des bookmakers
- `teams` : Infos des équipes
- `predictions` : Prédictions du modèle
- `backtests` : Résultats du backtesting

## 📝 License

MIT
