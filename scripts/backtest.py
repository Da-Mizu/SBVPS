"""
Backtesting du modèle de prédiction sur les matchs historiques
Applique Kelly Criterion pour la gestion de bankroll
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DATABASE_URL, MODELS_DIR
from src.logger import get_logger
from src.data.api_fetcher import FootballDataFetcher
from src.models.predictor import Predictor

logger = get_logger(__name__)

class Backtester:
    def __init__(self, initial_bankroll=1000.0, kelly_fraction=0.25):
        """
        Initialize Backtester
        
        Args:
            initial_bankroll: Starting capital ($)
            kelly_fraction: Fraction of Kelly to bet (0.25 = 25% Kelly)
        """
        self.initial_bankroll = initial_bankroll
        self.kelly_fraction = kelly_fraction
        self.current_bankroll = initial_bankroll
        
        # Charger le modèle
        model_path = MODELS_DIR / "model_v1.1.pkl"
        self.predictor = Predictor(model_filepath=model_path)
        
    def get_historical_matches(self):
        """Charger les matchs historiques de la base de données"""
        db_path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        
        # Charger les matchs avec résultats
        query = """
            SELECT m.match_id, m.home_team_id, m.away_team_id, 
                   h.name as home_name, a.name as away_name,
                   m.result, m.home_goals, m.away_goals,
                   f.* 
            FROM matches m
            JOIN teams h ON m.home_team_id = h.team_id
            JOIN teams a ON m.away_team_id = a.team_id
            JOIN features f ON m.match_id = f.match_id
            ORDER BY m.match_id
            LIMIT 50
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        logger.info(f"📂 Chargé {len(df)} matchs historiques")
        return df
    
    def generate_test_odds(self, prob_1, prob_x, prob_2):
        """Générer des odds de bookmaker pour test"""
        # Ajouter marge de 5% overround
        overround = 0.05
        
        # Convertir prob → odds
        odds_1 = 1 / (prob_1 * (1 + overround))
        odds_x = 1 / (prob_x * (1 + overround))
        odds_2 = 1 / (prob_2 * (1 + overround))
        
        return odds_1, odds_x, odds_2
    
    def kelly_bet(self, prob, odds):
        """Calculer mise Kelly"""
        if odds <= 1:
            return 0
        
        # Kelly: f* = (b*p - q) / b
        # où b = odds - 1, p = prob win, q = 1 - prob
        b = odds - 1
        p = prob
        q = 1 - p
        
        kelly = (b * p - q) / b if b > 0 else 0
        kelly = max(kelly, 0)  # Pas de paris négatifs
        
        # Appliquer fractional kelly
        kelly_fraction = kelly * self.kelly_fraction
        
        return kelly_fraction
    
    def backtest(self):
        """Exécuter le backtest"""
        logger.info("\n" + "=" * 80)
        logger.info("🎰 DÉMARRAGE BACKTEST")
        logger.info("=" * 80)
        
        matches_df = self.get_historical_matches()
        
        # Variables de tracking
        bets = []
        total_stake = 0
        total_return = 0
        wins = 0
        losses = 0
        draws = 0
        
        # Prédictions des matchs
        logger.info("\n🤖 Génération des prédictions...")
        
        # Prendre les colonnes de features (exclure match info)
        feature_cols = [col for col in matches_df.columns 
                       if col not in ['match_id', 'home_team_id', 'away_team_id', 
                                     'home_name', 'away_name', 'result', 
                                     'home_goals', 'away_goals', 'feature_id', 'created_at']]
        
        X = matches_df[feature_cols].copy()
        predictions = self.predictor.predict_matches(X)
        
        logger.info(f"Prédictions générées pour {len(predictions)} matchs")
        
        # Analyser chaque match
        logger.info("🔄 Analyse des matchs...")
        for idx in range(len(matches_df)):
            if idx % 10 == 0:
                logger.info(f"  Processing match {idx+1}/{len(matches_df)}")
            
            row = matches_df.iloc[idx]
            match_id = row['match_id']
            home_name = row['home_name']
            away_name = row['away_name']
            actual_result = row['result']
            
            # Prédictions du modèle
            pred = predictions.iloc[idx]
            prob_1 = pred['prob_1']
            prob_x = pred['prob_x']
            prob_2 = pred['prob_2']
            
            # Générer odds de test
            odds_1, odds_x, odds_2 = self.generate_test_odds(prob_1, prob_x, prob_2)
            
            # Trouver la prédiction la plus probable
            probs = {'1': prob_1, 'X': prob_x, '2': prob_2}
            predicted_result = max(probs, key=probs.get)
            predicted_prob = probs[predicted_result]
            
            # Odds associées
            odds_map = {'1': odds_1, 'X': odds_x, '2': odds_2}
            odds = odds_map[predicted_result]
            
            # Calculer mise Kelly
            kelly_bet_fraction = self.kelly_bet(predicted_prob, odds)
            stake = self.current_bankroll * kelly_bet_fraction
            
            if stake > 0:
                # Déterminer si on a gagné
                win = (predicted_result == actual_result)
                
                if win:
                    returns = stake * odds
                    profit = returns - stake
                    wins += 1
                else:
                    returns = 0
                    profit = -stake
                    losses += 1
                
                # Mise à jour bankroll
                self.current_bankroll += profit
                total_stake += stake
                total_return += returns
                
                # Tracker le pari
                bets.append({
                    'match_id': match_id,
                    'match': f"{home_name} vs {away_name}",
                    'predicted': predicted_result,
                    'actual': actual_result,
                    'prob': predicted_prob,
                    'odds': odds,
                    'stake': stake,
                    'win': win,
                    'profit': profit,
                    'bankroll': self.current_bankroll,
                })
        
        # Calculer les métriques
        bets_df = pd.DataFrame(bets)
        
        if len(bets_df) > 0:
            win_rate = wins / len(bets_df)
            roi = (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll
            
            # Sharpe Ratio (en assumant 252 jours par an, mais on peut adapter)
            returns_series = bets_df['profit'].values
            if len(returns_series) > 1:
                sharpe = np.mean(returns_series) / (np.std(returns_series) + 1e-10) * np.sqrt(252)
            else:
                sharpe = 0
            
            # Max Drawdown
            cumulative = (bets_df['profit'].cumsum() + self.initial_bankroll).values
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
            
            # Afficher résultats
            logger.info("\n" + "=" * 80)
            logger.info("📊 RÉSULTATS BACKTEST")
            logger.info("=" * 80)
            logger.info(f"\n💰 BANKROLL:")
            logger.info(f"   Initial: ${self.initial_bankroll:.2f}")
            logger.info(f"   Final:   ${self.current_bankroll:.2f}")
            logger.info(f"   Profit:  ${self.current_bankroll - self.initial_bankroll:+.2f}")
            
            logger.info(f"\n📈 PERFORMANCE:")
            logger.info(f"   Total Bets:  {len(bets_df)}")
            logger.info(f"   Wins:        {wins} ({win_rate:.1%})")
            logger.info(f"   Losses:      {losses}")
            logger.info(f"   ROI:         {roi:+.2%}")
            logger.info(f"   Sharpe:      {sharpe:.2f}")
            logger.info(f"   Max Drawdown: {max_drawdown:.2%}")
            
            logger.info(f"\n💡 SUMMARY:")
            if roi > 0:
                logger.info(f"   ✅ PROFITABLE: +{roi:.2%} ROI")
            else:
                logger.info(f"   ❌ LOSING: {roi:.2%} ROI")
            
            # Sauvegarder les résultats
            results_file = Path("data/backtest_results.csv")
            bets_df.to_csv(results_file, index=False)
            logger.info(f"\n📁 Résultats sauvegardés: {results_file}")
            
            return {
                'bets': bets_df,
                'roi': roi,
                'win_rate': win_rate,
                'sharpe': sharpe,
                'max_drawdown': max_drawdown,
                'final_bankroll': self.current_bankroll,
            }

if __name__ == "__main__":
    backtester = Backtester(initial_bankroll=1000.0, kelly_fraction=0.25)
    results = backtester.backtest()
