"""
Betting Value Analysis Tools - How to Use

Cette suite d'outils permet d'analyser la valeur des paris et d'identifier
les opportunités rentables basées sur les prédictions du modèle ML.
"""

# ============================================================================
# 📖 QUICK START
# ============================================================================

# Option 1: Interactive Mode (le plus facile!)
python scripts/value_check.py
# ➡️ Il te pose des questions, tu donnes les probabilités et cotes
# ➡️ Il te dit sur qui parier


# Option 2: Direct command line (avec un match spécifique)
python scripts/analyze_value.py \
  --match-name "France vs Iran" \
  --prob-1 0.50 \        # Probabilité Home Win (France)
  --prob-x 0.30 \        # Probabilité Draw
  --prob-2 0.20 \        # Probabilité Away Win (Iran)
  --odds-1 1.95 \        # Cote Bookmaker Home Win
  --odds-x 3.50 \        # Cote Bookmaker Draw
  --odds-2 4.00 \        # Cote Bookmaker Away Win
  --confidence 0.88      # Confiance du modèle


# Option 3: With real team data (auto-feature calculation)
python scripts/predict_real_match.py \
  --home "France" \
  --away "Iran" \
  --odds-1 1.95 \
  --odds-x 3.50 \
  --odds-2 4.00 \
  --model-version v1.0


# ============================================================================
# 🎯 UNDERSTANDING THE OUTPUT
# ============================================================================

📊 MODEL PREDICTIONS:
  → Ton modèle dit: "France 50%, Draw 30%, Iran 20%"

💰 BOOKMAKER ODDS:
  → Les cotes impliquent: "France 51.3%, Draw 28.6%, Iran 25%"
  → Note la différence!

🎯 IMPLIED PROBABILITIES:
  → Les cotes incluent une "marge" (~5% overround)
  → Overround = commission du bookmaker

💡 VALUE OPPORTUNITIES:
  → "Expected Value: +5.00%" = BET AVEC VALEUR! ✅
  → "Expected Value: -2.50%" = Pas de valeur ❌

🎯 RECOMMENDATION:
  → "BET ON: X (Draw)" = Meilleur pari avec edge positif


# ============================================================================
# 💡 CONCEPT: VALUE BETTING
# ============================================================================

Value betting = Parier quand la vraie probabilité > cote implicite

Exemple:
  • Ton modèle prédit: Draw 30% = Cote réelle devrait être 3.33
  • Bookmaker offre: Draw à 3.50 (plus généreuse!)
  • C'est un VALUE BET: tu as un edge statistique
  • EV = (30% × 3.50) - 70% = +5% par pari

À long terme:
  • +5% edge sur chaque pari
  • 1000 paris × +5% = +50% ROI! 🚀


# ============================================================================
# 🎲 KELLY CRITERION
# ============================================================================

Kelly % = Taille optimale du pari en fonction de l'edge

Exemples:
  • Edge +5%: Kelly = 0.01% de ton bankroll
  • Edge +10%: Kelly = 0.03% de ton bankroll
  • Nous utilisons Kelly Fraction (25%) = ULTRA CONSERVATEUR

Conseil: Ne jamais dépasser 5% du bankroll par pari


# ============================================================================
# 📊 EXAMPLE: France vs Iran
# ============================================================================

Input:
  Match: France vs Iran
  Proba: 50% (France), 30% (Draw), 20% (Iran)
  Cotes: 1.95 (France), 3.50 (Draw), 4.00 (Iran)

Output:
  ✅ France (1): EV = -2.50% → Ne pas parier
  ✅ Draw (X): EV = +5.00% → PARIER ICI! 🎯
  ✅ Iran (2): EV = -20.00% → Ne pas parier

Recommendation:
  "BET ON: Draw (X) with +5% expected edge"

Interprétation:
  • Sur 100 paris similaires: +5€ de profit par pari
  • 100 × 5€ = 500€ de profit total


# ============================================================================
# 🔄 WORKFLOW COMPLET
# ============================================================================

1. TON MODÈLE PRÉDIT:
   python scripts/predict_matches.py --league "Ligue 1" --season 2025 --version v1.0
   → Donne: France 50%, Draw 30%, Iran 20%

2. TU RÉCUPÈRES LES COTES:
   • Sur les sites de paris: 1.95, 3.50, 4.00
   • Ou depuis une API (Pinnacle, SmarketsBet)

3. TU ANALYSES LA VALEUR:
   python scripts/analyze_value.py \
     --match-name "France vs Iran" \
     --prob-1 0.50 --prob-x 0.30 --prob-2 0.20 \
     --odds-1 1.95 --odds-x 3.50 --odds-2 4.00

4. LE SYSTÈME RECOMMANDE:
   "BET ON: Draw (X)" ✅

5. TU PLACES TON PARI:
   • Montant: Kelly fraction (0.01% du bankroll)
   • Outcome: +5% edge statistique long-terme 🎯


# ============================================================================
# 🚀 NEXT STEPS: ÉTAPE 4 - BACKTESTING
# ============================================================================

Le système va bientôt pouvoir:
  1. Analyser des milliers de matches historiques
  2. Identifier tous les value bets (EV > 0)
  3. Simuler les paris avec Kelly Criterion
  4. Calculer ROI, Sharpe Ratio, Drawdown max
  5. Générer un rapport de performance

Cela t'aidera à valider si le modèle est vraiment profitable! 📊


# ============================================================================
# 💾 FILES CREATED
# ============================================================================

src/models/value_analyzer.py
  → Core logic pour analyser la valeur
  → Méthodes:
    • odds_to_probability()
    • calculate_expected_value()
    • analyze_match_odds()
    • kelly_criterion()
    • print_analysis()

scripts/analyze_value.py
  → CLI pour analyser un match spécifique
  → Usage: python scripts/analyze_value.py --match-name "X vs Y" ...

scripts/predict_real_match.py
  → Prédit un match réel avec données de stats
  → Auto-calcul des features depuis données de base

scripts/value_check.py
  → Mode interactif ultra-simple
  → Usage: python scripts/value_check.py


# ============================================================================
# ⚠️ IMPORTANT
# ============================================================================

⚠️ Ces outils sont pour l'ANALYSE uniquement
   Ne place de vrais paris que si tu comprends les risques!

⚠️ Le modèle peut se tromper
   Edge statistique + long-terme = profit, mais variance courte-terme existe

⚠️ Cotes varient rapidement
   Récupère-les au dernier moment avant de parier

⚠️ Les bookmakers ajustent aussi
   Si c'est clairement une valeur, les cotes changeront

🎯 Conseils:
  ✅ Teste d'abord avec des small bets
  ✅ Utilise Kelly Criterion conservateur (1/4 Kelly)
  ✅ Suit tes résultats sur un spreadsheet
  ✅ Cherche des patterns dans l'edge


# ============================================================================
# 📧 SUPPORT
# ============================================================================

Questions? Besoin d'aide?
  → Regarde les logs du terminal
  → Vérifie que tes probabilities somment à 1.0
  → Assure-toi que les cotes sont en format décimal (1.95, pas -105)

Happy betting! 🚀
"""

# Ce fichier est documentatif. Pour utiliser:
# python scripts/value_check.py
