"""
Quick betting value check - Simple interface for value betting analysis
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.value_analyzer import ValueAnalyzer
from src.logger import get_logger

logger = get_logger(__name__)


def quick_value_check():
    """Interactive value betting check"""
    
    logger.info("\n" + "="*80)
    logger.info("⚡ QUICK VALUE BETTING CHECK")
    logger.info("="*80)
    
    try:
        # Get match info
        match_name = input("\n📌 Match (e.g., 'France vs Iran'): ").strip()
        
        # Get probabilities
        logger.info("\n📊 Enter your model predictions (must sum to 1.0):")
        prob_1 = float(input("   Prob Home Win (0-1): "))
        prob_x = float(input("   Prob Draw (0-1): "))
        prob_2 = float(input("   Prob Away Win (0-1): "))
        
        total = prob_1 + prob_x + prob_2
        if abs(total - 1.0) > 0.01:
            logger.error(f"❌ Probabilities sum to {total:.2f}, must be ~1.0")
            return
        
        # Get odds
        logger.info("\n💰 Enter bookmaker odds (decimal format):")
        odds_1 = float(input("   Odds Home Win: "))
        odds_x = float(input("   Odds Draw: "))
        odds_2 = float(input("   Odds Away Win: "))
        
        confidence = float(input("\n🎯 Model confidence (0-1, default 0.8): ") or "0.8")
        
        # Analyze
        analyzer = ValueAnalyzer()
        analysis = analyzer.print_analysis(
            match_name=match_name,
            prob_1=prob_1,
            prob_x=prob_x,
            prob_2=prob_2,
            odds_1=odds_1,
            odds_x=odds_x,
            odds_2=odds_2,
            confidence=confidence
        )
        
    except ValueError as e:
        logger.error(f"❌ Invalid input: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n\nCancelled.")
        sys.exit(0)


if __name__ == "__main__":
    quick_value_check()
