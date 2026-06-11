# Football-Data.org API - Documentation

## 🔗 Endpoint Used
- **API Version:** v4
- **Base URL:** `https://api.football-data.org/v4`
- **Free Tier:** No authentication token required

---

## ⚠️ **Limitations du Free Tier**

### 1. **Erreur 403 - Accès Refusé**
- L'accès aux données détaillées des compétitions (World Cup, Euro, etc.) nécessite un **token payant**
- Football-data.org limite les données complètes aux utilisateurs payants

### 2. **Compétitions Accessibles (Free Tier)**
```
Certaines compétitions sont libres:
- Ligue 1 (FL1), Premier League (PL), La Liga (PD), Serie A (SA)
- Quelques coupes nationales
- UEFA Champions League (CL), Europa League (EL)
- But: NOT World Cup teams, Copa America, African Cup
```

### 3. **Solution Implémentée: Mock Database**
Au lieu de dépendre entièrement de l'API, le système utilise:

**Stratégie Hybride:**
1. ✅ **Essai d'API** (2s timeout pour chaque compétition)
2. ✅ **Fallback à BD Mock** si API timeout/403/non trouvé
3. ✅ **Stats Fixes** (Elo déterministe, pas random)

---

## 🎯 **Équipes Supportées (Mock Database)**

### Elite National Teams (Elo 1680-1705)
- France, Brazil/Brésil, Argentina/Argentine, Germany/Allemagne, Spain/Espagne

### Strong Teams (Elo 1590-1655)
- England/Angleterre, Netherlands/Pays-Bas, Belgium/Belgique, Portugal
- Italy/Italie, Uruguay, Croatia/Croatie, Switzerland/Suisse
- Denmark/Danemark, Sweden/Suède

### Americas (Elo 1520-1550)
- **Mexico/Mexique: 1550** ✅
- United States/USA/États-Unis: 1535
- Canada: 1520

### African Teams (Elo 1440-1510)
- **South Africa/Afrique du Sud: 1480** ✅
- Nigeria: 1510
- Senegal/Sénégal: 1505
- Egypt/Égypte: 1495
- Morocco/Maroc: 1490
- Cameroon/Cameroun: 1475
- Tunisia/Tunisie: 1460
- Ivory Coast/Côte d'Ivoire: 1455
- Ghana: 1440

### Club Teams
- PSG: 1660, Real Madrid: 1700, Barcelona: 1680, Lyon: 1550

---

## 🛠️ **Comment Ajouter de Nouvelles Équipes**

1. **Localiser le fichier:** `src/data/api_fetcher.py`
2. **Modifier la fonction:** `_search_mock_teams()` → `mock_teams` dict
3. **Format:** 
```python
'Team Name': {
    'id': unique_id,  # Numéro unique
    'name': 'Full Name',
    'shortName': 'Short',
    'tla': 'TLA',  # 3-letter code
    'crest': '',
    'elo': 1500  # Ranking power
}
```

4. **Ajouter à la base de stats:** `estimate_team_stats()` → `elo_database` dict

---

## 📊 **Architecture Courante**

```
User Input: "Mexico vs South Africa"
            ↓
    [search_team("Mexico")]
            ↓
    [Essai API (2s timeout)]
            ↓
    [API non accessible/403]
            ↓
    [Fallback: Mock DB]
            ↓
    [Trouvé dans _search_mock_teams()]
            ↓
    [estimate_team_stats("Mexico") → Elo: 1550]
            ↓
    [Prédiction avec stats fixes]
```

---

## 🔑 **Points Clés**

| Point | Solution |
|-------|----------|
| Mock data aleatoire? | ❌ NON - Stats fixes par équipe |
| Mexico trouvé? | ✅ OUI - Elo 1550 dans mock DB |
| Afrique du Sud? | ✅ OUI - Elo 1480 dans mock DB |
| Timeout de l'API? | ✅ Réduit à 2s, fallback rapide |
| Données déterministes? | ✅ OUI - Elo identique chaque exécution |

---

## 💡 **Pour l'Avenir (Étapes 5+)**

Pour accéder aux **vraies données** avec token:
1. S'inscrire sur [football-data.org](https://www.football-data.org/client/register)
2. Récupérer le token gratuit (Free Tier)
3. Passer le token via `HEADERS = {"X-Auth-Token": "YOUR_TOKEN"}`
4. Données plus complètes accessibles (environ 100+ compétitions)

---

**Références:**
- https://www.football-data.org/
- API: https://api.football-data.org/v4/
- Documentationaccompagnement Elo: https://en.wikipedia.org/wiki/Elo_rating_system
