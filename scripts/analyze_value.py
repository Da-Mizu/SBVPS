"""
Analyze value bets: given match probabilities and odds, determine which bets are profitable
"""
import argparse
import sys
from pathlib import Path

# Ajouter le projet root au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.value_analyzer import ValueAnalyzer
from src.logger import get_logger

logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze betting value for a match"
    )
    parser.add_argument(
        "--match-name",
        type=str,
        required=True,
        help="Match name (e.g., 'France vs Iran')"
    )
    parser.add_argument(
        "--prob-1",
        type=float,
        required=True,
        help="Model probability for Home Win/Team 1 (0-1)"
    )
    parser.add_argument(
        "--prob-x",
        type=float,
        required=True,
        help="Model probability for Draw (0-1)"
    )
    parser.add_argument(
        "--prob-2",
        type=float,
        required=True,
        help="Model probability for Away Win/Team 2 (0-1)"
    )
    parser.add_argument(
        "--odds-1",
        type=float,
        required=True,
        help="Bookmaker odds for Home Win (decimal format, e.g., 2.50)"
    )
    parser.add_argument(
        "--odds-x",
        type=float,
        required=True,
        help="Bookmaker odds for Draw"
    )
    parser.add_argument(
        "--odds-2",
        type=float,
        required=True,
        help="Bookmaker odds for Away Win"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Model confidence in prediction (0-1, default: 0.5)"
    )

    args = parser.parse_args()

    try:
        # Valider les probabilités
        total_prob = args.prob_1 + args.prob_x + args.prob_2
        if abs(total_prob - 1.0) > 0.01:
            logger.error(f"❌ Probabilities must sum to ~1.0 (got {total_prob:.2f})")
            sys.exit(1)

        # Analyser
        analyzer = ValueAnalyzer()
        analysis = analyzer.print_analysis(
            match_name=args.match_name,
            prob_1=args.prob_1,
            prob_x=args.prob_x,
            prob_2=args.prob_2,
            odds_1=args.odds_1,
            odds_x=args.odds_x,
            odds_2=args.odds_2,
            confidence=args.confidence
        )

    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
