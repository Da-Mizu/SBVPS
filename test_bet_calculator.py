#!/usr/bin/env python3
"""
Test Bet Calculator - Standalone demonstration
"""
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import sys

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Use absolute path to database
DB_PATH = str(project_root / "database" / "sbvps.db")

st.set_page_config(page_title="Bet Calculator Test", page_icon="💵", layout="wide")

st.title("💵 Bet Calculator - Test")

# Get database connection
def query_db(sql, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        if results:
            columns = [description[0] for description in cursor.description]
            conn.close()
            return pd.DataFrame([dict(row) for row in results], columns=columns)
        conn.close()
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

# Get a match with predictions and odds
match_query = """
    SELECT m.home_team_id, m.away_team_id, 
           t1.name as home_name, t2.name as away_name,
           p.prob_1, p.prob_x, p.prob_2, p.confidence,
           AVG(o.odd_1) as odd_1, AVG(o.odd_x) as odd_x, AVG(o.odd_2) as odd_2
    FROM matches m
    JOIN teams t1 ON m.home_team_id = t1.team_id
    JOIN teams t2 ON m.away_team_id = t2.team_id
    JOIN predictions p ON m.match_id = p.match_id
    LEFT JOIN odds o ON m.match_id = o.match_id
    WHERE m.league = 'Ligue 1'
    GROUP BY m.match_id
    LIMIT 1
"""

result = query_db(match_query)

if len(result) > 0:
    match = result.iloc[0]
    
    st.markdown("---")
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
    
    # Display current odds
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
            for i, (option, value, prob, odds) in enumerate(values_sorted, 1):
                color = "🟢" if value > 0.05 else "🟡" if value > 0 else "🔴"
                st.markdown(f"""
                **{i}. {option}** {color}
                - Value: {value:+.1%}
                - Win Prob: {prob:.1%} vs Odds: {odds:.2f}x
                """)
    
    st.divider()
    st.markdown("### 📝 Manual Odds Input Test")
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
        for i, (option, value, prob, odds) in enumerate(manual_values_sorted, 1):
            color = "🟢" if value > 0.05 else "🟡" if value > 0 else "🔴"
            st.markdown(f"""
            **{i}. {option}** {color}
            - Value: {value:+.1%}
            - Win Prob: {prob:.1%} vs Odds: {odds:.2f}x
            """)

else:
    st.error("No match data found in database!")
    st.info("Please generate sample data first using: python scripts/generate_fake_matches.py --n 380 --season 2025 --league 'Ligue 1' --save-db")
