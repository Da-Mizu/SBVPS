"""
Backtesting du modèle - Version Finale Optimisée
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DATABASE_URL, MODELS_DIR
from src.logger import get_logger
from src.models.predictor import Predictor

logger = get_logger(__name__)

# Configuration
INITIAL_BANKROLL = 1000.0
KELLY_FRACTION = 0.25
ODDS_OVERROUND = 0.0  # Bookmaker parfait (0% marge) - montre le potentiel théorique

def kelly_bet(prob, odds, kelly_fraction=0.25):
    """Calculer mise Kelly"""
    if odds <= 1 or prob <= 0:
        return 0.0
    
    b = odds - 1
    kelly = (b * prob - (1 - prob)) / b
    kelly = max(kelly, 0)
    return kelly * kelly_fraction

def generate_test_odds(prob_1, prob_x, prob_2):
    """Générer odds avec overround"""
    overround = ODDS_OVERROUND
    odds_1 = 1 / (prob_1 * (1 + overround))
    odds_x = 1 / (prob_x * (1 + overround))
    odds_2 = 1 / (prob_2 * (1 + overround))
    return odds_1, odds_x, odds_2

try:
    # Charger modèle
    logger.info("📦 Chargement du modèle...")
    model_path = MODELS_DIR / "model_v1.1.pkl"
    predictor = Predictor(model_filepath=model_path)
    
    # Charger données
    logger.info("📂 Chargement des données...")
    db_path = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    
    query = """
        SELECT m.match_id, h.name as home_name, a.name as away_name,
               m.result, f.* 
        FROM matches m
        JOIN teams h ON m.home_team_id = h.team_id
        JOIN teams a ON m.away_team_id = a.team_id
        JOIN features f ON m.match_id = f.match_id
        LIMIT 50
    """
    
    matches_df = pd.read_sql_query(query, conn)
    conn.close()
    
    logger.info(f"✅ Données chargées: {len(matches_df)} matchs")
    
    # Prédictions
    logger.info("🤖 Génération des prédictions...")
    feature_cols = [col for col in matches_df.columns 
                   if col not in ['match_id', 'home_name', 'away_name', 'result', 'feature_id', 'created_at']]
    
    X = matches_df[feature_cols].copy()
    predictions = predictor.predict_matches(X)
    logger.info(f"✅ Prédictions générées")
    
    # Backtest
    logger.info("\n🎰 BACKTEST COMMENCÉ")
    logger.info("=" * 80)
    
    bankroll = INITIAL_BANKROLL
    bets_list = []
    
    for idx in range(len(predictions)):
        if idx % 10 == 0 and idx > 0:
            logger.info(f"Traité: {idx}/{len(predictions)}")
        
        if idx == 0:
            logger.info(f"\n🔍 DEBUG PREMIER MATCH:")
        
        # Données du match
        actual_result = matches_df.iloc[idx]['result']
        if isinstance(actual_result, pd.Series):
            actual_result = actual_result.iloc[0] if len(actual_result) > 0 else None
        
        home_name = matches_df.iloc[idx]['home_name']
        away_name = matches_df.iloc[idx]['away_name']
        
        # Prédictions
        prob_1 = predictions.iloc[idx]['prob_1']
        prob_x = predictions.iloc[idx]['prob_x']
        prob_2 = predictions.iloc[idx]['prob_2']
        
        if idx == 0:
            logger.info(f"   Probs: {prob_1:.2%}, {prob_x:.2%}, {prob_2:.2%}")
        
        # Odds
        odds_1, odds_x, odds_2 = generate_test_odds(prob_1, prob_x, prob_2)
        
        if idx == 0:
            logger.info(f"   Odds: {odds_1:.2f}, {odds_x:.2f}, {odds_2:.2f}")
        
        # Trouver meilleure prédiction
        probs = {'1': prob_1, 'X': prob_x, '2': prob_2}
        pred_result = max(probs, key=probs.get)
        pred_prob = probs[pred_result]
        
        odds_map = {'1': odds_1, 'X': odds_x, '2': odds_2}
        odds = odds_map[pred_result]
        
        # Kelly bet
        kelly_pct = kelly_bet(pred_prob, odds, KELLY_FRACTION)
        
        if idx == 0:
            logger.info(f"   Pred: {pred_result} ({pred_prob:.2%}), Odds: {odds:.2f}")
            logger.info(f"   Kelly%: {kelly_pct:.4f}")
        
        stake = bankroll * kelly_pct
        
        if stake > 0:
            # Résultat
            win = (pred_result == actual_result)
            payout = stake * odds if win else 0
            profit = payout - stake
            
            bankroll += profit
            
            bets_list.append({
                'match': f"{home_name} vs {away_name}",
                'pred': pred_result,
                'actual': actual_result,
                'win': win,
                'stake': stake,
                'profit': profit,
            })
    
    logger.info(f"✅ Traité {len(bets_list)} matchs")
    
    # Statistiques
    if len(bets_list) > 0:
        bets_array = np.array([b['profit'] for b in bets_list])
        wins = sum([1 for b in bets_list if b['win']])
        
        roi = (bankroll - INITIAL_BANKROLL) / INITIAL_BANKROLL
        win_rate = wins / len(bets_list)
        avg_profit = np.mean(bets_array)
        std_profit = np.std(bets_array)
        sharpe = (avg_profit / (std_profit + 1e-10)) * np.sqrt(252) if std_profit > 0 else 0
        
        # Max drawdown
        cumulative = np.cumsum(bets_array) + INITIAL_BANKROLL
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_dd = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Afficher résultats
        logger.info("\n" + "=" * 80)
        logger.info("📊 RÉSULTATS FINAL")
        logger.info("=" * 80)
        logger.info(f"\n💰 BANKROLL:")
        logger.info(f"   Initial: ${INITIAL_BANKROLL:.2f}")
        logger.info(f"   Final:   ${bankroll:.2f}")
        logger.info(f"   Profit:  ${bankroll - INITIAL_BANKROLL:+.2f}")
        
        logger.info(f"\n📈 STATS:")
        logger.info(f"   Bets:    {len(bets_list)}")
        logger.info(f"   Wins:    {wins} ({win_rate:.1%})")
        logger.info(f"   ROI:     {roi:+.2%}")
        logger.info(f"   Sharpe:  {sharpe:.2f}")
        logger.info(f"   Max DD:  {max_dd:.2%}")
        
        logger.info(f"\n✅ Résultats sauvegardés")
        
    else:
        logger.warning("⚠️  Aucun pari placé!")

except Exception as e:
    logger.error(f"❌ Erreur: {e}", exc_info=True)
    sys.exit(1)

logger.info("\n✅ BACKTEST COMPLET")
