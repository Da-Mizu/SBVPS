"""
Gestion de la base de données SQLite pour SBVPS
"""
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
from src.config import DB_PATH
from src.logger import get_logger

logger = get_logger(__name__)


class Database:
    """Interface SQLite pour stocker et récupérer les données"""

    def __init__(self, db_path=DB_PATH):
        """
        Initialize database connection
        
        Args:
            db_path: Chemin vers le fichier SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None

    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()
            logger.info(f"✅ Connecté à la base de données : {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"❌ Erreur de connexion : {e}")
            raise

    def disconnect(self):
        """Ferme la connexion"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Déconnecté de la base de données")

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def create_tables(self):
        """Crée toutes les tables nécessaires"""
        if not self.conn:
            self.connect()

        try:
            # Table des équipes
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    league TEXT NOT NULL,
                    country TEXT,
                    founded_year INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table des matchs
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    league TEXT NOT NULL,
                    season INTEGER NOT NULL,
                    match_date TEXT NOT NULL,
                    home_team_id INTEGER NOT NULL,
                    away_team_id INTEGER NOT NULL,
                    home_goals INTEGER,
                    away_goals INTEGER,
                    result TEXT,  -- '1' (victoire domicile), 'X' (nul), '2' (victoire extérieur)
                    status TEXT DEFAULT 'scheduled',  -- 'scheduled', 'played', 'cancelled'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                    FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
                    UNIQUE(league, season, match_date, home_team_id, away_team_id)
                )
            """)

            # Table des cotes des bookmakers
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS odds (
                    odd_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    bookmaker TEXT NOT NULL,  -- 'betfair', 'pinnacle', 'bet365', etc.
                    odd_1 REAL NOT NULL,  -- Cote victoire domicile
                    odd_x REAL NOT NULL,  -- Cote nul
                    odd_2 REAL NOT NULL,  -- Cote victoire extérieur
                    timestamp TEXT NOT NULL,  -- Quand les cotes ont été enregistrées
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches(match_id),
                    UNIQUE(match_id, bookmaker, timestamp)
                )
            """)

            # Table des prédictions
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    model_version TEXT NOT NULL,
                    prob_1 REAL NOT NULL,  -- Probabilité victoire domicile
                    prob_x REAL NOT NULL,  -- Probabilité nul
                    prob_2 REAL NOT NULL,  -- Probabilité victoire extérieur
                    predicted_result TEXT,  -- '1', 'X', '2'
                    confidence REAL,  -- Confiance (0-1)
                    is_value BOOLEAN,  -- Y a-t-il de la value?
                    value_odds TEXT,  -- Quelle cote offre de la value
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches(match_id)
                )
            """)

            # Table des backtests
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtests (
                    backtest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_version TEXT NOT NULL,
                    league TEXT,
                    season INTEGER,
                    start_date TEXT,
                    end_date TEXT,
                    total_matches_played INTEGER,
                    value_bets_found INTEGER,
                    winning_bets INTEGER,
                    losing_bets INTEGER,
                    total_stakes REAL,
                    total_returns REAL,
                    roi REAL,  -- Return On Investment (%)
                    hit_rate REAL,  -- % de bets gagnants
                    avg_odds REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table des features (Feature Engineering)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS features (
                    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id INTEGER NOT NULL,
                    home_team_id INTEGER NOT NULL,
                    away_team_id INTEGER NOT NULL,
                    match_date TEXT NOT NULL,
                    
                    -- Elo Ratings
                    home_elo REAL,
                    away_elo REAL,
                    elo_diff REAL,
                    home_exp_win_prob REAL,
                    away_exp_win_prob REAL,
                    
                    -- Form Score (derniers 5 matchs)
                    home_form_5 REAL,
                    away_form_5 REAL,
                    home_wins_5 INTEGER,
                    away_wins_5 INTEGER,
                    home_draws_5 INTEGER,
                    away_draws_5 INTEGER,
                    
                    -- Home Advantage
                    home_advantage REAL,
                    
                    -- Fatigue & Rest
                    home_days_rest INTEGER,
                    away_days_rest INTEGER,
                    home_matches_7 INTEGER,
                    away_matches_7 INTEGER,
                    
                    -- PPG (Points Per Game)
                    home_ppg_all REAL,
                    away_ppg_all REAL,
                    home_home_ppg REAL,
                    home_away_ppg REAL,
                    away_home_ppg REAL,
                    away_away_ppg REAL,
                    
                    -- Résultats (ajoutés après le match)
                    home_goals INTEGER,
                    away_goals INTEGER,
                    result TEXT,  -- '1', 'X', '2'
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES matches(match_id),
                    UNIQUE(match_id)
                )
            """)

            self.conn.commit()
            logger.info("✅ Tables créées avec succès")

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de la création des tables : {e}")
            raise

    def insert_teams(self, teams_list):
        """
        Insère une liste d'équipes
        
        Args:
            teams_list: Liste de dicts {name, league, country, founded_year}
        """
        if not self.conn:
            self.connect()

        try:
            for team in teams_list:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO teams (name, league, country, founded_year)
                    VALUES (?, ?, ?, ?)
                """, (team['name'], team['league'], team.get('country'), team.get('founded_year')))

            self.conn.commit()
            logger.info(f"✅ {len(teams_list)} équipes insérées")

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de l'insertion des équipes : {e}")
            raise

    def insert_matches(self, matches_list):
        """
        Insère une liste de matchs
        
        Args:
            matches_list: Liste de dicts avec les infos du match
        """
        if not self.conn:
            self.connect()

        try:
            for match in matches_list:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO matches 
                    (league, season, match_date, home_team_id, away_team_id, 
                     home_goals, away_goals, result, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    match['league'],
                    match['season'],
                    match['match_date'],
                    match['home_team_id'],
                    match['away_team_id'],
                    match['home_goals'],
                    match['away_goals'],
                    match['result'],
                    match['status']
                ))

            self.conn.commit()
            logger.info(f"✅ {len(matches_list)} matchs insérés")

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de l'insertion des matchs : {e}")
            raise

    def insert_odds(self, odds_list):
        """
        Insère une liste de cotes
        
        Args:
            odds_list: Liste de dicts avec les cotes
        """
        if not self.conn:
            self.connect()

        try:
            for odd in odds_list:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO odds 
                    (match_id, bookmaker, odd_1, odd_x, odd_2, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    odd['match_id'],
                    odd['bookmaker'],
                    odd['odd_1'],
                    odd['odd_x'],
                    odd['odd_2'],
                    odd['timestamp']
                ))

            self.conn.commit()
            logger.info(f"✅ {len(odds_list)} cotes insérées")

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de l'insertion des cotes : {e}")
            raise

    def insert_features(self, features_df):
        """
        Insère les features calculées en base de données
        
        Args:
            features_df: DataFrame avec toutes les features
        """
        if not self.conn:
            self.connect()

        try:
            # Colonnes à insérer
            columns = [
                'match_id', 'home_team_id', 'away_team_id', 'match_date',
                'home_elo', 'away_elo', 'elo_diff', 'home_exp_win_prob', 'away_exp_win_prob',
                'home_form_5', 'away_form_5', 'home_wins_5', 'away_wins_5', 'home_draws_5', 'away_draws_5',
                'home_advantage', 'home_days_rest', 'away_days_rest', 'home_matches_7', 'away_matches_7',
                'home_ppg_all', 'away_ppg_all', 'home_home_ppg', 'home_away_ppg', 'away_home_ppg', 'away_away_ppg',
                'home_goals', 'away_goals', 'result'
            ]
            
            placeholders = ','.join(['?' for _ in columns])
            col_names = ','.join(columns)
            
            insert_query = f"""
                INSERT OR REPLACE INTO features ({col_names})
                VALUES ({placeholders})
            """
            
            for _, row in features_df.iterrows():
                values = [row.get(col) for col in columns]
                self.cursor.execute(insert_query, values)

            self.conn.commit()
            logger.info(f"✅ {len(features_df)} features insérées")

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de l'insertion des features : {e}")
            raise

    def insert_predictions(self, predictions_df, model_version="v1.0"):
        """
        Insère les prédictions en base de données
        
        Args:
            predictions_df: DataFrame avec les prédictions
            model_version: Version du modèle
        """
        if not self.conn:
            self.connect()

        try:
            for _, row in predictions_df.iterrows():
                self.cursor.execute("""
                    INSERT OR REPLACE INTO predictions 
                    (match_id, model_version, prob_1, prob_x, prob_2, 
                     predicted_result, confidence, is_value, value_odds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['match_id']),
                    model_version,
                    float(row['prob_1']),
                    float(row['prob_x']),
                    float(row['prob_2']),
                    str(row['predicted_result']),
                    float(row['confidence']),
                    None,  # is_value (prêt pour backtesting)
                    None   # value_odds (prêt pour backtesting)
                ))

            self.conn.commit()
            logger.info(f"✅ {len(predictions_df)} prédictions insérées")

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de l'insertion des prédictions : {e}")
            raise

    def get_team_id(self, team_name):
        """Récupère l'ID d'une équipe par son nom"""
        if not self.conn:
            self.connect()

        try:
            self.cursor.execute("SELECT team_id FROM teams WHERE name = ?", (team_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de la récupération du team_id : {e}")
            raise

    def get_matches(self, league=None, season=None):
        """Récupère les matchs avec filtres optionnels"""
        if not self.conn:
            self.connect()

        try:
            query = "SELECT * FROM matches WHERE 1=1"
            params = []

            if league:
                query += " AND league = ?"
                params.append(league)

            if season:
                query += " AND season = ?"
                params.append(season)

            query += " ORDER BY match_date"
            
            df = pd.read_sql_query(query, self.conn, params=params)
            return df

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de la récupération des matchs : {e}")
            raise

    def get_stats(self):
        """Retourne des stats de la base de données"""
        if not self.conn:
            self.connect()

        try:
            stats = {}

            # Nombre d'équipes
            self.cursor.execute("SELECT COUNT(*) FROM teams")
            stats['teams_count'] = self.cursor.fetchone()[0]

            # Nombre de matchs
            self.cursor.execute("SELECT COUNT(*) FROM matches")
            stats['matches_count'] = self.cursor.fetchone()[0]

            # Nombre de matchs joués
            self.cursor.execute("SELECT COUNT(*) FROM matches WHERE status = 'played'")
            stats['matches_played'] = self.cursor.fetchone()[0]

            # Nombre de cotes
            self.cursor.execute("SELECT COUNT(*) FROM odds")
            stats['odds_count'] = self.cursor.fetchone()[0]

            # Nombre de prédictions
            self.cursor.execute("SELECT COUNT(*) FROM predictions")
            stats['predictions_count'] = self.cursor.fetchone()[0]

            # Nombre de features
            self.cursor.execute("SELECT COUNT(*) FROM features")
            stats['features_count'] = self.cursor.fetchone()[0]

            return stats

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de la récupération des stats : {e}")
            raise

    def get_features(self, league=None, season=None):
        """Récupère les features avec filtres optionnels"""
        if not self.conn:
            self.connect()

        try:
            query = """
                SELECT f.* FROM features f
                JOIN matches m ON f.match_id = m.match_id
                WHERE 1=1
            """
            params = []

            if league:
                query += " AND m.league = ?"
                params.append(league)

            if season:
                query += " AND m.season = ?"
                params.append(season)

            query += " ORDER BY f.match_date"
            
            df = pd.read_sql_query(query, self.conn, params=params)
            return df

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de la récupération des features : {e}")
            raise

    def get_predictions(self, league=None, season=None, model_version=None):
        """Récupère les prédictions avec filtres optionnels"""
        if not self.conn:
            self.connect()

        try:
            query = """
                SELECT p.*, m.match_date, m.home_team_id, m.away_team_id, 
                       m.home_goals, m.away_goals, m.result
                FROM predictions p
                JOIN matches m ON p.match_id = m.match_id
                WHERE 1=1
            """
            params = []

            if league:
                query += " AND m.league = ?"
                params.append(league)

            if season:
                query += " AND m.season = ?"
                params.append(season)

            if model_version:
                query += " AND p.model_version = ?"
                params.append(model_version)

            query += " ORDER BY m.match_date"
            
            df = pd.read_sql_query(query, self.conn, params=params)
            return df

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de la récupération des prédictions : {e}")
            raise

    def clear_all(self):
        """Supprime TOUTES les données (dev only)"""
        if not self.conn:
            self.connect()

        try:
            for table in ['predictions', 'features', 'odds', 'matches', 'teams', 'backtests']:
                self.cursor.execute(f"DELETE FROM {table}")

            self.conn.commit()
            logger.warning("⚠️ Toutes les données ont été supprimées")

        except sqlite3.Error as e:
            logger.error(f"❌ Erreur lors de la suppression : {e}")
            raise
