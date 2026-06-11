"""
Générateur de données fictives réalistes pour SBVPS
Simule des matchs de Ligue 1 avec des résultats basés sur des paramètres réalistes
"""
import random
from datetime import datetime, timedelta
import numpy as np
from src.logger import get_logger
from src.config import FAKE_DATA_CONFIG

logger = get_logger(__name__)


class FakeDataCollector:
    """Génère des données fictives réalistes"""

    # Équipes réelles de Ligue 1 (saison 2025-26 fictive)
    LIGUE_1_TEAMS = [
        "Paris SG", "Marseille", "Lyon", "Toulouse", "Nice",
        "Bordeaux", "Lens", "Monaco", "Nantes", "Strasbourg",
        "Rennes", "Lille", "Brest", "Reims", "Angers",
        "Montpellier", "Le Havre", "Lorient", "Saint-Étienne", "Auxerre"
    ]

    # Autres ligues
    PREMIER_LEAGUE_TEAMS = [
        "Man City", "Liverpool", "Chelsea", "Arsenal", "Man United",
        "Tottenham", "Newcastle", "Brighton", "Aston Villa", "West Ham",
        "Fulham", "Brentford", "Everton", "Crystal Palace", "Ipswich",
        "Bournemouth", "Nottingham", "Luton", "Sheffield Utd", "Wolves"
    ]

    LA_LIGA_TEAMS = [
        "Real Madrid", "Barcelona", "Atletico Madrid", "Real Sociedad", "Valencia",
        "Sevilla", "Betis", "Villarreal", "Athletic Bilbao", "Osasuna",
        "Getafe", "Celta Vigo", "Alaves", "Rayo Vallecano", "Las Palmas",
        "Cadiz", "Granada", "Mallorca", "Real Valladolid", "Espanyol"
    ]

    SERIE_A_TEAMS = [
        "Inter Milan", "AC Milan", "Juventus", "AS Roma", "Lazio",
        "Napoli", "Fiorentina", "Atalanta", "Torino", "Genoa",
        "Cagliari", "Cremonese", "Sassuolo", "Lecce", "Sampdoria",
        "Monza", "Salernitana", "Hellas Verona", "Como", "Frosinone"
    ]

    def __init__(self):
        """Initialise le collecteur"""
        self.teams_by_league = {
            "Ligue 1": self.LIGUE_1_TEAMS,
            "Premier League": self.PREMIER_LEAGUE_TEAMS,
            "La Liga": self.LA_LIGA_TEAMS,
            "Serie A": self.SERIE_A_TEAMS,
        }
        self.elo_ratings = {}  # Stores Elo ratings for teams

    def generate_teams(self, league="Ligue 1"):
        """
        Génère la liste des équipes
        
        Args:
            league: Nom de la ligue
            
        Returns:
            Liste de dicts {name, league, country, founded_year}
        """
        teams = self.teams_by_league.get(league, self.LIGUE_1_TEAMS)
        
        teams_list = [
            {
                "name": team,
                "league": league,
                "country": self._get_country(league),
                "founded_year": random.randint(1880, 2000)
            }
            for team in teams
        ]

        logger.info(f"✅ {len(teams_list)} équipes générées pour {league}")
        return teams_list

    def _get_country(self, league):
        """Récupère le pays d'une ligue"""
        countries = {
            "Ligue 1": "France",
            "Premier League": "Angleterre",
            "La Liga": "Espagne",
            "Serie A": "Italie"
        }
        return countries.get(league, "Inconnue")

    def generate_matches(self, league="Ligue 1", season=2025, start_date="2025-08-01", num_matches=None):
        """
        Génère une saison de matchs réaliste
        
        Args:
            league: Nom de la ligue
            season: Année de la saison
            start_date: Date de début de la saison
            num_matches: Nombre de matchs à générer (par défaut: 380 pour 20 équipes)
            
        Returns:
            Liste de dicts {league, season, match_date, home_team, away_team, ...}
        """
        teams = self.teams_by_league.get(league, self.LIGUE_1_TEAMS)
        
        if num_matches is None:
            num_matches = len(teams) * (len(teams) - 1)  # Round-robin complet (aller-retour)

        # Initialiser les Elo ratings
        self._initialize_elo(teams)

        # Générer le calendrier (round-robin)
        matches = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        match_date = start

        # Créer les matchs (2 journées par semaine)
        all_matches = []
        for round_num in range(len(teams) - 1):
            round_matches = self._generate_round(teams, round_num)
            all_matches.extend(round_matches)

        # Trier et limiter
        all_matches = all_matches[:num_matches]

        # Assigner les dates (2 matchs par semaine en moyenne)
        matches_per_week = max(1, len(all_matches) // 17)  # ~17 semaines par saison
        
        for idx, match_pair in enumerate(all_matches):
            # Alterner entre mercredi et samedi
            weeks_passed = idx // matches_per_week
            if idx % 2 == 0:
                match_date = start + timedelta(weeks=weeks_passed, days=2)  # Mercredi
            else:
                match_date = start + timedelta(weeks=weeks_passed, days=5)  # Samedi

            # Générer les résultats
            home_goals, away_goals = self._generate_match_result(match_pair[0], match_pair[1])
            result = self._determine_result(home_goals, away_goals)

            matches.append({
                "league": league,
                "season": season,
                "match_date": match_date.strftime("%Y-%m-%d"),
                "match_time": f"{random.randint(15, 21)}:00",
                "home_team": match_pair[0],
                "away_team": match_pair[1],
                "home_goals": home_goals,
                "away_goals": away_goals,
                "result": result,
                "status": "played",
                "attendance": random.randint(15000, 80000)
            })

        logger.info(f"✅ {len(matches)} matchs générés pour {league} {season}")
        return matches

    def _initialize_elo(self, teams):
        """Initialise les ratings Elo avec une petite variation"""
        base_elo = 1500
        variation = 300

        for team in teams:
            self.elo_ratings[team] = base_elo + random.randint(-variation//2, variation//2)

    def _generate_round(self, teams, round_num):
        """Génère une journée de matchs (round-robin)"""
        matches = []
        n = len(teams)
        
        # Algorithme round-robin
        if round_num == 0:
            current = teams[:]
        else:
            # Rotation
            current = [teams[0]] + teams[n - round_num:] + teams[1:n - round_num]

        for i in range(n // 2):
            home = current[i]
            away = current[n - 1 - i]
            matches.append((home, away))

        return matches

    def _generate_match_result(self, home_team, away_team):
        """
        Génère un résultat de match réaliste basé sur les Elo ratings
        
        Returns:
            Tuple (home_goals, away_goals)
        """
        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)

        # Avantage domicile
        home_advantage = 1.1
        home_rating = home_elo * home_advantage

        # Probabilités basées sur Elo
        total_rating = home_rating + away_elo
        home_win_prob = home_rating / total_rating
        
        # Distribution des buts basée sur les probabilités (Poisson-like)
        avg_home_goals = 1.5 * home_win_prob + 0.5 * (1 - home_win_prob)
        avg_away_goals = 1.5 * (1 - home_win_prob) + 0.5 * home_win_prob

        home_goals = np.random.poisson(avg_home_goals)
        away_goals = np.random.poisson(avg_away_goals)

        # Update Elo ratings après le match
        self._update_elo(home_team, away_team, home_goals, away_goals)

        return home_goals, away_goals

    def _update_elo(self, home_team, away_team, home_goals, away_goals):
        """Mets à jour les ratings Elo après un match"""
        k_factor = 32

        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)

        # Score expectancy
        home_expected = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        away_expected = 1 / (1 + 10 ** ((home_elo - away_elo) / 400))

        # Résultat (1 = win, 0.5 = draw, 0 = loss)
        if home_goals > away_goals:
            home_result, away_result = 1, 0
        elif home_goals < away_goals:
            home_result, away_result = 0, 1
        else:
            home_result, away_result = 0.5, 0.5

        # Nouvelle Elo
        self.elo_ratings[home_team] = home_elo + k_factor * (home_result - home_expected)
        self.elo_ratings[away_team] = away_elo + k_factor * (away_result - away_expected)

    def _determine_result(self, home_goals, away_goals):
        """Détermine le résultat (1, X, 2)"""
        if home_goals > away_goals:
            return "1"
        elif home_goals < away_goals:
            return "2"
        else:
            return "X"

    def generate_odds(self, matches):
        """
        Génère des cotes réalistes pour les matchs
        
        Args:
            matches: Liste des matchs
            
        Returns:
            Liste de dicts {match_id, bookmaker, odd_1, odd_x, odd_2, timestamp}
        """
        odds_list = []
        bookmakers = ["Betfair", "Pinnacle", "Bet365", "William Hill"]

        for idx, match in enumerate(matches):
            home_goals = match["home_goals"]
            away_goals = match["away_goals"]

            # Calculer les probabilités réelles
            if home_goals > away_goals:
                true_prob_1 = 0.45 + random.uniform(0.1, 0.2)
                true_prob_x = 0.05 + random.uniform(0.0, 0.05)
                true_prob_2 = 0.30 + random.uniform(0.0, 0.15)
            elif home_goals < away_goals:
                true_prob_1 = 0.20 + random.uniform(0.0, 0.15)
                true_prob_x = 0.05 + random.uniform(0.0, 0.05)
                true_prob_2 = 0.50 + random.uniform(0.05, 0.2)
            else:
                true_prob_1 = 0.35 + random.uniform(0.0, 0.1)
                true_prob_x = 0.30 + random.uniform(0.1, 0.2)
                true_prob_2 = 0.35 + random.uniform(0.0, 0.1)

            # Normaliser
            total = true_prob_1 + true_prob_x + true_prob_2
            true_prob_1 /= total
            true_prob_x /= total
            true_prob_2 /= total

            # Convertir en cotes (1 / probabilité) avec margin du bookmaker
            margin = random.uniform(1.02, 1.06)  # 2-6% margin
            odd_1 = (1 / true_prob_1) * margin
            odd_x = (1 / true_prob_x) * margin
            odd_2 = (1 / true_prob_2) * margin

            # Ajouter de la variation entre les bookmakers
            for bookmaker in bookmakers:
                odds_list.append({
                    "match_id": idx + 1,
                    "bookmaker": bookmaker,
                    "odd_1": round(odd_1 + random.uniform(-0.1, 0.1), 2),
                    "odd_x": round(odd_x + random.uniform(-0.1, 0.1), 2),
                    "odd_2": round(odd_2 + random.uniform(-0.1, 0.1), 2),
                    "timestamp": match["match_date"]
                })

        logger.info(f"✅ {len(odds_list)} cotes générées pour {len(matches)} matchs")
        return odds_list
