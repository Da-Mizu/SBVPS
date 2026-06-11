"""
Fetch real football data from football-data.org API
Fallback to mock data if API unavailable
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.logger import get_logger
from src.config import FOOTBALL_DATA_API_TOKEN
import time

logger = get_logger(__name__)

# Football-data.org API
FOOTBALL_DATA_API = "https://api.football-data.org/v4"
# Use token from config if available
HEADERS = {
    "X-Auth-Token": FOOTBALL_DATA_API_TOKEN
}

# Cache for team stats to avoid duplicate API calls
_TEAM_STATS_CACHE = {}


class FootballDataFetcher:
    """Fetch real football data from football-data.org API"""

    @staticmethod
    def search_team(team_name: str, limit: int = 5) -> List[Dict]:
        """
        Search for teams by name using football-data.org API
        Falls back to mock data if API unavailable
        
        Args:
            team_name: Team name to search
            limit: Max results to return
            
        Returns:
            List of teams with IDs and info
        """
        try:
            logger.info(f"🔍 Searching for '{team_name}' via football-data.org API...")
            
            # Try different competition endpoints
            competitions = ['PL', 'CL', 'EC', 'WC']  
            
            for comp_code in competitions:
                try:
                    url = f"{FOOTBALL_DATA_API}/competitions/{comp_code}/teams"
                    response = requests.get(url, headers=HEADERS, timeout=2)  # Reduced timeout to 2s
                    
                    if response.status_code == 200:
                        data = response.json()
                        teams = data.get('teams', [])
                        
                        # Search by name
                        results = []
                        search_lower = team_name.lower()
                        for team in teams:
                            name_lower = team.get('name', '').lower()
                            short_lower = team.get('shortName', '').lower()
                            tla_lower = team.get('tla', '').lower()
                            
                            if (search_lower in name_lower or 
                                search_lower in short_lower or
                                search_lower == tla_lower):
                                results.append({
                                    'id': team.get('id'),
                                    'name': team.get('name'),
                                    'shortName': team.get('shortName'),
                                    'tla': team.get('tla'),
                                    'crest': team.get('crest', '')
                                })
                        
                        if results:
                            logger.info(f"   ✅ Found {len(results)} team(s) via API")
                            return results[:limit]
                
                except requests.Timeout:
                    logger.debug(f"   ⏱️ API timeout for {comp_code}")
                    continue
                except Exception as e:
                    logger.debug(f"   API search failed for {comp_code}: {e}")
                    continue
            
            logger.info(f"   Falling back to mock database...")
            
        except Exception as e:
            logger.debug(f"   API Error: {e}")
            logger.info(f"   Using mock database as fallback...")
        
        # Fallback: Mock teams database
        return FootballDataFetcher._search_mock_teams(team_name, limit)

    @staticmethod
    def _search_mock_teams(team_name: str, limit: int = 5) -> List[Dict]:
        """Search in mock teams database"""
        mock_teams = {
            # Elite National Teams
            'France': {'id': 773, 'name': 'France', 'shortName': 'France', 'tla': 'FRA', 'crest': '', 'elo': 1705},
            'Brazil': {'id': 770, 'name': 'Brazil', 'shortName': 'Brazil', 'tla': 'BRA', 'crest': '', 'elo': 1700},
            'Brésil': {'id': 770, 'name': 'Brazil', 'shortName': 'Brazil', 'tla': 'BRA', 'crest': '', 'elo': 1700},
            'Argentina': {'id': 760, 'name': 'Argentina', 'shortName': 'Argentina', 'tla': 'ARG', 'crest': '', 'elo': 1695},
            'Argentine': {'id': 760, 'name': 'Argentina', 'shortName': 'Argentina', 'tla': 'ARG', 'crest': '', 'elo': 1695},
            'Germany': {'id': 759, 'name': 'Germany', 'shortName': 'Germany', 'tla': 'DEU', 'crest': '', 'elo': 1680},
            'Allemagne': {'id': 759, 'name': 'Germany', 'shortName': 'Germany', 'tla': 'DEU', 'crest': '', 'elo': 1680},
            'Spain': {'id': 808, 'name': 'Spain', 'shortName': 'Spain', 'tla': 'ESP', 'crest': '', 'elo': 1690},
            'Espagne': {'id': 808, 'name': 'Spain', 'shortName': 'Spain', 'tla': 'ESP', 'crest': '', 'elo': 1690},
            
            # Strong National Teams
            'England': {'id': 770, 'name': 'England', 'shortName': 'England', 'tla': 'ENG', 'crest': '', 'elo': 1655},
            'Angleterre': {'id': 770, 'name': 'England', 'shortName': 'England', 'tla': 'ENG', 'crest': '', 'elo': 1655},
            'Netherlands': {'id': 771, 'name': 'Netherlands', 'shortName': 'Netherlands', 'tla': 'NLD', 'crest': '', 'elo': 1645},
            'Pays-Bas': {'id': 771, 'name': 'Netherlands', 'shortName': 'Netherlands', 'tla': 'NLD', 'crest': '', 'elo': 1645},
            'Belgium': {'id': 757, 'name': 'Belgium', 'shortName': 'Belgium', 'tla': 'BEL', 'crest': '', 'elo': 1630},
            'Belgique': {'id': 757, 'name': 'Belgium', 'shortName': 'Belgium', 'tla': 'BEL', 'crest': '', 'elo': 1630},
            'Portugal': {'id': 794, 'name': 'Portugal', 'shortName': 'Portugal', 'tla': 'POR', 'crest': '', 'elo': 1620},
            'Italy': {'id': 784, 'name': 'Italy', 'shortName': 'Italy', 'tla': 'ITA', 'crest': '', 'elo': 1610},
            'Italie': {'id': 784, 'name': 'Italy', 'shortName': 'Italy', 'tla': 'ITA', 'crest': '', 'elo': 1610},
            'Uruguay': {'id': 835, 'name': 'Uruguay', 'shortName': 'Uruguay', 'tla': 'URY', 'crest': '', 'elo': 1605},
            'Croatia': {'id': 776, 'name': 'Croatia', 'shortName': 'Croatia', 'tla': 'HRV', 'crest': '', 'elo': 1600},
            'Croatie': {'id': 776, 'name': 'Croatia', 'shortName': 'Croatia', 'tla': 'HRV', 'crest': '', 'elo': 1600},
            'Switzerland': {'id': 823, 'name': 'Switzerland', 'shortName': 'Switzerland', 'tla': 'CHE', 'crest': '', 'elo': 1595},
            'Suisse': {'id': 823, 'name': 'Switzerland', 'shortName': 'Switzerland', 'tla': 'CHE', 'crest': '', 'elo': 1595},
            'Denmark': {'id': 779, 'name': 'Denmark', 'shortName': 'Denmark', 'tla': 'DNK', 'crest': '', 'elo': 1590},
            'Danemark': {'id': 779, 'name': 'Denmark', 'shortName': 'Denmark', 'tla': 'DNK', 'crest': '', 'elo': 1590},
            'Sweden': {'id': 821, 'name': 'Sweden', 'shortName': 'Sweden', 'tla': 'SWE', 'crest': '', 'elo': 1575},
            'Suède': {'id': 821, 'name': 'Sweden', 'shortName': 'Sweden', 'tla': 'SWE', 'crest': '', 'elo': 1575},
            
            # Competitive Teams (Americas)
            'Mexico': {'id': 789, 'name': 'Mexico', 'shortName': 'Mexico', 'tla': 'MEX', 'crest': '', 'elo': 1550},
            'Mexique': {'id': 789, 'name': 'Mexico', 'shortName': 'Mexico', 'tla': 'MEX', 'crest': '', 'elo': 1550},
            'Japan': {'id': 787, 'name': 'Japan', 'shortName': 'Japan', 'tla': 'JPN', 'crest': '', 'elo': 1540},
            'Japon': {'id': 787, 'name': 'Japan', 'shortName': 'Japan', 'tla': 'JPN', 'crest': '', 'elo': 1540},
            'South Korea': {'id': 790, 'name': 'South Korea', 'shortName': 'S. Korea', 'tla': 'KOR', 'crest': '', 'elo': 1535},
            'Corée du Sud': {'id': 790, 'name': 'South Korea', 'shortName': 'S. Korea', 'tla': 'KOR', 'crest': '', 'elo': 1535},
            'Canada': {'id': 761, 'name': 'Canada', 'shortName': 'Canada', 'tla': 'CAN', 'crest': '', 'elo': 1520},
            'United States': {'id': 836, 'name': 'United States', 'shortName': 'USA', 'tla': 'USA', 'crest': '', 'elo': 1535},
            'USA': {'id': 836, 'name': 'United States', 'shortName': 'USA', 'tla': 'USA', 'crest': '', 'elo': 1535},
            'États-Unis': {'id': 836, 'name': 'United States', 'shortName': 'USA', 'tla': 'USA', 'crest': '', 'elo': 1535},
            'Poland': {'id': 793, 'name': 'Poland', 'shortName': 'Poland', 'tla': 'POL', 'crest': '', 'elo': 1525},
            'Pologne': {'id': 793, 'name': 'Poland', 'shortName': 'Poland', 'tla': 'POL', 'crest': '', 'elo': 1525},
            'Ukraine': {'id': 834, 'name': 'Ukraine', 'shortName': 'Ukraine', 'tla': 'UKR', 'crest': '', 'elo': 1505},
            
            # African Teams
            'South Africa': {'id': 1672, 'name': 'South Africa', 'shortName': 'S. Africa', 'tla': 'RSA', 'crest': '', 'elo': 1480},
            'Afrique du Sud': {'id': 1672, 'name': 'South Africa', 'shortName': 'S. Africa', 'tla': 'RSA', 'crest': '', 'elo': 1480},
            'Nigeria': {'id': 791, 'name': 'Nigeria', 'shortName': 'Nigeria', 'tla': 'NGR', 'crest': '', 'elo': 1510},
            'Senegal': {'id': 809, 'name': 'Senegal', 'shortName': 'Senegal', 'tla': 'SEN', 'crest': '', 'elo': 1505},
            'Sénégal': {'id': 809, 'name': 'Senegal', 'shortName': 'Senegal', 'tla': 'SEN', 'crest': '', 'elo': 1505},
            'Egypt': {'id': 780, 'name': 'Egypt', 'shortName': 'Egypt', 'tla': 'EGY', 'crest': '', 'elo': 1495},
            'Égypte': {'id': 780, 'name': 'Egypt', 'shortName': 'Egypt', 'tla': 'EGY', 'crest': '', 'elo': 1495},
            'Morocco': {'id': 792, 'name': 'Morocco', 'shortName': 'Morocco', 'tla': 'MAR', 'crest': '', 'elo': 1490},
            'Maroc': {'id': 792, 'name': 'Morocco', 'shortName': 'Morocco', 'tla': 'MAR', 'crest': '', 'elo': 1490},
            'Cameroon': {'id': 761, 'name': 'Cameroon', 'shortName': 'Cameroon', 'tla': 'CMR', 'crest': '', 'elo': 1475},
            'Cameroun': {'id': 761, 'name': 'Cameroon', 'shortName': 'Cameroon', 'tla': 'CMR', 'crest': '', 'elo': 1475},
            'Tunisia': {'id': 833, 'name': 'Tunisia', 'shortName': 'Tunisia', 'tla': 'TUN', 'crest': '', 'elo': 1460},
            'Tunisie': {'id': 833, 'name': 'Tunisia', 'shortName': 'Tunisia', 'tla': 'TUN', 'crest': '', 'elo': 1460},
            'Ivory Coast': {'id': 784, 'name': 'Ivory Coast', 'shortName': 'Ivory Coast', 'tla': 'CIV', 'crest': '', 'elo': 1455},
            'Côte d\'Ivoire': {'id': 784, 'name': 'Ivory Coast', 'shortName': 'Ivory Coast', 'tla': 'CIV', 'crest': '', 'elo': 1455},
            'Ghana': {'id': 783, 'name': 'Ghana', 'shortName': 'Ghana', 'tla': 'GHA', 'crest': '', 'elo': 1440},
            
            # Club Teams
            'PSG': {'id': 75, 'name': 'Paris Saint-Germain', 'shortName': 'PSG', 'tla': 'PSG', 'crest': '', 'elo': 1660},
            'Lyon': {'id': 65, 'name': 'Olympique Lyonnais', 'shortName': 'Lyon', 'tla': 'OL', 'crest': '', 'elo': 1550},
            'Real Madrid': {'id': 86, 'name': 'Real Madrid', 'shortName': 'Real', 'tla': 'RMA', 'crest': '', 'elo': 1700},
            'Barcelona': {'id': 81, 'name': 'FC Barcelona', 'shortName': 'Barcelona', 'tla': 'FCB', 'crest': '', 'elo': 1680},
        }
        
        # Search in mock data
        results = []
        search_lower = team_name.lower()
        for key, team_data in mock_teams.items():
            if search_lower in key.lower() or search_lower in team_data['name'].lower():
                # Remove elo from result (it's internal)
                result = {k: v for k, v in team_data.items() if k != 'elo'}
                results.append(result)
        
        return results[:limit]

    @staticmethod
    def estimate_team_stats(team_name: str, team_id: Optional[int] = None) -> Dict:
        """
        Get team stats from mock database (fixed Elo values, not random)
        
        Args:
            team_name: Team name
            team_id: Optional team ID
            
        Returns:
            Dict with team stats
        """
        # Check cache first
        if team_name in _TEAM_STATS_CACHE:
            return _TEAM_STATS_CACHE[team_name]
        
        logger.info(f"   📊 Getting stats for {team_name}...")
        
        # Fixed Elo database (based on FIFA/world rankings)
        elo_database = {
            # Elite National Teams
            'France': 1705, 'Brésil': 1700, 'Brazil': 1700,
            'Argentina': 1695, 'Argentine': 1695,
            'Germany': 1680, 'Allemagne': 1680,
            'Spain': 1690, 'Espagne': 1690,
            
            # Strong National Teams
            'England': 1655, 'Angleterre': 1655,
            'Netherlands': 1645, 'Pays-Bas': 1645,
            'Belgium': 1630, 'Belgique': 1630,
            'Portugal': 1620,
            'Italy': 1610, 'Italie': 1610,
            'Uruguay': 1605,
            'Croatia': 1600, 'Croatie': 1600,
            'Switzerland': 1595, 'Suisse': 1595,
            'Denmark': 1590, 'Danemark': 1590,
            'Sweden': 1575, 'Suède': 1575,
            
            # Competitive Teams (Americas & Asia)
            'Mexico': 1550, 'Mexique': 1550,
            'Japan': 1540, 'Japon': 1540,
            'South Korea': 1535, 'Corée du Sud': 1535,
            'United States': 1535, 'USA': 1535, 'États-Unis': 1535,
            'Poland': 1525, 'Pologne': 1525,
            'Ukraine': 1505,
            
            # African Teams
            'South Africa': 1480, 'Afrique du Sud': 1480,
            'Nigeria': 1510,
            'Senegal': 1505, 'Sénégal': 1505,
            'Egypt': 1495, 'Égypte': 1495,
            'Morocco': 1490, 'Maroc': 1490,
            'Cameroon': 1475, 'Cameroun': 1475,
            'Tunisia': 1460, 'Tunisie': 1460,
            'Ivory Coast': 1455, 'Côte d\'Ivoire': 1455,
            'Ghana': 1440,
            
            # Club Teams
            'PSG': 1660,
            'Real Madrid': 1700, 'Real': 1700,
            'Barcelona': 1680,
            'Lyon': 1550,
        }
        
        # Get Elo (default to 1500 if not found)
        elo = elo_database.get(team_name, 1500)
        
        stats = {
            'team_name': team_name,
            'elo': elo,
            'form_score': 1.4,  # Fixed form (neutral)
            'ppg': 1.5,         # Fixed PPG (neutral)
            'days_rest': 5.0,   # Fixed rest (neutral)
            'matches_7d': 0,    # Fixed matches (neutral)
        }
        
        # Cache it
        _TEAM_STATS_CACHE[team_name] = stats
        
        logger.info(f"      Elo: {elo}")
        
        return stats


def create_interactive_match_predictor() -> Optional[Dict]:
    """
    Interactive CLI for entering match info
    """
    logger.info("\n" + "=" * 80)
    logger.info("⚽ MATCH PREDICTOR - Enter Match Details")
    logger.info("=" * 80)
    
    fetcher = FootballDataFetcher()
    
    # Get teams
    logger.info("\n[1] Finding teams...")
    home_name = input("🏠 Home Team (e.g., 'PSG'): ").strip()
    away_name = input("✈️  Away Team (e.g., 'Lyon'): ").strip()
    
    if not home_name or not away_name:
        logger.error("❌ Team names required")
        return None
    
    # Get team data
    home_results = fetcher.search_team(home_name, limit=1)
    away_results = fetcher.search_team(away_name, limit=1)
    
    if home_results:
        logger.info(f"   ✅ Found: {home_results[0]['name']}")
    else:
        logger.warning(f"⚠️  Team '{home_name}' not found - using estimates")
    
    if away_results:
        logger.info(f"   ✅ Found: {away_results[0]['name']}")
    else:
        logger.warning(f"⚠️  Team '{away_name}' not found - using estimates")
    
    # Get team stats
    logger.info(f"\n[2] Team Stats:")
    home_stats = fetcher.estimate_team_stats(home_name)
    away_stats = fetcher.estimate_team_stats(away_name)
    
    logger.info(f"   {home_name}:")
    logger.info(f"      Elo: {home_stats['elo']}")
    logger.info(f"   {away_name}:")
    logger.info(f"      Elo: {away_stats['elo']}")
    
    # Get odds
    logger.info(f"\n[3] Enter Betting Odds:")
    try:
        odds_1 = float(input("   Odds Home (1): "))
        odds_x = float(input("   Odds Draw (X): "))
        odds_2 = float(input("   Odds Away (2): "))
    except ValueError:
        logger.error("❌ Invalid odds format")
        return None
    
    return {
        'home_name': home_name,
        'away_name': away_name,
        'home_stats': home_stats,
        'away_stats': away_stats,
        'odds_1': odds_1,
        'odds_x': odds_x,
        'odds_2': odds_2,
    }
