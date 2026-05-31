"""
Seralung Finance — Understand Risk. Invest with Confidence.
===========================================================
Professional 4-tab tool:
  1. Budget               — income + editable bills, 50/30/20, runway
  2. Financial Health     — circular health gauge + risk questionnaire + analysis
  3. Investment Portfolio — 5 model portfolios with full risk/return metrics
  4. Action Plan          — prioritised insights & recommendations

Detects phone vs desktop from the browser User-Agent and adapts the layout.

Run:  streamlit run Seralungfinance.py
Deps: streamlit plotly numpy pandas
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

st.set_page_config(page_title="Seralung Finance", layout="wide",
                   initial_sidebar_state="collapsed")

# ── DEVICE DETECTION (server-side via User-Agent, safe fallback) ──
def detect_mobile():
    try:
        ua = (st.context.headers.get("User-Agent", "") or "")
        return any(k in ua for k in ["Mobile", "Android", "iPhone", "iPad", "iPod", "Windows Phone"])
    except Exception:
        return False

IS_MOBILE = detect_mobile()

def cols(n, gap="small"):
    if IS_MOBILE:
        return [st.container() for _ in range(n)]
    return st.columns(n, gap=gap)

# ════════════════════════════════════════════════════════════════
# PALETTE  (light green)
# ════════════════════════════════════════════════════════════════
BG, CARD, BD   = "#EAF5EC", "#FFFFFF", "#CBE2D2"
TEXT, MUTED, DIM = "#10241A", "#54695E", "#95AC9E"
PRIMARY, PRIMARY_BG, PRIMARY_DK = "#16794D", "#E0F2E7", "#0E5C39"
LGREEN, LGREEN_BG = "#3DA968", "#EAF6EE"
GREEN, GREEN_BG = PRIMARY, PRIMARY_BG
AMBER, AMBER_BG = "#B7791F", "#FBF3E2"
RED,   RED_BG   = "#C53929", "#FBEAE7"
PURPLE, PURPLE_BG = "#7C3AED", "#F1ECFC"
TEAL,  TEAL_BG  = "#0E7C7B", "#DFF2F1"
SLATE, SLATE_BG = "#6B7280", "#F2F4F7"

FH = "'Plus Jakarta Sans', system-ui, sans-serif"
FM = "'JetBrains Mono', 'Fira Code', monospace"

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
    {"Expense": "Rent / Mortgage",  "Category": "Housing",        "Amount": 1800},
    {"Expense": "Electricity & Gas","Category": "Utilities",      "Amount": 200},
    {"Expense": "Groceries",        "Category": "Groceries",      "Amount": 650},
    {"Expense": "Car & Fuel",       "Category": "Transport",      "Amount": 350},
    {"Expense": "Health Insurance", "Category": "Insurance",      "Amount": 180},
    {"Expense": "Loan Repayment",   "Category": "Debt Repayment", "Amount": 400},
    {"Expense": "Streaming & Apps", "Category": "Subscriptions",  "Amount": 55},
    {"Expense": "Dining Out",       "Category": "Dining Out",     "Amount": 300},
])

# ════════════════════════════════════════════════════════════════
# INVESTMENT ENGINE
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
TIER_CLR = {"Defensive": TEAL, "Conservative": GREEN, "Balanced": PRIMARY,
            "Growth": AMBER, "Aggressive": RED}
TIER_BG  = {"Defensive": TEAL_BG, "Conservative": GREEN_BG, "Balanced": PRIMARY_BG,
            "Growth": AMBER_BG, "Aggressive": RED_BG}
TIER_LEVEL = {"Defensive": 1, "Conservative": 2, "Balanced": 3, "Growth": 4, "Aggressive": 5}
TIER_OPTIONS = {
    "Defensive": [
        "High-interest savings & term deposits",
        "Government bond ETFs (e.g. VGB, IAF)",
        "Cash management / money-market funds",
        "Capital-guaranteed products",
    ],
    "Conservative": [
        "Diversified bond ETFs (corporate + government)",
        "Blue-chip dividend ETFs",
        "Small allocation to broad index funds",
        "Defensive listed property (A-REIT ETFs)",
    ],
    "Balanced": [
        "Broad-market index ETFs (VAS, VGS, IVV)",
        "Balanced multi-asset funds (~60/40)",
        "Listed property / infrastructure ETFs",
        "Investment-grade bond ETFs for ballast",
    ],
    "Growth": [
        "Global & domestic equity ETFs (growth tilt)",
        "International index funds (developed + emerging)",
        "Sector / thematic ETFs as satellites",
        "Small allocation to quality individual stocks",
    ],
    "Aggressive": [
        "Growth & thematic equity ETFs",
        "Emerging-market & small-cap ETFs",
        "Selective individual growth stocks",
        "Small, capped crypto allocation (under 10%)",
    ],
}

# ════════════════════════════════════════════════════════════════
# RISK QUESTIONNAIRE  (10 questions)
# ════════════════════════════════════════════════════════════════
QUESTIONS = [
    ("When do you expect to need this money?",
     ["Under 3 years", "3–7 years", "7–15 years", "15+ years"]),
    ("How stable is your income?",
     ["Retired or fixed income", "Variable or self-employed", "Stable salary", "Very secure"]),
    ("If your portfolio fell 30% in three months, you would:",
     ["Sell everything", "Sell some", "Hold and wait", "Buy more at lower prices"]),
    ("How much investing experience do you have?",
     ["None", "Basic — shares & funds", "Three or more years active", "Ten or more years, multi-asset"]),
    ("Your primary investment goal:",
     ["Protect capital", "Modest growth with protection", "Balanced growth", "Maximum growth"]),
    ("Do you expect significant withdrawals within five years?",
     ["Yes — most of it", "Yes — a meaningful portion", "Possibly — small amounts", "No — long-term"]),
    ("Maximum annual loss you could absorb:",
     ["Under 5%", "5–15%", "15–25%", "25% or more"]),
    ("This investment is what share of your net worth?",
     ["Over 75%", "50–75%", "25–50%", "Under 25%"]),
    ("How do market swings make you feel?",
     ["Very anxious", "Uneasy", "Mostly calm", "Indifferent — it is normal"]),
    ("Your investment knowledge level:",
     ["Beginner", "Some understanding", "Confident", "Advanced"]),
]
TOL_PROFILES = {
    "Conservative":            {"range": (10, 18), "level": 1, "clr": GREEN,   "bg": GREEN_BG},
    "Moderately Conservative": {"range": (19, 25), "level": 2, "clr": TEAL,    "bg": TEAL_BG},
    "Balanced":                {"range": (26, 31), "level": 3, "clr": PRIMARY, "bg": PRIMARY_BG},
    "Growth":                  {"range": (32, 36), "level": 4, "clr": AMBER,   "bg": AMBER_BG},
    "Aggressive":              {"range": (37, 40), "level": 5, "clr": RED,     "bg": RED_BG},
}

# ════════════════════════════════════════════════════════════════
# SESSION DEFAULTS
# ════════════════════════════════════════════════════════════════
_DEF = {"income_primary": 6000, "income_secondary": 0, "current_savings": 15000,
        **{f"q{i}": 0 for i in range(1, 11)}}
for k, v in _DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ════════════════════════════════════════════════════════════════
# CALCULATIONS
# ════════════════════════════════════════════════════════════════
def portfolio_metrics(weights_pct):
    w = np.array(weights_pct, dtype=float) / 100.0
    rp  = float(w @ EXP_RETURNS)
    sd  = float(w @ COV @ w) ** 0.5
    sharpe = (rp - RISK_FREE) / sd if sd > 0 else 0.0
    z, phi = 1.645, 0.103138
    var95  = max(0.0, z * sd - rp)
    cvar95 = max(0.0, sd * (phi / 0.05) - rp)
    div_ratio = float(w @ VOLS) / sd if sd > 0 else 1.0
    max_dd = min(0.95, 2.4 * sd)
    return {"ret": rp, "vol": sd, "sharpe": sharpe, "var95": var95,
            "cvar95": cvar95, "div_ratio": div_ratio, "max_dd": max_dd}

TIER_METRICS = {t: portfolio_metrics(TIER_WEIGHTS[t]) for t in TIERS}

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
    essential = needs if needs > 0 else total_exp
    runway  = savings / essential if essential > 0 else 0.0
    dti     = debt / income if income > 0 else 0.0
    cat_sums = df.groupby("Category")["_amt"].sum().sort_values(ascending=False).to_dict()
    return {"income": income, "expenses": total_exp, "needs": needs, "wants": wants,
            "invest": invest, "debt": debt, "surplus": surplus, "savings_rate": sr,
            "runway": runway, "essential": essential, "dti": dti, "savings": savings, "cat_sums": cat_sums}

def financial_health_score(b):
    inc = b["income"]
    if inc <= 0:
        return 0, {}
    sr, run = b["savings_rate"], b["runway"]
    nr, wr, dti = b["needs"] / inc, b["wants"] / inc, b["dti"]
    p_sr   = 30 if sr >= 0.20 else max(0, sr) / 0.20 * 30
    p_run  = min(25, run / 6 * 25)
    p_nee  = 20 if nr <= 0.50 else max(0, 20 - (nr - 0.50) * 80)
    p_wan  = 15 if wr <= 0.30 else max(0, 15 - (wr - 0.30) * 60)
    p_debt = 10 if dti <= 0.20 else max(0, 10 - (dti - 0.20) * 40)
    total = round(min(100, p_sr + p_run + p_nee + p_wan + p_debt))
    return total, {
        "Savings rate": (round(p_sr), 30),
        "Emergency runway": (round(p_run), 25),
        "Needs control": (round(p_nee), 20),
        "Wants control": (round(p_wan), 15),
        "Debt load": (round(p_debt), 10),
    }

def health_rating(score):
    if score >= 80: return "Excellent", GREEN, GREEN_BG
    if score >= 65: return "Good",      TEAL,  TEAL_BG
    if score >= 45: return "Fair",      AMBER, AMBER_BG
    if score >= 25: return "At Risk",   RED,   RED_BG
    return            "Critical",        RED,   RED_BG

def risk_capacity(b):
    run = min(100, b["runway"] / 6 * 100)
    sr  = min(100, max(0, b["savings_rate"]) / 0.25 * 100)
    dti = max(0, 100 - b["dti"] / 0.50 * 100)
    return round(0.40 * run + 0.40 * sr + 0.20 * dti)

def capacity_level(cap):
    if cap >= 80: return 5, "Strong"
    if cap >= 60: return 4, "Solid"
    if cap >= 40: return 3, "Moderate"
    if cap >= 20: return 2, "Limited"
    return            1, "Fragile"

def quiz_total():
    return sum(int(st.session_state[f"q{i}"]) + 1 for i in range(1, 11))

def tolerance_profile():
    s = quiz_total()
    for name, d in TOL_PROFILES.items():
        lo, hi = d["range"]
        if lo <= s <= hi:
            return name, d, s
    return "Balanced", TOL_PROFILES["Balanced"], s

def recommended_tier(cap_lvl, tol_lvl):
    idx = max(1, min(5, min(cap_lvl, tol_lvl)))
    return TIERS[idx - 1], idx

# ════════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════════
HERO_PAD = "1.2rem 1.2rem 1.1rem" if IS_MOBILE else "1.6rem 2rem 1.4rem"
TITLE_SZ = "1.45rem" if IS_MOBILE else "1.9rem"
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: {BG} !important; font-family: {FH}; color: {TEXT} !important;
}}
.stApp, .stApp p, .stApp label, .stApp li,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {{ color: {TEXT}; }}
.block-container {{ padding: 0 {'0.7rem' if IS_MOBILE else '1.6rem'} 3rem; max-width: 1140px; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}
* {{ box-sizing: border-box; }}
h1,h2,h3,h4 {{ font-family: {FH} !important; font-weight: 700 !important; color: {TEXT} !important; margin: 0 !important; }}

[data-testid="stVerticalBlock"] {{ gap: 0.55rem !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 12px !important; }}

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
    background: {CARD} !important; border: 1px solid {BD} !important; border-radius: 8px !important;
    color: {TEXT} !important; font-family: {FM} !important; font-size: 0.92rem !important; padding: 7px 11px !important;
}}
.stNumberInput input:focus {{ border-color: {PRIMARY} !important; box-shadow: 0 0 0 3px rgba(22,121,77,0.15) !important; outline: none !important; }}
.stNumberInput button {{ background: {CARD} !important; border-color: {BD} !important; }}

div[data-testid="stRadio"] *, [data-testid="stRadio"] label * {{ color: {TEXT} !important; }}
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
    color: {TEXT} !important; font-family: {FH} !important; font-size: 0.88rem !important; margin: 0 !important; line-height: 1.4 !important;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label {{
    padding: 6px 10px; border-radius: 7px; margin-bottom: 2px; transition: background .12s ease; cursor: pointer;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label:hover {{ background: {PRIMARY_BG}; }}
div[data-testid="stRadio"] > label {{ font-family: {FH} !important; font-size: 0.78rem !important; text-transform: none !important; color: {MUTED} !important; font-weight: 500 !important; }}

.stButton > button {{
    background: {PRIMARY} !important; color: #fff !important; border: none !important; border-radius: 8px !important;
    font-family: {FH} !important; font-size: 0.93rem !important; font-weight: 600 !important; padding: 10px 26px !important;
    box-shadow: 0 3px 12px rgba(22,121,77,0.30) !important; transition: all .15s !important; width: 100%;
}}
.stButton > button:hover {{ background: {PRIMARY_DK} !important; transform: translateY(-1px) !important; }}

.stSelectbox > div > div {{ background: {CARD} !important; border: 1px solid {BD} !important; border-radius: 8px !important; font-family: {FH} !important; }}
[role="listbox"] *, [role="option"] {{ background: {CARD} !important; color: {TEXT} !important; }}

hr {{ border: none; border-top: 1px solid {BD}; margin: 0.8rem 0; }}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# UI HELPERS
# ════════════════════════════════════════════════════════════════
def note(text, kind="info"):
    cfg = {"info": (PRIMARY_BG, PRIMARY), "good": (GREEN_BG, GREEN),
           "warn": (AMBER_BG, AMBER), "alert": (RED_BG, RED)}
    bg, ac = cfg.get(kind, cfg["info"])
    st.markdown(f"<div style='background:{bg};border-left:3px solid {ac};border-radius:0 7px 7px 0;"
                f"padding:9px 13px;margin:5px 0;font-family:{FH};font-size:0.88rem;color:{TEXT};line-height:1.55;'>{text}</div>",
                unsafe_allow_html=True)

def section(label, color=PRIMARY):
    st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin:18px 0 9px;'>"
                f"<span style='font-family:{FH};font-size:0.78rem;letter-spacing:0.04em;text-transform:uppercase;"
                f"color:{color};white-space:nowrap;font-weight:700;'>{label}</span>"
                f"<div style='flex:1;height:1px;background:{BD};'></div></div>", unsafe_allow_html=True)

def metric_card(label, value, sub="", accent=PRIMARY, bg=CARD):
    st.markdown(f"<div style='background:{bg};border:1px solid {BD};border-top:3px solid {accent};"
                f"border-radius:0 0 10px 10px;padding:12px 14px;min-width:0;height:100%;'>"
                f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};font-weight:500;margin-bottom:5px;"
                f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{label}</div>"
                f"<div style='font-family:{FH};font-size:1.35rem;color:{accent};font-weight:700;line-height:1.2;word-break:break-word;'>{value}</div>"
                f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};margin-top:3px;line-height:1.4;'>{sub}</div></div>",
                unsafe_allow_html=True)

def circular_gauge(score, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"font": {"size": 46, "family": "Plus Jakarta Sans", "color": color}},
        gauge={"axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": MUTED,
                        "tickfont": {"size": 9, "family": "JetBrains Mono", "color": MUTED}},
               "bar": {"color": color, "thickness": 0.28},
               "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
               "steps": [{"range": [0, 25], "color": RED_BG}, {"range": [25, 45], "color": AMBER_BG},
                         {"range": [45, 65], "color": "#FFF7E0"}, {"range": [65, 80], "color": LGREEN_BG},
                         {"range": [80, 100], "color": GREEN_BG}],
               "threshold": {"line": {"color": color, "width": 4}, "thickness": 0.8, "value": score}}))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=230, margin=dict(t=18, b=8, l=22, r=22),
                      font={"family": "Plus Jakarta Sans", "color": TEXT})
    return fig

def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62,
                           marker=dict(colors=colors, line=dict(color="#fff", width=2)),
                           textinfo="label+percent",
                           textfont=dict(family="Plus Jakarta Sans, sans-serif", size=10, color=TEXT),
                           hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"))
    ann = [dict(text=center, x=0.5, y=0.5, font=dict(size=13, family="Plus Jakarta Sans", color=TEXT), showarrow=False)] if center else []
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=8, b=8, l=8, r=8), height=250, showlegend=False, annotations=ann)
    return fig

def bar_5030(needs_pct, wants_pct, save_pct):
    fig = go.Figure()
    cats = ["Needs", "Wants", "Savings"]
    fig.add_trace(go.Bar(name="Your %", x=cats, y=[needs_pct, wants_pct, save_pct],
                         marker_color=PRIMARY, marker_line_width=0, hovertemplate="%{x}: %{y:.0f}%<extra></extra>"))
    fig.add_trace(go.Bar(name="50/30/20 ideal", x=cats, y=[50, 30, 20],
                         marker_color=DIM, marker_line_width=0, hovertemplate="%{x} ideal: %{y}%<extra></extra>"))
    fig.update_layout(barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=8, b=8, l=8, r=8), height=230,
                      legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.12,
                                  font=dict(family="JetBrains Mono", size=9, color=MUTED)),
                      xaxis=dict(showgrid=False, tickfont=dict(family="Plus Jakarta Sans", size=11, color=TEXT)),
                      yaxis=dict(showgrid=True, gridcolor=BD, ticksuffix="%",
                                 tickfont=dict(family="JetBrains Mono", size=8, color=MUTED)),
                      bargap=0.3, bargroupgap=0.08)
    return fig

# ════════════════════════════════════════════════════════════════
# HEADER  (flat light-green, no gradient)
# ════════════════════════════════════════════════════════════════
logo = (f"<div style='width:{'40px' if IS_MOBILE else '48px'};height:{'40px' if IS_MOBILE else '48px'};"
        f"border-radius:13px;background:rgba(255,255,255,0.18);border:1px solid rgba(255,255,255,0.4);"
        f"display:flex;align-items:center;justify-content:center;font-family:{FH};"
        f"font-size:{'1.3rem' if IS_MOBILE else '1.6rem'};font-weight:800;color:#fff;'>S</div>")
st.markdown(
    f"<div style='background:{PRIMARY};border-radius:0 0 20px 20px;padding:{HERO_PAD};"
    f"margin:0 {'-0.7rem' if IS_MOBILE else '-1.6rem'} 1.2rem;box-shadow:0 4px 16px rgba(14,92,57,0.18);'>"
    f"<div style='display:flex;align-items:center;gap:13px;'>{logo}"
    f"<div><div style='font-family:{FH};font-size:{TITLE_SZ};font-weight:800;color:#fff;letter-spacing:-0.02em;line-height:1;'>Seralung Finance</div>"
    f"<div style='font-family:{FH};font-size:{'0.78rem' if IS_MOBILE else '0.9rem'};color:rgba(255,255,255,0.9);margin-top:4px;font-weight:500;'>"
    f"Understand Risk. Invest with Confidence.</div></div></div></div>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<div style='font-family:{FH};font-size:0.78rem;color:{MUTED};padding:0 0 8px;'>"
    f"<span style='background:{PRIMARY_BG};color:{PRIMARY_DK};font-weight:600;padding:3px 9px;border-radius:5px;'>Educational only</span>"
    f"&nbsp; Not personal financial advice — consult a licensed adviser before investing.</div>",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["Budget", "Financial Health", "Investment Portfolio", "Action Plan"])

# ════════════════════════════════════════════════════════════════
# TAB 1 — BUDGET
# ════════════════════════════════════════════════════════════════
with tab1:
    note("Enter your income and expenses. Add or remove bills directly in the table — every budget metric recalculates live.", "info")

    section("INCOME & SAVINGS")
    i1, i2, i3 = cols(3, gap="medium")
    with i1:
        st.number_input("Monthly primary income ($)", min_value=0, step=250, key="income_primary")
    with i2:
        st.number_input("Secondary income ($, optional)", min_value=0, step=100, key="income_secondary")
    with i3:
        st.number_input("Current cash savings ($)", min_value=0, step=1000, key="current_savings")

    income  = st.session_state["income_primary"] + st.session_state["income_secondary"]
    savings = st.session_state["current_savings"]

    section("YOUR BILLS & EXPENSES")
    st.caption("Edit any cell. Use the + at the bottom of the table to add a bill, or select a row and press delete to remove it.")
    bills = st.data_editor(
        DEFAULT_BILLS, num_rows="dynamic", use_container_width=True, hide_index=True, key="bills_editor",
        column_config={
            "Expense": st.column_config.TextColumn("Expense", width="medium"),
            "Category": st.column_config.SelectboxColumn("Category", options=EXPENSE_CATEGORIES, width="small"),
            "Amount": st.column_config.NumberColumn("Amount ($/mo)", min_value=0, step=10, format="$%d"),
        },
    )

    b = compute_budget(income, bills, savings)
    st.session_state["budget"] = b

    if income <= 0:
        note("Enter your monthly income above to see your budget analysis.", "warn")
    else:
        section("BUDGET SUMMARY")
        c1, c2, c3, c4 = cols(4, gap="small")
        with c1:
            metric_card("Total Income", f"${b['income']:,.0f}", "Per month", TEXT, BG)
        with c2:
            metric_card("Total Expenses", f"${b['expenses']:,.0f}", f"{b['expenses']/b['income']*100:.0f}% of income", AMBER, AMBER_BG)
        with c3:
            sc = GREEN if b["surplus"] > 0 else RED
            sbg = GREEN_BG if b["surplus"] > 0 else RED_BG
            metric_card("Monthly Surplus", f"${b['surplus']:,.0f}" if b["surplus"] >= 0 else f"-${abs(b['surplus']):,.0f}", "Income − expenses", sc, sbg)
        with c4:
            src = GREEN if b["savings_rate"] >= 0.20 else (AMBER if b["savings_rate"] >= 0.10 else RED)
            srbg = GREEN_BG if b["savings_rate"] >= 0.20 else (AMBER_BG if b["savings_rate"] >= 0.10 else RED_BG)
            metric_card("Savings Rate", f"{b['savings_rate']*100:.1f}%", "Surplus / income", src, srbg)

        section("50 / 30 / 20 RULE")
        nr = b["needs"] / b["income"] * 100
        wr = b["wants"] / b["income"] * 100
        sv = max(0, b["surplus"]) / b["income"] * 100
        colA, colB = cols(2, gap="large")
        with colA:
            st.plotly_chart(bar_5030(nr, wr, sv), use_container_width=True)
        with colB:
            st.markdown("<div style='padding-top:6px;'></div>", unsafe_allow_html=True)
            for lbl, val, ideal, hint in [
                ("Needs", nr, 50, "housing, food, transport, insurance, debt"),
                ("Wants", wr, 30, "dining, entertainment, shopping, travel"),
                ("Savings", sv, 20, "everything left over"),
            ]:
                ok = (val <= ideal + 2) if lbl != "Savings" else (val >= ideal - 2)
                clr = GREEN if ok else AMBER
                st.markdown(
                    f"<div style='background:{CARD};border:1px solid {BD};border-radius:8px;padding:9px 12px;margin-bottom:6px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    f"<span style='font-family:{FH};font-weight:700;color:{TEXT};font-size:0.9rem;'>{lbl}</span>"
                    f"<span style='font-family:{FM};font-weight:700;color:{clr};font-size:0.9rem;'>"
                    f"{val:.0f}% <span style='color:{MUTED};font-weight:400;'>/ {ideal}%</span></span></div>"
                    f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};margin-top:2px;'>{hint}</div></div>",
                    unsafe_allow_html=True)

        section("WHERE YOUR MONEY GOES")
        cd, ce = cols(2, gap="large")
        with cd:
            cats = {k: v for k, v in b["cat_sums"].items() if v > 0}
            if cats:
                palette = [PRIMARY, TEAL, AMBER, PURPLE, RED, LGREEN, SLATE,
                           "#0E7C7B", "#B7791F", "#7C3AED", "#3DA968", "#C53929", "#6B7280", "#16794D"]
                st.plotly_chart(donut(list(cats.keys()), list(cats.values()), palette[:len(cats)], f"${b['expenses']:,.0f}"),
                                use_container_width=True)
        with ce:
            st.markdown("<div style='padding-top:6px;'></div>", unsafe_allow_html=True)
            runway_clr = GREEN if b["runway"] >= 6 else (AMBER if b["runway"] >= 3 else RED)
            runway_bg  = GREEN_BG if b["runway"] >= 6 else (AMBER_BG if b["runway"] >= 3 else RED_BG)
            metric_card("Emergency Fund Runway", f"{b['runway']:.1f} months",
                        f"${b['savings']:,.0f} savings ÷ ${b['essential']:,.0f}/mo essentials", runway_clr, runway_bg)
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            if b["runway"] < 3:
                note("Your emergency fund is below 3 months of essential expenses. This is the most important fix before investing.", "alert")
            elif b["runway"] < 6:
                note("Aim for 6 months of essential expenses in accessible savings before taking on investment risk.", "warn")
            else:
                note("Healthy emergency buffer — a solid foundation to invest from.", "good")


# ════════════════════════════════════════════════════════════════
# TAB 2 — FINANCIAL HEALTH
# ════════════════════════════════════════════════════════════════
with tab2:
    b = st.session_state.get("budget", {})
    if not b or b.get("income", 0) <= 0:
        note("Complete the Budget tab first — financial health is calculated from your income and expenses.", "info")
    else:
        fh, parts = financial_health_score(b)
        rating, hclr, hbg = health_rating(fh)

        section("FINANCIAL HEALTH")
        g1, g2 = cols(2, gap="large")
        with g1:
            st.plotly_chart(circular_gauge(fh, hclr), use_container_width=True)
            st.markdown(f"<div style='text-align:center;margin-top:-12px;'>"
                        f"<span style='background:{hbg};color:{hclr};font-family:{FH};font-weight:700;"
                        f"font-size:0.95rem;padding:4px 16px;border-radius:20px;'>{rating}</span></div>",
                        unsafe_allow_html=True)
        with g2:
            st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
            for lbl, (got, mx) in parts.items():
                pctp = got / mx * 100
                clr = GREEN if pctp >= 70 else (AMBER if pctp >= 40 else RED)
                st.markdown(
                    f"<div style='margin-bottom:7px;'>"
                    f"<div style='display:flex;justify-content:space-between;font-family:{FH};font-size:0.82rem;margin-bottom:3px;'>"
                    f"<span style='color:{TEXT};font-weight:500;'>{lbl}</span>"
                    f"<span style='color:{clr};font-family:{FM};font-weight:600;'>{got}/{mx}</span></div>"
                    f"<div style='height:6px;background:rgba(0,0,0,0.07);border-radius:3px;overflow:hidden;'>"
                    f"<div style='width:{pctp:.0f}%;height:100%;background:{clr};border-radius:3px;'></div></div></div>",
                    unsafe_allow_html=True)

        cap = risk_capacity(b)
        cap_lvl, cap_word = capacity_level(cap)
        if fh < 45:
            note("Your financial foundation needs work. Strengthening savings and your emergency fund will do more for your wealth right now than any investment decision.", "alert")
        elif cap_lvl >= 4:
            note(f"Strong financial position — your capacity to absorb investment volatility is {cap_word.lower()}.", "good")
        else:
            note(f"Your financial health is {rating.lower()} and your risk capacity is {cap_word.lower()}.", "info")

        section("RISK PROFILE — 10 QUESTIONS", TEAL)
        note("These measure your personal comfort with volatility (your risk tolerance). Your profile updates live.", "info")
        for i, (q, opts) in enumerate(QUESTIONS):
            qk = f"q{i+1}"
            with st.container(border=True):
                st.markdown(f"<div style='display:flex;gap:9px;align-items:flex-start;'>"
                            f"<span style='background:{TEAL_BG};color:{TEAL};font-family:{FH};font-size:0.72rem;"
                            f"font-weight:700;padding:2px 8px;border-radius:4px;flex-shrink:0;margin-top:2px;'>{i+1:02d}/10</span>"
                            f"<span style='font-family:{FH};font-size:0.95rem;font-weight:600;color:{TEXT};line-height:1.4;'>{q}</span></div>",
                            unsafe_allow_html=True)
                idx = st.radio(q, list(range(len(opts))), format_func=lambda x, o=opts: o[x],
                               index=st.session_state[qk], key=f"r_{qk}", label_visibility="collapsed")
                st.session_state[qk] = idx

        tname, tdata, tscore = tolerance_profile()
        st.session_state["tol_name"]  = tname
        st.session_state["tol_level"] = tdata["level"]
        st.session_state["cap_level"] = cap_lvl
        st.session_state["cap_word"]  = cap_word
        st.session_state["fh_score"]  = fh

        section("RISK ANALYSIS", PURPLE)
        ra1, ra2, ra3 = cols(3, gap="small")
        with ra1:
            metric_card("Risk Tolerance", tname, f"Level {tdata['level']}/5 · score {tscore}/40", tdata["clr"], tdata["bg"])
        with ra2:
            cclr = [RED, RED, AMBER, TEAL, GREEN][cap_lvl-1]
            cbg  = [RED_BG, RED_BG, AMBER_BG, TEAL_BG, GREEN_BG][cap_lvl-1]
            metric_card("Risk Capacity", cap_word, f"Level {cap_lvl}/5 · from your budget", cclr, cbg)
        with ra3:
            rec_name, rec_idx = recommended_tier(cap_lvl, tdata["level"])
            metric_card("Suggested Tier", rec_name, "Prudent match (lower of the two)", TIER_CLR[rec_name], TIER_BG[rec_name])

        gap = tdata["level"] - cap_lvl
        if gap >= 2:
            note(f"Your appetite for risk ({tname}) is well above what your finances can currently support ({cap_word}). Starting below your comfort level protects you from being forced to sell in a downturn.", "alert")
        elif gap <= -2:
            note(f"Your finances could support more risk ({cap_word}) than you are comfortable with ({tname}). That is fine — comfort matters, and you can step up gradually as confidence grows.", "info")
        else:
            note("Your risk tolerance and financial capacity are well aligned — a strong position to build an investment plan from.", "good")


# ════════════════════════════════════════════════════════════════
# TAB 3 — INVESTMENT PORTFOLIO
# ════════════════════════════════════════════════════════════════
with tab3:
    note("Five model portfolios from lowest to highest risk, with the key risk and return figures for each.", "info")

    tol_lvl = st.session_state.get("tol_level", 3)
    cap_lvl = st.session_state.get("cap_level", 3)
    rec_name, rec_idx = recommended_tier(cap_lvl, tol_lvl)

    if "tol_level" not in st.session_state:
        note("Complete the Financial Health tab to see which tier is matched to you.", "warn")
    else:
        note(f"Based on your risk capacity and tolerance, your suggested starting tier is "
             f"<strong style='color:{TIER_CLR[rec_name]};'>{rec_name}</strong>.", "good")

    section("CHOOSE A TIER TO EXPLORE")
    choice = st.selectbox("Risk tier", TIERS, index=rec_idx - 1, label_visibility="collapsed")
    m = TIER_METRICS[choice]
    clr, cbg = TIER_CLR[choice], TIER_BG[choice]

    dl, dr = cols(2, gap="large")
    with dl:
        w = TIER_WEIGHTS[choice]
        active = [(MPT_ASSETS[i], w[i]) for i in range(len(w)) if w[i] > 0]
        apal = [TEAL, "#5A4A7A", PRIMARY, AMBER, LGREEN, PURPLE]
        st.plotly_chart(donut([a for a, _ in active], [v for _, v in active],
                              [apal[MPT_ASSETS.index(a)] for a, _ in active], choice),
                        use_container_width=True)
    with dr:
        st.markdown(
            f"<div style='background:{cbg};border:1px solid {BD};border-left:4px solid {clr};"
            f"border-radius:0 12px 12px 0;padding:14px 18px;margin-bottom:8px;'>"
            f"<div style='font-family:{FH};font-size:1.5rem;font-weight:800;color:{clr};'>{choice}"
            f"{'  ·  suggested for you' if choice == rec_name else ''}</div>"
            f"<div style='font-family:{FH};font-size:0.82rem;color:{MUTED};margin-top:2px;'>"
            f"Expected return <strong style='color:{TEXT};'>{m['ret']*100:.1f}%</strong> p.a. · "
            f"Volatility <strong style='color:{TEXT};'>{m['vol']*100:.1f}%</strong></div></div>",
            unsafe_allow_html=True)
        mm1, mm2 = cols(2, gap="small")
        with mm1:
            metric_card("Sharpe Ratio", f"{m['sharpe']:.2f}", "Return per unit of risk", PRIMARY, PRIMARY_BG)
            metric_card("Value at Risk (95%)", f"{m['var95']*100:.1f}%", "Worst year in 20 (1-yr)", RED, RED_BG)
        with mm2:
            metric_card("Diversification", f"{m['div_ratio']:.2f}×", "Higher = better spread", TEAL, TEAL_BG)
            metric_card("Est. Max Drawdown", f"{m['max_dd']*100:.0f}%", "Peak-to-trough estimate", AMBER, AMBER_BG)

    section("INVESTMENT OPTIONS FOR THIS TIER", clr)
    for opt in TIER_OPTIONS[choice]:
        st.markdown(f"<div style='background:{CARD};border:1px solid {BD};border-left:3px solid {clr};"
                    f"border-radius:0 8px 8px 0;padding:8px 13px;margin-bottom:5px;font-family:{FH};"
                    f"font-size:0.88rem;color:{TEXT};'>{opt}</div>", unsafe_allow_html=True)

    section("ALL TIERS COMPARED")
    rows = ""
    for i, t in enumerate(TIERS):
        mt = TIER_METRICS[t]
        hl = f"background:{TIER_BG[t]};" if t == rec_name else (f"background:{CARD};" if i % 2 == 0 else f"background:{BG};")
        star = " ★" if t == rec_name else ""
        rows += (f"<tr style='{hl}'>"
                 f"<td style='padding:8px 11px;font-family:{FH};font-weight:700;color:{TIER_CLR[t]};border-bottom:1px solid {BD};'>{t}{star}</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};font-size:0.82rem;color:{TEXT};border-bottom:1px solid {BD};'>{mt['ret']*100:.1f}%</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};font-size:0.82rem;color:{TEXT};border-bottom:1px solid {BD};'>{mt['vol']*100:.1f}%</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};font-size:0.82rem;color:{TEXT};border-bottom:1px solid {BD};'>{mt['sharpe']:.2f}</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};font-size:0.82rem;color:{RED};border-bottom:1px solid {BD};'>{mt['var95']*100:.1f}%</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};font-size:0.82rem;color:{RED};border-bottom:1px solid {BD};'>{mt['cvar95']*100:.1f}%</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};font-size:0.82rem;color:{AMBER};border-bottom:1px solid {BD};'>{mt['max_dd']*100:.0f}%</td></tr>")
    hdr = "".join(f"<th style='text-align:left;padding:7px 11px;background:{PRIMARY};color:#fff;font-family:{FH};"
                  f"font-size:0.7rem;text-transform:uppercase;letter-spacing:0.04em;font-weight:600;white-space:nowrap;'>{h}</th>"
                  for h in ["Tier", "Exp. Return", "Volatility", "Sharpe", "VaR 95%", "CVaR 95%", "Max DD"])
    st.markdown(
        f"<div style='border:1px solid {BD};border-radius:10px;overflow:hidden;overflow-x:auto;margin:4px 0;'>"
        f"<table style='width:100%;border-collapse:collapse;'><thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table></div>"
        f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};margin-top:6px;line-height:1.5;'>"
        f"<strong>VaR 95%</strong>: in the worst 1-in-20 year, losses are expected to exceed this. "
        f"<strong>CVaR 95%</strong>: the average loss in those worst-case years. "
        f"<strong>Max DD</strong>: estimated peak-to-trough fall. Figures use long-run market assumptions, not forecasts.</div>",
        unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 — ACTION PLAN
# ════════════════════════════════════════════════════════════════
with tab4:
    b = st.session_state.get("budget", {})
    if not b or b.get("income", 0) <= 0:
        note("Complete the Budget and Financial Health tabs to generate your action plan.", "info")
    else:
        fh = st.session_state.get("fh_score", financial_health_score(b)[0])
        cap_lvl = st.session_state.get("cap_level", 3)
        cap_word = st.session_state.get("cap_word", "Moderate")
        tol_lvl = st.session_state.get("tol_level", 3)
        tname = st.session_state.get("tol_name", "Balanced")
        rec_name, rec_idx = recommended_tier(cap_lvl, tol_lvl)

        recs = []
        if b["runway"] < 3:
            target = b["essential"] * 6
            gap_amt = max(0, target - b["savings"])
            if b["surplus"] > 0:
                txt = (f"You have {b['runway']:.1f} months of essential expenses saved. Aim for 6 months (~${target:,.0f}). "
                       f"At your current surplus of ${b['surplus']:,.0f}/mo, that is about {gap_amt/b['surplus']:.0f} months away.")
            else:
                txt = (f"You have {b['runway']:.1f} months saved and no monthly surplus — freeing up cash flow is the priority before building the buffer.")
            recs.append(("alert", "Build your emergency fund first", txt))
        elif b["runway"] < 6:
            recs.append(("warn", "Top up your emergency fund",
                f"You have {b['runway']:.1f} months saved. Building to 6 months gives a full buffer before taking investment risk."))

        sr = b["savings_rate"]
        if sr < 0:
            recs.append(("alert", "You are spending more than you earn",
                f"Your expenses exceed income by ${abs(b['surplus']):,.0f}/mo. Reducing your largest discretionary categories is the immediate priority — no investment can outrun a monthly deficit."))
        elif sr < 0.10:
            recs.append(("warn", "Lift your savings rate",
                f"You are saving {sr*100:.0f}% of income. Reaching 20% (${b['income']*0.20:,.0f}/mo) accelerates every financial goal. Trimming 'wants' is usually the fastest lever."))

        nr = b["needs"] / b["income"]
        wr = b["wants"] / b["income"]
        if nr > 0.55:
            recs.append(("warn", "Fixed costs are high",
                f"Needs are {nr*100:.0f}% of income (ideal ≤50%). Housing, transport, and insurance are the usual culprits — structural changes here free up the most room."))
        if wr > 0.32:
            recs.append(("info", "Discretionary spending is above the guide",
                f"Wants are {wr*100:.0f}% of income (ideal ≤30%). Redirecting part of this to savings compounds meaningfully over time."))

        if b["dti"] > 0.20:
            recs.append(("warn", "Debt load is elevated",
                f"Debt repayments are {b['dti']*100:.0f}% of income. Clearing high-interest debt is effectively a guaranteed return and usually beats investing while rates are high."))

        gap = tol_lvl - cap_lvl
        if gap >= 2:
            recs.append(("alert", "Do not invest beyond your capacity",
                f"Your comfort with risk ({tname}) is well above what your finances support ({cap_word}). Start at the {rec_name} tier and step up only as your buffer and surplus grow."))
        elif gap <= -2:
            recs.append(("info", "You can afford more growth when ready",
                f"Your finances ({cap_word}) could support more risk than your current comfort ({tname}). There is no rush — increase exposure gradually as confidence builds."))

        if fh >= 65 and b["runway"] >= 6:
            recs.append(("good", "You are ready to invest systematically",
                f"Strong foundation. Consider directing your ${max(0,b['surplus']):,.0f}/mo surplus into the {rec_name} portfolio via regular, automated contributions to smooth out market timing."))

        if not any(k in ("alert", "warn") for k, _, _ in recs):
            recs.append(("good", "Your finances are in good shape",
                "No critical issues detected. Keep contributing consistently and review quarterly as your situation changes."))

        order = {"alert": 0, "warn": 1, "info": 2, "good": 3}
        recs.sort(key=lambda r: order.get(r[0], 4))

        n_alert = sum(1 for r in recs if r[0] == "alert")
        n_warn = sum(1 for r in recs if r[0] == "warn")
        readiness = max(0, min(100, fh - n_alert * 12 - n_warn * 5))
        rdg, rclr, rbg = health_rating(readiness)

        section("INVESTMENT READINESS")
        rr1, rr2 = cols(2, gap="large")
        with rr1:
            st.plotly_chart(circular_gauge(readiness, rclr), use_container_width=True)
        with rr2:
            st.markdown(
                f"<div style='background:{rbg};border:1px solid {BD};border-left:4px solid {rclr};"
                f"border-radius:0 12px 12px 0;padding:16px 20px;margin-top:{'8px' if IS_MOBILE else '30px'};'>"
                f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};font-weight:600;text-transform:uppercase;letter-spacing:0.04em;'>Overall</div>"
                f"<div style='font-family:{FH};font-size:1.5rem;font-weight:800;color:{rclr};'>{rdg}</div>"
                f"<div style='font-family:{FH};font-size:0.85rem;color:{MUTED};margin-top:4px;line-height:1.5;'>"
                f"{n_alert} critical item{'s' if n_alert!=1 else ''} and {n_warn} to watch. "
                f"Suggested portfolio: <strong style='color:{TIER_CLR[rec_name]};'>{rec_name}</strong>.</div></div>",
                unsafe_allow_html=True)

        section("YOUR PRIORITISED ACTIONS", PURPLE)
        rank = 1
        for kind, title, text in recs:
            cfg = {"alert": (RED_BG, RED), "warn": (AMBER_BG, AMBER), "info": (PRIMARY_BG, PRIMARY), "good": (GREEN_BG, GREEN)}
            bg, ac = cfg.get(kind, cfg["info"])
            tag = {"alert": "Do first", "warn": "Important", "info": "Consider", "good": "On track"}.get(kind, "")
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BD};border-left:3px solid {ac};"
                f"border-radius:0 12px 12px 0;padding:13px 16px;margin-bottom:8px;'>"
                f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;flex-wrap:wrap;'>"
                f"<span style='background:{ac};color:#fff;font-family:{FH};font-size:0.8rem;font-weight:800;"
                f"width:24px;height:24px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;'>{rank}</span>"
                f"<span style='background:{bg};color:{ac};font-family:{FH};font-size:0.62rem;font-weight:700;"
                f"padding:2px 9px;border-radius:20px;text-transform:uppercase;letter-spacing:0.03em;'>{tag}</span>"
                f"<span style='font-family:{FH};font-size:1rem;font-weight:700;color:{TEXT};'>{title}</span></div>"
                f"<div style='font-family:{FH};font-size:0.88rem;color:{MUTED};line-height:1.55;padding-left:34px;'>{text}</div></div>",
                unsafe_allow_html=True)
            rank += 1


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown(
    f"<div style='border-top:1px solid {BD};margin-top:2rem;padding:14px 0 6px;font-family:{FH};"
    f"font-size:0.74rem;color:{DIM};text-align:center;'>"
    f"<strong style='color:{PRIMARY};'>Seralung Finance</strong> &nbsp;·&nbsp; Understand Risk. Invest with Confidence."
    f"<br><span style='font-size:0.68rem;'>Educational purposes only — not personal financial advice — "
    f"consult a licensed financial adviser before investing.</span></div>",
    unsafe_allow_html=True,
)
