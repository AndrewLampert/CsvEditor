"""
HC09 / Franchise CSV Editor (GUI) - HC09 Safe Trade Edition
- Tkinter GUI (no external deps)
- Loads play.csv (players), optional drpk.csv (draft picks), optional slri.csv (salary cap), optional trvw.csv (trainers), optional coch.csv (coaches), optional gmvw.csv (GMs)
- Case-sensitive columns ON PURPOSE (we only normalize invisible junk like BOM/whitespace)
- Stat editor shows ONLY stats that have descriptions (STAT_META)
- MAX columns are HARD-CODED for YOUR export (no duplicates, no guessing)
- Name editor (PFNA/PLNA) is ON the Players + Stats screen (with sanitizing to avoid crashes)
- Raw Column Editor lets you edit ANY column for the selected player
- Trading:
    * If team column is NOT TGID -> you can "Move player to selected team"
    * ALWAYS available: "HC09-SAFE SWAP TRADE" (swap player data across teams WITHOUT changing TGID)

Run:
  python hc09_gui_editor.py
"""

import csv
import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -----------------------------
# CONSTANTS / METADATA
# -----------------------------
TEAM_NAMES = {
    "1": "Bears (Chicago)", "2": "Bengals (Cincinnati)", "3": "Bills (Buffalo)", "4": "Broncos (Denver)",
    "5": "Browns (Cleveland)", "6": "Buccaneers (Tampa Bay)", "7": "Cardinals (Arizona)", "8": "Chargers (Los Angeles)",
    "9": "Chiefs (Kansas City)", "10": "Colts (Indianapolis)", "11": "Cowboys (Dallas)", "12": "Dolphins (Miami)",
    "13": "Eagles (Philadelphia)", "14": "Falcons (Atlanta)", "15": "49ers (San Francisco)", "16": "Giants (New York)",
    "17": "Jaguars (Jacksonville)", "18": "Jets (New York)", "19": "Lions (Detroit)", "20": "Packers (Green Bay)",
    "21": "Panthers (Carolina)", "22": "Patriots (New England)", "23": "Raiders (Las Vegas)", "24": "Rams (Los Angeles)",
    "25": "Ravens (Baltimore)", "26": "Commanders (Washington)", "27": "Saints (New Orleans)", "28": "Seahawks (Seattle)",
    "29": "Steelers (Pittsburgh)", "30": "Titans (Tennessee)", "31": "Vikings (Minnesota)", "32": "Texans (Houston)",
    "33": "Free Agents", "1015": "Draft Class"
}

PLAYER_FIRST_NAME_CODE = "PFNA"
PLAYER_LAST_NAME_CODE = "PLNA"
PLAYER_POS_CODE = "PPOS"
PREFERRED_TEAM_COLS = ["TID", "TEAM", "TMID", "TGID"]  # TGID last as fallback

DRAFT_PICK_ID = "DPID"
DRAFT_PICK_NUM = "DPNM"
DRAFT_PICK_YEAR = "DPYO"

SALARY_CAP_KEY = "SCAD"
AGE_COL = "PAGE"
YEARS_COL = "PYRP"

POSITIONS = {
    "0": "QB", "1": "HB", "2": "FB", "3": "WR", "4": "TE",
    "5": "LT", "6": "LG", "7": "C", "8": "RG", "9": "RT",
    "10": "LE", "11": "RE", "12": "DT", "13": "LOLB", "14": "MLB",
    "15": "ROLB", "16": "CB", "17": "FS", "18": "SS", "19": "K", "20": "P"
}

# Position display order (QB, HB, FB, WR, TE, OL, DL, LB, CB, FS, SS, K, P)
POSITION_ORDER = {
    "0": 0,    # QB
    "1": 1,    # HB
    "2": 2,    # FB
    "3": 3,    # WR
    "4": 4,    # TE
    "5": 5,    # LT
    "6": 6,    # LG
    "7": 7,    # C
    "8": 8,    # RG
    "9": 9,    # RT
    "10": 10,  # LE
    "12": 11,  # DT
    "11": 12,  # RE
    "13": 13,  # LOLB
    "14": 14,  # MLB
    "15": 15,  # ROLB
    "16": 16,  # CB
    "17": 17,  # FS
    "18": 18,  # SS
    "19": 19,  # K
    "20": 20,  # P
}

STAT_MAX_VALUE = 99

# -----------------------------
# Stat descriptions (only these appear in the Stat Editor)
# -----------------------------
STAT_META = {
    "PSPD": ("Speed", "Top-end running speed"),
    "PAGI": ("Agility", "Change of direction / lateral movement"),
    "PACC": ("Acceleration", "Burst to top speed"),
    "PSTR": ("Strength", "Power of player (blocking/tackling)"),
    "PAWR": ("Awareness", "Football IQ and reaction time"),
    "PSTA": ("Stamina", "Fatigue resistance"),
    "PINJ": ("Injury", "Durability / injury resistance"),
    "PLTR": ("Trucking", "Run through tackles / power after contact"),
    "PTGH": ("Toughness", "Plays through hits / durability vs big contact"),
    "PELU": ("Elusiveness", "Jukes and evasive moves"),
    "PBCV": ("Vision", "Ball carrier vision / cutbacks"),
    "PLSA": ("Stiff Arm", "Stiff-arm effectiveness"),
    "PLSM": ("Spin Move", "Spin move success"),
    "PLJM": ("Juke Move", "Juke effectiveness"),
    "PCAR": ("Carrying", "Ball security"),
    "PTHP": ("Throw Power", "QB arm strength"),
    "PTHA": ("Throw Accuracy", "Overall QB accuracy"),
    "PCTH": ("Catching", "Catch reliability"),
    "PLSC": ("Spectacular Catch", "Aggressive catches"),
    "PLCI": ("Catch In Traffic", "Catches through contact"),
    "PLRR": ("Route Running", "Route precision"),
    "PLRL": ("Release", "Beating press coverage"),
    "PJMP": ("Jump", "Vertical leap"),
    "PPBK": ("Pass Block", "Pass protection"),
    "PPBS": ("Pass Block Power", "Anchor vs power rush"),
    "PPBF": ("Pass Block Finesse", "Mirror finesse rush"),
    "PRBK": ("Run Block", "Run blocking"),
    "PRBS": ("Run Block Strength", "Run blocking strength / anchor"),
    "PLIB": ("Impact Blocking", "Dominant run-game blocks"),
    "PTAK": ("Tackling", "Tackle success"),
    "PLHT": ("Hit Power", "Big hit strength"),
    "PRBF": ("Pass Rush Finesse", "Speed/finesse rush"),
    "PLPm": ("Power Move", "DL power pass rush move"),
    "PFMS": ("Finesse Move", "DL finesse pass rush move"),
    "PBSG": ("Block Shed", "Shedding blockers"),
    "PLPU": ("Pursuit", "Closing speed & angles"),
    "PLPR": ("Play Recognition", "Reads plays faster"),
    "PLMC": ("Man Coverage", "Man-to-man coverage"),
    "PLZC": ("Zone Coverage", "Zone awareness"),
    "PLPE": ("Press", "Jam WRs at line"),
    "PKPR": ("Kick Power", "Kicker leg strength"),
    "PKAC": ("Kick Accuracy", "FG accuracy"),
    "PKRT": ("Kick Return", "Return ability"),
    "PLRN": ("Learning", "Development speed"),
}

# -----------------------------
# HARD-CODED MAX columns (matches YOUR header dump)
# Case-sensitive.
# -----------------------------
PLAYER_MAX_HARDCODED = {
    "PSPD": "PSDX",
    "PAGI": "PAGX",
    "PACC": "PACX",
    "PSTR": "PSTX",
    "PAWR": "PAWX",
    "PSTA": "PSAX",
    "PINJ": "PINX",
    "PLTR": "PLTX",
    "PTGH": "PTGX",
    "PELU": "PELX",
    "PBCV": "PBCX",
    "PLSA": "PLSX",
    "PLSM": "PSMx",   # lowercase x in your file
    "PLJM": "PLJX",
    "PCAR": "PCAX",
    "PTHP": "PTPX",
    "PTHA": "PTAX",
    "PCTH": "PCTX",
    "PLSC": "PSCX",
    "PLCI": "PLCX",
    "PLRR": "PRRX",
    "PLRL": "PRLX",
    "PJMP": "PJMX",
    "PPBK": "PPBX",
    "PPBS": "PPSX",
    "PPBF": "PPFX",
    "PRBK": "PRBX",
    "PRBS": "PRSX",
    "PLIB": "PIBX",
    "PTAK": "PTKX",
    "PLHT": "PLHX",
    "PRBF": "PRFX",
    "PLPm": "PPMX",
    "PFMS": "PFMX",
    "PBSG": "PBSX",
    "PLPU": "PPUX",
    "PLPR": "PPRX",
    "PLMC": "PLMX",
    "PLZC": "PLZX",
    "PLPE": "PPEX",
    "PKPR": "PKPX",
    "PKAC": "PKAX",
    "PKRT": "PKRX",
    "PLRN": "PLRX",
}

# -----------------------------
# HC09-safe trade: do NOT swap these keys
# Add more here if you discover crashy fields in your file.
# -----------------------------
IMMUTABLE_KEYS = {
    "TGID",  # team ownership in your export
    "PGID",  # player global ID
    "POID",  # often a portrait / appearance / internal reference
}

# -----------------------------
# Utilities
# -----------------------------
def _norm_key(s: str) -> str:
    """Keep case EXACT. Only remove invisible junk that breaks exact matches."""
    if s is None:
        return s
    return (
        s.replace("\ufeff", "")
         .replace("\xa0", " ")
         .replace("\r", "")
         .replace("\n", "")
         .replace("\t", " ")
         .strip()
    )

def clamp_stat(v: int) -> int:
    return max(0, min(STAT_MAX_VALUE, v))

def safe_int(s):
    try:
        if s is None:
            return None
        s = str(s).strip()
        if s == "":
            return None
        return int(s)
    except Exception:
        return None

def detect_team_col_case_sensitive(headers):
    hs = set(headers or [])
    for c in PREFERRED_TEAM_COLS:
        if c in hs:
            return c
    return None

def build_player_max_map(headers):
    """Use ONLY hard-coded mapping that exists in THIS file's headers."""
    hs = set(headers or [])
    out = {}
    for base, mx in PLAYER_MAX_HARDCODED.items():
        if base in STAT_META and mx in hs:
            out[base] = mx
    return out

def sanitize_name(raw: str, max_len: int = 15) -> str:
    """
    HC09 can crash on weird chars / long strings.
    - Keep letters, space, apostrophe, hyphen, period
    - Collapse spaces
    - Trim length
    """
    if raw is None:
        return ""
    s = raw.strip()
    s = re.sub(r"[^A-Za-z\.\'\-\s]", "", s)  # drop weird chars
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        s = s[:max_len].strip()
    return s

def swap_players_safe(p1: dict, p2: dict, immutable_keys: set):
    """
    HC09-safe swap:
    swap all values for keys that exist in BOTH dicts, except immutable keys.
    """
    # only swap keys shared by both rows
    shared_keys = set(p1.keys()) & set(p2.keys())
    for k in shared_keys:
        if k in immutable_keys:
            continue
        p1[k], p2[k] = p2[k], p1[k]

# -----------------------------
# CSV model
# -----------------------------
class CSVModel:
    def __init__(self):
        self.play_path = ""
        self.drpk_path = ""
        self.slri_path = ""
        # Optional staff CSVs
        self.trainer_path = ""
        self.coach_path = ""
        self.gm_path = ""

        self.players = []          # list[dict]
        self.player_headers = []   # list[str]
        self.picks = []            # list[dict]
        self.pick_headers = []     # list[str]
        self.salaries = []         # list[dict]
        self.salary_headers = []   # list[str]

        self.trainers = []         # list[dict]
        self.trainer_headers = []  # list[str]
        self.coaches = []          # list[dict]
        self.coach_headers = []    # list[str]
        self.gms = []              # list[dict]
        self.gm_headers = []       # list[str]

        self.team_col = None
        self.max_map = {}

    def load_csv(self, path):
        if not path or not os.path.isfile(path):
            return [], []
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            raw_headers = reader.fieldnames or []
            headers = [_norm_key(h) for h in raw_headers]
            rows = []
            for row in reader:
                cleaned = {}
                for k, v in row.items():
                    nk = _norm_key(k)
                    cleaned[nk] = v
                rows.append(cleaned)
        return rows, headers

    def save_csv(self, rows, headers, original_file):
        if not original_file:
            raise ValueError("No original file path to save.")
        base, ext = os.path.splitext(original_file)
        out = f"{base}_modified{ext}"
        n = 1
        while os.path.exists(out):
            out = f"{base}_modified_{n}{ext}"
            n += 1
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return out

    def load_all(self, play_path, drpk_path="", slri_path="", trainer_path="", coach_path="", gm_path=""):
        self.play_path = play_path or ""
        self.drpk_path = drpk_path or ""
        self.slri_path = slri_path or ""
        self.trainer_path = trainer_path or ""
        self.coach_path = coach_path or ""
        self.gm_path = gm_path or ""

        self.players, self.player_headers = self.load_csv(self.play_path)
        self.picks, self.pick_headers = self.load_csv(self.drpk_path) if self.drpk_path else ([], [])
        self.salaries, self.salary_headers = self.load_csv(self.slri_path) if self.slri_path else ([], [])
        self.trainers, self.trainer_headers = self.load_csv(self.trainer_path) if self.trainer_path else ([], [])
        self.coaches, self.coach_headers = self.load_csv(self.coach_path) if self.coach_path else ([], [])
        self.gms, self.gm_headers = self.load_csv(self.gm_path) if self.gm_path else ([], [])

        if not self.players:
            raise ValueError("play.csv loaded 0 players/rows.")

        self.team_col = detect_team_col_case_sensitive(self.player_headers)
        self.max_map = build_player_max_map(self.player_headers)

    def player_name(self, row):
        fn = (row.get(PLAYER_FIRST_NAME_CODE, "") or "").strip()
        ln = (row.get(PLAYER_LAST_NAME_CODE, "") or "").strip()
        nm = f"{fn} {ln}".strip()
        return nm if nm else "(No Name)"

    def player_pos(self, row):
        code = (row.get(PLAYER_POS_CODE, "") or "").strip()
        return POSITIONS.get(code, "UNK")

    def player_team_id(self, row):
        if not self.team_col:
            return ""
        return (row.get(self.team_col, "") or "").strip()

    def set_player_team_id(self, row, tid):
        if not self.team_col:
            return
        row[self.team_col] = str(tid)

# -----------------------------
# GUI
# -----------------------------
class SwapTradeDialog(tk.Toplevel):
    """
    HC09-safe swap trade dialog:
    pick Team 1 -> player, Team 2 -> player, then swap (without changing TGID/IDs).
    """
    def __init__(self, parent, model: CSVModel):
        super().__init__(parent)
        self.title("HC09-SAFE SWAP TRADE (does not change TGID)")
        self.geometry("980x520")
        self.minsize(900, 480)
        self.parent = parent
        self.model = model

        self.team1 = tk.StringVar(value="33")
        self.team2 = tk.StringVar(value="1")

        self.idx1 = None  # real index into model.players
        self.idx2 = None

        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        warn = (
            "This trade swaps player DATA between two roster rows, but keeps TGID/IDs unchanged.\n"
            "That is the safest method when TGID is the only team column."
        )
        ttk.Label(top, text=warn).pack(anchor="w")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.LabelFrame(body, text="Team 1 (choose player to send)")
        right = ttk.LabelFrame(body, text="Team 2 (choose player to send)")

        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # Team dropdowns
        self.cmb_t1 = ttk.Combobox(left, state="readonly", width=28)
        self.cmb_t2 = ttk.Combobox(right, state="readonly", width=28)

        team_vals = [f"{tid}: {name}" for tid, name in TEAM_NAMES.items()]
        self.cmb_t1["values"] = team_vals
        self.cmb_t2["values"] = team_vals

        # default selections
        self._set_combo_to_tid(self.cmb_t1, "33")
        self._set_combo_to_tid(self.cmb_t2, "1")

        self.cmb_t1.pack(anchor="w", padx=10, pady=(10, 6))
        self.cmb_t2.pack(anchor="w", padx=10, pady=(10, 6))

        self.cmb_t1.bind("<<ComboboxSelected>>", lambda e: self._refresh_roster(1))
        self.cmb_t2.bind("<<ComboboxSelected>>", lambda e: self._refresh_roster(2))

        # Rosters
        self.lst1 = tk.Listbox(left, exportselection=False)
        self.lst2 = tk.Listbox(right, exportselection=False)
        self.lst1.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.lst2.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.lst1.bind("<<ListboxSelect>>", lambda e: self._on_pick_player(1))
        self.lst2.bind("<<ListboxSelect>>", lambda e: self._on_pick_player(2))

        # bottom controls
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(bottom, text="Immutable keys not swapped: " + ", ".join(sorted(IMMUTABLE_KEYS))).pack(side="left")

        ttk.Button(bottom, text="Swap (HC09-safe trade)", command=self._do_swap).pack(side="right")
        ttk.Button(bottom, text="Close", command=self.destroy).pack(side="right", padx=(0, 8))

        self._refresh_roster(1)
        self._refresh_roster(2)

    def _set_combo_to_tid(self, cmb, tid):
        for i, label in enumerate(cmb["values"]):
            if str(label).startswith(str(tid) + ":"):
                cmb.current(i)
                return
        if cmb["values"]:
            cmb.current(0)

    def _combo_tid(self, cmb):
        v = cmb.get()
        if ":" in v:
            return v.split(":", 1)[0].strip()
        return v.strip()

    def _refresh_roster(self, which):
        tid = self._combo_tid(self.cmb_t1 if which == 1 else self.cmb_t2)
        lst = self.lst1 if which == 1 else self.lst2

        lst.delete(0, tk.END)
        mapping = []

        team_col = self.model.team_col
        if not team_col:
            # if somehow no team col, show all
            filtered = list(enumerate(self.model.players))
        else:
            filtered = [(i, r) for i, r in enumerate(self.model.players)
                        if (r.get(team_col, "") or "").strip() == tid]

        for i, r in filtered:
            pos = self.model.player_pos(r)
            name = self.model.player_name(r)
            mapping.append(i)
            lst.insert(tk.END, f"{pos}  {name}   (row#{i})")

        if which == 1:
            self.map1 = mapping
            self.idx1 = None
        else:
            self.map2 = mapping
            self.idx2 = None

        # auto-select first
        if lst.size() > 0:
            lst.selection_set(0)
            lst.activate(0)
            self._on_pick_player(which)

    def _on_pick_player(self, which):
        lst = self.lst1 if which == 1 else self.lst2
        sel = lst.curselection()
        if not sel:
            return
        lb_idx = sel[0]
        if which == 1:
            if lb_idx < len(self.map1):
                self.idx1 = self.map1[lb_idx]
        else:
            if lb_idx < len(self.map2):
                self.idx2 = self.map2[lb_idx]

    def _do_swap(self):
        if self.idx1 is None or self.idx2 is None:
            messagebox.showwarning("Pick players", "Select one player on each side.")
            return
        if self.idx1 == self.idx2:
            messagebox.showwarning("Same row", "You selected the same row on both sides.")
            return

        p1 = self.model.players[self.idx1]
        p2 = self.model.players[self.idx2]

        n1 = self.model.player_name(p1)
        n2 = self.model.player_name(p2)

        swap_players_safe(p1, p2, IMMUTABLE_KEYS)

        messagebox.showinfo("Trade complete", f"✅ HC09-SAFE SWAP TRADE COMPLETED\n\n{n1}  ⇄  {n2}")

        # Refresh the parent's views
        self.parent.refresh_players_for_team()
        self.parent.refresh_stats_for_player()
        self.parent.refresh_picks()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HC09 CSV Editor (GUI) - Safe Trades")
        self.geometry("1320x820")
        self.minsize(1180, 700)

        self.model = CSVModel()

        self.selected_team_id = tk.StringVar(value="")
        self.selected_player_index = None
        self.selected_stat_key = None
        self._player_index_map = []
        self._pick_index_map = []  # For acquire picks dropdown mapping

        self._build_ui()

    # ---------- UI layout ----------
    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Button(top, text="Load CSVs", command=self.on_load).pack(side="left")
        ttk.Button(top, text="Save CSVs", command=self.on_save).pack(side="left", padx=(8, 0))

        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Button(top, text="HC09-SAFE SWAP TRADE", command=self.on_open_swap_trade).pack(side="left")
        self.btn_move_trade = ttk.Button(top, text="Move Player → Selected Team", command=self.on_move_trade_to_selected_team)
        self.btn_move_trade.pack(side="left", padx=(8, 0))

        self.lbl_status = ttk.Label(top, text="Load play.csv to begin.")
        self.lbl_status.pack(side="left", padx=12)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_players = ttk.Frame(self.notebook)
        self.tab_picks = ttk.Frame(self.notebook)
        self.tab_cap = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_players, text="Players + Stats")
        self.notebook.add(self.tab_picks, text="Draft Picks")
        self.notebook.add(self.tab_cap, text="Salary Cap")

        self._build_players_tab()
        self._build_picks_tab()
        self._build_cap_tab()
        # New staff tabs
        self._build_trainer_tab()
        self._build_coach_tab()
        self._build_gm_tab()

    def _build_players_tab(self):
        root = self.tab_players

        # Left: Teams
        left = ttk.Frame(root)
        left.pack(side="left", fill="y", padx=(0, 8), pady=6)

        ttk.Label(left, text="Teams").pack(anchor="w")
        self.lst_teams = tk.Listbox(left, height=28, exportselection=False)
        self.lst_teams.pack(fill="y")
        self.lst_teams.bind("<<ListboxSelect>>", self.on_team_select)

        # Middle: Players
        mid = ttk.Frame(root)
        mid.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=6)

        ttk.Label(mid, text="Players on Team (play.csv)").pack(anchor="w")
        self.lst_players = tk.Listbox(mid, height=28, exportselection=False)
        self.lst_players.pack(fill="both", expand=True)
        self.lst_players.bind("<<ListboxSelect>>", self.on_player_select)

        # Right: Name editor + Stats editor + Raw editor
        right = ttk.Frame(root)
        right.pack(side="left", fill="both", expand=True, pady=6)

        # --- Name Editor ---
        namefrm = ttk.LabelFrame(right, text="Name Editor (PFNA / PLNA) (sanitized to avoid crashes)")
        namefrm.pack(fill="x", pady=(0, 10))

        ttk.Label(namefrm, text="First (PFNA)").grid(row=0, column=0, sticky="w")
        self.ent_first = ttk.Entry(namefrm, width=22)
        self.ent_first.grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(namefrm, text="Last (PLNA)").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.ent_last = ttk.Entry(namefrm, width=22)
        self.ent_last.grid(row=0, column=3, sticky="w", padx=6)

        ttk.Button(namefrm, text="Apply Name", command=self.on_apply_name).grid(row=0, column=4, sticky="w", padx=8)
        namefrm.grid_columnconfigure(5, weight=1)

        ttk.Label(right, text="Stats (described only)").pack(anchor="w")

        cols = ("stat", "cur_col", "cur_val", "max_col", "max_val")
        self.tree_stats = ttk.Treeview(right, columns=cols, show="headings", height=16)
        for c, w in zip(cols, [260, 90, 80, 90, 80]):
            self.tree_stats.heading(c, text=c)
            self.tree_stats.column(c, width=w, anchor="w")
        self.tree_stats.pack(fill="both", expand=True)
        self.tree_stats.bind("<<TreeviewSelect>>", self.on_stat_select)

        self.txt_desc = tk.Text(right, height=4, wrap="word")
        self.txt_desc.pack(fill="x", pady=(8, 8))
        self.txt_desc.configure(state="disabled")

        edit = ttk.Frame(right)
        edit.pack(fill="x")

        ttk.Label(edit, text="New CURRENT").grid(row=0, column=0, sticky="w")
        self.ent_new_cur = ttk.Entry(edit, width=10)
        self.ent_new_cur.grid(row=0, column=1, sticky="w", padx=(6, 10))

        ttk.Label(edit, text="New MAX").grid(row=0, column=2, sticky="w")
        self.ent_new_max = ttk.Entry(edit, width=10)
        self.ent_new_max.grid(row=0, column=3, sticky="w", padx=(6, 10))

        ttk.Button(edit, text="Apply", command=self.on_apply_stat).grid(row=0, column=4, sticky="w")
        ttk.Button(edit, text="Set Both (Max then Cur)", command=self.on_apply_both).grid(row=0, column=5, sticky="w", padx=(8, 0))

        info = ttk.Frame(right)
        info.pack(fill="x", pady=(10, 0))

        ttk.Label(info, text="Age").grid(row=0, column=0, sticky="w")
        self.ent_age = ttk.Entry(info, width=8)
        self.ent_age.grid(row=0, column=1, sticky="w", padx=(6, 16))
        ttk.Label(info, text="Years").grid(row=0, column=2, sticky="w")
        self.ent_years = ttk.Entry(info, width=8)
        self.ent_years.grid(row=0, column=3, sticky="w", padx=(6, 16))
        ttk.Button(info, text="Apply Age/Years", command=self.on_apply_age_years).grid(row=0, column=4, sticky="w")

        # Raw column editor (ANY column)
        raw = ttk.LabelFrame(right, text="Raw Column Editor (any header)")
        raw.pack(fill="x", pady=(10, 0))

        ttk.Label(raw, text="Column").grid(row=0, column=0, sticky="w")
        self.cmb_raw_col = ttk.Combobox(raw, width=22, state="readonly")
        self.cmb_raw_col.grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(raw, text="Value").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.ent_raw_val = ttk.Entry(raw, width=26)
        self.ent_raw_val.grid(row=0, column=3, sticky="w", padx=6)

        ttk.Button(raw, text="Apply", command=self.on_apply_raw_column).grid(row=0, column=4, sticky="w", padx=8)

    def _build_picks_tab(self):
        root = self.tab_picks
        top = ttk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="Draft Picks (drpk.csv)").pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_picks).pack(side="left", padx=8)

        cols = ("team", "pick", "year_offset")
        self.tree_picks = ttk.Treeview(root, columns=cols, show="headings", height=22)
        for c, w in zip(cols, [320, 120, 120]):
            self.tree_picks.heading(c, text=c)
            self.tree_picks.column(c, width=w, anchor="w")
        self.tree_picks.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        bottom = ttk.Frame(root)
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(bottom, text="Acquire picks: From Team").pack(side="left")
        self.cmb_pick_from = ttk.Combobox(bottom, width=24, state="readonly")
        team_vals = [f"{tid}: {name}" for tid, name in TEAM_NAMES.items()]
        self.cmb_pick_from["values"] = team_vals
        self.cmb_pick_from.pack(side="left", padx=6)
        self.cmb_pick_from.bind("<<ComboboxSelected>>", self._on_from_team_changed)

        ttk.Label(bottom, text="→ To Team").pack(side="left", padx=(10, 0))
        self.cmb_pick_to = ttk.Combobox(bottom, width=24, state="readonly")
        self.cmb_pick_to["values"] = team_vals
        self.cmb_pick_to.pack(side="left", padx=6)

        ttk.Label(bottom, text="Pick(s)").pack(side="left", padx=(10, 0))
        self.cmb_pick_idxs = ttk.Combobox(bottom, width=30, state="readonly")
        self.cmb_pick_idxs.pack(side="left", padx=6)

        ttk.Button(bottom, text="Acquire", command=self.on_acquire_picks).pack(side="left", padx=8)

    def _build_cap_tab(self):
        root = self.tab_cap
        frm = ttk.Frame(root)
        frm.pack(fill="x", padx=10, pady=14)

        ttk.Label(frm, text="Salary Cap (slri.csv)").grid(row=0, column=0, sticky="w")
        self.ent_cap = ttk.Entry(frm, width=18)
        self.ent_cap.grid(row=0, column=1, sticky="w", padx=8)
        ttk.Button(frm, text="Apply (max 260,000,000)", command=self.on_apply_cap).grid(row=0, column=2, sticky="w", padx=8)

        self.lbl_cap_status = ttk.Label(root, text="Load slri.csv to edit cap.")
        self.lbl_cap_status.pack(anchor="w", padx=10, pady=(8, 0))

    # ---------- Staff Tabs (Trainer / Coach / GM) ----------
    def _build_trainer_tab(self):
        root = ttk.Frame(self.notebook)
        self.tab_trainer = root
        self.notebook.add(self.tab_trainer, text="Trainer")

        top = ttk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)
        ttk.Label(top, text="Trainer (trvw.csv)").pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_trainer).pack(side="left", padx=8)

        self.tree_trainer = ttk.Treeview(root, show="headings", height=20)
        self.tree_trainer.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Bottom editor for SKPT
        btm = ttk.Frame(root)
        btm.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(btm, text="Selected SKPT:").pack(side="left")
        self.ent_trainer_skpt = ttk.Entry(btm, width=12)
        self.ent_trainer_skpt.pack(side="left", padx=(6, 8))
        ttk.Button(btm, text="Apply SKPT", command=self._apply_trainer_skpt).pack(side="left")
        self.tree_trainer.bind("<<TreeviewSelect>>", lambda e: self._on_trainer_select())
        self.tree_trainer.bind("<Double-1>", lambda e: self._on_tree_double_click(e, self.tree_trainer))

    def _build_coach_tab(self):
        root = ttk.Frame(self.notebook)
        self.tab_coach = root
        self.notebook.add(self.tab_coach, text="Coach")

        top = ttk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)
        ttk.Label(top, text="Coach (coch.csv)").pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_coach).pack(side="left", padx=8)

        # Search controls for coach first/last name
        self.coach_search_var = tk.StringVar()
        ttk.Label(top, text="Search:").pack(side="left", padx=(12, 4))
        self.ent_coach_search = ttk.Entry(top, textvariable=self.coach_search_var, width=20)
        self.ent_coach_search.pack(side="left")
        ttk.Button(top, text="Find", command=lambda: self.refresh_coach()).pack(side="left", padx=(6, 4))
        ttk.Button(top, text="Clear", command=lambda: (self.coach_search_var.set(""), self.refresh_coach())).pack(side="left")

        self.tree_coach = ttk.Treeview(root, show="headings", height=20)
        self.tree_coach.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Bottom editor for SKPT
        btm = ttk.Frame(root)
        btm.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(btm, text="Selected SKPT:").pack(side="left")
        self.ent_coach_skpt = ttk.Entry(btm, width=12)
        self.ent_coach_skpt.pack(side="left", padx=(6, 8))
        ttk.Button(btm, text="Apply SKPT", command=self._apply_coach_skpt).pack(side="left")
        self.tree_coach.bind("<<TreeviewSelect>>", lambda e: self._on_coach_select())
        self.tree_coach.bind("<Double-1>", lambda e: self._on_tree_double_click(e, self.tree_coach))

    def _build_gm_tab(self):
        root = ttk.Frame(self.notebook)
        self.tab_gm = root
        self.notebook.add(self.tab_gm, text="GM")

        top = ttk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)
        ttk.Label(top, text="GM (gmvw.csv)").pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh_gm).pack(side="left", padx=8)

        self.tree_gm = ttk.Treeview(root, show="headings", height=20)
        self.tree_gm.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Bottom editor for SKPT
        btm = ttk.Frame(root)
        btm.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(btm, text="Selected SKPT:").pack(side="left")
        self.ent_gm_skpt = ttk.Entry(btm, width=12)
        self.ent_gm_skpt.pack(side="left", padx=(6, 8))
        ttk.Button(btm, text="Apply SKPT", command=self._apply_gm_skpt).pack(side="left")
        self.tree_gm.bind("<<TreeviewSelect>>", lambda e: self._on_gm_select())
        self.tree_gm.bind("<Double-1>", lambda e: self._on_tree_double_click(e, self.tree_gm))

    # ---------- Load / Save ----------
    def on_load(self):
        try:
            play = filedialog.askopenfilename(
                title="Select play.csv (players)",
                filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
            )
            if not play:
                return

            drpk = filedialog.askopenfilename(
                title="Optional: Select drpk.csv (draft picks)",
                filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
            )
            slri = filedialog.askopenfilename(
                title="Optional: Select slri.csv (salary cap)",
                filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
            )

            trainer = filedialog.askopenfilename(
                title="Optional: Select trainer.csv (staff)",
                filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
            )
            coach = filedialog.askopenfilename(
                title="Optional: Select coach.csv (staff)",
                filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
            )
            gm = filedialog.askopenfilename(
                title="Optional: Select gm.csv (staff)",
                filetypes=[("CSV", "*.csv"), ("All files", "*.*")]
            )

            self.model.load_all(play, drpk, slri, trainer, coach, gm)

            if not self.model.team_col:
                messagebox.showwarning(
                    "Team Column Not Found",
                    "Could not detect a team column in play.csv (case-sensitive search: TID/TEAM/TMID/TGID)."
                )

            self.lbl_status.configure(
                text=f"Loaded: {os.path.basename(play)}  | TeamCol={self.model.team_col or 'N/A'}  | Players={len(self.model.players)}"
            )

            # enable/disable move-trade button
            # If team col is TGID, we do NOT want to change it (your requirement).
            if (self.model.team_col or "") == "TGID":
                self.btn_move_trade.state(["disabled"])
            else:
                self.btn_move_trade.state(["!disabled"])

            self.refresh_teams()
            self.refresh_picks()
            self.refresh_cap()
            self.refresh_trainer()
            self.refresh_coach()
            self.refresh_gm()
            self.refresh_raw_columns()
            self._select_default_team()

        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def on_save(self):
        try:
            if not self.model.players:
                messagebox.showinfo("Nothing to save", "Load CSVs first.")
                return

            out1 = self.model.save_csv(self.model.players, self.model.player_headers, self.model.play_path)
            outs = [out1]

            if self.model.picks and self.model.drpk_path:
                out2 = self.model.save_csv(self.model.picks, self.model.pick_headers, self.model.drpk_path)
                outs.append(out2)

            if self.model.salaries and self.model.slri_path:
                out3 = self.model.save_csv(self.model.salaries, self.model.salary_headers, self.model.slri_path)
                outs.append(out3)

            # Save optional staff CSVs
            if self.model.trainers and self.model.trainer_path:
                out4 = self.model.save_csv(self.model.trainers, self.model.trainer_headers, self.model.trainer_path)
                outs.append(out4)
            if self.model.coaches and self.model.coach_path:
                out5 = self.model.save_csv(self.model.coaches, self.model.coach_headers, self.model.coach_path)
                outs.append(out5)
            if self.model.gms and self.model.gm_path:
                out6 = self.model.save_csv(self.model.gms, self.model.gm_headers, self.model.gm_path)
                outs.append(out6)

            messagebox.showinfo("Saved", "Saved:\n\n" + "\n".join(outs))
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    # ---------- Teams / Players ----------
    def refresh_teams(self):
        self.lst_teams.delete(0, tk.END)
        for tid, name in TEAM_NAMES.items():
            self.lst_teams.insert(tk.END, f"{tid}: {name}")

    def _select_default_team(self):
        target = "33"  # Free Agents
        idx = None
        for i in range(self.lst_teams.size()):
            if self.lst_teams.get(i).startswith(target + ":"):
                idx = i
                break
        if idx is None and self.lst_teams.size() > 0:
            idx = 0
        if idx is not None:
            self.lst_teams.selection_clear(0, tk.END)
            self.lst_teams.selection_set(idx)
            self.lst_teams.activate(idx)
            self.on_team_select()

    def on_team_select(self, event=None):
        sel = self.lst_teams.curselection()
        if not sel:
            return
        txt = self.lst_teams.get(sel[0])
        tid = txt.split(":", 1)[0].strip()
        self.selected_team_id.set(tid)
        self.refresh_players_for_team()

    def refresh_players_for_team(self):
        self.lst_players.delete(0, tk.END)
        self.selected_player_index = None
        self.clear_stats_view()

        tid = self.selected_team_id.get()
        if not tid or not self.model.players:
            return

        if self.model.team_col:
            filtered = [(i, r) for i, r in enumerate(self.model.players)
                        if (r.get(self.model.team_col, "") or "").strip() == tid]
        else:
            filtered = list(enumerate(self.model.players))

        # Sort by position (custom order), then first name, then last name
        filtered = sorted(filtered, key=lambda item: (
            POSITION_ORDER.get((item[1].get(PLAYER_POS_CODE, "") or "").strip(), 999),
            item[1].get(PLAYER_FIRST_NAME_CODE, "").strip(),
            item[1].get(PLAYER_LAST_NAME_CODE, "").strip()
        ))

        self._player_index_map = [i for i, _ in filtered]

        for i, r in filtered:
            pos = self.model.player_pos(r)
            name = self.model.player_name(r)
            age = (r.get(AGE_COL, "") or "").strip()
            yrs = (r.get(YEARS_COL, "") or "").strip()
            self.lst_players.insert(tk.END, f"{pos}  {name}   (Age:{age or '-'} Yrs:{yrs or '-'})")

        if self.lst_players.size() > 0:
            self.lst_players.selection_set(0)
            self.lst_players.activate(0)
            self.on_player_select()

    def on_player_select(self, event=None):
        sel = self.lst_players.curselection()
        if not sel:
            return
        lb_idx = sel[0]
        real_idx = self._player_index_map[lb_idx]
        self.selected_player_index = real_idx
        self.refresh_stats_for_player()

        r = self.model.players[real_idx]

        # Prefill Age/Years
        self.ent_age.delete(0, tk.END)
        self.ent_age.insert(0, (r.get(AGE_COL, "") or "").strip())
        self.ent_years.delete(0, tk.END)
        self.ent_years.insert(0, (r.get(YEARS_COL, "") or "").strip())

        # Prefill Name Editor
        self.ent_first.delete(0, tk.END)
        self.ent_first.insert(0, (r.get(PLAYER_FIRST_NAME_CODE, "") or "").strip())
        self.ent_last.delete(0, tk.END)
        self.ent_last.insert(0, (r.get(PLAYER_LAST_NAME_CODE, "") or "").strip())

        # Prefill raw column value
        self.on_raw_column_changed()

    # ---------- Name Editor ----------
    def on_apply_name(self):
        if self.selected_player_index is None:
            messagebox.showinfo("No player", "Select a player first.")
            return

        r = self.model.players[self.selected_player_index]
        headers_set = set(self.model.player_headers)

        fn_raw = self.ent_first.get()
        ln_raw = self.ent_last.get()

        fn = sanitize_name(fn_raw, max_len=15)
        ln = sanitize_name(ln_raw, max_len=15)

        if fn != fn_raw.strip() or ln != ln_raw.strip():
            messagebox.showinfo(
                "Name sanitized",
                "Your name was sanitized to reduce HC09 crash risk.\n\n"
                f"First: '{fn_raw.strip()}' -> '{fn}'\n"
                f"Last:  '{ln_raw.strip()}' -> '{ln}'"
            )

        if PLAYER_FIRST_NAME_CODE in headers_set:
            r[PLAYER_FIRST_NAME_CODE] = fn
        else:
            messagebox.showwarning("Missing column", f"{PLAYER_FIRST_NAME_CODE} not found in play.csv headers.")

        if PLAYER_LAST_NAME_CODE in headers_set:
            r[PLAYER_LAST_NAME_CODE] = ln
        else:
            messagebox.showwarning("Missing column", f"{PLAYER_LAST_NAME_CODE} not found in play.csv headers.")

        self.refresh_players_for_team()

    # ---------- Stats ----------
    def clear_stats_view(self):
        for iid in self.tree_stats.get_children():
            self.tree_stats.delete(iid)
        self.selected_stat_key = None
        self._set_desc("")
        self.ent_new_cur.delete(0, tk.END)
        self.ent_new_max.delete(0, tk.END)

    def refresh_stats_for_player(self):
        self.clear_stats_view()
        if self.selected_player_index is None:
            return
        r = self.model.players[self.selected_player_index]
        headers_set = set(self.model.player_headers)

        for base_key in STAT_META.keys():
            cur_col = base_key if base_key in headers_set else None
            max_col = self.model.max_map.get(base_key)
            if not cur_col and not max_col:
                continue

            nice, _ = STAT_META.get(base_key, (base_key, ""))
            cur_val = (r.get(cur_col, "") if cur_col else "")
            max_val = (r.get(max_col, "") if max_col else "")

            self.tree_stats.insert(
                "",
                tk.END,
                iid=base_key,
                values=(nice, cur_col or "N/A", cur_val or "-", max_col or "N/A", max_val or "-")
            )

    def on_stat_select(self, event=None):
        sel = self.tree_stats.selection()
        if not sel:
            return
        base_key = sel[0]
        self.selected_stat_key = base_key

        nice, desc = STAT_META.get(base_key, (base_key, ""))
        self._set_desc(f"{nice} ({base_key})\n\n{desc}")

        r = self.model.players[self.selected_player_index]
        headers_set = set(self.model.player_headers)

        cur_col = base_key if base_key in headers_set else None
        max_col = self.model.max_map.get(base_key)

        self.ent_new_cur.delete(0, tk.END)
        self.ent_new_max.delete(0, tk.END)
        if cur_col:
            self.ent_new_cur.insert(0, (r.get(cur_col, "") or "").strip())
        if max_col:
            self.ent_new_max.insert(0, (r.get(max_col, "") or "").strip())

    def _set_desc(self, text):
        self.txt_desc.configure(state="normal")
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", text)
        self.txt_desc.configure(state="disabled")

    def _enforce_current_le_max(self, row, cur_col, max_col):
        if not cur_col or not max_col:
            return
        c = safe_int(row.get(cur_col, ""))
        m = safe_int(row.get(max_col, ""))
        if c is None or m is None:
            return
        if c > m:
            row[cur_col] = str(m)

    def on_apply_stat(self):
        if self.selected_player_index is None or not self.selected_stat_key:
            return
        base_key = self.selected_stat_key
        r = self.model.players[self.selected_player_index]
        headers_set = set(self.model.player_headers)

        cur_col = base_key if base_key in headers_set else None
        max_col = self.model.max_map.get(base_key)

        new_cur = self.ent_new_cur.get().strip()
        new_max = self.ent_new_max.get().strip()

        try:
            if new_cur != "" and cur_col:
                r[cur_col] = str(clamp_stat(int(new_cur)))
            if new_max != "" and max_col:
                r[max_col] = str(clamp_stat(int(new_max)))

            self._enforce_current_le_max(r, cur_col, max_col)
            self.refresh_stats_for_player()
            self.tree_stats.selection_set(base_key)
            self.tree_stats.see(base_key)
        except Exception as e:
            messagebox.showerror("Apply Error", str(e))

    def on_apply_both(self):
        if self.selected_player_index is None or not self.selected_stat_key:
            return
        base_key = self.selected_stat_key
        r = self.model.players[self.selected_player_index]
        headers_set = set(self.model.player_headers)

        cur_col = base_key if base_key in headers_set else None
        max_col = self.model.max_map.get(base_key)

        new_cur = self.ent_new_cur.get().strip()
        new_max = self.ent_new_max.get().strip()

        try:
            if new_max != "" and max_col:
                r[max_col] = str(clamp_stat(int(new_max)))
            if new_cur != "" and cur_col:
                r[cur_col] = str(clamp_stat(int(new_cur)))

            self._enforce_current_le_max(r, cur_col, max_col)
            self.refresh_stats_for_player()
            self.tree_stats.selection_set(base_key)
            self.tree_stats.see(base_key)
        except Exception as e:
            messagebox.showerror("Apply Error", str(e))

    def on_apply_age_years(self):
        if self.selected_player_index is None:
            return
        r = self.model.players[self.selected_player_index]
        a = self.ent_age.get().strip()
        y = self.ent_years.get().strip()
        try:
            if AGE_COL in set(self.model.player_headers) and a != "":
                r[AGE_COL] = str(max(0, min(99, int(a))))
            if YEARS_COL in set(self.model.player_headers) and y != "":
                r[YEARS_COL] = str(max(0, min(30, int(y))))
            self.refresh_players_for_team()
        except Exception as e:
            messagebox.showerror("Apply Error", str(e))

    # ---------- Trades ----------
    def on_open_swap_trade(self):
        if not self.model.players:
            messagebox.showinfo("Load first", "Load play.csv first.")
            return
        SwapTradeDialog(self, self.model)

    def on_move_trade_to_selected_team(self):
        """
        Only works if we have a non-TGID team column.
        Your export: TGID only -> button disabled.
        """
        if not self.model.players or self.selected_player_index is None:
            return
        if not self.model.team_col:
            messagebox.showwarning("No team column", "Team column not detected.")
            return
        if self.model.team_col == "TGID":
            messagebox.showwarning(
                "TGID-only file",
                "Your play.csv only has TGID as the team column.\n\n"
                "Use 'HC09-SAFE SWAP TRADE' instead (it does NOT change TGID)."
            )
            return

        dest_tid = self.selected_team_id.get()
        if not dest_tid:
            return

        r = self.model.players[self.selected_player_index]
        src_tid = self.model.player_team_id(r)

        if src_tid == dest_tid:
            messagebox.showinfo("No change", "Player already on that team.")
            return

        self.model.set_player_team_id(r, dest_tid)
        self.refresh_players_for_team()

    # ---------- Picks ----------
    def refresh_picks(self):
        for iid in self.tree_picks.get_children():
            self.tree_picks.delete(iid)
        if not self.model.picks:
            self.cmb_pick_from.set("")
            self.cmb_pick_to.set("")
            self.cmb_pick_idxs.set("")
            self.cmb_pick_idxs["values"] = []
            return

        # Sort picks by team, then by year offset (0, 1, 3...), then by round
        sorted_picks = sorted(
            enumerate(self.model.picks),
            key=lambda item: (
                int((item[1].get(DRAFT_PICK_ID, "") or "").strip() or "99999"),  # Team ID first
                y if (y := safe_int(item[1].get(DRAFT_PICK_YEAR, ""))) is not None else 999,  # Year offset (0, 1, 3...)
                (safe_int(item[1].get(DRAFT_PICK_NUM, "")) or 0) // 32  # Round number
            )
        )

        # Create a mapping of year offsets to sequential display numbers (1, 2, 3...)
        unique_years = sorted(set(
            safe_int(p.get(DRAFT_PICK_YEAR, "")) 
            for _, p in sorted_picks 
            if safe_int(p.get(DRAFT_PICK_YEAR, "")) is not None
        ))
        year_map = {y: i + 1 for i, y in enumerate(unique_years)}

        for i, (orig_idx, p) in enumerate(sorted_picks):
            tid = (p.get(DRAFT_PICK_ID, "") or "").strip()
            pick_num = safe_int(p.get(DRAFT_PICK_NUM, ""))
            year_off = safe_int(p.get(DRAFT_PICK_YEAR, ""))

            pick_disp = "-" if pick_num is None else str(pick_num + 1)
            team_name = TEAM_NAMES.get(tid, tid or "Unknown")
            round_num = (pick_num + 1 - 1) // 32 + 1 if pick_num is not None else "-"
            
            # Display year using sequential mapping: 0→1, 1→2, 3→3, etc.
            year_display = year_map.get(year_off, "-") if year_off is not None else "-"

            self.tree_picks.insert("", tk.END, iid=str(orig_idx),
                                  values=(f"{tid}: {team_name}", f"R{round_num}:{pick_disp}", str(year_display)))
        
        # Reset dropdowns
        if self.cmb_pick_from["values"]:
            self.cmb_pick_from.current(0)
            self._on_from_team_changed()

    def _on_from_team_changed(self, event=None):
        """Populate picks dropdown when 'from team' is selected."""
        from_combo_val = self.cmb_pick_from.get()
        if not from_combo_val or ":" not in from_combo_val:
            self.cmb_pick_idxs["values"] = []
            return

        from_tid = from_combo_val.split(":", 1)[0].strip()
        
        # Get all picks for this team
        team_picks_raw = []
        for model_idx, p in enumerate(self.model.picks):
            if (p.get(DRAFT_PICK_ID, "") or "").strip() == from_tid:
                pick_num = safe_int(p.get(DRAFT_PICK_NUM, ""))
                year_off = safe_int(p.get(DRAFT_PICK_YEAR, ""))
                round_num = (pick_num + 1 - 1) // 32 + 1 if pick_num is not None else 999
                team_picks_raw.append((model_idx, pick_num, year_off, round_num))
        
        # Sort by year offset (ascending = most recent first), then round, then pick number
        # This ensures consistent ordering: all Yr:0 first, then Yr:1, etc.
        team_picks_raw.sort(key=lambda x: (
            y if (y := x[2]) is not None else 999,  # year_off
            x[3],  # round_num
            p if (p := x[1]) is not None else 999  # pick_num
        ))
        
        # Create a mapping of year offsets to sequential display numbers (1, 2, 3...)
        unique_years = sorted(set(y for _, _, y, _ in team_picks_raw if y is not None))
        year_map = {y: i + 1 for i, y in enumerate(unique_years)}
        
        # Create display list with indexes and store model indices
        pick_displays = []
        self._pick_index_map = []  # Store model indices for later reference
        for local_idx, (model_idx, pick_num, year_off, round_num) in enumerate(team_picks_raw):
            # Display year using sequential mapping: 0→1, 1→2, 3→3, etc.
            year_display = year_map.get(year_off, "?") if year_off is not None else "?"
            pick_display = f"R{round_num}:{pick_num + 1 if pick_num is not None else '-'} (Yr:{year_display})  [Idx:{local_idx}]"
            pick_displays.append(pick_display)
            self._pick_index_map.append(model_idx)  # Store the actual model index
        
        self.cmb_pick_idxs["values"] = pick_displays
        if pick_displays:
            self.cmb_pick_idxs.current(0)

    def on_acquire_picks(self):
        if not self.model.picks:
            messagebox.showinfo("No picks", "Load drpk.csv to edit picks.")
            return

        from_combo_val = self.cmb_pick_from.get()
        to_combo_val = self.cmb_pick_to.get()
        pick_display = self.cmb_pick_idxs.get()

        if not from_combo_val or not to_combo_val or not pick_display:
            messagebox.showwarning("Missing selection", "Select from team, to team, and pick(s).")
            return

        from_tid = from_combo_val.split(":", 1)[0].strip() if ":" in from_combo_val else from_combo_val
        to_tid = to_combo_val.split(":", 1)[0].strip() if ":" in to_combo_val else to_combo_val

        # Get the current index from the dropdown
        current_display_idx = self.cmb_pick_idxs.current()
        if current_display_idx < 0 or current_display_idx >= len(self._pick_index_map):
            messagebox.showwarning("Invalid selection", "Please select a valid pick.")
            return

        # Get the actual model index from the mapping
        model_idx = self._pick_index_map[current_display_idx]

        # Modify the pick directly in model.picks
        self.model.picks[model_idx][DRAFT_PICK_ID] = to_tid

        messagebox.showinfo("Acquired", f"Moved pick from {from_tid} → {to_tid}")
        self.refresh_picks()
        self._on_from_team_changed()  # Refresh picks dropdown

    # ---------- Salary Cap ----------
    def refresh_cap(self):
        if not self.model.salaries:
            self.lbl_cap_status.configure(text="Load slri.csv to edit cap.")
            self.ent_cap.delete(0, tk.END)
            return

        cap_row = self.model.salaries[0]
        cap_val = cap_row.get(SALARY_CAP_KEY, cap_row.get("SCAD", "0"))
        self.ent_cap.delete(0, tk.END)
        self.ent_cap.insert(0, str(cap_val))
        self.lbl_cap_status.configure(text=f"Loaded slri.csv rows: {len(self.model.salaries)}")

    def _populate_tree_with_rows(self, tree: ttk.Treeview, headers: list, rows: list):
        # Clear existing
        for iid in tree.get_children():
            tree.delete(iid)

        if not headers:
            tree["columns"] = ()
            return

        tree["columns"] = headers
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=140, anchor="w")

        for i, r in enumerate(rows):
            vals = [ (r.get(h, "") or "") for h in headers ]
            tree.insert("", tk.END, iid=str(i), values=vals)

    def refresh_trainer(self):
        # Show TGID and SKPT if present (display team name for TGID)
        desired = ["TGID", "SKPT"]
        headers = [h for h in desired if h in (self.model.trainer_headers or [])]
        if not headers:
            self._populate_tree_with_rows(self.tree_trainer, self.model.trainer_headers, self.model.trainers)
            return

        # Prepare rows as (model_idx, row) for sorting
        rows = list(enumerate(self.model.trainers))

        # Sort by TGID if present, numeric when possible
        if "TGID" in (self.model.trainer_headers or []):
            def tg_key(ir):
                _, r = ir
                tid = (r.get("TGID", "") or "").strip()
                tnum = safe_int(tid)
                return (0, tnum) if tnum is not None else (1, tid)
            rows = sorted(rows, key=tg_key)

        # Clear and set columns
        for iid in self.tree_trainer.get_children():
            self.tree_trainer.delete(iid)

        self.tree_trainer["columns"] = headers
        for h in headers:
            self.tree_trainer.heading(h, text=h)
            self.tree_trainer.column(h, width=160, anchor="w")

        for idx, r in rows:
            vals = []
            for h in headers:
                if h == "TGID":
                    tid = (r.get("TGID", "") or "").strip()
                    vals.append(f"{tid}: {TEAM_NAMES.get(tid, tid)}" if tid else "")
                else:
                    vals.append((r.get(h, "") or ""))
            self.tree_trainer.insert("", tk.END, iid=str(idx), values=vals)

    def _on_trainer_select(self):
        sel = self.tree_trainer.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            return
        # find SKPT value from model if present
        row = self.model.trainers[idx]
        sk = row.get("SKPT") if row is not None else None
        self.ent_trainer_skpt.delete(0, tk.END)
        if sk is not None:
            self.ent_trainer_skpt.insert(0, str(sk))

    def _apply_trainer_skpt(self):
        sel = self.tree_trainer.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a trainer row first.")
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            return
        val = self.ent_trainer_skpt.get().strip()
        try:
            v = safe_int(val)
            if v is None:
                raise ValueError("Invalid integer")
            orig = v
            # Clamp to allowed range
            v = max(0, min(131071, v))
            self.model.trainers[idx]["SKPT"] = str(v)
            self.refresh_trainer()
            if orig != v:
                # show only the clamped numeric value (no decimal)
                messagebox.showinfo("SKPT", str(v))
        except Exception as e:
            messagebox.showerror("Invalid SKPT", str(e))

    def refresh_coach(self):
        # Prefer TGID + name + SKPT when available
        desired = ["TGID", "CFNM", "CLNM", "SKPT"]
        headers = [h for h in desired if h in (self.model.coach_headers or [])]
        if not headers:
            headers = self.model.coach_headers

        # Build filtering predicate from search box (first/last name)
        q = (self.coach_search_var.get() or "").strip().lower() if hasattr(self, 'coach_search_var') else ""

        # Prepare rows as (model_idx, row) and apply filter
        rows = list(enumerate(self.model.coaches))
        if q:
            def match(r):
                fn = (r.get("CFNM", "") or "").lower()
                ln = (r.get("CLNM", "") or "").lower()
                return q in fn or q in ln
            rows = [(i, r) for i, r in rows if match(r)]

        # Sort by TGID if present, numeric when possible
        if "TGID" in (self.model.coach_headers or []):
            def tg_key(ir):
                _, r = ir
                tid = (r.get("TGID", "") or "").strip()
                tnum = safe_int(tid)
                return (0, tnum) if tnum is not None else (1, tid)
            rows = sorted(rows, key=lambda ir: (tg_key(ir), (ir[1].get("CLNM", "") or ""), (ir[1].get("CFNM", "") or "")))
        else:
            rows = sorted(rows, key=lambda ir: ((ir[1].get("CLNM", "") or ""), (ir[1].get("CFNM", "") or "")))

        # clear and set columns
        for iid in self.tree_coach.get_children():
            self.tree_coach.delete(iid)

        self.tree_coach["columns"] = headers or []
        for h in headers or []:
            self.tree_coach.heading(h, text=h)
            self.tree_coach.column(h, width=140, anchor="w")

        # Insert rows using original model indices as iids
        for idx, r in rows:
            vals = []
            for h in headers or []:
                if h == "TGID":
                    tid = (r.get("TGID", "") or "").strip()
                    vals.append(f"{tid}: {TEAM_NAMES.get(tid, tid)}" if tid else "")
                else:
                    vals.append((r.get(h, "") or ""))
            self.tree_coach.insert("", tk.END, iid=str(idx), values=vals)

    def _on_coach_select(self):
        sel = self.tree_coach.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            return
        row = self.model.coaches[idx]
        sk = row.get("SKPT") if row is not None else None
        self.ent_coach_skpt.delete(0, tk.END)
        if sk is not None:
            self.ent_coach_skpt.insert(0, str(sk))

    def _apply_coach_skpt(self):
        sel = self.tree_coach.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a coach row first.")
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            return
        val = self.ent_coach_skpt.get().strip()
        try:
            v = safe_int(val)
            if v is None:
                raise ValueError("Invalid integer")
            orig = v
            # Clamp to allowed range
            v = max(0, min(131071, v))
            self.model.coaches[idx]["SKPT"] = str(v)
            self.refresh_coach()
            if orig != v:
                messagebox.showinfo("SKPT", str(v))
        except Exception as e:
            messagebox.showerror("Invalid SKPT", str(e))

    def refresh_gm(self):
        # Show TGID and SKPT if present (display team name for TGID)
        desired = ["TGID", "SKPT"]
        headers = [h for h in desired if h in (self.model.gm_headers or [])]
        if not headers:
            self._populate_tree_with_rows(self.tree_gm, self.model.gm_headers, self.model.gms)
            return

        # Prepare rows as (model_idx, row) for sorting
        rows = list(enumerate(self.model.gms))

        # Sort by TGID if present, numeric when possible
        if "TGID" in (self.model.gm_headers or []):
            def tg_key(ir):
                _, r = ir
                tid = (r.get("TGID", "") or "").strip()
                tnum = safe_int(tid)
                return (0, tnum) if tnum is not None else (1, tid)
            rows = sorted(rows, key=tg_key)

        # Clear and set columns
        for iid in self.tree_gm.get_children():
            self.tree_gm.delete(iid)

        self.tree_gm["columns"] = headers
        for h in headers:
            self.tree_gm.heading(h, text=h)
            self.tree_gm.column(h, width=160, anchor="w")

        for idx, r in rows:
            vals = []
            for h in headers:
                if h == "TGID":
                    tid = (r.get("TGID", "") or "").strip()
                    vals.append(f"{tid}: {TEAM_NAMES.get(tid, tid)}" if tid else "")
                else:
                    vals.append((r.get(h, "") or ""))
            self.tree_gm.insert("", tk.END, iid=str(idx), values=vals)

    def _on_gm_select(self):
        sel = self.tree_gm.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            return
        row = self.model.gms[idx]
        sk = row.get("SKPT") if row is not None else None
        self.ent_gm_skpt.delete(0, tk.END)
        if sk is not None:
            self.ent_gm_skpt.insert(0, str(sk))

    def _apply_gm_skpt(self):
        sel = self.tree_gm.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a GM row first.")
            return
        iid = sel[0]
        try:
            idx = int(iid)
        except Exception:
            return
        val = self.ent_gm_skpt.get().strip()
        try:
            v = safe_int(val)
            if v is None:
                raise ValueError("Invalid integer")
            orig = v
            # Clamp to allowed range
            v = max(0, min(131071, v))
            self.model.gms[idx]["SKPT"] = str(v)
            self.refresh_gm()
            if orig != v:
                messagebox.showinfo("SKPT", str(v))
        except Exception as e:
            messagebox.showerror("Invalid SKPT", str(e))

    def _on_tree_double_click(self, event, tree: ttk.Treeview):
        # Identify clicked row/column
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        rowid = tree.identify_row(event.y)
        col = tree.identify_column(event.x)  # returns like '#1'
        if not rowid or not col:
            return
        try:
            col_idx = int(col.replace('#', '')) - 1
        except Exception:
            return
        cols = list(tree["columns"]) if tree["columns"] else []
        if col_idx < 0 or col_idx >= len(cols):
            return
        colname = cols[col_idx]
        if colname != "SKPT":
            return

        bbox = tree.bbox(rowid, column=col)
        if not bbox:
            return
        x, y, w, h = bbox

        # Create entry overlay
        entry = ttk.Entry(tree)
        entry.place(x=x, y=y, width=w, height=h)
        # prefill with current value
        cur = tree.set(rowid, colname)
        entry.insert(0, cur)
        entry.focus_set()

        def finish(save: bool):
            val = entry.get().strip()
            entry.destroy()
            if not save:
                return
            try:
                # Accept integer or integer-like float (e.g. "131071.0")
                v = None
                try:
                    v = int(val)
                except Exception:
                    try:
                        f = float(val)
                        v = int(f)
                    except Exception:
                        v = None

                if v is None:
                    raise ValueError("Invalid integer")

                orig_v = v
                # Clamp to allowed range
                v = max(0, min(131071, v))

                try:
                    idx = int(rowid)
                except Exception:
                    return

                if tree is self.tree_trainer:
                    self.model.trainers[idx]["SKPT"] = str(v)
                    self.refresh_trainer()
                elif tree is self.tree_coach:
                    self.model.coaches[idx]["SKPT"] = str(v)
                    self.refresh_coach()
                elif tree is self.tree_gm:
                    self.model.gms[idx]["SKPT"] = str(v)
                    self.refresh_gm()
            except Exception as e:
                messagebox.showerror("Invalid SKPT", str(e))

        entry.bind("<Return>", lambda e: finish(True))
        entry.bind("<FocusOut>", lambda e: finish(True))
        entry.bind("<Escape>", lambda e: finish(False))

    def on_apply_cap(self):
        if not self.model.salaries:
            messagebox.showinfo("No salary data", "Load slri.csv first.")
            return
        raw = self.ent_cap.get().strip()
        try:
            v = int(raw)
            v = max(0, min(260_000_000, v))
            cap_row = self.model.salaries[0]
            if SALARY_CAP_KEY in cap_row:
                cap_row[SALARY_CAP_KEY] = str(v)
            else:
                cap_row["SCAD"] = str(v)
            messagebox.showinfo("Updated", f"Salary cap set to {v}")
        except Exception as e:
            messagebox.showerror("Cap Error", str(e))

    # ---------- Raw Column Editor ----------
    def refresh_raw_columns(self):
        if not self.model.player_headers:
            self.cmb_raw_col["values"] = []
            return
        self.cmb_raw_col["values"] = self.model.player_headers
        self.cmb_raw_col.current(0)
        self.cmb_raw_col.bind("<<ComboboxSelected>>", lambda e: self.on_raw_column_changed())

    def on_raw_column_changed(self):
        if self.selected_player_index is None:
            return
        col = self.cmb_raw_col.get().strip()
        if not col:
            return
        r = self.model.players[self.selected_player_index]
        self.ent_raw_val.delete(0, tk.END)
        self.ent_raw_val.insert(0, (r.get(col, "") or "").strip())

    def on_apply_raw_column(self):
        if self.selected_player_index is None:
            messagebox.showinfo("No player", "Select a player first.")
            return
        col = self.cmb_raw_col.get().strip()
        if not col:
            return
        val = self.ent_raw_val.get()
        self.model.players[self.selected_player_index][col] = val
        self.refresh_stats_for_player()
        self.refresh_players_for_team()

if __name__ == "__main__":
    app = App()
    app.mainloop()
