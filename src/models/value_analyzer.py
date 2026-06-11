"""
Value Betting Analyzer - Identify profitable betting opportunities
Compares model predictions vs bookmaker odds to find positive expected value bets
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from src.logger import get_logger

logger = get_logger(__name__)


class ValueAnalyzer:
    """Analyze betting value: compare probabilities vs odds"""

    def __init__(self, min_value_threshold=1.05):
        """
        Initialize Value Analyzer
        
        Args:
            min_value_threshold: Minimum value ratio to consider (1.05 = +5% edge)
        """
        self.min_value_threshold = min_value_threshold

    def odds_to_probability(self, odds: float) -> float:
        """
        Convert decimal odds to implied probability
        
        Args:
            odds: Decimal odds (e.g., 2.50)
            
        Returns:
            Implied probability (0-1)
        """
        if odds <= 0:
            return 0
        return 1 / odds

    def probability_to_odds(self, probability: float) -> float:
        """
        Convert probability to decimal odds
        
        Args:
            probability: Probability (0-1)
            
        Returns:
            Decimal odds
        """
        if probability <= 0 or probability >= 1:
            return 0
        return 1 / probability

    def calculate_expected_value(self, 
                                 model_prob: float, 
                                 odds: float,
                                 stake: float = 100) -> Dict:
        """
        Calculate expected value (EV) for a bet
        
        Args:
            model_prob: Model's estimated probability (0-1)
            odds: Bookmaker's decimal odds
            stake: Bet amount (default: 100)
            
        Returns:
            Dict with EV analysis
        """
        implied_prob = self.odds_to_probability(odds)
        
        # Expected value calculation
        ev_pct = (model_prob * odds - 1) * 100
        
        # Potential returns
        if odds > 0:
            profit_if_win = stake * (odds - 1)  # Profit only (not total)
            loss_if_lose = stake
            ev_amount = (model_prob * profit_if_win) - ((1 - model_prob) * loss_if_lose)
        else:
            profit_if_win = 0
            loss_if_lose = 0
            ev_amount = 0
        
        return {
            'model_prob': model_prob,
            'implied_prob': implied_prob,
            'odds': odds,
            'ev_pct': ev_pct,
            'potential_win': profit_if_win,
            'potential_loss': loss_if_lose,
            'ev_amount': ev_amount,
            'is_value': ev_pct > 0
        }

    def analyze_match_odds(self, 
                          prob_1: float, 
                          prob_x: float, 
                          prob_2: float,
                          odds_1: float,
                          odds_x: float,
                          odds_2: float) -> Dict:
        """
        Analyze all three betting options for a match
        
        Args:
            prob_1, prob_x, prob_2: Model probabilities
            odds_1, odds_x, odds_2: Bookmaker odds
            
        Returns:
            Dict with value analysis for each outcome
        """
        results = {
            '1 (Home Win)': self.calculate_expected_value(prob_1, odds_1),
            'X (Draw)': self.calculate_expected_value(prob_x, odds_x),
            '2 (Away Win)': self.calculate_expected_value(prob_2, odds_2),
        }
        
        # Find best value bet
        best_bet = None
        best_ev = -float('inf')
        
        for outcome, ev_data in results.items():
            if ev_data['is_value'] and ev_data['ev_pct'] > best_ev:
                best_ev = ev_data['ev_pct']
                best_bet = outcome
        
        return {
            'outcomes': results,
            'best_bet': best_bet,
            'best_ev_pct': best_ev if best_bet else 0,
            'has_value': best_bet is not None
        }

    def kelly_criterion(self, model_prob: float, odds: float, kelly_fraction: float = 0.25) -> float:
        """
        Calculate Kelly Criterion optimal bet size
        
        Args:
            model_prob: Model's estimated probability
            odds: Decimal odds
            kelly_fraction: Fractional kelly to use (default: 0.25 = conservative)
            
        Returns:
            Recommended bet size as % of bankroll
        """
        if odds <= 0 or model_prob <= 0 or model_prob >= 1:
            return 0
        
        decimal_odds = odds
        prob_win = model_prob
        prob_loss = 1 - model_prob
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = probability win, q = probability loss
        b = decimal_odds - 1
        
        kelly_pct = (b * prob_win - prob_loss) / b
        
        # Use fractional kelly for safety
        kelly_pct = kelly_pct * kelly_fraction
        
        # Never bet more than we can afford to lose
        return max(0, min(kelly_pct, 0.05))  # Cap at 5% of bankroll

    def print_analysis(self, 
                      match_name: str,
                      prob_1: float,
                      prob_x: float, 
                      prob_2: float,
                      odds_1: float,
                      odds_x: float,
                      odds_2: float,
                      confidence: float = None):
        """Print formatted analysis of match value opportunities"""
        
        logger.info("\n" + "="*80)
        logger.info(f"VALUE BETTING ANALYSIS - {match_name}")
        logger.info("="*80)
        
        # Model predictions
        logger.info(f"\n📊 MODEL PREDICTIONS (Confidence: {confidence*100:.1f}%):")
        logger.info(f"   Home Win (1): {prob_1*100:5.1f}%")
        logger.info(f"   Draw (X):     {prob_x*100:5.1f}%")
        logger.info(f"   Away Win (2): {prob_2*100:5.1f}%")
        
        # Bookmaker odds
        logger.info(f"\n💰 BOOKMAKER ODDS:")
        logger.info(f"   Home Win (1): {odds_1:.2f}")
        logger.info(f"   Draw (X):     {odds_x:.2f}")
        logger.info(f"   Away Win (2): {odds_2:.2f}")
        
        # Implied probabilities
        logger.info(f"\n🎯 IMPLIED PROBABILITIES (from odds):")
        impl_1 = self.odds_to_probability(odds_1)
        impl_x = self.odds_to_probability(odds_x)
        impl_2 = self.odds_to_probability(odds_2)
        logger.info(f"   Home Win (1): {impl_1*100:5.1f}%")
        logger.info(f"   Draw (X):     {impl_x*100:5.1f}%")
        logger.info(f"   Away Win (2): {impl_2*100:5.1f}%")
        logger.info(f"   Overround:    {((impl_1 + impl_x + impl_2 - 1) * 100):.1f}% (margin)")
        
        # Value analysis
        analysis = self.analyze_match_odds(prob_1, prob_x, prob_2, odds_1, odds_x, odds_2)
        
        logger.info(f"\n💡 VALUE OPPORTUNITIES:")
        for outcome, ev_data in analysis['outcomes'].items():
            status = "✅ VALUE" if ev_data['is_value'] else "❌ NO VALUE"
            logger.info(f"\n   {outcome}:")
            logger.info(f"      Expected Value: {ev_data['ev_pct']:+.2f}%")
            logger.info(f"      EV per $100: ${ev_data['ev_amount']:+.2f}")
            logger.info(f"      Kelly % (25%): {self.kelly_criterion(ev_data['model_prob'], ev_data['odds']):.2f}%")
            logger.info(f"      Status: {status}")
        
        # Recommendation
        if analysis['best_bet']:
            logger.info(f"\n🎯 RECOMMENDATION:")
            logger.info(f"   BET ON: {analysis['best_bet']}")
            logger.info(f"   Expected Edge: {analysis['best_ev_pct']:+.2f}%")
            logger.info(f"   This gives positive expected value long-term")
        else:
            logger.info(f"\n⚠️  NO VALUE BETS FOUND")
            logger.info(f"   All outcomes are overpriced relative to model predictions")
        
        logger.info("\n" + "="*80 + "\n")
        
        return analysis

    def simulate_bets(self, 
                     analysis_list: list,
                     initial_bankroll: float = 1000,
                     kelly_fraction: float = 0.25) -> Dict:
        """
        Simulate a series of bets using Kelly Criterion
        
        Args:
            analysis_list: List of (prob, odds) tuples
            initial_bankroll: Starting bankroll
            kelly_fraction: Kelly fraction to use
            
        Returns:
            Simulation results
        """
        bankroll = initial_bankroll
        results = []
        
        for analysis in analysis_list:
            prob_1, odds_1, prob_x, odds_x, prob_2, odds_2 = analysis
            
            # Find best bet
            ev_1 = (prob_1 * odds_1 - 1)
            ev_x = (prob_x * odds_x - 1)
            ev_2 = (prob_2 * odds_2 - 1)
            
            if max(ev_1, ev_x, ev_2) <= 0:
                continue  # Skip if no value
            
            # Determine best bet
            best_ev = max(ev_1, ev_x, ev_2)
            if best_ev == ev_1:
                prob, odds = prob_1, odds_1
            elif best_ev == ev_x:
                prob, odds = prob_x, odds_x
            else:
                prob, odds = prob_2, odds_2
            
            # Kelly sizing
            bet_size = bankroll * self.kelly_criterion(prob, odds, kelly_fraction)
            
            # Simulate outcome (random)
            won = np.random.random() < prob
            
            if won:
                bankroll += bet_size * (odds - 1)
            else:
                bankroll -= bet_size
            
            results.append({
                'bet_size': bet_size,
                'odds': odds,
                'won': won,
                'bankroll': bankroll
            })
        
        return {
            'final_bankroll': bankroll,
            'profit': bankroll - initial_bankroll,
            'roi': ((bankroll - initial_bankroll) / initial_bankroll) * 100,
            'bets': len(results),
            'wins': sum(1 for r in results if r['won']),
            'win_rate': sum(1 for r in results if r['won']) / len(results) if results else 0
        }
