"""
Feature Engineering pour SBVPS
Calcule les indicateurs prédictifs à partir des données brutes
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.logger import get_logger

logger = get_logger(__name__)


class FeatureEngineer:
    """Calcule les features pour le ML"""

    def __init__(self, db, elo_k_factor=32, elo_initial=1500):
        """
        Initialize Feature Engineer
        
        Args:
            db: Instance Database
            elo_k_factor: K-factor pour calcul Elo
            elo_initial: Rating Elo initial
        """
        self.db = db
        self.elo_k_factor = elo_k_factor
        self.elo_initial = elo_initial
        self.team_elo_history = {}

    def calculate_all_features(self, league="Ligue 1", season=2025):
        """
        Calcule tous les features pour une ligue et saison
        
        Args:
            league: Nom de la ligue
            season: Année de la saison
            
        Returns:
            DataFrame avec toutes les features
        """
        logger.info(f"🔧 Calcul de tous les features pour {league} {season}...")
        
        # Charger les matchs
        matches_df = self.db.get_matches(league=league, season=season)
        
        if len(matches_df) == 0:
            logger.warning(f"Aucun match trouvé pour {league} {season}")
            return pd.DataFrame()
        
        # Trier par date
        matches_df = matches_df.sort_values('match_date').reset_index(drop=True)
        
        # Initialiser les features
        features_list = []
        
        # Initialiser Elo ratings
        self._initialize_elo_ratings(matches_df)
        
        # Calculer les features pour chaque match
        for idx, match in matches_df.iterrows():
            match_id = match['match_id']
            home_team_id = match['home_team_id']
            away_team_id = match['away_team_id']
            match_date = match['match_date']
            
            features = {
                'match_id': match_id,
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'match_date': match_date,
            }
            
            # Avant le match : calculer les features
            features.update(self.calculate_features_before_match(
                home_team_id, away_team_id, match_date, matches_df[:idx]
            ))
            
            # Après le match : update Elo et ajouter résultat
            home_goals = match['home_goals']
            away_goals = match['away_goals']
            result = match['result']
            
            features['home_goals'] = home_goals
            features['away_goals'] = away_goals
            features['result'] = result
            
            # Update Elo après le match
            self._update_elo_after_match(home_team_id, away_team_id, home_goals, away_goals)
            
            features_list.append(features)
        
        features_df = pd.DataFrame(features_list)
        logger.info(f"✅ {len(features_df)} matchs traités")
        
        return features_df

    def calculate_features_before_match(self, home_team_id, away_team_id, match_date, previous_matches):
        """
        Calcule les features AVANT un match
        
        Args:
            home_team_id: ID équipe domicile
            away_team_id: ID équipe extérieur
            match_date: Date du match
            previous_matches: DataFrame des matchs précédents
            
        Returns:
            Dict avec toutes les features
        """
        features = {}
        
        # ELO Ratings
        home_elo = self.team_elo_history.get(home_team_id, self.elo_initial)
        away_elo = self.team_elo_history.get(away_team_id, self.elo_initial)
        
        features['home_elo'] = home_elo
        features['away_elo'] = away_elo
        features['elo_diff'] = home_elo - away_elo
        
        # Expected Win Probability (from Elo)
        features['home_exp_win_prob'] = self._calculate_elo_win_probability(home_elo, away_elo)
        features['away_exp_win_prob'] = 1 - features['home_exp_win_prob']
        
        # Form Score (derniers matchs)
        home_form = self.calculate_form_score(home_team_id, match_date, previous_matches, matches_back=5)
        away_form = self.calculate_form_score(away_team_id, match_date, previous_matches, matches_back=5)
        
        features['home_form_5'] = home_form['ppg']
        features['away_form_5'] = away_form['ppg']
        features['home_wins_5'] = home_form['wins']
        features['away_wins_5'] = away_form['wins']
        features['home_draws_5'] = home_form['draws']
        features['away_draws_5'] = away_form['draws']
        
        # Home Advantage
        home_advantage_effect = self.calculate_home_advantage(home_team_id, match_date, previous_matches)
        features['home_advantage'] = home_advantage_effect
        
        # Fatigue (jours depuis dernier match)
        home_days_rest = self.calculate_days_rest(home_team_id, match_date, previous_matches)
        away_days_rest = self.calculate_days_rest(away_team_id, match_date, previous_matches)
        
        features['home_days_rest'] = home_days_rest
        features['away_days_rest'] = away_days_rest
        
        # Matches joués récemment (fatigue cumulée)
        home_matches_7 = self.count_matches_in_period(home_team_id, match_date, previous_matches, days=7)
        away_matches_7 = self.count_matches_in_period(away_team_id, match_date, previous_matches, days=7)
        
        features['home_matches_7'] = home_matches_7
        features['away_matches_7'] = away_matches_7
        
        # PPG (Points Per Game) historique
        home_ppg_all = self.calculate_form_score(home_team_id, match_date, previous_matches, matches_back=100)
        away_ppg_all = self.calculate_form_score(away_team_id, match_date, previous_matches, matches_back=100)
        
        features['home_ppg_all'] = home_ppg_all['ppg']
        features['away_ppg_all'] = away_ppg_all['ppg']
        
        # Home/Away split
        home_home_ppg = self.calculate_home_away_ppg(home_team_id, match_date, previous_matches, home=True)
        home_away_ppg = self.calculate_home_away_ppg(home_team_id, match_date, previous_matches, home=False)
        away_home_ppg = self.calculate_home_away_ppg(away_team_id, match_date, previous_matches, home=True)
        away_away_ppg = self.calculate_home_away_ppg(away_team_id, match_date, previous_matches, home=False)
        
        features['home_home_ppg'] = home_home_ppg
        features['home_away_ppg'] = home_away_ppg
        features['away_home_ppg'] = away_home_ppg
        features['away_away_ppg'] = away_away_ppg
        
        return features

    def calculate_form_score(self, team_id, match_date, previous_matches, matches_back=5):
        """
        Calcule le score de forme (derniers N matchs)
        
        Returns:
            Dict {ppg, wins, draws, losses, matches}
        """
        # Filtrer les matchs de cette équipe avant la date
        team_matches = previous_matches[
            ((previous_matches['home_team_id'] == team_id) | 
             (previous_matches['away_team_id'] == team_id)) &
            (previous_matches['match_date'] < match_date)
        ].copy()
        
        if len(team_matches) == 0:
            return {'ppg': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'matches': 0}
        
        # Prendre les derniers N matchs
        team_matches = team_matches.tail(matches_back)
        
        points = 0
        wins = draws = losses = 0
        
        for _, match in team_matches.iterrows():
            is_home = match['home_team_id'] == team_id
            result = match['result']
            
            if is_home:
                if result == '1':
                    points += 3
                    wins += 1
                elif result == 'X':
                    points += 1
                    draws += 1
                else:
                    losses += 1
            else:
                if result == '2':
                    points += 3
                    wins += 1
                elif result == 'X':
                    points += 1
                    draws += 1
                else:
                    losses += 1
        
        matches = len(team_matches)
        ppg = points / matches if matches > 0 else 0
        
        return {
            'ppg': ppg,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'matches': matches
        }

    def calculate_home_advantage(self, team_id, match_date, previous_matches):
        """
        Calcule l'avantage domicile (différence PPG domicile vs extérieur)
        """
        home_ppg = self.calculate_home_away_ppg(team_id, match_date, previous_matches, home=True)
        away_ppg = self.calculate_home_away_ppg(team_id, match_date, previous_matches, home=False)
        
        return home_ppg - away_ppg if (home_ppg + away_ppg) > 0 else 0.4  # Default 0.4 PPG

    def calculate_home_away_ppg(self, team_id, match_date, previous_matches, home=True):
        """
        Calcule PPG à domicile ou en extérieur
        """
        if home:
            team_matches = previous_matches[
                (previous_matches['home_team_id'] == team_id) &
                (previous_matches['match_date'] < match_date)
            ].copy()
            result_key = '1'  # Home win
        else:
            team_matches = previous_matches[
                (previous_matches['away_team_id'] == team_id) &
                (previous_matches['match_date'] < match_date)
            ].copy()
            result_key = '2'  # Away win
        
        if len(team_matches) == 0:
            return 1.5 if home else 1.0  # Defaults
        
        points = 0
        for _, match in team_matches.iterrows():
            result = match['result']
            if result == result_key:
                points += 3
            elif result == 'X':
                points += 1
        
        return points / len(team_matches)

    def calculate_days_rest(self, team_id, match_date, previous_matches):
        """
        Calcule le nombre de jours depuis le dernier match
        """
        team_matches = previous_matches[
            ((previous_matches['home_team_id'] == team_id) | 
             (previous_matches['away_team_id'] == team_id)) &
            (previous_matches['match_date'] < match_date)
        ].copy()
        
        if len(team_matches) == 0:
            return 365  # Début de saison
        
        last_match_date = pd.to_datetime(team_matches.iloc[-1]['match_date'])
        current_date = pd.to_datetime(match_date)
        
        days_rest = (current_date - last_match_date).days
        return days_rest

    def count_matches_in_period(self, team_id, match_date, previous_matches, days=7):
        """
        Compte le nombre de matchs dans les N derniers jours
        """
        cutoff_date = pd.to_datetime(match_date) - timedelta(days=days)
        
        team_matches = previous_matches[
            ((previous_matches['home_team_id'] == team_id) | 
             (previous_matches['away_team_id'] == team_id)) &
            (pd.to_datetime(previous_matches['match_date']) >= cutoff_date) &
            (previous_matches['match_date'] < match_date)
        ]
        
        return len(team_matches)

    def _initialize_elo_ratings(self, matches_df):
        """Initialise les ratings Elo pour toutes les équipes"""
        all_team_ids = set(matches_df['home_team_id'].unique()) | set(matches_df['away_team_id'].unique())
        
        for team_id in all_team_ids:
            self.team_elo_history[team_id] = self.elo_initial

    def _calculate_elo_win_probability(self, elo1, elo2):
        """Calcule la probabilité de victoire basée sur Elo"""
        return 1 / (1 + 10 ** ((elo2 - elo1) / 400))

    def _update_elo_after_match(self, home_team_id, away_team_id, home_goals, away_goals):
        """Met à jour les Elo ratings après un match"""
        home_elo = self.team_elo_history.get(home_team_id, self.elo_initial)
        away_elo = self.team_elo_history.get(away_team_id, self.elo_initial)
        
        # Avantage domicile
        home_elo_adjusted = home_elo + 50  # Boost temporaire pour calcul
        
        # Expected probabilities
        home_expected = self._calculate_elo_win_probability(home_elo_adjusted, away_elo)
        away_expected = 1 - home_expected
        
        # Résultat
        if home_goals > away_goals:
            home_result, away_result = 1, 0
        elif home_goals < away_goals:
            home_result, away_result = 0, 1
        else:
            home_result, away_result = 0.5, 0.5
        
        # Nouvelles Elo
        self.team_elo_history[home_team_id] = home_elo + self.elo_k_factor * (home_result - home_expected)
        self.team_elo_history[away_team_id] = away_elo + self.elo_k_factor * (away_result - away_expected)
