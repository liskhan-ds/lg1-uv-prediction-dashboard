import os
import sqlite3
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sra_data.db")

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

def parse_espn_date(date_str):
    if not date_str:
        return "", ""
    try:
        dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # France / Italy Time: CEST in summer (UTC+2), CET in winter (UTC+1)
        dt_fr = dt_utc.astimezone(timezone(timedelta(hours=2)))
        # KST Time: UTC+9
        dt_kst = dt_utc.astimezone(timezone(timedelta(hours=9)))
        return dt_fr.strftime("%Y-%m-%d"), dt_kst.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10], date_str[:10]

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

def load_rosters_from_json():
    json_path = os.path.join(BASE_DIR, "rosters_2026.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load rosters_2026.json: {e}")
    return {}

TEAMS_ROSTER = load_rosters_from_json()

def ensure_team_roster(team_name):
    if team_name not in TEAMS_ROSTER:
        TEAMS_ROSTER[team_name] = {
            "starters": [
                {"pos": "GK", "name": f"{team_name} GK", "att_uv": 0.15, "def_uv": 0.45},
                {"pos": "DF", "name": f"{team_name} DF1", "att_uv": 0.30, "def_uv": 0.45},
                {"pos": "DF", "name": f"{team_name} DF2", "att_uv": 0.25, "def_uv": 0.50},
                {"pos": "DF", "name": f"{team_name} DF3", "att_uv": 0.25, "def_uv": 0.50},
                {"pos": "DF", "name": f"{team_name} DF4", "att_uv": 0.35, "def_uv": 0.40},
                {"pos": "MF", "name": f"{team_name} MF1", "att_uv": 0.40, "def_uv": 0.45},
                {"pos": "MF", "name": f"{team_name} MF2", "att_uv": 0.40, "def_uv": 0.45},
                {"pos": "MF", "name": f"{team_name} MF3", "att_uv": 0.55, "def_uv": 0.35},
                {"pos": "FW", "name": f"{team_name} FW1", "att_uv": 0.60, "def_uv": 0.25},
                {"pos": "FW", "name": f"{team_name} FW2", "att_uv": 0.60, "def_uv": 0.25},
                {"pos": "FW", "name": f"{team_name} FW3", "att_uv": 0.65, "def_uv": 0.20},
            ],
            "subs": [
                {"pos": "FW", "name": f"{team_name} Sub1", "att_uv": 0.50, "def_uv": 0.20},
                {"pos": "MF", "name": f"{team_name} Sub2", "att_uv": 0.40, "def_uv": 0.30},
                {"pos": "MF", "name": f"{team_name} Sub3", "att_uv": 0.35, "def_uv": 0.35},
                {"pos": "DF", "name": f"{team_name} Sub4", "att_uv": 0.20, "def_uv": 0.40},
                {"pos": "GK", "name": f"{team_name} Sub5", "att_uv": 0.10, "def_uv": 0.35},
            ]
        }

def get_team_roster(team_name, absentees=None):
    std_tname = normalize_team_name(team_name)
    ensure_team_roster(std_tname)
    roster = TEAMS_ROSTER.get(std_tname, {"starters": [], "subs": []})
    if isinstance(roster, list):
        available = [p for p in roster if p.get("name") not in (absentees or [])]
        gks = [p for p in available if p.get("pos") in ["G", "GK"]]
        dfs = [p for p in available if p.get("pos") in ["D", "DF"]]
        mfs = [p for p in available if p.get("pos") in ["M", "MF"]]
        fws = [p for p in available if p.get("pos") in ["F", "FW"]]
        starters = gks[:1] + dfs[:4] + mfs[:3] + fws[:3]
        subs = (gks[1:2] + dfs[4:6] + mfs[3:5] + fws[3:5])[:5]
        return {"starters": starters, "subs": subs}
    
    starters = list(roster.get("starters", []))
    subs = list(roster.get("subs", []))
    
    if absentees:
        active_starters = [p for p in starters if p.get("name") not in absentees]
        missing_count = len(starters) - len(active_starters)
        if missing_count > 0:
            available_subs = [p for p in subs if p.get("name") not in absentees]
            substitutes = available_subs[:missing_count]
            starters = active_starters + substitutes
            
    return {"starters": starters, "subs": subs}

def calculate_player_uv(player_data, team_name=""):
    p_name = player_data.get("name", "")
    p_pos = player_data.get("pos", "MF")
    
    if p_name in OFFICIAL_STATS:
        rating, xg_90 = OFFICIAL_STATS[p_name]
    else:
        rating = 6.80
        xg_90 = 0.10
        
    std_tname = normalize_team_name(team_name)
    conceded_per_game = TEAM_CONCEDED_PER_GAME.get(std_tname, 1.40)
    def_uv = max(0.1, round(0.50 * (rating / 7.0) * (1.20 / max(0.5, conceded_per_game)), 2))
    
    goals_per_game = TEAM_GOALS_PER_GAME.get(std_tname, 1.30)
    
    pos_clean = "GK" if p_pos in ["G", "GK"] else ("DF" if p_pos in ["D", "DF"] else ("MF" if p_pos in ["M", "MF"] else "FW"))
    
    if pos_clean == "FW":
        base_att = 0.65 * (rating / 7.0) * (1.0 + xg_90)
    elif pos_clean == "MF":
        base_att = 0.45 * (rating / 7.0) * (1.0 + (xg_90 * 0.5))
    elif pos_clean == "DF":
        base_att = 0.30 * (rating / 7.0)
    else:
        base_att = 0.15 * (rating / 7.0)
        
    att_uv = max(0.1, round(base_att * (goals_per_game / 1.30), 2))
    
    att_uv = min(2.0, max(0.1, att_uv))
    def_uv = min(2.0, max(0.1, def_uv))
    
    return {"att_uv": att_uv, "def_uv": def_uv, "total_uv": att_uv + def_uv}

def calculate_wuv(team_name, absentees=None):
    std_tname = normalize_team_name(team_name)
    roster_info = get_team_roster(std_tname, absentees)
    starters = roster_info["starters"]
    
    att_list = []
    def_list = []
    
    for p in starters:
        uv_res = calculate_player_uv(p, std_tname)
        att_list.append(uv_res["att_uv"])
        def_list.append(uv_res["def_uv"])
        
    raw_team_att = sum(att_list) if att_list else 5.5
    raw_team_def = sum(def_list) if def_list else 5.5
    raw_team_uv = raw_team_att + raw_team_def
    
    goals_pg = TEAM_GOALS_PER_GAME.get(std_tname, 1.30)
    conc_pg = TEAM_CONCEDED_PER_GAME.get(std_tname, 1.40)
    
    off_factor = goals_pg / 1.40
    def_factor = 1.30 / conc_pg
    
    if std_tname in LOW_POSSESSION_TEAMS:
        tactical_mod = 0.95
    else:
        tactical_mod = 1.05
        
    scaled_team_uv = 11.0 * (raw_team_uv / 11.0) * (0.4 * off_factor + 0.4 * def_factor + 0.2 * tactical_mod)
    scaled_team_uv = max(8.5, min(14.5, round(scaled_team_uv, 2)))
    
    return {
        "team_name": std_tname,
        "raw_team_uv": round(raw_team_uv, 2),
        "team_wuv": scaled_team_uv,
        "starters_count": len(starters)
    }

def get_match_prediction(home_team, away_team):
    h_info = calculate_wuv(home_team)
    a_info = calculate_wuv(away_team)
    
    h_total = h_info["team_wuv"] + 0.25
    a_total = a_info["team_wuv"]
    
    gap = h_total - a_total
    
    if abs(gap) <= 0.40:
        winner = "Draw"
        code = "DRAW"
    elif gap > 0.40:
        winner = f"{home_team} Win"
        code = "HOME"
    else:
        winner = f"{away_team} Win"
        code = "AWAY"
        
    z = gap
    lh = 1.55 * z
    la = -1.55 * z
    ld = 0.35 - 1.25 * abs(z)
    
    eh, ed, ea = np.exp(lh), np.exp(ld), np.exp(la)
    tot = eh + ed + ea
    
    p_home = round((eh / tot) * 100, 1)
    p_draw = round((ed / tot) * 100, 1)
    p_away = round((ea / tot) * 100, 1)
    
    sc_h = int(round(1.35 * (h_total / 11.0)))
    sc_a = int(round(1.35 * (a_total / 11.0)))
    
    if code == "DRAW":
        sc_h = sc_a = int(round((sc_h + sc_a) / 2.0))
    elif code == "HOME" and sc_h <= sc_a:
        sc_h = sc_a + 1
    elif code == "AWAY" and sc_a <= sc_h:
        sc_a = sc_h + 1
        
    return {
        "home_wuv": h_info,
        "away_wuv": a_info,
        "h_total": h_total,
        "a_total": a_total,
        "gap": gap,
        "winner": winner,
        "code": code,
        "p_home": p_home,
        "p_draw": p_draw,
        "p_away": p_away,
        "sc_h": sc_h,
        "sc_a": sc_a
    }

def run_pipeline():
    url_mw1 = "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard?dates=20260820-20260825"
    url_mw2 = "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard?dates=20260826-20260901"
    url_mw3 = "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard?dates=20260902-20260908"
    
    try:
        resp_mw1 = requests.get(url_mw1, timeout=10).json()
        resp_mw2 = requests.get(url_mw2, timeout=10).json()
        resp_mw3 = requests.get(url_mw3, timeout=10).json()
    except Exception as e:
        print(f"Error fetching ESPN API: {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id TEXT UNIQUE,
        round_name TEXT NOT NULL,
        home_team TEXT NOT NULL,
        away_team TEXT NOT NULL,
        match_date TEXT NOT NULL,
        fr_date TEXT,
        kst_date TEXT,
        home_wuv REAL NOT NULL,
        away_wuv REAL NOT NULL,
        home_total_wuv REAL NOT NULL,
        away_total_wuv REAL NOT NULL,
        gap REAL NOT NULL,
        predicted_winner TEXT NOT NULL,
        prob_home REAL NOT NULL,
        prob_draw REAL NOT NULL,
        prob_away REAL NOT NULL,
        score_home INTEGER NOT NULL,
        score_away INTEGER NOT NULL,
        actual_score_home INTEGER,
        actual_score_away INTEGER,
        actual_winner TEXT,
        is_correct INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("PRAGMA table_info(predictions)")
    cols = [r[1] for r in cursor.fetchall()]
    if "fr_date" not in cols:
        cursor.execute("ALTER TABLE predictions ADD COLUMN fr_date TEXT")
    if "kst_date" not in cols:
        cursor.execute("ALTER TABLE predictions ADD COLUMN kst_date TEXT")

    def process_espn_events(events, round_label, mw_prefix):
        for idx, e in enumerate(events, 1):
            comp = e.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
                
            home_comp = competitors[0] if competitors[0].get("homeAway") == "home" else competitors[1]
            away_comp = competitors[1] if competitors[0].get("homeAway") == "home" else competitors[0]
            
            h_team_raw = home_comp.get("team", {}).get("displayName", "")
            a_team_raw = away_comp.get("team", {}).get("displayName", "")
            
            h_team = normalize_team_name(h_team_raw)
            a_team = normalize_team_name(a_team_raw)
            
            date_raw = e.get("date", "")
            fr_d, kst_d = parse_espn_date(date_raw)
            
            status_type = e.get("status", {}).get("type", {}).get("name", "")
            is_completed = (status_type == "STATUS_FULL_TIME")
            is_cancelled = status_type in ["STATUS_POSTPONED", "STATUS_CANCELED", "STATUS_SUSPENDED", "STATUS_ABANDONED"]
            
            act_sc_h = int(home_comp.get("score")) if (is_completed and home_comp.get("score") is not None) else None
            act_sc_a = int(away_comp.get("score")) if (is_completed and away_comp.get("score") is not None) else None
            
            if is_completed and act_sc_h is not None and act_sc_a is not None:
                if act_sc_h > act_sc_a:
                    act_winner = f"{h_team} Win"
                elif act_sc_a > act_sc_h:
                    act_winner = f"{a_team} Win"
                else:
                    act_winner = "Draw"
            elif is_cancelled:
                act_winner = "Postponed"
            else:
                act_winner = None
                
            mid = f"2026_{mw_prefix}_{idx}"
            
            cursor.execute("SELECT predicted_winner FROM predictions WHERE match_id = ?", (mid,))
            existing = cursor.fetchone()
            
            if existing:
                pred_winner = existing[0]
                if is_completed and act_winner is not None:
                    if (act_winner == pred_winner) or (h_team in act_winner and h_team in pred_winner) or (a_team in act_winner and a_team in pred_winner):
                        is_corr = 1
                    else:
                        is_corr = 0
                else:
                    is_corr = None
                    
                cursor.execute("""
                UPDATE predictions SET
                    fr_date = ?,
                    kst_date = ?,
                    actual_score_home = ?,
                    actual_score_away = ?,
                    actual_winner = ?,
                    is_correct = ?
                WHERE match_id = ?
                """, (fr_d, kst_d, act_sc_h, act_sc_a, act_winner, is_corr, mid))
            else:
                pred = get_match_prediction(h_team, a_team)
                pred_winner = pred["winner"]
                
                if is_completed and act_winner is not None:
                    if (act_winner == pred_winner) or (h_team in act_winner and h_team in pred_winner) or (a_team in act_winner and a_team in pred_winner):
                        is_corr = 1
                    else:
                        is_corr = 0
                else:
                    is_corr = None
                    
                cursor.execute("""
                INSERT INTO predictions (
                    match_id, round_name, home_team, away_team, match_date, fr_date, kst_date,
                    home_wuv, away_wuv, home_total_wuv, away_total_wuv,
                    gap, predicted_winner, prob_home, prob_draw, prob_away,
                    score_home, score_away,
                    actual_score_home, actual_score_away, actual_winner, is_correct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    mid, round_label, h_team, a_team, date_raw[:10], fr_d, kst_d,
                    pred["home_wuv"]["team_wuv"], pred["away_wuv"]["team_wuv"], pred["h_total"], pred["a_total"],
                    pred["gap"], pred_winner, pred["p_home"], pred["p_draw"], pred["p_away"],
                    pred["sc_h"], pred["sc_a"],
                    act_sc_h, act_sc_a, act_winner, is_corr
                ))

    process_espn_events(resp_mw1.get("events", []), "Round 1 (Gameweek 1)", "MW1")
    process_espn_events(resp_mw2.get("events", []), "Round 2 (Gameweek 2)", "MW2")
    process_espn_events(resp_mw3.get("events", []), "Round 3 (Gameweek 3)", "MW3")

    conn.commit()
    conn.close()
    print("✅ Pipeline run complete! sra_data.db successfully updated.")

if __name__ == "__main__":
    print(f"🚀 Serie A (SRA) 정규 시즌 파이프라인 시작 (개인 UV 0.1~2.0 & 팀 11.0 WUV 합성 로직 적용)", flush=True)
    run_pipeline()
