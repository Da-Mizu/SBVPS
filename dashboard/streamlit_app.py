"""
SBVPS Dashboard - Streamlit Application
Sports Betting Value Prediction System
"""
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
import sys
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import DATABASE_URL, MODELS_DIR
from src.logger import get_logger
from src.models.predictor import Predictor

logger = get_logger(__name__)

# Page Config
st.set_page_config(
    page_title="SBVPS - Sports Betting Value Prediction",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive { color: #28a745; font-weight: bold; }
    .negative { color: #dc3545; font-weight: bold; }
    .neutral { color: #17a2b8; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - Navigation et Filtres
# ============================================================================
st.sidebar.title("⚽ SBVPS Dashboard")

# Compétition selector
competition = st.sidebar.selectbox(
    "Select Competition",
    ["Ligue 1", "World Cup"],
    key="competition_selector",
    label_visibility="collapsed"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["📊 Overview", "🎯 Predictions", "📈 Features", "💰 Value Betting", "💵 Bet Calculator", "⚙️ Settings"],
    label_visibility="collapsed"
)

# Database connection
@st.cache_resource
def get_db_connection():
    db_path = DATABASE_URL.replace("sqlite:///", "")
    return sqlite3.connect(db_path)

def query_db(query, params=()):
    conn = get_db_connection()
    df = pd.read_sql_query(query, conn, params=params)
    return df

# Get predictor
@st.cache_resource
def get_predictor():
    model_path = MODELS_DIR / "model_v1.1.pkl"
    if model_path.exists():
        return Predictor(model_filepath=str(model_path))
    return None

def check_tables_exist():
    """Check if database tables exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        return len(tables) > 0
    except:
        return False

def show_setup_required():
    """Show setup instructions"""
    st.warning("🔧 Database Setup Required", icon="⚠️")
    st.markdown("""
    The database is empty. You need to generate sample data first.
    
    **Step-by-step setup:**
    
    1. **Generate Sample Data** (in terminal):
    ```bash
    python scripts/generate_fake_matches.py --n 380 --season 2025 --league "Ligue 1" --save-db
    ```
    
    2. **Engineer Features** (calculate features):
    ```bash
    python scripts/engineer_features.py --league "Ligue 1" --season 2025
    ```
    
    3. **Train Model** (train ML model):
    ```bash
    python scripts/train_model.py --league "Ligue 1" --season 2025
    ```
    
    4. **Refresh Dashboard** (in VS Code):
    - Press `R` or refresh the browser page
    
    Once data is generated, this dashboard will display:
    - Match statistics and results
    - Model predictions and confidence scores
    - Value betting opportunities
    - Feature analysis and correlations
    """)

# ============================================================================
# PAGE 1: OVERVIEW
# ============================================================================
if page == "📊 Overview":
    st.title(f"📊 SBVPS Dashboard - {competition}")
    
    if not check_tables_exist():
        show_setup_required()
    else:
        try:
            # Stats - filtrés par compétition
            stats_query = f"""
                SELECT 
                    (SELECT COUNT(*) FROM teams WHERE league LIKE '%{competition}%') as teams_count,
                    (SELECT COUNT(*) FROM matches WHERE league LIKE '%{competition}%') as matches_count,
                    (SELECT COUNT(*) FROM features WHERE match_id IN (SELECT match_id FROM matches WHERE league LIKE '%{competition}%')) as features_count,
                    (SELECT COUNT(*) FROM predictions WHERE match_id IN (SELECT match_id FROM matches WHERE league LIKE '%{competition}%')) as predictions_count,
                    (SELECT COUNT(*) FROM odds WHERE match_id IN (SELECT match_id FROM matches WHERE league LIKE '%{competition}%')) as odds_count
            """
            stats = query_db(stats_query).iloc[0]
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("🏆 Teams", int(stats['teams_count']))
            with col2:
                st.metric("⚽ Matches", int(stats['matches_count']))
            with col3:
                st.metric("🔢 Features", int(stats['features_count']))
            with col4:
                st.metric("🎲 Predictions", int(stats['predictions_count']))
            with col5:
                st.metric("📊 Odds", int(stats['odds_count']))
            
            st.divider()
            
            # Match Results Distribution
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Match Results Distribution")
                results_query = f"""
                    SELECT result, COUNT(*) as count 
                    FROM matches 
                    WHERE league LIKE '%{competition}%'
                    GROUP BY result
                """
                results_df = query_db(results_query)
                
                result_names = {"1": "Home Win", "X": "Draw", "2": "Away Win"}
                results_df['result_name'] = results_df['result'].map(result_names)
                
                fig = px.pie(
                    results_df,
                    values='count',
                    names='result_name',
                    color_discrete_map={
                        'Home Win': '#2ecc71',
                        'Draw': '#3498db',
                        'Away Win': '#e74c3c'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Predictions Distribution")
                pred_query = f"""
                    SELECT predicted_result, COUNT(*) as count 
                    FROM predictions 
                    WHERE match_id IN (SELECT match_id FROM matches WHERE league LIKE '%{competition}%')
                    GROUP BY predicted_result
                """
                pred_df = query_db(pred_query)
                
                if len(pred_df) > 0:
                    pred_df['result_name'] = pred_df['predicted_result'].map(result_names)
                    fig = px.pie(
                        pred_df,
                        values='count',
                        names='result_name',
                        color_discrete_map={
                            'Home Win': '#2ecc71',
                            'Draw': '#3498db',
                            'Away Win': '#e74c3c'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No predictions yet. Train model first.")
            
            st.divider()
            
            # Latest Matches
            st.subheader("📅 Recent Matches")
            matches_query = f"""
                SELECT match_id, match_date, home_team_id, away_team_id, 
                       home_goals, away_goals, result, league, season
                FROM matches
                WHERE league LIKE '%{competition}%'
                ORDER BY match_date DESC
                LIMIT 10
            """
            matches_df = query_db(matches_query)
            st.dataframe(matches_df, use_container_width=True, hide_index=True)
            
        except Exception as e:
            st.error(f"Error loading overview: {str(e)}")

# ============================================================================
# PAGE 2: PREDICTIONS
# ============================================================================
elif page == "🎯 Predictions":
    st.title(f"🎯 Match Predictions - {competition}")
    
    if not check_tables_exist():
        show_setup_required()
    else:
        try:
            # Get predictions with confidence - filtrées par compétition
            pred_query = f"""
                SELECT p.match_id, p.predicted_result, p.confidence,
                       p.prob_1 as prob_home, p.prob_x as prob_draw, p.prob_2 as prob_away,
                       m.match_date, m.league, m.season
                FROM predictions p
                JOIN matches m ON p.match_id = m.match_id
                WHERE m.league LIKE '%{competition}%'
                ORDER BY p.confidence DESC
                LIMIT 50
            """
            predictions_df = query_db(pred_query)
            
            if len(predictions_df) == 0:
                st.warning("No predictions available. Train the model first.")
            else:
                # Filters
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_conf = st.slider(
                        "Min Confidence",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.5,
                        step=0.05
                    )
                
                with col2:
                    leagues = predictions_df['league'].unique()
                    selected_league = st.selectbox("League", ["All"] + list(leagues))
                
                with col3:
                    pred_result = st.selectbox("Predicted Result", ["All", "1 (Home)", "X (Draw)", "2 (Away)"])
                
                # Filter data
                filtered_df = predictions_df[predictions_df['confidence'] >= min_conf].copy()
                
                if selected_league != "All":
                    filtered_df = filtered_df[filtered_df['league'] == selected_league]
                
                if pred_result != "All":
                    result_map = {"1 (Home)": "1", "X (Draw)": "X", "2 (Away)": "2"}
                    filtered_df = filtered_df[filtered_df['predicted_result'] == result_map[pred_result]]
                
                st.subheader(f"Predictions ({len(filtered_df)} matches)")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Average Confidence", f"{filtered_df['confidence'].mean():.2%}")
                with col2:
                    st.metric("High Confidence (>70%)", len(filtered_df[filtered_df['confidence'] > 0.7]))
                with col3:
                    st.metric("Medium Confidence (50-70%)", len(filtered_df[(filtered_df['confidence'] >= 0.5) & (filtered_df['confidence'] <= 0.7)]))
                with col4:
                    st.metric("Low Confidence (<50%)", len(filtered_df[filtered_df['confidence'] < 0.5]))
                
                st.divider()
                
                # Confidence Distribution
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=filtered_df['confidence'],
                    nbinsx=20,
                    name='Confidence',
                    marker_color='#3498db'
                ))
                fig.update_layout(
                    title_text="Prediction Confidence Distribution",
                    xaxis_title="Confidence",
                    yaxis_title="Count",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                
                # Top Predictions
                st.subheader("Top Predictions by Confidence")
                display_df = filtered_df[[
                    'match_id', 'predicted_result', 'confidence', 
                    'prob_home', 'prob_draw', 'prob_away', 'match_date'
                ]].head(20).copy()
                
                display_df['confidence'] = display_df['confidence'].apply(lambda x: f"{x:.1%}")
                display_df['prob_home'] = display_df['prob_home'].apply(lambda x: f"{x:.1%}")
                display_df['prob_draw'] = display_df['prob_draw'].apply(lambda x: f"{x:.1%}")
                display_df['prob_away'] = display_df['prob_away'].apply(lambda x: f"{x:.1%}")
                display_df['predicted_result'] = display_df['predicted_result'].map({
                    "1": "🏠 Home", "X": "⚪ Draw", "2": "⛔ Away"
                })
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error loading predictions: {str(e)}")

# ============================================================================
# PAGE 3: FEATURES ANALYSIS
# ============================================================================
elif page == "📈 Features":
    st.title(f"📈 Features Analysis - {competition}")
    
    if not check_tables_exist():
        show_setup_required()
    else:
        try:
            features_query = f"""
                SELECT f.* FROM features f
                JOIN matches m ON f.match_id = m.match_id
                WHERE m.league LIKE '%{competition}%'
                LIMIT 100
            """
            features_df = query_db(features_query)
            
            if len(features_df) == 0:
                st.warning("No features available. Run feature engineering first.")
            else:
                # Select feature to analyze
                numeric_cols = features_df.select_dtypes(include=[np.number]).columns.tolist()
                selected_feature = st.selectbox("Select Feature to Analyze", numeric_cols)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.histogram(
                        features_df,
                        x=selected_feature,
                        nbins=30,
                        title=f"Distribution of {selected_feature}",
                        color_discrete_sequence=['#3498db']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    stats = features_df[selected_feature].describe()
                    st.subheader("Statistics")
                    st.write(f"**Count**: {stats['count']:.0f}")
                    st.write(f"**Mean**: {stats['mean']:.4f}")
                    st.write(f"**Std**: {stats['std']:.4f}")
                    st.write(f"**Min**: {stats['min']:.4f}")
                    st.write(f"**25%**: {stats['25%']:.4f}")
                    st.write(f"**50%**: {stats['50%']:.4f}")
                    st.write(f"**75%**: {stats['75%']:.4f}")
                    st.write(f"**Max**: {stats['max']:.4f}")
                
                st.divider()
                
                # Feature Correlation
                st.subheader("Feature Correlations")
                corr_matrix = features_df[numeric_cols].corr()
                
                fig = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0,
                    zmin=-1,
                    zmax=1
                ))
                fig.update_layout(
                    title="Feature Correlation Matrix",
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                
                # Top Features Table
                st.subheader("Sample Features Data")
                st.dataframe(features_df.head(10), use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error loading features: {str(e)}")

# ============================================================================
# PAGE 4: VALUE BETTING
# ============================================================================
elif page == "💰 Value Betting":
    st.title(f"💰 Value Betting Analysis - {competition}")
    
    if not check_tables_exist():
        show_setup_required()
    else:
        try:
            # Query odds and predictions - filtrées par compétition
            value_query = f"""
                SELECT p.match_id, p.predicted_result, p.prob_1 as prob_home, p.prob_x as prob_draw, p.prob_2 as prob_away,
                       ROUND(AVG(o.odd_1), 2) as home_odds, ROUND(AVG(o.odd_x), 2) as draw_odds, ROUND(AVG(o.odd_2), 2) as away_odds,
                       m.match_date, m.league
                FROM predictions p
                JOIN matches m ON p.match_id = m.match_id
                LEFT JOIN odds o ON p.match_id = o.match_id
                WHERE m.league LIKE '%{competition}%'
                GROUP BY p.match_id
                LIMIT 100
            """
            value_df = query_db(value_query)
            
            if len(value_df) == 0:
                st.warning("No odds data available for value analysis.")
            else:
                # Calculate value
                value_df['value_home'] = (value_df['prob_home'] * value_df['home_odds']) - 1
                value_df['value_draw'] = (value_df['prob_draw'] * value_df['draw_odds']) - 1
                value_df['value_away'] = (value_df['prob_away'] * value_df['away_odds']) - 1
                
                # Find best value bets
                st.subheader("📊 Value Betting Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    positive_value = len(value_df[(value_df['value_home'] > 0.05) | (value_df['value_draw'] > 0.05) | (value_df['value_away'] > 0.05)])
                    st.metric("Positive Value Opportunities", positive_value)
                
                with col2:
                    high_value = len(value_df[(value_df['value_home'] > 0.20) | (value_df['value_draw'] > 0.20) | (value_df['value_away'] > 0.20)])
                    st.metric("High Value (>20%)", high_value)
                
                with col3:
                    best_value = max(
                        value_df['value_home'].max(),
                        value_df['value_draw'].max(),
                        value_df['value_away'].max()
                    )
                    st.metric("Best Value", f"{best_value:.1%}")
                
                st.divider()
                
                # Value Distribution
                fig = px.histogram(
                    title="Value Distribution",
                    nbins=20,
                    color_discrete_sequence=['#3498db']
                )
                
                all_values = list(value_df['value_home']) + list(value_df['value_draw']) + list(value_df['value_away'])
                fig.add_trace(go.Histogram(
                    x=all_values,
                    nbinsx=20,
                    name='Value %',
                    marker_color='#3498db'
                ))
                
                fig.update_layout(
                    title_text="Value Betting Distribution",
                    xaxis_title="Value (%)",
                    yaxis_title="Count",
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                
                # Top Value Bets
                st.subheader("Top Value Betting Opportunities")
                
                top_bets = []
                for _, row in value_df.iterrows():
                    if row['value_home'] > 0:
                        top_bets.append({
                            'Match': row['match_id'],
                            'Bet': 'Home Win',
                            'Prob': row['prob_home'],
                            'Odds': row['home_odds'],
                            'Value': row['value_home'],
                            'Date': row['match_date']
                        })
                    if row['value_draw'] > 0:
                        top_bets.append({
                            'Match': row['match_id'],
                            'Bet': 'Draw',
                            'Prob': row['prob_draw'],
                            'Odds': row['draw_odds'],
                            'Value': row['value_draw'],
                            'Date': row['match_date']
                        })
                    if row['value_away'] > 0:
                        top_bets.append({
                            'Match': row['match_id'],
                            'Bet': 'Away Win',
                            'Prob': row['prob_away'],
                            'Odds': row['away_odds'],
                            'Value': row['value_away'],
                            'Date': row['match_date']
                        })
                
                if top_bets:
                    top_bets_df = pd.DataFrame(top_bets).sort_values('Value', ascending=False).head(20)
                    top_bets_df['Prob'] = top_bets_df['Prob'].apply(lambda x: f"{x:.1%}")
                    top_bets_df['Odds'] = top_bets_df['Odds'].apply(lambda x: f"{x:.2f}")
                    top_bets_df['Value'] = top_bets_df['Value'].apply(lambda x: f"{x:.1%}")
                    
                    st.dataframe(top_bets_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No positive value bets found at this moment.")
        
        except Exception as e:
            st.error(f"Error loading value betting analysis: {str(e)}")

# ============================================================================
# PAGE 5: BET CALCULATOR
# ============================================================================
elif page == "💵 Bet Calculator":
    st.title("💵 Smart Bet Calculator")
    
    st.markdown("""
    Analyze betting value for any match in the database or compare World Cup teams. 
    Enter odds and get a recommendation based on probability analysis. The system prioritizes accuracy over hype.
    """)
    
    # Choose betting mode
    betting_mode = st.radio(
        "Betting Mode",
        ["📊 Database Match", "🏆 World Cup Teams"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # ================================================================
    # WORLD CUP TEAM SELECTOR MODE
    # ================================================================
    if betting_mode == "🏆 World Cup Teams":
        st.subheader("🏆 World Cup Team Betting Analysis")
        
        # World Cup teams with ELO ratings (used to calculate draw probability)
        world_cup_teams = {
            "Argentina": {"win_prob": 0.12, "elo": 1695},
            "France": {"win_prob": 0.11, "elo": 1705},
            "Brazil": {"win_prob": 0.13, "elo": 1700},
            "Spain": {"win_prob": 0.08, "elo": 1690},
            "England": {"win_prob": 0.09, "elo": 1655},
            "Germany": {"win_prob": 0.07, "elo": 1680},
            "Netherlands": {"win_prob": 0.06, "elo": 1645},
            "Belgium": {"win_prob": 0.05, "elo": 1630},
            "Italy": {"win_prob": 0.04, "elo": 1610},
            "Portugal": {"win_prob": 0.05, "elo": 1620},
            "Denmark": {"win_prob": 0.03, "elo": 1590},
            "Sweden": {"win_prob": 0.02, "elo": 1575},
            "Norway": {"win_prob": 0.02, "elo": 1560},
            "Mexico": {"win_prob": 0.02, "elo": 1550},
            "Uruguay": {"win_prob": 0.03, "elo": 1605},
            "Poland": {"win_prob": 0.01, "elo": 1525},
            "Croatia": {"win_prob": 0.04, "elo": 1600},
            "Serbia": {"win_prob": 0.01, "elo": 1500},
            "Czech Republic": {"win_prob": 0.01, "elo": 1510},
            "Romania": {"win_prob": 0.005, "elo": 1450},
            "Greece": {"win_prob": 0.01, "elo": 1480},
            "Hungary": {"win_prob": 0.005, "elo": 1460},
            "Ukraine": {"win_prob": 0.01, "elo": 1505},
            "Turkey": {"win_prob": 0.02, "elo": 1540},
            "Japan": {"win_prob": 0.01, "elo": 1540},
            "South Korea": {"win_prob": 0.01, "elo": 1535},
            "China": {"win_prob": 0.005, "elo": 1420},
            "Australia": {"win_prob": 0.005, "elo": 1480},
            "New Zealand": {"win_prob": 0.005, "elo": 1470},
            "South Africa": {"win_prob": 0.005, "elo": 1480},
            "Egypt": {"win_prob": 0.005, "elo": 1440},
            "Morocco": {"win_prob": 0.01, "elo": 1500},
        }
        
        def calculate_draw_probability(elo1: float, elo2: float) -> float:
            """
            Calculate draw probability based on ELO difference
            - When teams are equally strong (small ELO diff) → high draw probability
            - When one team is much stronger → lower draw probability
            
            Args:
                elo1: ELO rating of team 1
                elo2: ELO rating of team 2
                
            Returns:
                Draw probability (0.0 to 1.0)
            """
            elo_diff = abs(elo1 - elo2)
            
            # Sigmoid-based model: draw probability decreases with ELO difference
            # Base draw probability ≈ 0.25 when teams are equal
            base_draw_prob = 0.25
            
            # For every 100 ELO points difference, reduce draw prob by ~0.05
            # Formula: draw_prob = base * e^(-0.01 * elo_diff)
            import math
            draw_prob = base_draw_prob * math.exp(-0.01 * elo_diff)
            
            return min(max(draw_prob, 0.05), 0.50)  # Clamp between 0.05 and 0.50
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            team1 = st.selectbox(
                "🏠 Team 1",
                sorted(world_cup_teams.keys()),
                key="wc_team1"
            )
            odd1 = st.number_input(
                f"Odds for {team1} to Win",
                min_value=1.01,
                max_value=100.0,
                value=5.0,
                step=0.10,
                key="wc_odd1"
            )
        
        with col2:
            team2 = st.selectbox(
                "⛔ Team 2",
                sorted(world_cup_teams.keys()),
                key="wc_team2"
            )
            odd2 = st.number_input(
                f"Odds for {team2} to Win",
                min_value=1.01,
                max_value=100.0,
                value=5.0,
                step=0.10,
                key="wc_odd2"
            )
        
        with col3:
            st.markdown("**⚪ Draw Analysis** (Auto-calculated)")
            # Calculate draw probability automatically based on ELO difference
            if team1 != team2:
                elo1 = world_cup_teams[team1]["elo"]
                elo2 = world_cup_teams[team2]["elo"]
                draw_probability = calculate_draw_probability(elo1, elo2)
            else:
                draw_probability = 0.25
            
            # Get raw probabilities
            prob1 = world_cup_teams[team1]["win_prob"]
            prob2 = world_cup_teams[team2]["win_prob"]
            
            # Normalize probabilities so they sum to 1 (for fair comparison)
            total_prob = prob1 + prob2 + draw_probability
            prob1_norm = prob1 / total_prob
            prob2_norm = prob2 / total_prob
            prob_draw_norm = draw_probability / total_prob
            
            # Display normalized draw probability for consistency
            st.metric(f"Draw Prob", f"{prob_draw_norm:.1%}")
            
            odd_draw = st.number_input(
                "⚪ Draw Odds",
                min_value=1.01,
                max_value=100.0,
                value=3.5,
                step=0.10,
                key="wc_odd_draw"
            )
        
        st.divider()
        
        # Validate selection
        if team1 == team2:
            st.error("❌ Please select two different teams!")
        else:
            # Probabilities already normalized above in the Draw Analysis section
            st.markdown("### 🎲 Predicted Probabilities")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(f"🏠 {team1}", f"{prob1_norm*100:.1f}%")
            with col2:
                st.metric(f"⚪ Draw", f"{prob_draw_norm*100:.1f}%")
            with col3:
                st.metric(f"⛔ {team2}", f"{prob2_norm*100:.1f}%")
            
            st.divider()
            
            # Calculate value
            value1 = (prob1_norm * odd1) - 1
            value_draw = (prob_draw_norm * odd_draw) - 1
            value2 = (prob2_norm * odd2) - 1
            
            st.markdown("### 💰 Betting Value Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"#### 🏠 {team1}")
                st.metric(f"Probability", f"{prob1_norm:.1%}")
                st.metric(f"Odds", f"{odd1:.2f}")
                st.metric(f"Expected Value", f"{value1:+.2%}")
                
                if value1 > 0.10:
                    st.success("✅ **STRONG BET!** Excellent value")
                elif value1 > 0.05:
                    st.success("✅ **BET** Good value")
                elif value1 > 0:
                    st.warning("⚠️ **MARGINAL** Slight positive value")
                else:
                    st.error(f"❌ **AVOID** Expected loss: {value1:.2%}")
            
            with col2:
                st.markdown(f"#### ⚪ Draw")
                st.metric(f"Probability", f"{prob_draw_norm:.1%}")
                st.metric(f"Odds", f"{odd_draw:.2f}")
                st.metric(f"Expected Value", f"{value_draw:+.2%}")
                
                if value_draw > 0.10:
                    st.success("✅ **STRONG BET!** Excellent value")
                elif value_draw > 0.05:
                    st.success("✅ **BET** Good value")
                elif value_draw > 0:
                    st.warning("⚠️ **MARGINAL** Slight positive value")
                else:
                    st.error(f"❌ **AVOID** Expected loss: {value_draw:.2%}")
            
            with col3:
                st.markdown(f"#### ⛔ {team2}")
                st.metric(f"Probability", f"{prob2_norm:.1%}")
                st.metric(f"Odds", f"{odd2:.2f}")
                st.metric(f"Expected Value", f"{value2:+.2%}")
                
                if value2 > 0.10:
                    st.success("✅ **STRONG BET!** Excellent value")
                elif value2 > 0.05:
                    st.success("✅ **BET** Good value")
                elif value2 > 0:
                    st.warning("⚠️ **MARGINAL** Slight positive value")
                else:
                    st.error(f"❌ **AVOID** Expected loss: {value2:.2%}")
            
            st.divider()
            
            # Recommendation
            st.markdown("### 🎯 Betting Recommendation")
            
            values = [
                (f"🏠 {team1}", value1, odd1, prob1_norm),
                (f"⚪ Draw", value_draw, odd_draw, prob_draw_norm),
                (f"⛔ {team2}", value2, odd2, prob2_norm)
            ]
            values_sorted = sorted(values, key=lambda x: x[1], reverse=True)
            
            best = values_sorted[0]
            
            if best[1] > 0.10:
                st.success(f"### ✅ Best Bet: {best[0]}")
                st.markdown(f"""
                **Value**: {best[1]:+.1%}  
                **Probability**: {best[3]:.1%}  
                **Odds**: {best[2]:.2f}  
                **Per €10 bet**: €{10 * (best[2] - 1) - 10 * (1 - best[3]):+.2f} expected profit
                """)
            elif best[1] > 0.05:
                st.warning(f"### ⚠️ Moderate Bet: {best[0]}")
                st.markdown(f"""
                **Value**: {best[1]:+.1%}  
                **Probability**: {best[3]:.1%}  
                **Odds**: {best[2]:.2f}
                """)
            elif best[1] > 0:
                st.info(f"### ℹ️ Marginal: {best[0]}")
                st.markdown(f"Slight positive value ({best[1]:+.1%}), but not recommended")
            else:
                st.error("### ❌ No Value Bets Available")
                st.markdown(f"All options show negative expected value. Best value: {best[0]} ({best[1]:+.1%})")
            
            st.divider()
            st.markdown("### 📈 All Options Ranked")
            for i, (option, value, odds_val, prob) in enumerate(values_sorted, 1):
                color = "🟢" if value > 0.05 else "🟡" if value > 0 else "🔴"
                st.markdown(f"""
                **{i}. {option}** {color}
                - Value: {value:+.1%}
                - Win Prob: {prob:.1%} vs Odds: {odds_val:.2f}x
                """)
    
    # ================================================================
    # DATABASE MATCH MODE (existing functionality)
    # ================================================================
    else:
        try:
                # Get a match with predictions and odds
                match_query = f"""
                    SELECT m.home_team_id, m.away_team_id, 
                           t1.name as home_name, t2.name as away_name,
                           p.prob_1, p.prob_x, p.prob_2, p.confidence,
                           AVG(o.odd_1) as odd_1, AVG(o.odd_x) as odd_x, AVG(o.odd_2) as odd_2
                    FROM matches m
                    JOIN teams t1 ON m.home_team_id = t1.team_id
                    JOIN teams t2 ON m.away_team_id = t2.team_id
                    JOIN predictions p ON m.match_id = p.match_id
                    LEFT JOIN odds o ON m.match_id = o.match_id
                    WHERE m.league LIKE '%{competition}%'
                    GROUP BY m.match_id
                    LIMIT 1
                """
                
                result = query_db(match_query)
                
                if len(result) > 0:
                    match = result.iloc[0]
                    
                    st.divider()
                    st.subheader(f"⚽ {match['home_name']} vs {match['away_name']}")
                    
                    # Display predictions
                    st.markdown("### 🎲 Predicted Probabilities")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("🏠 Home Win", f"{match['prob_1']*100:.1f}%")
                    with col2:
                        st.metric("⚪ Draw", f"{match['prob_x']*100:.1f}%")
                    with col3:
                        st.metric("⛔ Away Win", f"{match['prob_2']*100:.1f}%")
                    
                    st.divider()
                    
                    # Display current odds if available
                    if match['odd_1'] and not pd.isna(match['odd_1']):
                        st.markdown("### 📊 Current Database Odds")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("🏠 Home Win Odds", f"{match['odd_1']:.2f}")
                        with col2:
                            st.metric("⚪ Draw Odds", f"{match['odd_x']:.2f}")
                        with col3:
                            st.metric("⛔ Away Win Odds", f"{match['odd_2']:.2f}")
                        
                        st.divider()
                        
                        # Calculate value with database odds
                        home_value = (match['prob_1'] * match['odd_1']) - 1
                        draw_value = (match['prob_x'] * match['odd_x']) - 1
                        away_value = (match['prob_2'] * match['odd_2']) - 1
                        
                        values_sorted = sorted([
                            ("🏠 Home Win", home_value, match['prob_1'], match['odd_1']),
                            ("⚪ Draw", draw_value, match['prob_x'], match['odd_x']),
                            ("⛔ Away Win", away_value, match['prob_2'], match['odd_2'])
                        ], key=lambda x: x[1], reverse=True)
                        
                        best = values_sorted[0]
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.markdown("### 🎯 Betting Recommendation (Database Odds)")
                            
                            if best[1] > 0.05:
                                st.success(f"✅ **BET ON: {best[0]}**")
                                st.markdown(f"""
                                - **Value**: {best[1]:+.1%}
                                - **Probability**: {best[2]:.1%}
                                - **Odds**: {best[3]:.2f}
                                - **Expected Profit**: {best[1]*100:+.1f}% per €1
                                """)
                            elif best[1] > 0:
                                st.warning(f"⚠️ **Small Value on: {best[0]}**")
                                st.markdown(f"""
                                - **Value**: {best[1]:+.1%}
                                - **Probability**: {best[2]:.1%}
                                - **Odds**: {best[3]:.2f}
                                """)
                            else:
                                st.error("❌ **NO VALUE BETS** - All options show negative expected value")
                        
                        with col2:
                            st.markdown("### 📈 All Options Ranked")
                            for i, (option, value, prob, odds_val) in enumerate(values_sorted, 1):
                                color = "🟢" if value > 0.05 else "🟡" if value > 0 else "🔴"
                                st.markdown(f"""
                                **{i}. {option}** {color}
                                - Value: {value:+.1%}
                                - Win Prob: {prob:.1%} vs Odds: {odds_val:.2f}x
                                """)
                    
                    st.divider()
                    st.markdown("### 📝 Manual Odds Input")
                    st.markdown("Enter custom odds to see the betting recommendation:")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        manual_odd_1 = st.number_input(
                            "🏠 Home Win Odds",
                            min_value=1.01,
                            max_value=100.0,
                            value=float(match['odd_1']) if match['odd_1'] and not pd.isna(match['odd_1']) else 2.0,
                            step=0.05,
                            key="manual_odd_1"
                        )
                    
                    with col2:
                        manual_odd_x = st.number_input(
                            "⚪ Draw Odds",
                            min_value=1.01,
                            max_value=100.0,
                            value=float(match['odd_x']) if match['odd_x'] and not pd.isna(match['odd_x']) else 3.0,
                            step=0.05,
                            key="manual_odd_x"
                        )
                    
                    with col3:
                        manual_odd_2 = st.number_input(
                            "⛔ Away Win Odds",
                            min_value=1.01,
                            max_value=100.0,
                            value=float(match['odd_2']) if match['odd_2'] and not pd.isna(match['odd_2']) else 3.5,
                            step=0.05,
                            key="manual_odd_2"
                        )
                    
                    # Calculate with manual odds
                    manual_home_value = (match['prob_1'] * manual_odd_1) - 1
                    manual_draw_value = (match['prob_x'] * manual_odd_x) - 1
                    manual_away_value = (match['prob_2'] * manual_odd_2) - 1
                    
                    manual_values_sorted = sorted([
                        ("🏠 Home Win", manual_home_value, match['prob_1'], manual_odd_1),
                        ("⚪ Draw", manual_draw_value, match['prob_x'], manual_odd_x),
                        ("⛔ Away Win", manual_away_value, match['prob_2'], manual_odd_2)
                    ], key=lambda x: x[1], reverse=True)
                    
                    manual_best = manual_values_sorted[0]
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("### 🎯 Betting Recommendation (Manual Odds)")
                        
                        if manual_best[1] > 0.05:
                            st.success(f"✅ **BET ON: {manual_best[0]}**")
                            st.markdown(f"""
                            - **Value**: {manual_best[1]:+.1%}
                            - **Probability**: {manual_best[2]:.1%}
                            - **Odds**: {manual_best[3]:.2f}
                            - **Expected Profit**: {manual_best[1]*100:+.1f}% per €1
                            """)
                        elif manual_best[1] > 0:
                            st.warning(f"⚠️ **Small Value on: {manual_best[0]}**")
                            st.markdown(f"""
                            - **Value**: {manual_best[1]:+.1%}
                            - **Probability**: {manual_best[2]:.1%}
                            - **Odds**: {manual_best[3]:.2f}
                            """)
                        else:
                            st.error("❌ **NO VALUE BETS** - All options show negative expected value")
                    
                    with col2:
                        st.markdown("### 📈 All Options Ranked")
                        for i, (option, value, prob, odds_val) in enumerate(manual_values_sorted, 1):
                            color = "🟢" if value > 0.05 else "🟡" if value > 0 else "🔴"
                            st.markdown(f"""
                            **{i}. {option}** {color}
                            - Value: {value:+.1%}
                            - Win Prob: {prob:.1%} vs Odds: {odds_val:.2f}x
                            """)
                else:
                    st.error("No match data found in database!")
                    st.info("Please generate sample data first using: python scripts/generate_fake_matches.py")
        
        except Exception as e:
            st.error(f"Error in bet calculator: {str(e)}")

# ============================================================================
# PAGE 6: SETTINGS
# ============================================================================
elif page == "⚙️ Settings":
    st.title("⚙️ Settings & System Info")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📁 System Paths")
        st.code(f"Project Root: {project_root}")
        st.code(f"Database: {DATABASE_URL}")
        st.code(f"Models Dir: {MODELS_DIR}")
    
    with col2:
        st.subheader("📦 About SBVPS")
        st.info("""
        **SBVPS** - Sports Betting Value Prediction System
        
        A machine learning system for identifying value betting opportunities in sports.
        
        **Stack:**
        - Python 3.11+
        - XGBoost / LightGBM
        - Streamlit (this dashboard)
        - SQLite Database
        """)
    
    st.divider()
    
    # Model Info
    st.subheader("🤖 Model Information")
    
    try:
        model_path = MODELS_DIR / "model_v1.1.pkl"
        if model_path.exists():
            st.success(f"✅ Model found: {model_path.name}")
            st.code(f"Size: {model_path.stat().st_size / 1024:.1f} KB")
            st.code(f"Modified: {pd.Timestamp(model_path.stat().st_mtime, unit='s')}")
        else:
            st.warning("⚠️ Model not found. Train the model first.")
    except Exception as e:
        st.error(f"Error checking model: {str(e)}")
    
    st.divider()
    
    # Database Stats
    st.subheader("💾 Database Status")
    
    try:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        db_file = Path(db_path)
        
        if db_file.exists():
            st.success(f"✅ Database found: {db_file.name}")
            st.code(f"Size: {db_file.stat().st_size / 1024:.1f} KB")
            st.code(f"Modified: {pd.Timestamp(db_file.stat().st_mtime, unit='s')}")
            
            # Table sizes
            stats_query = """
                SELECT 
                    'teams' as table_name, COUNT(*) as count FROM teams
                UNION ALL
                SELECT 'matches', COUNT(*) FROM matches
                UNION ALL
                SELECT 'features', COUNT(*) FROM features
                UNION ALL
                SELECT 'predictions', COUNT(*) FROM predictions
                UNION ALL
                SELECT 'odds', COUNT(*) FROM odds
            """
            table_stats = query_db(stats_query)
            st.dataframe(table_stats, use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Database not found. Generate data first.")
    except Exception as e:
        st.error(f"Error checking database: {str(e)}")

# Footer
st.divider()
st.markdown("""
---
**SBVPS Dashboard** | Last Updated: 2026-06-15 | [GitHub](https://github.com/Da-Mizu/SBVPS)
""")
