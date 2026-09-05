import os
import json
import sqlite3
import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sra_data.db")
ROSTER_PATH = os.path.join(BASE_DIR, "rosters_2026.json")

TEAM_NAME_MAP = {
    "Internazionale": "Internazionale", "Inter Milan": "Internazionale", "Inter": "Internazionale",
    "AC Milan": "AC Milan", "Milan": "AC Milan",
    "Juventus": "Juventus",
    "Napoli": "Napoli",
    "Atalanta": "Atalanta",
    "AS Roma": "AS Roma", "Roma": "AS Roma",
    "Lazio": "Lazio",
    "Fiorentina": "Fiorentina",
    "Bologna": "Bologna",
    "Torino": "Torino",
    "Genoa": "Genoa",
    "Udinese": "Udinese",
    "Cagliari": "Cagliari",
    "Parma": "Parma",
    "Monza": "Monza",
    "Como": "Como",
    "Lecce": "Lecce",
    "Venezia": "Venezia",
    "Sassuolo": "Sassuolo",
    "Frosinone": "Frosinone"
}

def normalize_team_name(raw_name):
    for key, val in TEAM_NAME_MAP.items():
        if key.lower() in raw_name.lower() or raw_name.lower() in key.lower():
            return val
    return raw_name

OFFICIAL_STATS = {
    "Lautaro Martínez": (7.80, 0.70), "Nicolò Barella": (7.65, 0.20), "Alessandro Bastoni": (7.55, 0.05),
    "Hakan Çalhanoğlu": (7.55, 0.25), "Marcus Thuram": (7.50, 0.45), "Benjamin Pavard": (7.40, 0.05),
    "Yann Sommer": (7.35, 0.0), "Federico Dimarco": (7.50, 0.15), "Denzel Dumfries": (7.30, 0.10),
    "Rafael Leão": (7.70, 0.40), "Christian Pulisic": (7.50, 0.35), "Theo Hernández": (7.45, 0.15),
    "Mike Maignan": (7.40, 0.0), "Álvaro Morata": (7.30, 0.40), "Tijjani Reijnders": (7.35, 0.20),
    "Dušan Vlahović": (7.65, 0.60), "Bremer": (7.55, 0.05), "Kenan Yildiz": (7.40, 0.25),
    "Teun Koopmeiners": (7.50, 0.30), "Douglas Luiz": (7.35, 0.15), "Michele Di Gregorio": (7.30, 0.0),
    "Khvicha Kvaratskhelia": (7.65, 0.38), "Romelu Lukaku": (7.55, 0.50), "Alessandro Buongiorno": (7.45, 0.05),
    "Scott McTominay": (7.40, 0.25), "Alex Meret": (7.25, 0.0), "Frank Anguissa": (7.30, 0.10),
    "Ademola Lookman": (7.60, 0.50), "Mateo Retegui": (7.50, 0.55), "Éderson": (7.45, 0.18),
    "Giorgio Scalvini": (7.35, 0.05), "Marco Carnesecchi": (7.30, 0.0), "Charles De Ketelaere": (7.40, 0.28),
    "Paulo Dybala": (7.60, 0.40), "Artem Dovbyk": (7.40, 0.45), "Lorenzo Pellegrini": (7.30, 0.20),
    "Gianluca Mancini": (7.30, 0.08), "Mile Svilar": (7.30, 0.0), "Matias Soulé": (7.30, 0.30),
    "Mattia Zaccagni": (7.35, 0.30), "Valentín Castellanos": (7.25, 0.35), "Matteo Guendouzi": (7.25, 0.12),
    "Ivan Provedel": (7.20, 0.0), "Nuno Tavares": (7.30, 0.05),
    "Moise Kean": (7.35, 0.45), "Albert Guðmundsson": (7.40, 0.35), "David de Gea": (7.30, 0.0),
    "Riccardo Orsolini": (7.30, 0.35), "Santiago Castro": (7.25, 0.30), "Remo Freuler": (7.20, 0.10),
    "Lukasz Skorupski": (7.20, 0.0),
    "Duván Zapata": (7.25, 0.40), "Samuele Ricci": (7.25, 0.10), "Vanja Milinković-Savić": (7.20, 0.0),
    "Andrea Pinamonti": (7.15, 0.35), "Junior Messias": (7.10, 0.20), "Josep Martínez": (7.10, 0.0),
    "Lorenzo Lucca": (7.15, 0.30), "Florian Thauvin": (7.20, 0.25), "Maduka Okoye": (7.10, 0.0),
    "Roberto Piccoli": (7.05, 0.25), "Yerry Mina": (7.10, 0.05), "Simone Scuffet": (7.05, 0.0),
    "Dennis Man": (7.20, 0.30), "Ange-Yoan Bonny": (7.10, 0.25), "Zion Suzuki": (7.10, 0.0),
    "Matteo Pessina": (7.10, 0.15), "Dany Mota": (7.05, 0.20), "Stefano Turati": (7.05, 0.0),
    "Patrick Cutrone": (7.15, 0.35), "Gabriel Strefezza": (7.10, 0.20), "Pepe Reina": (7.00, 0.0),
    "Nikola Krstović": (7.05, 0.30), "Wladimiro Falcone": (7.10, 0.0),
    "Joel Pohjanpalo": (7.10, 0.35), "Jesse Joronen": (7.00, 0.0),
    "Armand Laurienté": (7.20, 0.30), "Domenico Berardi": (7.40, 0.35)
}

TEAM_CONCEDED_PER_GAME = {
    "Internazionale": 0.85, "Juventus": 0.90, "Napoli": 1.00, "AC Milan": 1.10,
    "Atalanta": 1.15, "Lazio": 1.20, "AS Roma": 1.25, "Bologna": 1.25,
    "Fiorentina": 1.30, "Torino": 1.35, "Genoa": 1.40, "Udinese": 1.45,
    "Cagliari": 1.50, "Monza": 1.50, "Parma": 1.55, "Como": 1.60,
    "Lecce": 1.65, "Sassuolo": 1.70, "Venezia": 1.75, "Frosinone": 1.80
}

TEAM_GOALS_PER_GAME = {
    "Internazionale": 2.10, "Atalanta": 2.00, "AC Milan": 1.90, "Juventus": 1.80,
    "Napoli": 1.80, "AS Roma": 1.60, "Lazio": 1.50, "Fiorentina": 1.50,
    "Bologna": 1.40, "Torino": 1.20, "Udinese": 1.15, "Genoa": 1.10,
    "Parma": 1.10, "Sassuolo": 1.10, "Cagliari": 1.05, "Como": 1.05,
    "Monza": 1.00, "Lecce": 0.95, "Venezia": 0.90, "Frosinone": 0.85
}

LOW_POSSESSION_TEAMS = ["Lecce", "Venezia", "Frosinone", "Monza", "Como", "Cagliari", "Parma"]

MATCHWEEK_1_ABSENCES = {
    "Internazionale": ["Tajon Buchanan"],
    "AC Milan": ["Alessandro Florenzi", "Ismaël Bennacer"],
    "Juventus": ["Arkadiusz Milik", "Fabio Miretti"],
    "Atalanta": ["Giorgio Scalvini", "Gianluca Scamacca"],
    "AS Roma": ["Alexis Saelemaekers"]
}

def get_team_roster(team_name, absentees=None):
    if not os.path.exists(ROSTER_PATH):
        return {"starters": [], "subs": []}
    with open(ROSTER_PATH, "r", encoding="utf-8") as f:
        rosters = json.load(f)
        
    std_tname = normalize_team_name(team_name)
    plist = rosters.get(std_tname, [])
    if not plist:
        for k, v in rosters.items():
            if k.lower() in team_name.lower() or team_name.lower() in k.lower():
                plist = v
                break
                
    if absentees is None:
        absentees = MATCHWEEK_1_ABSENCES.get(std_tname, [])
        
    available = [p for p in plist if p.get("name") not in absentees]
    
    for p in available:
        p["calc_uv"] = calculate_player_uv(p, std_tname)
        
    gks = sorted([p for p in available if p.get("pos") in ["G", "GK"]], key=lambda x: x["calc_uv"], reverse=True)
    dfs = sorted([p for p in available if p.get("pos") in ["D", "DF"]], key=lambda x: x["calc_uv"], reverse=True)
    mfs = sorted([p for p in available if p.get("pos") in ["M", "MF"]], key=lambda x: x["calc_uv"], reverse=True)
    fws = sorted([p for p in available if p.get("pos") in ["F", "FW"]], key=lambda x: x["calc_uv"], reverse=True)
    
    starters = gks[:1] + dfs[:4] + mfs[:3] + fws[:3]
    subs = (gks[1:2] + dfs[4:6] + mfs[3:5] + fws[3:5])[:5]
    return {"starters": starters, "subs": subs}

def calculate_player_uv(player_data, team_name=""):
    p_name_raw = player_data.get("name", "")
    
    rating = None
    goals_per90 = 0.0
    position = player_data.get("pos", "M")
    
    matched = False
    for off_name, (off_r, off_g90) in OFFICIAL_STATS.items():
        if off_name.lower() in p_name_raw.lower() or p_name_raw.lower() in off_name.lower():
            rating = off_r
            goals_per90 = off_g90
            matched = True
            break
            
    pos_clean = "GK" if position in ["G", "GK"] else ("DF" if position in ["D", "DF"] else ("MF" if position in ["M", "MF"] else "FW"))
    
    std_tname = normalize_team_name(team_name)
    tgoals = TEAM_GOALS_PER_GAME.get(std_tname, 1.30)
    is_low_poss = std_tname in LOW_POSSESSION_TEAMS
    
    if rating is None:
        if pos_clean == "GK":
            raw_uv = 0.95
        elif pos_clean == "DF":
            raw_uv = 0.90
        elif pos_clean == "MF":
            raw_uv = 0.82 if is_low_poss else 0.88
        else: # FW
            raw_uv = 0.78 if tgoals < 1.1 else 0.85
    elif rating >= 6.65:
        if pos_clean == "GK":
            raw_uv = 1.0 + (rating - 6.65) * 0.45
        elif pos_clean == "DF":
            raw_uv = 1.0 + (rating - 6.65) * 0.40
        elif pos_clean == "MF":
            raw_uv = 1.0 + (rating - 6.65) * 0.35
            if is_low_poss:
                raw_uv -= 0.08
        else: # FW
            raw_uv = 1.0 + (rating - 6.65) * 0.35 + (goals_per90 * 0.20)
            if goals_per90 < 0.15 or tgoals < 1.1:
                fw_penalty = min(0.15, round(0.10 + (0.15 - max(goals_per90, 0.0)) * 0.33, 3))
                raw_uv -= fw_penalty
    else:
        slope = 0.80 if pos_clean == "MF" else 0.65
        raw_uv = 1.0 + (rating - 6.65) * slope + (goals_per90 * 0.20 if pos_clean == "FW" else 0.0)
        if pos_clean == "MF" and is_low_poss:
            raw_uv -= 0.08
        elif pos_clean == "FW" and (goals_per90 < 0.15 or tgoals < 1.1):
            fw_penalty = min(0.15, round(0.10 + (0.15 - max(goals_per90, 0.0)) * 0.33, 3))
            raw_uv -= fw_penalty
        
    conc = TEAM_CONCEDED_PER_GAME.get(std_tname, 1.30)
    if pos_clean in ["GK", "DF"] and conc > 1.4:
        def_penalty = min(0.12, round(0.04 + (conc - 1.4) * 0.10, 3))
        raw_uv -= def_penalty
        
    return round(min(max(raw_uv, 0.4), 2.0), 3)

def calculate_wuv(team_name, absentees=None):
    std_tname = normalize_team_name(team_name)
    roster = get_team_roster(std_tname, absentees=absentees)
    starters = roster.get("starters", [])
    subs = roster.get("subs", [])
    
    st_uvs = [calculate_player_uv(p, std_tname) for p in starters]
    sub_uvs = [calculate_player_uv(p, std_tname) for p in subs]
    
    st_avg = sum(st_uvs) / len(st_uvs) if st_uvs else 0.95
    sub_avg = sum(sub_uvs) / len(sub_uvs) if sub_uvs else 0.85
    
    raw_wuv = (0.85 * st_avg + 0.15 * sub_avg)
    team_wuv = round(11.0 + 10.5 * (raw_wuv - 0.835), 2)
    
    pos_sums = {"GK": 0.0, "DF": 0.0, "MF": 0.0, "FW": 0.0}
    starters_detail = []
    for p in starters:
        uv = calculate_player_uv(p, std_tname)
        pos = p.get("pos", "M")
        pos_clean = "GK" if pos in ["G","GK"] else ("DF" if pos in ["D","DF"] else ("MF" if pos in ["M","MF"] else "FW"))
        pos_sums[pos_clean] += uv
        starters_detail.append({"name": p.get("name"), "pos": pos_clean, "uv": uv})
        
    st_tot_sum = sum(st_uvs)
    gk_wuv = round(team_wuv * (pos_sums["GK"] / st_tot_sum), 2) if st_tot_sum > 0 else 1.0
    df_wuv = round(team_wuv * (pos_sums["DF"] / st_tot_sum), 2) if st_tot_sum > 0 else 4.0
    mf_wuv = round(team_wuv * (pos_sums["MF"] / st_tot_sum), 2) if st_tot_sum > 0 else 3.0
    fw_wuv = round(team_wuv * (pos_sums["FW"] / st_tot_sum), 2) if st_tot_sum > 0 else 3.0
    
    return {
        "team_wuv": team_wuv,
        "st_avg": round(st_avg, 3),
        "sub_avg": round(sub_avg, 3),
        "st_sum": round(st_tot_sum, 3),
        "sub_sum": round(sum(sub_uvs), 3),
        "gk_wuv": gk_wuv,
        "df_wuv": df_wuv,
        "mf_wuv": mf_wuv,
        "fw_wuv": fw_wuv,
        "starters_detail": starters_detail
    }

# -----------------------------------------------------------------------------
# 1. Page Configuration and Unified Top Navigation
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Serie A AI Match Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Top Navigation Bar (7 Leagues)
nav_cols = st.columns(7)
with nav_cols[0]:
    st.link_button("🏀 NBA ↗", "https://nba-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[1]:
    st.link_button("⚾ MLB ↗", "https://mlb-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[2]:
    st.button("⚽ Serie A (Current)", disabled=True, use_container_width=True)
with nav_cols[3]:
    st.link_button("⚽ La Liga ↗", "https://llg-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[4]:
    st.link_button("🏒 NHL ↗", "https://nhl-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[5]:
    st.link_button("🏈 NFL ↗", "https://nfl-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[6]:
    st.link_button("⚽ MLS ↗", "https://mls-uv-prediction.streamlit.app/", use_container_width=True)

st.divider()

# Main Title and Description
st.title("⚽ Serie A AI Match Predictor")

def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame([])
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(predictions)")
        cols = [row[1] for row in cursor.fetchall()]
        
        order_col = "date" if "date" in cols else "id"
        df_db = pd.read_sql_query(f"SELECT * FROM predictions ORDER BY {order_col} ASC", conn)
        conn.close()
        
        if not df_db.empty:
            if "round_name" not in df_db.columns:
                df_db["round_name"] = "Round 1 (Gameweek 1)"
            if "date" not in df_db.columns and "match_date" in df_db.columns:
                df_db["date"] = df_db["match_date"]
            if "fr_date" in df_db.columns:
                df_db["local_date"] = df_db["fr_date"]
            elif "uk_date" in df_db.columns:
                df_db["local_date"] = df_db["uk_date"]
            else:
                df_db["local_date"] = df_db.get("date", df_db.get("match_date", "2026-08"))
            if "kst_date" not in df_db.columns:
                df_db["kst_date"] = df_db.get("date", df_db.get("match_date", "2026-08"))
            if "visit_team" not in df_db.columns and "away_team" in df_db.columns:
                df_db["visit_team"] = df_db["away_team"]
            if "visit_uv" not in df_db.columns and "away_wuv" in df_db.columns:
                df_db["visit_uv"] = df_db["away_wuv"]
            if "home_uv" not in df_db.columns and "home_total_wuv" in df_db.columns:
                df_db["home_uv"] = df_db["home_total_wuv"]
            if "predicted_gap" not in df_db.columns and "gap" in df_db.columns:
                df_db["predicted_gap"] = df_db["gap"]
            if "actual_winner" not in df_db.columns:
                df_db["actual_winner"] = ""
            if "is_correct" not in df_db.columns:
                df_db["is_correct"] = None
                
        return df_db
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame([])

df = load_data()

if not df.empty and "actual_winner" in df.columns:
    df["total_no"] = range(1, len(df) + 1)
    stats_df = df[df["actual_winner"].notna() & (df["actual_winner"] != "")].copy()
else:
    df = pd.DataFrame(columns=[
        "total_no", "date", "local_date", "kst_date", "round_name", "home_team", "visit_team",
        "predicted_winner", "predicted_gap", "prob_home", "prob_draw", "prob_away",
        "home_uv", "visit_uv", "actual_winner", "actual_score_home", "actual_score_away", "is_correct"
    ])
    stats_df = pd.DataFrame([])

st.header("📊 Cumulative Prediction Scorecard")
total_stats = len(stats_df)
correct_total = stats_df['is_correct'].sum() if total_stats > 0 else 0

col_acc, col_track = st.columns([2, 1])

if total_stats > 0:
    total_acc = (correct_total / total_stats) * 100
    status_suffix = " (⚡ God Tier, Market Distortion)" if total_acc >= 55 else ""
    
    with col_acc:
        st.subheader(f"Overall Completed Match Accuracy: `{total_acc:.2f}%`{status_suffix}")
        st.markdown(f"**Correct Predictions:** {int(correct_total)} / **Completed Matches:** {total_stats} (Total Scheduled: {len(df)} Games)")
    
    with col_track:
        remaining = 100 - total_stats
        if remaining > 0:
            st.metric("Matches Until 100-Game System Validation", f"{remaining} Games Remaining")
        else:
            st.metric("System Validation Status", "Validation Complete (God Tier)")
else:
    with col_acc:
        st.subheader(f"Total Target Matches: `{len(df)} Games`")
        st.markdown(f"**Predicted Matches:** {len(df)} Games (Live Accuracy Tallying)")
    with col_track:
        st.metric("System Status", "Live Predictions Active")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. Prediction Scorecard by Round (Serie A Gameweek)
# -----------------------------------------------------------------------------
st.header("📈 Prediction Scorecard by Round (Serie A Gameweek)")

if not stats_df.empty:
    group_col = 'round_name' if 'round_name' in stats_df.columns else 'date'
    round_stats = stats_df.groupby(group_col, sort=False).agg(
        total_games=('home_team', 'count'),
        correct_games=('is_correct', 'sum')
    ).reset_index()

    round_stats['accuracy'] = (round_stats['correct_games'] / round_stats['total_games']) * 100
    
    def get_bar_color(acc):
        if acc >= 55: return '#A020F0'      # Purple (God Tier)
        elif acc >= 50: return '#FF0000'    # Red (Master / AI)
        elif acc >= 45: return '#FFA500'    # Orange (Pro / Expert)
        elif acc >= 38: return '#1E90FF'    # Blue (Hardworking Amateur)
        elif acc >= 30: return '#008000'    # Green (Normal Person)
        else: return '#808080'             # Gray (Do Not Predict)

    round_stats['bar_color'] = round_stats['accuracy'].apply(get_bar_color)
    round_stats['label_text'] = round_stats.apply(
        lambda x: f"{int(x['correct_games'])}/{int(x['total_games'])}", 
        axis=1
    )

    round_stats_7d = round_stats.tail(7)

    base = alt.Chart(round_stats_7d).encode(x=alt.X(group_col, title='Serie A Gameweek', sort=None))
    bars = base.mark_bar().encode(
        y=alt.Y('accuracy', title='Accuracy (%)', scale=alt.Scale(domain=[0, 110])),
        color=alt.Color('bar_color', scale=None),
        tooltip=[group_col, 'accuracy', 'total_games', 'correct_games']
    )
    text = base.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold').encode(
        y='accuracy', text='label_text'
    )
    st.altair_chart((bars + text).properties(height=320), use_container_width=True)
else:
    st.info("💡 Scheduled match predictions complete! (Real-time accuracy by round will be tallied as matches complete.)")

st.markdown("""
<div style="text-align: center; padding: 12px; background-color: #f0f2f6; border-radius: 10px; line-height: 1.6;">
    <span style="color: #A020F0;">●</span> <b>God Tier</b> (55%↑) &nbsp;&nbsp;
    <span style="color: #FF0000;">●</span> <b>Master / AI</b> (50%~55%) &nbsp;&nbsp;
    <span style="color: #FFA500;">●</span> <b>Pro / Expert</b> (45%~50%) &nbsp;&nbsp;
    <span style="color: #1E90FF;">●</span> <b>Hardworking Amateur</b> (38%~45%) &nbsp;&nbsp;
    <span style="color: #008000;">●</span> <b>Normal Person</b> (30%~38%) &nbsp;&nbsp;
    <span style="color: #808080;">●</span> <b>Do Not Predict</b> (30%↓)
    <br><small>* Statistical breakeven is achieved from an average of ~46%-48%+ due to 3-Way (Win/Draw/Loss) nature.</small>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. Gameweek Match Report (Matchup Card List)
# -----------------------------------------------------------------------------
st.header("📋 Gameweek Match Report (10 Matchups)")

def extract_round_num(text):
    import re
    m = re.search(r'Round\s*(\d+)', str(text))
    return int(m.group(1)) if m else 0

if 'round_name' in df.columns:
    unique_dates = sorted(df['round_name'].unique(), key=extract_round_num, reverse=True)
    
    pending_df = df[df['actual_winner'].isna() | (df['actual_winner'] == '')]
    default_idx = 0
    if not pending_df.empty:
        pending_rounds = sorted(pending_df['round_name'].unique(), key=extract_round_num, reverse=False)
        target_round = pending_rounds[0]
        if target_round in unique_dates:
            default_idx = unique_dates.index(target_round)
            
    selected_date = st.selectbox("Select Gameweek to inspect:", unique_dates, index=default_idx)
    filtered_df = df[df['round_name'] == selected_date].copy().reset_index(drop=True)
else:
    unique_dates = sorted(df['date'].unique(), reverse=True)
    selected_date = st.selectbox("Select Gameweek to inspect:", unique_dates, index=0)
    filtered_df = df[df['date'] == selected_date].copy().reset_index(drop=True)

if not filtered_df.empty:
    filtered_df['day_no'] = range(1, len(filtered_df) + 1)
    
    completed_in_round = filtered_df[filtered_df['actual_winner'].notna() & (filtered_df['actual_winner'] != '') & (~filtered_df['actual_winner'].isin(['Postponed', 'Canceled', '경기 연기', '경기 취소', '연기됨', '취소됨']))]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Matches in Gameweek", f"{len(filtered_df)} Matches")
    col2.metric("Completed Matches", f"{len(completed_in_round)} Matches")
    
    if not completed_in_round.empty:
        corr_cnt = int(completed_in_round['is_correct'].sum())
        acc = (corr_cnt / len(completed_in_round)) * 100
        col3.metric("Gameweek Accuracy", f"{acc:.1f}% ({corr_cnt}/{len(completed_in_round)})")
    else:
        col3.metric("Gameweek Accuracy", "⏳ Scheduled")

    # Dashboard report dataframe
    display_df = pd.DataFrame()
    display_df['No.'] = filtered_df['day_no']
    display_df['Match Date (FR)'] = filtered_df['local_date']
    display_df['Match Date (KST)'] = filtered_df['kst_date']
    display_df['Home Team'] = filtered_df.apply(lambda r: f"{r['home_team']} ({r['home_total_wuv']:.2f} WUV)" if ('home_total_wuv' in r and pd.notna(r.get('home_total_wuv'))) else (f"{r['home_team']} ({r['home_uv']:.2f} WUV)" if pd.notna(r.get('home_uv')) else r['home_team']), axis=1)
    display_df['Away Team'] = filtered_df.apply(lambda r: f"{r['visit_team']} ({r['visit_uv']:.2f} WUV)" if pd.notna(r.get('visit_uv')) else r['visit_team'], axis=1)
    display_df['AI Prediction'] = filtered_df['predicted_winner']
    display_df['3-Way Probabilities [Home%|Draw%|Away%]'] = filtered_df.apply(
        lambda r: f"[{r['prob_home']:.1f}% | {r['prob_draw']:.1f}% | {r['prob_away']:.1f}%]", axis=1
    )
    display_df['Predicted Gap (ΔWUV)'] = filtered_df['predicted_gap'].apply(lambda x: f"{x:+.2f}")
    display_df['Actual Result'] = filtered_df.apply(lambda r: f"{int(r['actual_score_home'])} : {int(r['actual_score_away'])} ({r['actual_winner']})" if (pd.notna(r.get('actual_score_home')) and pd.notna(r.get('actual_winner')) and r['actual_winner'] not in ['', 'Postponed', 'Canceled', '경기 연기', '경기 취소', '연기됨', '취소됨']) else (r['actual_winner'] if (pd.notna(r.get('actual_winner')) and r['actual_winner'] != '') else "Pending"), axis=1)
    
    def get_status_tag(r):
        act = r['actual_winner']
        if not act or pd.isna(act) or act == '':
            return "⏳ Pending"
        if act in ['Postponed', 'Canceled', '경기 연기', '경기 취소', '연기됨', '취소됨']:
            return "🚫 Postponed/Canceled"
        return "✅ Correct" if r['is_correct'] == 1 else "❌ Incorrect"
        
    display_df['Status'] = filtered_df.apply(get_status_tag, axis=1)

    st.dataframe(display_df, hide_index=True, use_container_width=True)

# -----------------------------------------------------------------------------
# 9. [최하단] 푸터 문구 (MLB/NBA 템플릿과 100% 동일)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888888; padding-top: 20px;">
        <p>ⓒ DROPSHOT (사업자 번호: 578-81-03214)</p>
        <p>Contact us: liskhan@gmail.com</p>
    </div>
    """,
    unsafe_allow_html=True
)
