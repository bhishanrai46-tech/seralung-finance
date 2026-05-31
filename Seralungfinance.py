"""
Seralung Finance — Understand Risk. Invest with Confidence.
===========================================================
Responsive personal-finance app. Detects phone vs desktop from the
browser User-Agent and adapts the layout; responsive CSS is the backup.

Tabs:  Money  ·  Money Health  ·  Your Style  ·  Next Steps

Plain-English throughout — the quantitative engine (MPT covariance model)
runs underneath but never shows jargon to the user.

Run:  streamlit run Seralungfinance.py
Deps: streamlit plotly numpy pandas
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

st.set_page_config(page_title="Seralung Finance", layout="wide",
                   initial_sidebar_state="collapsed")

# ── DEVICE DETECTION (server-side via User-Agent, with safe fallback) ──
def detect_mobile():
    try:
        ua = (st.context.headers.get("User-Agent", "") or "")
        return any(k in ua for k in ["Mobile", "Android", "iPhone", "iPad", "iPod", "Windows Phone"])
    except Exception:
        return False

IS_MOBILE = detect_mobile()

def cols(n, gap="small"):
    """Return n columns on desktop; stacked full-width containers on mobile."""
    if IS_MOBILE:
        return [st.container() for _ in range(n)]
    return st.columns(n, gap=gap)

# ════════════════════════════════════════════════════════════════
# PALETTE  (modern indigo / violet — matches the reference look)
# ════════════════════════════════════════════════════════════════
BG, CARD, BD   = "#F5F6FB", "#FFFFFF", "#E6E8F2"
TEXT, MUTED, DIM = "#1A1D2E", "#6B7280", "#9AA0AE"
PRIMARY, PRIMARY_DK, PRIMARY_BG = "#4F46E5", "#4338CA", "#EEEFFE"
VIOLET, VIOLET_BG = "#7C3AED", "#F2ECFD"
YELLOW, YELLOW_BG = "#F5D547", "#FDF6D6"
GREEN,  GREEN_BG  = "#16A34A", "#E7F6EC"
AMBER,  AMBER_BG  = "#D97706", "#FBEFDD"
RED,    RED_BG    = "#DC2626", "#FBE7E7"
TEAL,   TEAL_BG   = "#0EA5A4", "#DEF5F4"
PINK,   PINK_BG   = "#EC4899", "#FCE7F1"

FH = "'Plus Jakarta Sans', system-ui, sans-serif"
FM = "'JetBrains Mono', 'Fira Code', monospace"

CAT_PALETTE = [PRIMARY, VIOLET, YELLOW, TEAL, PINK, GREEN, AMBER, "#64748B",
               "#8B5CF6", "#F59E0B", "#14B8A6", "#EF4444", "#3B82F6", "#A855F7"]

# ════════════════════════════════════════════════════════════════
# BUDGET MODEL
# ════════════════════════════════════════════════════════════════
EXPENSE_CATEGORIES = [
    "Housing", "Utilities", "Groceries", "Transport", "Insurance",
    "Healthcare", "Debt Repayment", "Dining Out", "Entertainment",
    "Shopping", "Subscriptions", "Travel", "Savings/Invest", "Other",
]
CATEGORY_TYPE = {
    "Housing": "Need", "Utilities": "Need", "Groceries": "Need",
    "Transport": "Need", "Insurance": "Need", "Healthcare": "Need",
    "Debt Repayment": "Need", "Dining Out": "Want", "Entertainment": "Want",
    "Shopping": "Want", "Subscriptions": "Want", "Travel": "Want",
    "Savings/Invest": "Savings", "Other": "Want",
}
DEFAULT_BILLS = pd.DataFrame([
    {"Bill": "Rent / Mortgage",  "Category": "Housing",        "Amount": 1800},
    {"Bill": "Electricity & Gas","Category": "Utilities",      "Amount": 200},
    {"Bill": "Groceries",        "Category": "Groceries",      "Amount": 650},
    {"Bill": "Car & Fuel",       "Category": "Transport",      "Amount": 350},
    {"Bill": "Health Insurance", "Category": "Insurance",      "Amount": 180},
    {"Bill": "Loan Repayment",   "Category": "Debt Repayment", "Amount": 400},
    {"Bill": "Streaming & Apps", "Category": "Subscriptions",  "Amount": 55},
    {"Bill": "Dining Out",       "Category": "Dining Out",     "Amount": 300},
])

# ════════════════════════════════════════════════════════════════
# QUANT ENGINE  (runs quietly — never shown as jargon)
# ════════════════════════════════════════════════════════════════
MPT_ASSETS = ["Cash", "Bonds", "Equity ETFs", "Stocks", "Property", "Crypto"]
EXP_RETURNS = np.array([0.035, 0.045, 0.080, 0.095, 0.070, 0.180])
VOLS        = np.array([0.010, 0.050, 0.150, 0.240, 0.140, 0.650])
RISK_FREE   = 0.035
CORR = np.array([
    [ 1.00,  0.15,  0.00, -0.05,  0.05,  0.00],
    [ 0.15,  1.00,  0.25,  0.10,  0.30,  0.05],
    [ 0.00,  0.25,  1.00,  0.88,  0.60,  0.35],
    [-0.05,  0.10,  0.88,  1.00,  0.50,  0.40],
    [ 0.05,  0.30,  0.60,  0.50,  1.00,  0.25],
    [ 0.00,  0.05,  0.35,  0.40,  0.25,  1.00],
])
COV = np.outer(VOLS, VOLS) * CORR

TIERS = ["Defensive", "Conservative", "Balanced", "Growth", "Aggressive"]
TIER_WEIGHTS = {
    "Defensive":    [40, 40, 12,  0,  8,  0],
    "Conservative": [22, 33, 25,  3, 15,  2],
    "Balanced":     [10, 22, 35, 10, 18,  5],
    "Growth":       [ 5, 12, 45, 18, 15,  5],
    "Aggressive":   [ 2,  5, 48, 25, 12,  8],
}
# Friendly faces for each tier (level 1-5)
STYLE_META = {
    "Defensive": {"name": "Safe & Sound", "level": 1, "clr": TEAL, "bg": TEAL_BG,
                  "tag": "Calm and steady",
                  "blurb": "Your money stays well protected and grows slowly. Very few surprises — great if you don't want stress.",
                  "bump_word": "Barely moves — very few surprises.",
                  "grow_word": "Slow & steady"},
    "Conservative": {"name": "Slow & Steady", "level": 2, "clr": GREEN, "bg": GREEN_BG,
                  "tag": "Mostly safe, a little growth",
                  "blurb": "Mostly safe with a little room to grow. Gentle ups and downs you'll barely notice.",
                  "bump_word": "Small dips now and then — nothing scary.",
                  "grow_word": "Gentle growth"},
    "Balanced": {"name": "Balanced Mix", "level": 3, "clr": PRIMARY, "bg": PRIMARY_BG,
                  "tag": "A healthy mix of both",
                  "blurb": "An even mix of safe and growing. Some bumps along the way, but more growth over the years.",
                  "bump_word": "Expect some ups and downs — they smooth out over time.",
                  "grow_word": "Solid growth"},
    "Growth": {"name": "Growing Strong", "level": 4, "clr": VIOLET, "bg": VIOLET_BG,
                  "tag": "Aiming for more growth",
                  "blurb": "Reaching for stronger growth. Expect real ups and downs — patience is the secret ingredient.",
                  "bump_word": "Bigger swings — it can drop a fair bit in a rough year, then recover.",
                  "grow_word": "Strong growth"},
    "Aggressive": {"name": "Bold & Brave", "level": 5, "clr": RED, "bg": RED_BG,
                  "tag": "Going for maximum growth",
                  "blurb": "Going for the most growth possible. It's a bumpy ride — only if a sharp drop won't make you panic.",
                  "bump_word": "Big swings both ways — only pick this if you can stay calm when it dips.",
                  "grow_word": "Fast (but wild)"},
}
TIER_OPTIONS = {
    "Defensive": ["Savings accounts & term deposits", "Government bonds (very safe loans to the government)", "Cash savings funds"],
    "Conservative": ["Bond funds (a bundle of safe loans)", "Steady dividend funds", "A small slice of share funds"],
    "Balanced": ["Index funds (one basket holding many companies)", "A ready-made 'balanced' fund", "A mix of shares and bonds"],
    "Growth": ["Share index funds (local & global)", "International funds", "A few solid individual companies"],
    "Aggressive": ["Growth-focused share funds", "Smaller & up-and-coming companies", "A tiny slice of crypto (keep it small)"],
}

# ════════════════════════════════════════════════════════════════
# FRIENDLY 5-QUESTION RISK CHECK
# ════════════════════════════════════════════════════════════════
QUESTIONS = [
    ("When will you need most of this money?",
     ["Soon — under 3 years", "In a few years — 3 to 7", "A long way off — 7 to 15", "Way in the future — 15+"]),
    ("Your investments drop a lot for a few months. What do you do?",
     ["Sell everything — too stressful", "Sell some to feel safer", "Sit tight and wait", "Buy more while it's cheap"]),
    ("What matters more to you right now?",
     ["Keeping my money safe", "Mostly safe, a little growth", "A balance of both", "Growing as much as possible"]),
    ("How do you feel when money goes up and down?",
     ["Really anxious", "A bit uneasy", "Pretty calm", "Totally fine — it's normal"]),
    ("How much do you know about investing?",
     ["Complete beginner", "I know the basics", "Fairly comfortable", "Very experienced"]),
]
# personality from total (5 questions → 5..20)
PERSONALITY = [
    ((5, 8),   "Cautious",   1),
    ((9, 11),  "Careful",    2),
    ((12, 14), "Balanced",   3),
    ((15, 17), "Confident",  4),
    ((18, 20), "Bold",       5),
]

# ════════════════════════════════════════════════════════════════
# SESSION DEFAULTS
# ════════════════════════════════════════════════════════════════
_DEF = {"income_primary": 6000, "income_secondary": 0, "current_savings": 15000,
        **{f"q{i}": 0 for i in range(1, 6)}}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════════════════════════════════════
# CALCULATIONS  (verified, guarded against divide-by-zero)
# ════════════════════════════════════════════════════════════════
def compute_budget(income, bills_df, savings):
    df = bills_df.copy()
    df["_amt"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0).clip(lower=0)
    df = df[df["_amt"] > 0]
    df["_type"] = df["Category"].map(CATEGORY_TYPE).fillna("Want")
    total_exp = float(df["_amt"].sum())
    needs   = float(df.loc[df["_type"] == "Need", "_amt"].sum())
    wants   = float(df.loc[df["_type"] == "Want", "_amt"].sum())
    invest  = float(df.loc[df["_type"] == "Savings", "_amt"].sum())
    debt    = float(df.loc[df["Category"] == "Debt Repayment", "_amt"].sum())
    surplus = income - total_exp
    sr      = surplus / income if income > 0 else 0.0
    # Emergency runway uses ESSENTIAL (needs) expenses — what you must cover in a crisis.
    essential = needs if needs > 0 else total_exp
    runway  = savings / essential if essential > 0 else 0.0
    dti     = debt / income if income > 0 else 0.0
    cat_sums = df.groupby("Category")["_amt"].sum().sort_values(ascending=False).to_dict()
    return {"income": income, "expenses": total_exp, "needs": needs, "wants": wants,
            "invest": invest, "debt": debt, "surplus": surplus, "savings_rate": sr,
            "runway": runway, "essential": essential, "dti": dti, "savings": savings,
            "cat_sums": cat_sums}

def financial_health_score(b):
    inc = b["income"]
    if inc <= 0:
        return 0, {}
    sr  = b["savings_rate"]
    run = b["runway"]
    nr  = b["needs"] / inc
    wr  = b["wants"] / inc
    dti = b["dti"]
    p_sr   = 30 if sr >= 0.20 else max(0, sr) / 0.20 * 30
    p_run  = min(25, run / 6 * 25)
    p_nee  = 20 if nr <= 0.50 else max(0, 20 - (nr - 0.50) * 80)
    p_wan  = 15 if wr <= 0.30 else max(0, 15 - (wr - 0.30) * 60)
    p_debt = 10 if dti <= 0.20 else max(0, 10 - (dti - 0.20) * 40)
    total = round(min(100, p_sr + p_run + p_nee + p_wan + p_debt))
    parts = {
        "Saving habit":   (round(p_sr), 30),
        "Safety net":     (round(p_run), 25),
        "Spending balance": (round(p_nee), 20),
        "Fun-money balance": (round(p_wan), 15),
        "Debt":           (round(p_debt), 10),
    }
    return total, parts

def health_word(score):
    if score >= 80: return "Thriving",  GREEN,  GREEN_BG
    if score >= 65: return "Healthy",   TEAL,   TEAL_BG
    if score >= 45: return "Getting there", AMBER, AMBER_BG
    if score >= 25: return "Needs some love", RED, RED_BG
    return            "Let's build this up", RED, RED_BG

def risk_capacity(b):
    run = min(100, b["runway"] / 6 * 100)
    sr  = min(100, max(0, b["savings_rate"]) / 0.25 * 100)
    dti = max(0, 100 - b["dti"] / 0.50 * 100)
    return round(0.40 * run + 0.40 * sr + 0.20 * dti)

def capacity_level(cap):
    if cap >= 80: return 5, "very strong"
    if cap >= 60: return 4, "strong"
    if cap >= 40: return 3, "okay"
    if cap >= 20: return 2, "a bit tight"
    return            1, "fragile"

def quiz_total():
    return sum(int(st.session_state[f"q{i}"]) + 1 for i in range(1, 6))

def personality():
    s = quiz_total()
    for (lo, hi), name, lvl in PERSONALITY:
        if lo <= s <= hi:
            return name, lvl, s
    return "Balanced", 3, s

def recommended_tier(cap_lvl, tol_lvl):
    idx = max(1, min(5, min(cap_lvl, tol_lvl)))
    return TIERS[idx - 1], idx

def tier_return(tier):
    w = np.array(TIER_WEIGHTS[tier], dtype=float) / 100.0
    return float(w @ EXP_RETURNS)

def grow_estimate(tier, start=1000, years=10):
    return start * (1 + tier_return(tier)) ** years

# ════════════════════════════════════════════════════════════════
# CSS  (modern + responsive)
# ════════════════════════════════════════════════════════════════
HERO_PAD = "1.2rem 1.2rem 1.1rem" if IS_MOBILE else "1.7rem 2.1rem 1.5rem"
TITLE_SZ = "1.45rem" if IS_MOBILE else "1.95rem"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: {BG} !important; font-family: {FH}; color: {TEXT} !important;
}}
.stApp, .stApp p, .stApp label, .stApp li,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {{ color: {TEXT}; }}
.block-container {{ padding: 0 {'0.7rem' if IS_MOBILE else '1.6rem'} 3rem; max-width: 1180px; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}
* {{ box-sizing: border-box; }}
h1,h2,h3,h4 {{ font-family: {FH} !important; font-weight: 700 !important; color: {TEXT} !important; margin: 0 !important; }}

[data-testid="stVerticalBlock"] {{ gap: 0.6rem !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px !important; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 5px; border-bottom: 1px solid {BD}; background: transparent; padding: 0; flex-wrap: wrap; }}
.stTabs [data-baseweb="tab"] {{
    font-family: {FH}; font-size: {'0.85rem' if IS_MOBILE else '1rem'}; text-transform: none; color: {MUTED};
    background: transparent; border: none; font-weight: 600;
    border-bottom: 3px solid transparent; padding: {'10px 13px' if IS_MOBILE else '13px 22px'};
    border-radius: 10px 10px 0 0; transition: all .15s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: {PRIMARY} !important; background: {PRIMARY_BG} !important; }}
.stTabs [aria-selected="true"] {{
    color: {PRIMARY} !important; border-bottom: 3px solid {PRIMARY} !important;
    background: {PRIMARY_BG} !important; font-weight: 700 !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.1rem; background: transparent; }}

div[data-testid="stNumberInput"] label, div[data-testid="stSelectbox"] label {{
    font-family: {FH} !important; font-size: 0.78rem !important; text-transform: none !important;
    color: {MUTED} !important; font-weight: 500 !important;
}}
.stNumberInput input {{
    background: {CARD} !important; border: 1px solid {BD} !important; border-radius: 9px !important;
    color: {TEXT} !important; font-family: {FM} !important; font-size: 0.95rem !important; padding: 8px 12px !important;
}}
.stNumberInput input:focus {{ border-color: {PRIMARY} !important; box-shadow: 0 0 0 3px rgba(79,70,229,0.15) !important; outline: none !important; }}
.stNumberInput button {{ background: {CARD} !important; border-color: {BD} !important; }}

div[data-testid="stRadio"] *, [data-testid="stRadio"] label * {{ color: {TEXT} !important; }}
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
    color: {TEXT} !important; font-family: {FH} !important; font-size: 0.9rem !important; margin: 0 !important; line-height: 1.4 !important;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label {{
    padding: 7px 11px; border-radius: 9px; margin-bottom: 3px; transition: background .12s ease; cursor: pointer;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label:hover {{ background: {PRIMARY_BG}; }}
div[data-testid="stRadio"] > label {{ font-family: {FH} !important; font-size: 0.78rem !important; text-transform: none !important; color: {MUTED} !important; font-weight: 500 !important; }}

.stButton > button {{
    background: {PRIMARY} !important; color: #fff !important; border: none !important; border-radius: 10px !important;
    font-family: {FH} !important; font-size: 0.95rem !important; font-weight: 600 !important; padding: 11px 26px !important;
    box-shadow: 0 4px 14px rgba(79,70,229,0.30) !important; transition: all .15s !important; width: 100%;
}}
.stButton > button:hover {{ background: {PRIMARY_DK} !important; transform: translateY(-1px) !important; }}

.stSelectbox > div > div {{ background: {CARD} !important; border: 1px solid {BD} !important; border-radius: 9px !important; font-family: {FH} !important; }}
[role="listbox"] *, [role="option"] {{ background: {CARD} !important; color: {TEXT} !important; }}

hr {{ border: none; border-top: 1px solid {BD}; margin: 0.8rem 0; }}

@media (max-width: 640px) {{
    .block-container {{ padding: 0 0.7rem 2rem; }}
}}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# UI HELPERS
# ════════════════════════════════════════════════════════════════
def note(text, kind="info"):
    cfg = {"info": (PRIMARY_BG, PRIMARY), "good": (GREEN_BG, GREEN),
           "warn": (AMBER_BG, AMBER), "alert": (RED_BG, RED)}
    bg, ac = cfg.get(kind, cfg["info"])
    st.markdown(f"<div style='background:{bg};border-left:3px solid {ac};border-radius:0 9px 9px 0;"
                f"padding:10px 14px;margin:5px 0;font-family:{FH};font-size:0.9rem;color:{TEXT};line-height:1.55;'>{text}</div>",
                unsafe_allow_html=True)

def section(label, color=PRIMARY):
    st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin:18px 0 9px;'>"
                f"<span style='font-family:{FH};font-size:0.82rem;letter-spacing:0.02em;color:{color};"
                f"white-space:nowrap;font-weight:700;'>{label}</span>"
                f"<div style='flex:1;height:1px;background:{BD};'></div></div>", unsafe_allow_html=True)

def big_kpi(label, value, sub, bg, txt, pill_bg, pill_txt):
    st.markdown(
        f"<div style='background:{bg};border-radius:16px;padding:16px 18px;height:100%;"
        f"box-shadow:0 4px 16px rgba(26,29,46,0.06);'>"
        f"<span style='display:inline-block;background:{pill_bg};color:{pill_txt};font-family:{FH};"
        f"font-size:0.72rem;font-weight:600;padding:3px 11px;border-radius:20px;'>{label}</span>"
        f"<div style='font-family:{FH};font-size:1.7rem;font-weight:800;color:{txt};margin-top:12px;line-height:1.1;'>{value}</div>"
        f"<div style='font-family:{FH};font-size:0.76rem;color:{txt};opacity:0.75;margin-top:3px;'>{sub}</div></div>",
        unsafe_allow_html=True)

def stat_card(label, value, sub="", accent=PRIMARY, bg=CARD):
    st.markdown(f"<div style='background:{bg};border:1px solid {BD};border-radius:14px;padding:13px 15px;height:100%;'>"
                f"<div style='font-family:{FH};font-size:0.74rem;color:{MUTED};font-weight:500;margin-bottom:5px;'>{label}</div>"
                f"<div style='font-family:{FH};font-size:1.3rem;color:{accent};font-weight:800;line-height:1.15;'>{value}</div>"
                f"<div style='font-family:{FH};font-size:0.74rem;color:{MUTED};margin-top:3px;line-height:1.4;'>{sub}</div></div>",
                unsafe_allow_html=True)

def bump_dots(level):
    out = ""
    for i in range(5):
        on = i < level
        c = [GREEN, TEAL, PRIMARY, VIOLET, RED][min(level-1, 4)] if on else BD
        out += f"<span style='display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:4px;background:{c};'></span>"
    return out

def circular_gauge(score, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"font": {"size": 44, "family": "Plus Jakarta Sans", "color": color}},
        gauge={"axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": MUTED,
                        "tickfont": {"size": 9, "family": "JetBrains Mono", "color": MUTED}},
               "bar": {"color": color, "thickness": 0.30},
               "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
               "steps": [{"range": [0, 25], "color": RED_BG}, {"range": [25, 45], "color": AMBER_BG},
                         {"range": [45, 65], "color": "#FFF7DD"}, {"range": [65, 80], "color": TEAL_BG},
                         {"range": [80, 100], "color": GREEN_BG}],
               "threshold": {"line": {"color": color, "width": 4}, "thickness": 0.82, "value": score}}))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=230, margin=dict(t=18, b=8, l=22, r=22),
                      font={"family": "Plus Jakarta Sans", "color": TEXT})
    return fig

def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.64,
                           marker=dict(colors=colors, line=dict(color="#fff", width=2)),
                           textinfo="label+percent",
                           textfont=dict(family="Plus Jakarta Sans, sans-serif", size=10, color=TEXT),
                           hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"))
    ann = [dict(text=center, x=0.5, y=0.5, font=dict(size=13, family="Plus Jakarta Sans", color=TEXT), showarrow=False)] if center else []
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=8, b=8, l=8, r=8), height=250, showlegend=False, annotations=ann)
    return fig

def hbar(labels, values, colors):
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h",
                           marker=dict(color=colors, line_width=0),
                           text=[f"${v:,.0f}" for v in values], textposition="auto",
                           textfont=dict(family="Plus Jakarta Sans", size=10, color="#fff"),
                           hovertemplate="%{y}: $%{x:,.0f}<extra></extra>"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=6, b=6, l=6, r=6), height=max(180, 38 * len(labels)),
                      xaxis=dict(showgrid=True, gridcolor=BD, tickprefix="$",
                                 tickfont=dict(family="JetBrains Mono", size=8, color=MUTED)),
                      yaxis=dict(showgrid=False, tickfont=dict(family="Plus Jakarta Sans", size=11, color=TEXT)),
                      bargap=0.28)
    return fig

# ════════════════════════════════════════════════════════════════
# HEADER  (desktop dashboard hero / mobile app header)
# ════════════════════════════════════════════════════════════════
logo = (f"<div style='width:{'40px' if IS_MOBILE else '48px'};height:{'40px' if IS_MOBILE else '48px'};"
        f"border-radius:13px;background:rgba(255,255,255,0.18);border:1px solid rgba(255,255,255,0.4);"
        f"display:flex;align-items:center;justify-content:center;font-family:{FH};"
        f"font-size:{'1.3rem' if IS_MOBILE else '1.6rem'};font-weight:800;color:#fff;'>S</div>")
st.markdown(
    f"<div style='background:linear-gradient(125deg,{PRIMARY_DK} 0%,{PRIMARY} 50%,{VIOLET} 100%);"
    f"border-radius:0 0 24px 24px;padding:{HERO_PAD};margin:0 {'-0.7rem' if IS_MOBILE else '-1.6rem'} 1.2rem;"
    f"box-shadow:0 8px 26px rgba(67,56,202,0.28);'>"
    f"<div style='display:flex;align-items:center;gap:13px;'>{logo}"
    f"<div><div style='font-family:{FH};font-size:{TITLE_SZ};font-weight:800;color:#fff;letter-spacing:-0.02em;line-height:1;'>Seralung Finance</div>"
    f"<div style='font-family:{FH};font-size:{'0.78rem' if IS_MOBILE else '0.9rem'};color:rgba(255,255,255,0.9);margin-top:4px;font-weight:500;'>"
    f"Understand Risk. Invest with Confidence.</div></div></div>"
    f"<div style='font-family:{FH};font-size:0.74rem;color:rgba(255,255,255,0.85);margin-top:12px;'>"
    f"<span style='background:rgba(255,255,255,0.18);padding:3px 10px;border-radius:20px;'>"
    f"{'📱 ' if False else ''}A friendly guide to your money — no jargon, no stress.</span></div></div>",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["Money", "Money Health", "Your Style", "Next Steps"])

# ════════════════════════════════════════════════════════════════
# TAB 1 — MONEY
# ════════════════════════════════════════════════════════════════
with tab1:
    note("Start here. Pop in what comes in and what goes out — rough numbers are totally fine. Everything else builds on this.", "info")

    section("WHAT COMES IN")
    c1, c2, c3 = cols(3, gap="medium")
    with c1:
        st.number_input("Monthly income ($)", min_value=0, step=250, key="income_primary")
    with c2:
        st.number_input("Extra income ($, optional)", min_value=0, step=100, key="income_secondary")
    with c3:
        st.number_input("Savings you have now ($)", min_value=0, step=1000, key="current_savings")

    income  = st.session_state["income_primary"] + st.session_state["income_secondary"]
    savings = st.session_state["current_savings"]

    section("YOUR MONTHLY BILLS")
    st.caption("Edit any cell. Tap **+** at the bottom of the table to add a bill, or select a row and press delete to remove it.")
    bills = st.data_editor(
        DEFAULT_BILLS, num_rows="dynamic", use_container_width=True, hide_index=True, key="bills_editor",
        column_config={
            "Bill": st.column_config.TextColumn("Bill", width="medium"),
            "Category": st.column_config.SelectboxColumn("Category", options=EXPENSE_CATEGORIES, width="small"),
            "Amount": st.column_config.NumberColumn("Amount ($/mo)", min_value=0, step=10, format="$%d"),
        },
    )

    b = compute_budget(income, bills, savings)
    st.session_state["budget"] = b

    if income <= 0:
        note("Add your monthly income above and your numbers will appear here.", "warn")
    else:
        section("YOUR MONTH AT A GLANCE")
        k1, k2, k3 = cols(3, gap="medium")
        with k1:
            big_kpi("Money in", f"${b['income']:,.0f}", "every month", PRIMARY, "#fff", "rgba(255,255,255,0.22)", "#fff")
        with k2:
            big_kpi("Money out", f"${b['expenses']:,.0f}", f"{b['expenses']/b['income']*100:.0f}% of what you earn", YELLOW, "#3A3000", "rgba(0,0,0,0.10)", "#3A3000")
        with k3:
            kept = b["surplus"]
            kc = GREEN if kept > 0 else RED
            big_kpi("You keep", f"${kept:,.0f}" if kept >= 0 else f"-${abs(kept):,.0f}",
                    f"that's {b['savings_rate']*100:.0f}% of your income", CARD, kc, PRIMARY_BG, PRIMARY)

        if b["surplus"] < 0:
            note("Heads up — right now a little more is going out than coming in. The Next Steps tab has gentle ideas to fix that.", "alert")
        elif b["savings_rate"] >= 0.20:
            note(f"Nice work — you're keeping {b['savings_rate']*100:.0f}% of your income. That's a strong saving habit.", "good")

        section("WHERE YOUR MONEY GOES")
        cc1, cc2 = cols(2, gap="medium")
        with cc1:
            cats = {k: v for k, v in b["cat_sums"].items() if v > 0}
            if cats:
                st.plotly_chart(donut(list(cats.keys()), list(cats.values()),
                                      CAT_PALETTE[:len(cats)], f"${b['expenses']:,.0f}"),
                                use_container_width=True)
        with cc2:
            top = list(b["cat_sums"].items())[:6]
            if top:
                st.plotly_chart(hbar([t[0] for t in top][::-1], [t[1] for t in top][::-1],
                                     CAT_PALETTE[:len(top)][::-1]), use_container_width=True)

        # Plain-English spending insights
        section("WHAT WE NOTICED")
        insights = []
        if b["cat_sums"]:
            top_cat = list(b["cat_sums"].keys())[0]
            top_amt = b["cat_sums"][top_cat]
            insights.append(("info", f"Your biggest expense is <strong>{top_cat}</strong> at ${top_amt:,.0f}/month "
                             f"({top_amt/b['expenses']*100:.0f}% of spending)."))
        hr = b["needs"] / b["income"] if b["income"] else 0
        if hr > 0.55:
            insights.append(("warn", f"Your essentials take up {hr*100:.0f}% of your income — a bit high. "
                             f"The comfy target is around half."))
        wr = b["wants"] / b["income"] if b["income"] else 0
        if wr > 0.32:
            insights.append(("warn", f"Fun spending is {wr*100:.0f}% of your income. Trimming a little here is the "
                             f"easiest way to save more."))
        if b["surplus"] > 0 and b["savings_rate"] < 0.20:
            insights.append(("info", f"You're saving {b['savings_rate']*100:.0f}%. Nudging toward 20% "
                             f"(about ${b['income']*0.20:,.0f}/mo) would speed up your goals."))
        if not insights:
            insights.append(("good", "Your spending looks well balanced. Keep it up!"))
        for kind, txt in insights:
            note(txt, kind)

        section("YOUR SAFETY NET")
        sn1, sn2 = cols(2, gap="medium")
        with sn1:
            rc = GREEN if b["runway"] >= 6 else (AMBER if b["runway"] >= 3 else RED)
            rbg = GREEN_BG if b["runway"] >= 6 else (AMBER_BG if b["runway"] >= 3 else RED_BG)
            stat_card("Safety net", f"{b['runway']:.1f} months",
                      f"if income stopped, your savings cover {b['runway']:.1f} months of essentials", rc, rbg)
        with sn2:
            st.markdown("<div style='padding-top:2px;'></div>", unsafe_allow_html=True)
            if b["runway"] < 3:
                note("Building this up to 3 months is the best first move before investing. It's your cushion if life surprises you.", "alert")
            elif b["runway"] < 6:
                note("You're getting there. Aiming for 6 months of essentials gives you a comfortable cushion.", "warn")
            else:
                note("Lovely — you've got a solid cushion. That's a great place to start investing from.", "good")


# ════════════════════════════════════════════════════════════════
# TAB 2 — MONEY HEALTH
# ════════════════════════════════════════════════════════════════
with tab2:
    b = st.session_state.get("budget", {})
    if not b or b.get("income", 0) <= 0:
        note("Add your money details in the Money tab first — your health score is built from them.", "info")
    else:
        fh, parts = financial_health_score(b)
        word, hclr, hbg = health_word(fh)

        section("YOUR MONEY HEALTH")
        g1, g2 = cols(2, gap="medium")
        with g1:
            st.plotly_chart(circular_gauge(fh, hclr), use_container_width=True)
            st.markdown(f"<div style='text-align:center;margin-top:-10px;'>"
                        f"<span style='background:{hbg};color:{hclr};font-family:{FH};font-weight:700;"
                        f"font-size:1rem;padding:5px 18px;border-radius:20px;'>{word}</span></div>",
                        unsafe_allow_html=True)
        with g2:
            st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
            for lbl, (got, mx) in parts.items():
                pctp = got / mx * 100
                clr = GREEN if pctp >= 70 else (AMBER if pctp >= 40 else RED)
                w = ["needs love", "okay", "great"][2 if pctp >= 70 else (1 if pctp >= 40 else 0)]
                st.markdown(
                    f"<div style='margin-bottom:9px;'>"
                    f"<div style='display:flex;justify-content:space-between;font-family:{FH};font-size:0.85rem;margin-bottom:4px;'>"
                    f"<span style='color:{TEXT};font-weight:600;'>{lbl}</span>"
                    f"<span style='color:{clr};font-weight:700;'>{w}</span></div>"
                    f"<div style='height:9px;background:#EDEFF6;border-radius:5px;overflow:hidden;'>"
                    f"<div style='width:{pctp:.0f}%;height:100%;background:{clr};border-radius:5px;'></div></div></div>",
                    unsafe_allow_html=True)

        if fh < 45:
            note("Your foundation needs a little love. Building your savings and safety net now will do more for you than any investing choice — and it's very doable.", "alert")
        elif fh >= 65:
            note("Your money is in good shape. You've built a strong base to start investing from.", "good")
        else:
            note("You're on your way. A few small tweaks (see Next Steps) will lift this nicely.", "info")

        # Risk personality
        section("WHAT FEELS RIGHT FOR YOU?", VIOLET)
        note("Five quick questions — no right answers. They help us find an investing style that fits *you*.", "info")
        for i, (q, opts) in enumerate(QUESTIONS):
            qk = f"q{i+1}"
            with st.container(border=True):
                st.markdown(f"<div style='display:flex;gap:9px;align-items:flex-start;'>"
                            f"<span style='background:{VIOLET_BG};color:{VIOLET};font-family:{FH};font-size:0.74rem;"
                            f"font-weight:700;padding:2px 9px;border-radius:6px;flex-shrink:0;margin-top:2px;'>{i+1} of 5</span>"
                            f"<span style='font-family:{FH};font-size:0.98rem;font-weight:600;color:{TEXT};line-height:1.4;'>{q}</span></div>",
                            unsafe_allow_html=True)
                idx = st.radio(q, list(range(len(opts))), format_func=lambda x, o=opts: o[x],
                               index=st.session_state[qk], key=f"r_{qk}", label_visibility="collapsed")
                st.session_state[qk] = idx

        pname, plvl, pscore = personality()
        cap = risk_capacity(b)
        cap_lvl, cap_word = capacity_level(cap)
        rec_name, rec_idx = recommended_tier(cap_lvl, plvl)
        st.session_state["plvl"] = plvl
        st.session_state["pname"] = pname
        st.session_state["cap_lvl"] = cap_lvl
        st.session_state["cap_word"] = cap_word
        st.session_state["fh"] = fh

        section("WHAT THIS TELLS US", VIOLET)
        r1, r2, r3 = cols(3, gap="medium")
        pclr = [GREEN, TEAL, PRIMARY, VIOLET, RED][plvl-1]
        pbg  = [GREEN_BG, TEAL_BG, PRIMARY_BG, VIOLET_BG, RED_BG][plvl-1]
        with r1:
            stat_card("How you feel about risk", pname, "your comfort level", pclr, pbg)
        with r2:
            cclr = [RED, AMBER, PRIMARY, TEAL, GREEN][cap_lvl-1]
            cbg  = [RED_BG, AMBER_BG, PRIMARY_BG, TEAL_BG, GREEN_BG][cap_lvl-1]
            stat_card("What your wallet can handle", cap_word.title(), "based on your savings & spending", cclr, cbg)
        with r3:
            sm = STYLE_META[rec_name]
            stat_card("Your best-fit style", sm["name"], "matches both of the above", sm["clr"], sm["bg"])

        gap = plvl - cap_lvl
        if gap >= 2:
            note(f"You're drawn to more risk ({pname}) than your wallet can comfortably handle right now ({cap_word}). Starting a little safer protects you from nasty surprises — you can always step up later.", "warn")
        elif gap <= -2:
            note(f"Your wallet could handle more than you're comfortable with — and that's perfectly fine. Comfort matters most. You can grow into more later, at your own pace.", "info")
        else:
            note("Your comfort and your wallet are nicely in sync — a great place to start from.", "good")


# ════════════════════════════════════════════════════════════════
# TAB 3 — YOUR STYLE
# ════════════════════════════════════════════════════════════════
with tab3:
    note("Investing styles, from calmest to boldest. Pick the one that feels right — there's no wrong answer, only what fits you.", "info")

    plvl = st.session_state.get("plvl", 3)
    cap_lvl = st.session_state.get("cap_lvl", 3)
    rec_name, rec_idx = recommended_tier(cap_lvl, plvl)

    if "plvl" not in st.session_state:
        note("Answer the quick questions in Money Health and we'll highlight your best-fit style.", "warn")
    else:
        sm = STYLE_META[rec_name]
        note(f"Your best fit looks like <strong style='color:{sm['clr']};'>{sm['name']}</strong> — but feel free to explore them all.", "good")

    section("THE FIVE STYLES")
    for t in TIERS:
        sm = STYLE_META[t]
        is_rec = (t == rec_name)
        badge = (f"<span style='background:{sm['clr']};color:#fff;font-family:{FH};font-size:0.66rem;font-weight:700;"
                 f"padding:2px 9px;border-radius:20px;margin-left:8px;'>BEST FIT FOR YOU</span>") if is_rec else ""
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {(sm['clr'] if is_rec else BD)};"
            f"border-left:5px solid {sm['clr']};border-radius:14px;padding:13px 16px;margin-bottom:8px;"
            f"{'box-shadow:0 4px 16px rgba(79,70,229,0.12);' if is_rec else ''}'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;'>"
            f"<div style='font-family:{FH};font-size:1.1rem;font-weight:800;color:{TEXT};'>{sm['name']}{badge}</div>"
            f"<div style='display:flex;align-items:center;gap:7px;'>"
            f"<span style='font-family:{FH};font-size:0.72rem;color:{MUTED};'>bumpiness</span>{bump_dots(sm['level'])}</div></div>"
            f"<div style='font-family:{FH};font-size:0.88rem;color:{MUTED};margin-top:5px;line-height:1.5;'>{sm['blurb']}</div>"
            f"<div style='font-family:{FH};font-size:0.8rem;color:{sm['clr']};font-weight:600;margin-top:6px;'>{sm['grow_word']}</div></div>",
            unsafe_allow_html=True)

    section("TAKE A CLOSER LOOK")
    style_names = [STYLE_META[t]["name"] for t in TIERS]
    pick = st.selectbox("Choose a style", style_names, index=rec_idx - 1, label_visibility="collapsed")
    chosen_tier = TIERS[style_names.index(pick)]
    sm = STYLE_META[chosen_tier]

    d1, d2 = cols(2, gap="medium")
    with d1:
        w = TIER_WEIGHTS[chosen_tier]
        active = [(MPT_ASSETS[i], w[i]) for i in range(len(w)) if w[i] > 0]
        apal = [TEAL, "#6366F1", PRIMARY, VIOLET, GREEN, PINK]
        st.plotly_chart(donut([a for a, _ in active], [v for _, v in active],
                              [apal[MPT_ASSETS.index(a)] for a, _ in active], sm["name"].split()[0]),
                        use_container_width=True)
    with d2:
        g10 = grow_estimate(chosen_tier, 1000, 10)
        st.markdown(
            f"<div style='background:{sm['bg']};border:1px solid {BD};border-left:4px solid {sm['clr']};"
            f"border-radius:0 14px 14px 0;padding:14px 18px;margin-bottom:8px;'>"
            f"<div style='font-family:{FH};font-size:1.3rem;font-weight:800;color:{sm['clr']};'>{sm['name']}</div>"
            f"<div style='font-family:{FH};font-size:0.85rem;color:{MUTED};margin-top:3px;'>{sm['tag']}</div></div>",
            unsafe_allow_html=True)
        stat_card("The ride", sm["grow_word"], sm["bump_word"], sm["clr"], CARD)
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        stat_card("A rough idea", f"~${g10:,.0f}",
                  f"$1,000 left alone for 10 years might grow to about this — markets wobble, so it's a guide, not a promise", PRIMARY, PRIMARY_BG)

    # Comfort match
    diff = sm["level"] - rec_idx
    if "plvl" in st.session_state:
        if diff == 0:
            note(f"This is your best-fit style — a great match for both your comfort and your wallet.", "good")
        elif abs(diff) == 1:
            note("This is a reasonable fit for you — close to your sweet spot.", "info")
        elif diff >= 2:
            note("This one's bolder than what suits you right now. It could feel stressful in a downturn — worth easing in gradually if you're keen.", "warn")
        else:
            note("This one's safer than you need — totally fine, and very calming. You could grow a bit more if you ever wanted to.", "info")

    section(f"WAYS TO INVEST IN THIS STYLE", sm["clr"])
    for opt in TIER_OPTIONS[chosen_tier]:
        st.markdown(f"<div style='background:{CARD};border:1px solid {BD};border-left:3px solid {sm['clr']};"
                    f"border-radius:0 10px 10px 0;padding:9px 14px;margin-bottom:5px;font-family:{FH};"
                    f"font-size:0.9rem;color:{TEXT};'>{opt}</div>", unsafe_allow_html=True)
    note("These are common, beginner-friendly building blocks — not recommendations to buy. When you're ready, a licensed adviser can help you choose specifics.", "info")


# ════════════════════════════════════════════════════════════════
# TAB 4 — NEXT STEPS
# ════════════════════════════════════════════════════════════════
with tab4:
    b = st.session_state.get("budget", {})
    if not b or b.get("income", 0) <= 0:
        note("Fill in the Money tab and the quick questions in Money Health — then your personal plan appears here.", "info")
    else:
        fh = st.session_state.get("fh", financial_health_score(b)[0])
        cap_lvl = st.session_state.get("cap_lvl", 3)
        cap_word = st.session_state.get("cap_word", "okay")
        plvl = st.session_state.get("plvl", 3)
        pname = st.session_state.get("pname", "Balanced")
        rec_name, rec_idx = recommended_tier(cap_lvl, plvl)
        rec_friendly = STYLE_META[rec_name]["name"]

        recs = []
        if b["runway"] < 3:
            target = b["essential"] * 6
            gap_amt = max(0, target - b["savings"])
            if b["surplus"] > 0:
                txt = (f"You've got {b['runway']:.1f} months of essentials saved. Aiming for 6 months (about ${target:,.0f}) "
                       f"gives you a real cushion. At ${b['surplus']:,.0f} saved per month, that's roughly {gap_amt/b['surplus']:.0f} months away.")
            else:
                txt = (f"You've got {b['runway']:.1f} months saved. First, free up a little monthly room (see the spending tips below) — "
                       f"then this buffer will grow on its own.")
            recs.append(("alert", "Build your safety net first", txt))
        elif b["runway"] < 6:
            recs.append(("warn", "Top up your safety net", f"You're at {b['runway']:.1f} months. Reaching 6 gives you a comfy cushion before investing more."))

        sr = b["savings_rate"]
        if sr < 0:
            recs.append(("alert", "Spend a little less than you earn", f"Right now about ${abs(b['surplus']):,.0f} more goes out than comes in each month. Trimming your biggest 'fun' categories is the quickest win — no investment can outrun a monthly gap."))
        elif sr < 0.10:
            recs.append(("warn", "Lift your saving a little", f"You're saving {sr*100:.0f}%. Working toward 20% (about ${b['income']*0.20:,.0f}/mo) really speeds things up. Small cuts add up fast."))

        wr = b["wants"] / b["income"]
        if wr > 0.32:
            recs.append(("info", "Trim fun spending a touch", f"Fun money is {wr*100:.0f}% of income (a comfy target is ~30%). Even a small trim, redirected to savings, compounds over time."))

        if b["dti"] > 0.20:
            recs.append(("warn", "Chip away at debt", f"Debt payments are {b['dti']*100:.0f}% of your income. Clearing higher-interest debt is like a guaranteed return — usually worth doing before investing."))

        gap = plvl - cap_lvl
        if gap >= 2:
            recs.append(("alert", "Start gentler than your gut says", f"You lean {pname.lower()}, but your wallet says go a little safer for now. Begin with the {rec_friendly} style and step up as your cushion grows."))

        if fh >= 65 and b["runway"] >= 6:
            recs.append(("good", "You're ready to start investing", f"Strong foundation! Consider putting your ${max(0,b['surplus']):,.0f}/mo spare into the {rec_friendly} style automatically each month — steady and stress-free."))

        if not any(k in ("alert", "warn") for k, _, _ in recs):
            recs.append(("good", "You're in great shape", "Nothing urgent to fix. Keep saving steadily and check back now and then as life changes."))

        order = {"alert": 0, "warn": 1, "info": 2, "good": 3}
        recs.sort(key=lambda r: order.get(r[0], 4))

        n_alert = sum(1 for r in recs if r[0] == "alert")
        n_warn = sum(1 for r in recs if r[0] == "warn")
        ready = max(0, min(100, fh - n_alert * 12 - n_warn * 5))
        rword, rclr, rbg = health_word(ready)

        section("HOW READY ARE YOU TO INVEST?")
        rr1, rr2 = cols(2, gap="medium")
        with rr1:
            st.plotly_chart(circular_gauge(ready, rclr), use_container_width=True)
        with rr2:
            st.markdown(
                f"<div style='background:{rbg};border:1px solid {BD};border-left:4px solid {rclr};"
                f"border-radius:0 14px 14px 0;padding:16px 20px;margin-top:{'8px' if IS_MOBILE else '34px'};'>"
                f"<div style='font-family:{FH};font-size:1.4rem;font-weight:800;color:{rclr};'>{rword}</div>"
                f"<div style='font-family:{FH};font-size:0.88rem;color:{MUTED};margin-top:5px;line-height:1.5;'>"
                f"{n_alert} thing{'s' if n_alert!=1 else ''} to tackle first, {n_warn} to keep an eye on. "
                f"When you're set, your style is <strong style='color:{STYLE_META[rec_name]['clr']};'>{rec_friendly}</strong>.</div></div>",
                unsafe_allow_html=True)

        section("YOUR PERSONAL PLAN", VIOLET)
        rank = 1
        for kind, title, text in recs:
            cfg = {"alert": (RED_BG, RED), "warn": (AMBER_BG, AMBER), "info": (PRIMARY_BG, PRIMARY), "good": (GREEN_BG, GREEN)}
            bg, ac = cfg.get(kind, cfg["info"])
            tag = {"alert": "Do first", "warn": "Soon", "info": "When you can", "good": "You've got this"}.get(kind, "")
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BD};border-left:3px solid {ac};"
                f"border-radius:0 12px 12px 0;padding:13px 16px;margin-bottom:8px;'>"
                f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;flex-wrap:wrap;'>"
                f"<span style='background:{ac};color:#fff;font-family:{FH};font-size:0.8rem;font-weight:800;"
                f"width:24px;height:24px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;'>{rank}</span>"
                f"<span style='background:{bg};color:{ac};font-family:{FH};font-size:0.64rem;font-weight:700;"
                f"padding:2px 9px;border-radius:20px;text-transform:uppercase;letter-spacing:0.03em;'>{tag}</span>"
                f"<span style='font-family:{FH};font-size:1rem;font-weight:700;color:{TEXT};'>{title}</span></div>"
                f"<div style='font-family:{FH};font-size:0.88rem;color:{MUTED};line-height:1.55;padding-left:34px;'>{text}</div></div>",
                unsafe_allow_html=True)
            rank += 1


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown(
    f"<div style='border-top:1px solid {BD};margin-top:2rem;padding:16px 0 6px;font-family:{FH};"
    f"font-size:0.74rem;color:{DIM};text-align:center;'>"
    f"<strong style='color:{PRIMARY};'>Seralung Finance</strong> &nbsp;·&nbsp; Understand Risk. Invest with Confidence."
    f"<br><span style='font-size:0.68rem;'>A friendly learning tool — not personal financial advice. "
    f"For big money decisions, chat with a licensed adviser.</span></div>",
    unsafe_allow_html=True,
)
