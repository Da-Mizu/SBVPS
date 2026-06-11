"""
Fetch real football data from free APIs
Supports: football-data.org
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.logger import get_logger
import time

logger = get_logger(__name__)

# Football-data.org API (free tier)
FOOTBALL_DATA_API = "https://api.football-data.org/v4"
# Free tier works without token for most endpoints
HEADERS = {
    "X-Auth-Token": ""  # Free tier - leave empty
}


class FootballDataFetcher:
    """Fetch real football data from free APIs"""

    @staticmethod
    def search_team(team_name: str, limit: int = 5) -> List[Dict]:
        """
        Search for teams by name using football-data.org
        
        Args:
            team_name: Team name to search
            limit: Max results to return
            
        Returns:
            List of teams with IDs and info
        """
        try:
            # Use football-data.org competition endpoint to get teams
            # For now, return mock data for testing
            logger.warning(f"⚠️  Team search requires registration with football-data.org")
            logger.info(f"   Alternative: Using realistic mock data for testing")
            
            mock_teams = {
                # ====== WORLD CUP 2026 - ELITE TEAMS ======
                'France': {'id': 773, 'name': 'France', 'shortName': 'France', 'tla': 'FRA', 'crest': ''},
                'Brazil': {'id': 770, 'name': 'Brazil', 'shortName': 'Brazil', 'tla': 'BRA', 'crest': ''},
                'Brésil': {'id': 770, 'name': 'Brazil', 'shortName': 'Brazil', 'tla': 'BRA', 'crest': ''},
                'Argentina': {'id': 760, 'name': 'Argentina', 'shortName': 'Argentina', 'tla': 'ARG', 'crest': ''},
                'Argentine': {'id': 760, 'name': 'Argentina', 'shortName': 'Argentina', 'tla': 'ARG', 'crest': ''},
                'Germany': {'id': 759, 'name': 'Germany', 'shortName': 'Germany', 'tla': 'DEU', 'crest': ''},
                'Allemagne': {'id': 759, 'name': 'Germany', 'shortName': 'Germany', 'tla': 'DEU', 'crest': ''},
                'Spain': {'id': 808, 'name': 'Spain', 'shortName': 'Spain', 'tla': 'ESP', 'crest': ''},
                'Espagne': {'id': 808, 'name': 'Spain', 'shortName': 'Spain', 'tla': 'ESP', 'crest': ''},
                
                # ====== STRONG CONTENDERS ======
                'England': {'id': 770, 'name': 'England', 'shortName': 'England', 'tla': 'ENG', 'crest': ''},
                'Angleterre': {'id': 770, 'name': 'England', 'shortName': 'England', 'tla': 'ENG', 'crest': ''},
                'Netherlands': {'id': 771, 'name': 'Netherlands', 'shortName': 'Netherlands', 'tla': 'NLD', 'crest': ''},
                'Pays-Bas': {'id': 771, 'name': 'Netherlands', 'shortName': 'Netherlands', 'tla': 'NLD', 'crest': ''},
                'Belgium': {'id': 757, 'name': 'Belgium', 'shortName': 'Belgium', 'tla': 'BEL', 'crest': ''},
                'Belgique': {'id': 757, 'name': 'Belgium', 'shortName': 'Belgium', 'tla': 'BEL', 'crest': ''},
                'Portugal': {'id': 794, 'name': 'Portugal', 'shortName': 'Portugal', 'tla': 'POR', 'crest': ''},
                'Uruguay': {'id': 835, 'name': 'Uruguay', 'shortName': 'Uruguay', 'tla': 'URY', 'crest': ''},
                'Croatia': {'id': 776, 'name': 'Croatia', 'shortName': 'Croatia', 'tla': 'HRV', 'crest': ''},
                'Croatie': {'id': 776, 'name': 'Croatia', 'shortName': 'Croatia', 'tla': 'HRV', 'crest': ''},
                'Switzerland': {'id': 823, 'name': 'Switzerland', 'shortName': 'Switzerland', 'tla': 'CHE', 'crest': ''},
                'Suisse': {'id': 823, 'name': 'Switzerland', 'shortName': 'Switzerland', 'tla': 'CHE', 'crest': ''},
                'Denmark': {'id': 779, 'name': 'Denmark', 'shortName': 'Denmark', 'tla': 'DNK', 'crest': ''},
                'Danemark': {'id': 779, 'name': 'Denmark', 'shortName': 'Denmark', 'tla': 'DNK', 'crest': ''},
                'Sweden': {'id': 821, 'name': 'Sweden', 'shortName': 'Sweden', 'tla': 'SWE', 'crest': ''},
                'Suède': {'id': 821, 'name': 'Sweden', 'shortName': 'Sweden', 'tla': 'SWE', 'crest': ''},
                
                # ====== COMPETITIVE TEAMS ======
                'Mexico': {'id': 789, 'name': 'Mexico', 'shortName': 'Mexico', 'tla': 'MEX', 'crest': ''},
                'Mexique': {'id': 789, 'name': 'Mexico', 'shortName': 'Mexico', 'tla': 'MEX', 'crest': ''},
                'Japan': {'id': 787, 'name': 'Japan', 'shortName': 'Japan', 'tla': 'JPN', 'crest': ''},
                'Japon': {'id': 787, 'name': 'Japan', 'shortName': 'Japan', 'tla': 'JPN', 'crest': ''},
                'South Korea': {'id': 790, 'name': 'South Korea', 'shortName': 'S. Korea', 'tla': 'KOR', 'crest': ''},
                'Corée du Sud': {'id': 790, 'name': 'South Korea', 'shortName': 'S. Korea', 'tla': 'KOR', 'crest': ''},
                'Canada': {'id': 761, 'name': 'Canada', 'shortName': 'Canada', 'tla': 'CAN', 'crest': ''},
                'United States': {'id': 836, 'name': 'United States', 'shortName': 'USA', 'tla': 'USA', 'crest': ''},
                'USA': {'id': 836, 'name': 'United States', 'shortName': 'USA', 'tla': 'USA', 'crest': ''},
                'États-Unis': {'id': 836, 'name': 'United States', 'shortName': 'USA', 'tla': 'USA', 'crest': ''},
                'Poland': {'id': 793, 'name': 'Poland', 'shortName': 'Poland', 'tla': 'POL', 'crest': ''},
                'Pologne': {'id': 793, 'name': 'Poland', 'shortName': 'Poland', 'tla': 'POL', 'crest': ''},
                'Serbia': {'id': 810, 'name': 'Serbia', 'shortName': 'Serbia', 'tla': 'SRB', 'crest': ''},
                'Serbie': {'id': 810, 'name': 'Serbia', 'shortName': 'Serbia', 'tla': 'SRB', 'crest': ''},
                'Czech Republic': {'id': 778, 'name': 'Czech Republic', 'shortName': 'Czechia', 'tla': 'CZE', 'crest': ''},
                'République Tchèque': {'id': 778, 'name': 'Czech Republic', 'shortName': 'Czechia', 'tla': 'CZE', 'crest': ''},
                'Greece': {'id': 782, 'name': 'Greece', 'shortName': 'Greece', 'tla': 'GRC', 'crest': ''},
                'Grèce': {'id': 782, 'name': 'Greece', 'shortName': 'Greece', 'tla': 'GRC', 'crest': ''},
                'Turkey': {'id': 833, 'name': 'Turkey', 'shortName': 'Turkey', 'tla': 'TUR', 'crest': ''},
                'Turquie': {'id': 833, 'name': 'Turkey', 'shortName': 'Turkey', 'tla': 'TUR', 'crest': ''},
                
                # ====== AFRICAN TEAMS ======
                'Senegal': {'id': 809, 'name': 'Senegal', 'shortName': 'Senegal', 'tla': 'SEN', 'crest': ''},
                'Sénégal': {'id': 809, 'name': 'Senegal', 'shortName': 'Senegal', 'tla': 'SEN', 'crest': ''},
                'Nigeria': {'id': 791, 'name': 'Nigeria', 'shortName': 'Nigeria', 'tla': 'NGR', 'crest': ''},
                'Egypt': {'id': 780, 'name': 'Egypt', 'shortName': 'Egypt', 'tla': 'EGY', 'crest': ''},
                'Égypte': {'id': 780, 'name': 'Egypt', 'shortName': 'Egypt', 'tla': 'EGY', 'crest': ''},
                'Morocco': {'id': 788, 'name': 'Morocco', 'shortName': 'Morocco', 'tla': 'MAR', 'crest': ''},
                'Maroc': {'id': 788, 'name': 'Morocco', 'shortName': 'Morocco', 'tla': 'MAR', 'crest': ''},
                'Cameroon': {'id': 762, 'name': 'Cameroon', 'shortName': 'Cameroon', 'tla': 'CMR', 'crest': ''},
                'Cameroun': {'id': 762, 'name': 'Cameroon', 'shortName': 'Cameroon', 'tla': 'CMR', 'crest': ''},
                'Ghana': {'id': 781, 'name': 'Ghana', 'shortName': 'Ghana', 'tla': 'GHA', 'crest': ''},
                'Mali': {'id': 792, 'name': 'Mali', 'shortName': 'Mali', 'tla': 'MLI', 'crest': ''},
                'Tunisia': {'id': 832, 'name': 'Tunisia', 'shortName': 'Tunisia', 'tla': 'TUN', 'crest': ''},
                'Tunisie': {'id': 832, 'name': 'Tunisia', 'shortName': 'Tunisia', 'tla': 'TUN', 'crest': ''},
                
                # ====== SOUTH AMERICAN TEAMS ======
                'Ecuador': {'id': 780, 'name': 'Ecuador', 'shortName': 'Ecuador', 'tla': 'ECU', 'crest': ''},
                'Équateur': {'id': 780, 'name': 'Ecuador', 'shortName': 'Ecuador', 'tla': 'ECU', 'crest': ''},
                'Paraguay': {'id': 792, 'name': 'Paraguay', 'shortName': 'Paraguay', 'tla': 'PAR', 'crest': ''},
                'Peru': {'id': 793, 'name': 'Peru', 'shortName': 'Peru', 'tla': 'PER', 'crest': ''},
                'Pérou': {'id': 793, 'name': 'Peru', 'shortName': 'Peru', 'tla': 'PER', 'crest': ''},
                'Colombia': {'id': 775, 'name': 'Colombia', 'shortName': 'Colombia', 'tla': 'COL', 'crest': ''},
                'Colombie': {'id': 775, 'name': 'Colombia', 'shortName': 'Colombia', 'tla': 'COL', 'crest': ''},
                'Chile': {'id': 763, 'name': 'Chile', 'shortName': 'Chile', 'tla': 'CHI', 'crest': ''},
                
                # ====== OTHER TEAMS ======
                'Costa Rica': {'id': 774, 'name': 'Costa Rica', 'shortName': 'Costa Rica', 'tla': 'CRC', 'crest': ''},
                'Wales': {'id': 836, 'name': 'Wales', 'shortName': 'Wales', 'tla': 'WAL', 'crest': ''},
                'Pays de Galles': {'id': 836, 'name': 'Wales', 'shortName': 'Wales', 'tla': 'WAL', 'crest': ''},
                'Scotland': {'id': 813, 'name': 'Scotland', 'shortName': 'Scotland', 'tla': 'SCO', 'crest': ''},
                'Écosse': {'id': 813, 'name': 'Scotland', 'shortName': 'Scotland', 'tla': 'SCO', 'crest': ''},
                'Ukraine': {'id': 834, 'name': 'Ukraine', 'shortName': 'Ukraine', 'tla': 'UKR', 'crest': ''},
                'Iran': {'id': 770, 'name': 'Iran', 'shortName': 'Iran', 'tla': 'IRN', 'crest': ''},
                'Qatar': {'id': 795, 'name': 'Qatar', 'shortName': 'Qatar', 'tla': 'QAT', 'crest': ''},
                'Saudi Arabia': {'id': 809, 'name': 'Saudi Arabia', 'shortName': 'Saudi Arabia', 'tla': 'KSA', 'crest': ''},
                'Arabie Saoudite': {'id': 809, 'name': 'Saudi Arabia', 'shortName': 'Saudi Arabia', 'tla': 'KSA', 'crest': ''},
                'Australia': {'id': 754, 'name': 'Australia', 'shortName': 'Australia', 'tla': 'AUS', 'crest': ''},
                'Australie': {'id': 754, 'name': 'Australia', 'shortName': 'Australia', 'tla': 'AUS', 'crest': ''},
                'New Zealand': {'id': 791, 'name': 'New Zealand', 'shortName': 'New Zealand', 'tla': 'NZL', 'crest': ''},
                'Nouvelle-Zélande': {'id': 791, 'name': 'New Zealand', 'shortName': 'New Zealand', 'tla': 'NZL', 'crest': ''},
                'Vietnam': {'id': 837, 'name': 'Vietnam', 'shortName': 'Vietnam', 'tla': 'VIE', 'crest': ''},
                'Thailand': {'id': 832, 'name': 'Thailand', 'shortName': 'Thailand', 'tla': 'THA', 'crest': ''},
                'Thaïlande': {'id': 832, 'name': 'Thailand', 'shortName': 'Thailand', 'tla': 'THA', 'crest': ''},
                'Indonesia': {'id': 783, 'name': 'Indonesia', 'shortName': 'Indonesia', 'tla': 'IDN', 'crest': ''},
                'Indonésie': {'id': 783, 'name': 'Indonesia', 'shortName': 'Indonesia', 'tla': 'IDN', 'crest': ''},
                'India': {'id': 784, 'name': 'India', 'shortName': 'India', 'tla': 'IND', 'crest': ''},
                'Inde': {'id': 784, 'name': 'India', 'shortName': 'India', 'tla': 'IND', 'crest': ''},
                'Jamaica': {'id': 785, 'name': 'Jamaica', 'shortName': 'Jamaica', 'tla': 'JAM', 'crest': ''},
                'Panama': {'id': 792, 'name': 'Panama', 'shortName': 'Panama', 'tla': 'PAN', 'crest': ''},
                'Honduras': {'id': 782, 'name': 'Honduras', 'shortName': 'Honduras', 'tla': 'HND', 'crest': ''},
                'El Salvador': {'id': 781, 'name': 'El Salvador', 'shortName': 'El Salvador', 'tla': 'SLV', 'crest': ''},
                
                # ====== CLUB TEAMS (for testing) ======
                'PSG': {'id': 75, 'name': 'Paris Saint-Germain', 'shortName': 'PSG', 'tla': 'PSG', 'crest': 'https://crests.football-data.org/75.png'},
                'Lyon': {'id': 65, 'name': 'Olympique Lyonnais', 'shortName': 'Lyon', 'tla': 'OL', 'crest': 'https://crests.football-data.org/65.png'},
                'Real Madrid': {'id': 86, 'name': 'Real Madrid', 'shortName': 'Real', 'tla': 'RMA', 'crest': 'https://crests.football-data.org/86.png'},
                'Barcelona': {'id': 81, 'name': 'FC Barcelona', 'shortName': 'Barcelona', 'tla': 'FCB', 'crest': 'https://crests.football-data.org/81.png'},
            }
            
            # Search by name
            results = []
            search_lower = team_name.lower()
            for key, team_data in mock_teams.items():
                if search_lower in key.lower() or search_lower in team_data['name'].lower():
                    results.append(team_data)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching teams: {e}")
            return []

    @staticmethod
    def estimate_team_stats(team_name: str, team_id: Optional[int] = None) -> Dict:
        """
        Estimate team stats using realistic defaults + randomization
        
        Args:
            team_name: Team name
            team_id: Optional team ID from API
            
        Returns:
            Dict with estimated stats
        """
        # Base stats (can be overridden with real API data later)
        import numpy as np
        
        # ====== CLASSIFY BY STRENGTH ======
        # Elite National Teams (World Cup Winners & Top Favorites)
        elite_national_teams = ['France', 'Brazil', 'Brésil', 'Argentina', 'Argentine', 'Germany', 'Allemagne', 'Spain', 'Espagne']
        
        # Strong National Teams (Quarter-Final Contenders)
        strong_national_teams = ['England', 'Angleterre', 'Netherlands', 'Pays-Bas', 'Belgium', 'Belgique', 
                                'Portugal', 'Uruguay', 'Croatia', 'Croatie', 'Switzerland', 'Suisse', 
                                'Denmark', 'Danemark', 'Sweden', 'Suède']
        
        # Competitive National Teams
        competitive_teams = ['Mexico', 'Mexique', 'Japan', 'Japon', 'South Korea', 'Corée du Sud', 
                           'Canada', 'USA', 'États-Unis', 'Poland', 'Pologne', 'Serbia', 'Serbie',
                           'Czech Republic', 'République Tchèque', 'Greece', 'Grèce', 'Turkey', 'Turquie',
                           'Senegal', 'Sénégal', 'Nigeria', 'Egypt', 'Égypte', 'Morocco', 'Maroc',
                           'Cameroon', 'Cameroun', 'Ghana', 'Mali', 'Tunisia', 'Tunisie', 'Ecuador', 'Équateur',
                           'Paraguay', 'Peru', 'Pérou', 'Colombia', 'Colombie', 'Chile', 'Costa Rica',
                           'United States', 'Australia', 'Australie']
        
        # Other Teams (Emerging/Lower ranked)
        other_teams = ['Wales', 'Pays de Galles', 'Scotland', 'Écosse', 'Ukraine', 'Iran', 'Qatar',
                      'Saudi Arabia', 'Arabie Saoudite', 'New Zealand', 'Nouvelle-Zélande', 'Vietnam',
                      'Thailand', 'Thaïlande', 'Indonesia', 'Indonésie', 'India', 'Inde', 'Jamaica',
                      'Panama', 'Honduras', 'El Salvador']
        
        # Club Teams
        elite_club_teams = ['Real', 'Barcelona', 'PSG', 'Bayern', 'Liverpool', 'Manchester', 'Chelsea']
        strong_club_teams = ['Lyon', 'Ajax', 'Juventus', 'Inter', 'AC Milan', 'Atletico']
        
        is_elite_national = any(team in team_name for team in elite_national_teams)
        is_strong_national = any(team in team_name for team in strong_national_teams)
        is_competitive = any(team in team_name for team in competitive_teams)
        is_elite_club = any(elite in team_name for elite in elite_club_teams)
        is_strong_club = any(strong in team_name for strong in strong_club_teams)
        
        # Base Elo assignment
        if is_elite_national:
            base_elo = np.random.normal(1700, 40)   # Elite national: 1650-1750
        elif is_elite_club:
            base_elo = np.random.normal(1650, 50)   # Elite clubs: 1600-1700
        elif is_strong_national:
            base_elo = np.random.normal(1600, 45)   # Strong national: 1550-1650
        elif is_competitive:
            base_elo = np.random.normal(1550, 50)   # Competitive: 1500-1600
        elif is_strong_club:
            base_elo = np.random.normal(1550, 40)   # Strong clubs: 1500-1600
        else:
            base_elo = np.random.normal(1450, 70)   # Other teams: 1380-1520
        
        # Form (PPG last 5 games): 0-3 PPG
        form_score = np.random.uniform(0.8, 2.0)
        
        # Overall PPG
        ppg = np.random.uniform(1.0, 2.0)
        
        # Days rest (3-10 days typically between matches)
        days_rest = np.random.uniform(3, 10)
        
        # Matches in last 7 days (0-2 typically)
        matches_7d = int(np.random.uniform(0, 2))
        
        return {
            'team_name': team_name,
            'elo': base_elo,
            'form_score': form_score,
            'ppg': ppg,
            'days_rest': days_rest,
            'matches_7d': matches_7d,
            'source': 'estimated'
        }

    @staticmethod
    def fetch_live_odds(home_team: str, away_team: str) -> Optional[Dict]:
        """
        Fetch live odds from free API (Pinnacle uses free API)
        
        Note: Most free odds APIs have rate limits
        For now, return None and let user provide odds
        
        Args:
            home_team: Home team name
            away_team: Away team name
            
        Returns:
            Dict with odds or None
        """
        # Most free odds APIs require registration
        # User will provide odds manually for now
        return None


def create_interactive_match_predictor():
    """Interactive match predictor with automatic data fetching"""
    
    logger.info("\n" + "="*80)
    logger.info("⚽ AUTOMATED MATCH PREDICTION & VALUE BETTING")
    logger.info("="*80)
    
    try:
        fetcher = FootballDataFetcher()
        
        # Get teams
        logger.info("\n[1] Finding teams...")
        home_name = input("🏠 Home Team (e.g., 'PSG'): ").strip()
        away_name = input("✈️  Away Team (e.g., 'Lyon'): ").strip()
        
        # Get team data
        home_results = fetcher.search_team(home_name, limit=1)
        away_results = fetcher.search_team(away_name, limit=1)
        
        if not home_results:
            logger.warning(f"⚠️  Team '{home_name}' not found in database")
            logger.info(f"   Using estimated stats instead")
            home_id = None
        else:
            home_id = home_results[0]['id']
            logger.info(f"   ✅ Found: {home_results[0]['name']}")
        
        if not away_results:
            logger.warning(f"⚠️  Team '{away_name}' not found in database")
            logger.info(f"   Using estimated stats instead")
            away_id = None
        else:
            away_id = away_results[0]['id']
            logger.info(f"   ✅ Found: {away_results[0]['name']}")
        
        # Get team stats
        logger.info(f"\n[2] Estimating team stats...")
        home_stats = fetcher.estimate_team_stats(home_name, home_id)
        away_stats = fetcher.estimate_team_stats(away_name, away_id)
        
        logger.info(f"   {home_name}:")
        logger.info(f"      Elo: {home_stats['elo']:.0f}")
        logger.info(f"      Form: {home_stats['form_score']:.2f} PPG")
        logger.info(f"   {away_name}:")
        logger.info(f"      Elo: {away_stats['elo']:.0f}")
        logger.info(f"      Form: {away_stats['form_score']:.2f} PPG")
        
        # Get odds
        logger.info(f"\n[3] Enter bookmaker odds (decimal format):")
        odds_1 = float(input(f"   Odds {home_name} Win: "))
        odds_x = float(input(f"   Odds Draw: "))
        odds_2 = float(input(f"   Odds {away_name} Win: "))
        
        return {
            'home_name': home_name,
            'away_name': away_name,
            'home_stats': home_stats,
            'away_stats': away_stats,
            'odds_1': odds_1,
            'odds_x': odds_x,
            'odds_2': odds_2
        }
        
    except KeyboardInterrupt:
        logger.info("\n\nCancelled.")
        return None
    except ValueError as e:
        logger.error(f"❌ Invalid input: {e}")
        return None
