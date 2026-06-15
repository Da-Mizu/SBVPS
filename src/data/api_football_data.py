"""
API Fetcher for football-data.org
Récupère les données de matchs depuis l'API football-data.org
"""
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import FOOTBALL_DATA_API_TOKEN, FOOTBALL_DATA_API_BASE_URL, WORLD_CUP_COMPETITION_ID
from src.logger import get_logger

logger = get_logger(__name__)


class FootballDataAPIFetcher:
    """
    Récupère les données depuis football-data.org API
    Priorité: API > Base de données
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize API fetcher
        
        Args:
            api_token: Token API de football-data.org
        """
        self.api_token = api_token or FOOTBALL_DATA_API_TOKEN
        self.base_url = FOOTBALL_DATA_API_BASE_URL
        self.headers = {}
        
        if self.api_token:
            self.headers = {"X-Auth-Token": self.api_token}
            logger.info("✅ API token configuré pour football-data.org")
        else:
            logger.warning("⚠️  Pas de token API. Utilisation limitée (API rate limited)")
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Effectue une requête HTTP à l'API
        
        Args:
            endpoint: Chemin de l'endpoint
            params: Paramètres de la requête
            
        Returns:
            Réponse JSON ou None si erreur
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("⚠️  Rate limit atteint. Réessayez plus tard.")
                return None
            elif response.status_code == 404:
                logger.warning(f"⚠️  Endpoint non trouvé: {endpoint}")
                return None
            else:
                logger.error(f"❌ Erreur API {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout lors de la requête API")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur requête API: {e}")
            return None
    
    def get_world_cup_2026_matches(self) -> Optional[pd.DataFrame]:
        """
        Récupère les matchs de la Coupe du Monde 2026
        
        Returns:
            DataFrame avec les matchs ou None si erreur
        """
        logger.info("🌍 Récupération des matchs de la Coupe du Monde 2026...")
        
        data = self._make_request(f"/competitions/{WORLD_CUP_COMPETITION_ID}/matches")
        
        if not data or "matches" not in data:
            logger.warning("⚠️  Impossible de récupérer les matchs World Cup depuis l'API")
            return None
        
        matches = []
        for match in data["matches"]:
            try:
                matches.append({
                    "match_id": match.get("id"),
                    "match_date": match.get("utcDate"),
                    "home_team": match.get("homeTeam", {}).get("name"),
                    "home_team_id": match.get("homeTeam", {}).get("id"),
                    "away_team": match.get("awayTeam", {}).get("name"),
                    "away_team_id": match.get("awayTeam", {}).get("id"),
                    "home_goals": match.get("score", {}).get("fullTime", {}).get("home"),
                    "away_goals": match.get("score", {}).get("fullTime", {}).get("away"),
                    "status": match.get("status"),
                    "league": "World Cup",
                    "season": 2026,
                    "home_odds": None,
                    "draw_odds": None,
                    "away_odds": None,
                })
            except Exception as e:
                logger.error(f"❌ Erreur parsing match: {e}")
                continue
        
        logger.info(f"✅ {len(matches)} matchs World Cup récupérés depuis l'API")
        return pd.DataFrame(matches) if matches else None
    
    def get_competition_matches(self, competition_code: str, season: int = 2025) -> Optional[pd.DataFrame]:
        """
        Récupère les matchs d'une compétition
        
        Args:
            competition_code: Code de la compétition (ex: 'FL1' pour Ligue 1)
            season: Saison (ex: 2025)
            
        Returns:
            DataFrame avec les matchs
        """
        logger.info(f"⚽ Récupération des matchs {competition_code} saison {season}...")
        
        endpoint = f"/competitions/{competition_code}/matches"
        params = {"season": season}
        
        data = self._make_request(endpoint, params)
        
        if not data or "matches" not in data:
            logger.warning(f"⚠️  Impossible de récupérer les matchs depuis l'API")
            return None
        
        matches = []
        for match in data["matches"]:
            try:
                matches.append({
                    "match_id": match.get("id"),
                    "match_date": match.get("utcDate"),
                    "home_team": match.get("homeTeam", {}).get("name"),
                    "home_team_id": match.get("homeTeam", {}).get("id"),
                    "away_team": match.get("awayTeam", {}).get("name"),
                    "away_team_id": match.get("awayTeam", {}).get("id"),
                    "home_goals": match.get("score", {}).get("fullTime", {}).get("home"),
                    "away_goals": match.get("score", {}).get("fullTime", {}).get("away"),
                    "status": match.get("status"),
                    "league": data.get("competition", {}).get("name", "Unknown"),
                    "season": season,
                })
            except Exception as e:
                logger.error(f"❌ Erreur parsing match: {e}")
                continue
        
        logger.info(f"✅ {len(matches)} matchs récupérés depuis l'API")
        return pd.DataFrame(matches) if matches else None
    
    def get_team_standings(self, competition_code: str, season: int = 2025) -> Optional[pd.DataFrame]:
        """
        Récupère le classement d'une compétition
        
        Args:
            competition_code: Code de la compétition
            season: Saison
            
        Returns:
            DataFrame avec le classement
        """
        logger.info(f"🏆 Récupération du classement {competition_code}...")
        
        endpoint = f"/competitions/{competition_code}/standings"
        params = {"season": season}
        
        data = self._make_request(endpoint, params)
        
        if not data or "standings" not in data:
            logger.warning("⚠️  Impossible de récupérer le classement depuis l'API")
            return None
        
        standings = []
        for standing_group in data["standings"]:
            for team in standing_group.get("table", []):
                standings.append({
                    "rank": team.get("position"),
                    "team_name": team.get("team", {}).get("name"),
                    "team_id": team.get("team", {}).get("id"),
                    "played": team.get("playedGames"),
                    "won": team.get("won"),
                    "draw": team.get("draw"),
                    "lost": team.get("lost"),
                    "points": team.get("points"),
                    "goals_for": team.get("goalsDiff"),
                })
        
        logger.info(f"✅ Classement récupéré: {len(standings)} équipes")
        return pd.DataFrame(standings) if standings else None
    
    def api_is_available(self) -> bool:
        """Vérifie si l'API est accessible"""
        if not self.api_token:
            logger.warning("⚠️  Pas de token API configuré")
            return False
        
        data = self._make_request("/competitions")
        return data is not None
    
    def get_world_cup_standings(self) -> Optional[pd.DataFrame]:
        """Récupère le classement de la Coupe du Monde 2026"""
        return self.get_team_standings("WC", 2026)


def fetch_world_cup_data_from_api(api_token: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Récupère les données World Cup depuis l'API
    
    Args:
        api_token: Token API (optionnel, utilise .env par défaut)
        
    Returns:
        Tuple de (matches_df, standings_df) ou (None, None) si erreur
    """
    fetcher = FootballDataAPIFetcher(api_token)
    
    if not fetcher.api_is_available():
        logger.error("❌ API non accessible")
        return None, None
    
    matches_df = fetcher.get_world_cup_2026_matches()
    standings_df = fetcher.get_world_cup_standings()
    
    return matches_df, standings_df
