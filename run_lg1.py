import os
import sqlite3
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lg1_data.db")

TEAM_NAME_MAP = {
    "Paris Saint-Germain": "Paris Saint-Germain", "PSG": "Paris Saint-Germain",
    "AS Monaco": "AS Monaco", "Monaco": "AS Monaco",
    "Marseille": "Marseille", "Olympique de Marseille": "Marseille",
    "Lille": "Lille", "LOSC Lille": "Lille",
    "Lyon": "Lyon", "Olympique Lyonnais": "Lyon",
    "Stade Rennais": "Stade Rennais", "Rennes": "Stade Rennais",
    "Lens": "Lens", "RC Lens": "Lens",
    "Nice": "Nice", "OGC Nice": "Nice",
    "Brest": "Brest", "Stade Brestois": "Brest",
    "Toulouse": "Toulouse",
    "Strasbourg": "Strasbourg",
    "AJ Auxerre": "AJ Auxerre", "Auxerre": "AJ Auxerre",
    "Le Havre AC": "Le Havre AC", "Le Havre": "Le Havre AC",
    "Angers": "Angers", "Angers SCO": "Angers",
    "Lorient": "Lorient", "FC Lorient": "Lorient",
    "Troyes": "Troyes", "ESTAC Troyes": "Troyes",
    "Paris FC": "Paris FC",
    "Le Mans": "Le Mans"
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
        # France Local Time: CEST in summer (UTC+2), CET in winter (UTC+1)
        dt_fr = dt_utc.astimezone(timezone(timedelta(hours=2)))
        # KST Time: UTC+9
        dt_kst = dt_utc.astimezone(timezone(timedelta(hours=9)))
        return dt_fr.strftime("%Y-%m-%d"), dt_kst.strftime("%Y-%m-%d")
    except Exception:
        return date_str[:10], date_str[:10]

OFFICIAL_STATS = {
    "Ousmane Dembélé": (7.70, 0.45), "Bradley Barcola": (7.65, 0.40), "Vitinha": (7.60, 0.20),
    "Achraf Hakimi": (7.55, 0.15), "Warren Zaïre-Emery": (7.50, 0.15), "Gianluigi Donnarumma": (7.45, 0.0),
    "Marquinhos": (7.45, 0.05), "Nuno Mendes": (7.40, 0.10), "João Neves": (7.50, 0.15),
    "Gonçalo Ramos": (7.40, 0.50), "Désiré Doué": (7.35, 0.25),
    "Aleksandr Golovin": (7.50, 0.25), "Denis Zakaria": (7.40, 0.15), "Folarin Balogun": (7.35, 0.40),
    "Bremer": (7.55, 0.05), "Breel Embolo": (7.30, 0.35), "Maghnes Akliouche": (7.40, 0.30),
    "Vanderson": (7.35, 0.10), "Radosław Majecki": (7.25, 0.0),
    "Mason Greenwood": (7.65, 0.55), "Elye Wahi": (7.35, 0.40), "Pierre-Emile Højbjerg": (7.45, 0.15),
    "Adrien Rabiot": (7.50, 0.20), "Leonardo Balerdi": (7.35, 0.05), "Gerónimo Rulli": (7.30, 0.0),
    "Jonathan Rowe": (7.30, 0.30),
    "Jonathan David": (7.65, 0.60), "Edon Zhegrova": (7.50, 0.35), "Angel Gomes": (7.40, 0.15),
    "Bafodé Diakité": (7.35, 0.08), "Lucas Chevalier": (7.40, 0.0), "Benjamin André": (7.30, 0.10),
    "Rayan Cherki": (7.45, 0.25), "Alexandre Lacazette": (7.55, 0.50), "Georges Mikautadze": (7.40, 0.45),
    "Malick Fofana": (7.35, 0.30), "Lucas Perri": (7.25, 0.0), "Nemanja Matić": (7.30, 0.05),
    "Florian Sotoca": (7.25, 0.25), "Andy Diouf": (7.25, 0.15), "Brice Samba": (7.35, 0.0),
    "Przemysław Frankowski": (7.25, 0.10),
    "Terem Moffi": (7.35, 0.45), "Jeremie Boga": (7.30, 0.25), "Gaëtan Laborde": (7.30, 0.35),
    "Marcin Bułka": (7.35, 0.0), "Dante": (7.25, 0.05),
    "Amine Gouiri": (7.35, 0.35), "Ludovic Blas": (7.30, 0.25), "Arnaud Kalimuendo": (7.35, 0.40),
    "Steve Mandanda": (7.25, 0.0),
    "Romain Del Castillo": (7.35, 0.30), "Ludovic Ajorque": (7.30, 0.35), "Pierre Lees-Melou": (7.40, 0.20),
    "Marco Bizot": (7.30, 0.0),
    "Emanuel Emegha": (7.25, 0.35), "Andrey Santos": (7.30, 0.20), "Sebastian Nanasi": (7.30, 0.25),
    "Djordje Petrovic": (7.25, 0.0),
    "Vincent Sierro": (7.25, 0.20), "Guillaume Restes": (7.25, 0.0),
    "Donovan Léon": (7.15, 0.0), "Lassine Sinayoko": (7.15, 0.25),
    "Arthur Desmas": (7.15, 0.0), "Emmanuel Sabbi": (7.10, 0.20),
    "Himad Abdelli": (7.15, 0.15), "Yahia Fofana": (7.15, 0.0),
    "Yvon Mvogo": (7.15, 0.0), "Laurent Abergel": (7.15, 0.10),
    "Xavier Chavalerin": (7.05, 0.10), "Nicolas Lemaître": (7.00, 0.0),
    "Ilan Kebbal": (7.15, 0.20), "Obed Nkambadio": (7.05, 0.0),
    "Dame Gueye": (7.00, 0.15), "Nicolas Kocik": (6.95, 0.0)
}

TEAM_CONCEDED_PER_GAME = {
    "Paris Saint-Germain": 0.80, "Lille": 0.95, "Nice": 1.00, "AS Monaco": 1.05,
    "Marseille": 1.10, "Lens": 1.15, "Brest": 1.20, "Lyon": 1.25,
    "Stade Rennais": 1.30, "Strasbourg": 1.35, "Toulouse": 1.40, "AJ Auxerre": 1.45,
    "Le Havre AC": 1.50, "Lorient": 1.55, "Angers": 1.60, "Troyes": 1.65,
    "Paris FC": 1.70, "Le Mans": 1.75
}

TEAM_GOALS_PER_GAME = {
    "Paris Saint-Germain": 2.30, "AS Monaco": 1.95, "Marseille": 1.90, "Lille": 1.80,
    "Lyon": 1.70, "Lens": 1.50, "Nice": 1.50, "Stade Rennais": 1.45,
    "Brest": 1.40, "Strasbourg": 1.30, "Toulouse": 1.20, "AJ Auxerre": 1.15,
    "Angers": 1.05, "Lorient": 1.05, "Le Havre AC": 1.00, "Troyes": 0.95,
    "Paris FC": 0.90, "Le Mans": 0.85
}

LOW_POSSESSION_TEAMS = ["Angers", "Le Havre AC", "Lorient", "Troyes", "Paris FC", "Le Mans", "AJ Auxerre"]

MATCHWEEK_1_ABSENCES = {
    "Paris Saint-Germain": ["Lucas Hernández"],
    "AS Monaco": ["Edan Diop"],
    "Marseille": ["Valentin Rongier"],
    "Lille": ["Ethan Mbappé"],
    "Lyon": ["Ernest Nuamah"]
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
    url_mw1 = "https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard?dates=20260815-20260825"
    url_mw2 = "https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard?dates=20260826-20260901"
    url_mw3 = "https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard?dates=20260902-20260908"
    
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
    print("✅ Pipeline run complete! lg1_data.db successfully updated.")

if __name__ == "__main__":
    print(f"🚀 Ligue 1 (LG1) 정규 시즌 파이프라인 시작 (개인 UV 0.1~2.0 & 팀 11.0 WUV 합성 로직 적용)", flush=True)
    run_pipeline()
