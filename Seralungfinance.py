"""
Seralung Finance — Understand Risk. Invest with Confidence.
============================================================
Pages: ?page=budget | health | portfolio | simulator | actions

Run:   streamlit run Seralungfinance.py
Deps:  streamlit plotly numpy pandas
"""

import uuid
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Seralung Finance", layout="wide",
                   initial_sidebar_state="collapsed")

# Anti-flash injection (before anything else renders)
st.markdown("<style>html,body{background-color:#EAF5EC!important;color-scheme:light!important}</style>",
            unsafe_allow_html=True)

PLOTLY_CFG = {"displayModeBar":False,"scrollZoom":False,"doubleClick":False,
              "showAxisDragHandles":False,"showAxisRangeEntryBoxes":False}

def detect_mobile():
    try:
        ua = (st.context.headers.get("User-Agent","") or "")
        return any(k in ua for k in ["Mobile","Android","iPhone","iPad","iPod","Windows Phone"])
    except Exception:
        return False

IS_MOBILE = detect_mobile()

def cols(n, gap="small"):
    if IS_MOBILE: return [st.container() for _ in range(n)]
    return st.columns(n, gap=gap)

# ── Palette ─────────────────────────────────────────────────────
BG, CARD, BD         = "#EAF5EC", "#FFFFFF", "#CBE2D2"
TEXT, MUTED, DIM     = "#10241A", "#54695E", "#95AC9E"
PRIMARY, PRIMARY_BG, PRIMARY_DK = "#16794D", "#E0F2E7", "#0E5C39"
LGREEN, LGREEN_BG    = "#3DA968", "#EAF6EE"
GREEN,  GREEN_BG     = PRIMARY, PRIMARY_BG
AMBER,  AMBER_BG     = "#B7791F", "#FBF3E2"
RED,    RED_BG       = "#C53929", "#FBEAE7"
PURPLE, PURPLE_BG    = "#7C3AED", "#F1ECFC"
TEAL,   TEAL_BG      = "#0E7C7B", "#DFF2F1"
SLATE,  SLATE_BG     = "#6B7280", "#F2F4F7"

FH = "'Plus Jakarta Sans', system-ui, sans-serif"
FM = "'JetBrains Mono', 'Fira Code', monospace"

HOVER_STYLE = dict(bgcolor=CARD, bordercolor=BD,
                   font=dict(family="Plus Jakarta Sans, sans-serif", size=12, color=TEXT))
PLOTLY_BASE = dict(font=dict(family="Plus Jakarta Sans, sans-serif", color=TEXT),
                   paper_bgcolor=CARD, plot_bgcolor="rgba(0,0,0,0)",
                   hoverlabel=HOVER_STYLE, dragmode=False)

# ── Budget model ─────────────────────────────────────────────────
EXPENSE_CATEGORIES = ["Housing","Utilities","Groceries","Transport","Insurance","Healthcare",
    "Debt Repayment","Dining Out","Entertainment","Shopping","Subscriptions","Travel",
    "Savings/Invest","Other"]
CATEGORY_TYPE = {
    "Housing":"Need","Utilities":"Need","Groceries":"Need","Transport":"Need",
    "Insurance":"Need","Healthcare":"Need","Debt Repayment":"Need",
    "Dining Out":"Want","Entertainment":"Want","Shopping":"Want",
    "Subscriptions":"Want","Travel":"Want","Savings/Invest":"Savings","Other":"Want"}
DEFAULT_BILLS = [
    {"expense":"Rent / Mortgage",   "category":"Housing",        "amount":1800},
    {"expense":"Electricity & Gas", "category":"Utilities",      "amount":200},
    {"expense":"Groceries",         "category":"Groceries",      "amount":650},
    {"expense":"Car & Fuel",        "category":"Transport",      "amount":350},
    {"expense":"Health Insurance",  "category":"Insurance",      "amount":180},
    {"expense":"Loan Repayment",    "category":"Debt Repayment", "amount":400},
    {"expense":"Streaming & Apps",  "category":"Subscriptions",  "amount":55},
    {"expense":"Dining Out",        "category":"Dining Out",     "amount":300}]

# ── Investment engine (MPT) ──────────────────────────────────────
MPT_ASSETS  = ["Cash","Bonds","Equity ETFs","Stocks","Property","Crypto"]
EXP_RETURNS = np.array([0.035,0.045,0.080,0.095,0.070,0.180])
VOLS        = np.array([0.010,0.050,0.150,0.240,0.140,0.650])
RISK_FREE   = 0.035
CORR = np.array([[ 1.00, 0.15, 0.00,-0.05, 0.05, 0.00],
                 [ 0.15, 1.00, 0.25, 0.10, 0.30, 0.05],
                 [ 0.00, 0.25, 1.00, 0.88, 0.60, 0.35],
                 [-0.05, 0.10, 0.88, 1.00, 0.50, 0.40],
                 [ 0.05, 0.30, 0.60, 0.50, 1.00, 0.25],
                 [ 0.00, 0.05, 0.35, 0.40, 0.25, 1.00]])
COV = np.outer(VOLS, VOLS) * CORR

TIERS = ["Defensive","Conservative","Balanced","Growth","Aggressive"]
TIER_WEIGHTS = {"Defensive":[40,40,12,0,8,0],"Conservative":[22,33,25,3,15,2],
                "Balanced":[10,22,35,10,18,5],"Growth":[5,12,45,18,15,5],
                "Aggressive":[2,5,48,25,12,8]}
TIER_CLR = {"Defensive":TEAL,"Conservative":GREEN,"Balanced":PRIMARY,"Growth":AMBER,"Aggressive":RED}
TIER_BG  = {"Defensive":TEAL_BG,"Conservative":GREEN_BG,"Balanced":PRIMARY_BG,
            "Growth":AMBER_BG,"Aggressive":RED_BG}
TIER_OPTIONS = {
    "Defensive":    ["High-interest savings & term deposits",
                     "Government bond ETFs (e.g. VGB, IAF)",
                     "Cash management / money-market funds",
                     "Capital-guaranteed products"],
    "Conservative": ["Diversified bond ETFs (corporate + government)",
                     "Blue-chip dividend ETFs",
                     "Small allocation to broad index funds",
                     "Defensive listed property (A-REIT ETFs)"],
    "Balanced":     ["Broad-market index ETFs (VAS, VGS, IVV)",
                     "Balanced multi-asset funds (~60/40)",
                     "Listed property / infrastructure ETFs",
                     "Investment-grade bond ETFs for ballast"],
    "Growth":       ["Global & domestic equity ETFs (growth tilt)",
                     "International index funds (developed + emerging)",
                     "Sector / thematic ETFs as satellites",
                     "Small allocation to quality individual stocks"],
    "Aggressive":   ["Growth & thematic equity ETFs",
                     "Emerging-market & small-cap ETFs",
                     "Selective individual growth stocks",
                     "Small, capped crypto allocation (under 10%)"]}

# ── Risk questionnaire ───────────────────────────────────────────
QUESTIONS = [
    ("When do you expect to need this money?",
     ["Under 3 years","3–7 years","7–15 years","15+ years"]),
    ("How stable is your income?",
     ["Retired or fixed income","Variable or self-employed","Stable salary","Very secure"]),
    ("If your portfolio fell 30% in three months, you would:",
     ["Sell everything","Sell some","Hold and wait","Buy more at lower prices"]),
    ("How much investing experience do you have?",
     ["None","Basic — shares & funds","Three or more years active","Ten or more years, multi-asset"]),
    ("Your primary investment goal:",
     ["Protect capital","Modest growth with protection","Balanced growth","Maximum growth"]),
    ("Do you expect significant withdrawals within five years?",
     ["Yes — most of it","Yes — a meaningful portion","Possibly — small amounts","No — long-term"]),
    ("Maximum annual loss you could absorb:",
     ["Under 5%","5–15%","15–25%","25% or more"]),
    ("This investment is what share of your net worth?",
     ["Over 75%","50–75%","25–50%","Under 25%"]),
    ("How do market swings make you feel?",
     ["Very anxious","Uneasy","Mostly calm","Indifferent — it is normal"]),
    ("Your investment knowledge level:",
     ["Beginner","Some understanding","Confident","Advanced"])]
TOL_PROFILES = {
    "Conservative":            {"range":(10,18),"level":1,"clr":GREEN,   "bg":GREEN_BG},
    "Moderately Conservative": {"range":(19,25),"level":2,"clr":TEAL,    "bg":TEAL_BG},
    "Balanced":                {"range":(26,31),"level":3,"clr":PRIMARY, "bg":PRIMARY_BG},
    "Growth":                  {"range":(32,36),"level":4,"clr":AMBER,   "bg":AMBER_BG},
    "Aggressive":              {"range":(37,40),"level":5,"clr":RED,     "bg":RED_BG}}

# ── Session state ────────────────────────────────────────────────
_DEF = {"income_primary":6000,"income_secondary":0,"current_savings":15000,
        "user_age":30, **{f"q{i}":0 for i in range(1,11)}}
for k,v in _DEF.items():
    if k not in st.session_state: st.session_state[k] = v

if "bills_list" not in st.session_state:
    st.session_state["bills_list"] = []
    for i,row in enumerate(DEFAULT_BILLS):
        bid = f"b{i:02d}"
        st.session_state["bills_list"].append({"id":bid,**row})
        st.session_state[f"bill_{bid}_name"] = row["expense"]
        st.session_state[f"bill_{bid}_cat"]  = row["category"]
        st.session_state[f"bill_{bid}_amt"]  = int(row["amount"])

# ── Calculations ─────────────────────────────────────────────────
def portfolio_metrics(weights_pct):
    w  = np.array(weights_pct,dtype=float)/100.0
    rp = float(w @ EXP_RETURNS)
    sd = float(w @ COV @ w)**0.5
    sharpe = (rp-RISK_FREE)/sd if sd>0 else 0.0
    z,phi  = 1.645, 0.103138
    var95  = max(0.0, z*sd-rp);  cvar95 = max(0.0, sd*(phi/0.05)-rp)
    div_r  = float(w @ VOLS)/sd if sd>0 else 1.0
    return {"ret":rp,"vol":sd,"sharpe":sharpe,"var95":var95,
            "cvar95":cvar95,"div_ratio":div_r,"max_dd":min(0.95,2.4*sd)}

TIER_METRICS = {t: portfolio_metrics(TIER_WEIGHTS[t]) for t in TIERS}

def _safe_float(x, default=0.0):
    try:
        if x is None: return default
        if isinstance(x,float) and (np.isnan(x) or np.isinf(x)): return default
        return float(x)
    except (TypeError,ValueError): return default

def compute_budget(income, bills_df, savings):
    income = max(0.0,_safe_float(income)); savings = max(0.0,_safe_float(savings))
    if isinstance(bills_df,list): bills_df = pd.DataFrame(bills_df)
    if not isinstance(bills_df,pd.DataFrame):
        bills_df = pd.DataFrame(columns=["Expense","Category","Amount"])
    df = bills_df.copy()
    for col in ("Expense","Category","Amount"):
        if col not in df.columns: df[col] = np.nan
    df = df.dropna(how="all")
    df["Expense"]  = df["Expense"].fillna("").astype(str)
    df["Category"] = df["Category"].fillna("Other").astype(str).replace("","Other")
    df.loc[~df["Category"].isin(EXPENSE_CATEGORIES),"Category"] = "Other"
    df["_amt"] = pd.to_numeric(df["Amount"],errors="coerce").fillna(0.0).clip(lower=0.0)
    df = df[df["_amt"]>0].reset_index(drop=True)
    df["_type"] = df["Category"].map(CATEGORY_TYPE).fillna("Want")
    total_exp = float(df["_amt"].sum())
    needs  = float(df.loc[df["_type"]=="Need",    "_amt"].sum())
    wants  = float(df.loc[df["_type"]=="Want",    "_amt"].sum())
    invest = float(df.loc[df["_type"]=="Savings", "_amt"].sum())
    debt   = float(df.loc[df["Category"]=="Debt Repayment","_amt"].sum())
    surplus = income - total_exp; sr = surplus/income if income>0 else 0.0
    essential = needs if needs>0 else total_exp
    runway = savings/essential if essential>0 else 0.0
    dti    = debt/income if income>0 else 0.0
    cat_sums = df.groupby("Category")["_amt"].sum().sort_values(ascending=False).to_dict()
    return {"income":income,"expenses":total_exp,"needs":needs,"wants":wants,
            "invest":invest,"debt":debt,"surplus":surplus,"savings_rate":sr,
            "runway":runway,"essential":essential,"dti":dti,"savings":savings,
            "cat_sums":cat_sums,"bill_count":int(len(df))}

def financial_health_score(b):
    inc = b["income"]
    if inc<=0: return 0,{}
    sr,run = b["savings_rate"],b["runway"]
    nr,wr,dti = b["needs"]/inc, b["wants"]/inc, b["dti"]
    p_sr=30 if sr>=0.20 else max(0,sr)/0.20*30; p_run=min(25,run/6*25)
    p_nee=20 if nr<=0.50 else max(0,20-(nr-0.50)*80)
    p_wan=15 if wr<=0.30 else max(0,15-(wr-0.30)*60)
    p_debt=10 if dti<=0.20 else max(0,10-(dti-0.20)*40)
    return round(min(100,p_sr+p_run+p_nee+p_wan+p_debt)), {
        "Savings rate":(round(p_sr),30),"Emergency runway":(round(p_run),25),
        "Needs control":(round(p_nee),20),"Wants control":(round(p_wan),15),
        "Debt load":(round(p_debt),10)}

def health_rating(s):
    if s>=80: return "Excellent",GREEN,  GREEN_BG
    if s>=65: return "Good",     TEAL,   TEAL_BG
    if s>=45: return "Fair",     AMBER,  AMBER_BG
    if s>=25: return "At Risk",  RED,    RED_BG
    return          "Critical",  RED,    RED_BG

def risk_capacity(b):
    run=min(100,b["runway"]/6*100); sr=min(100,max(0,b["savings_rate"])/0.25*100)
    dti=max(0,100-b["dti"]/0.50*100)
    return round(0.40*run+0.40*sr+0.20*dti)

def capacity_level(cap):
    if cap>=80: return 5,"Strong"
    if cap>=60: return 4,"Solid"
    if cap>=40: return 3,"Moderate"
    if cap>=20: return 2,"Limited"
    return           1,"Fragile"

def quiz_total():
    return sum(int(st.session_state.get(f"q{i}",0))+1 for i in range(1,11))

def tolerance_profile():
    s = quiz_total()
    for name,d in TOL_PROFILES.items():
        lo,hi = d["range"]
        if lo<=s<=hi: return name,d,s
    return "Balanced",TOL_PROFILES["Balanced"],s

def recommended_tier(cap_lvl, tol_lvl):
    idx = max(1,min(5,min(cap_lvl,tol_lvl)))
    return TIERS[idx-1], idx

def run_simulation(initial, monthly_contrib, annual_return, annual_vol, years, n_sim=400):
    mr=annual_return/12; mv=annual_vol/(12**0.5)
    portfolio = np.full(n_sim, max(0.0,float(initial)))
    snapshots = [portfolio.copy()]
    for m in range(years*12):
        shocks = np.random.normal(mr,mv,n_sim)
        portfolio = np.maximum(0.0, portfolio*(1+shocks)) + max(0.0,float(monthly_contrib))
        if (m+1)%12==0: snapshots.append(portfolio.copy())
    return np.array(snapshots)  # (years+1, n_sim)

# ════════════════════════════════════════════════════════════════
# CSS — full design system matching screenshots
# ════════════════════════════════════════════════════════════════
HERO_PAD = "1.1rem 1.1rem 1.0rem" if IS_MOBILE else "1.5rem 2rem 1.3rem"
TITLE_SZ = "1.35rem" if IS_MOBILE else "1.85rem"
SIDE_PAD = "0.7rem"  if IS_MOBILE else "1.6rem"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"] {{
    background:{BG} !important; font-family:{FH}; color:{TEXT} !important;
    color-scheme:light !important;
}}
.stApp,.stApp p,.stApp label,.stApp li,
[data-testid="stMarkdownContainer"],[data-testid="stWidgetLabel"] {{ color:{TEXT}; }}
.block-container {{ padding:0 {SIDE_PAD} 3rem; max-width:1160px; }}
#MainMenu,footer,header {{ visibility:hidden; }}
.stDeployButton {{ display:none !important; }}
* {{ box-sizing:border-box; }}
h1,h2,h3,h4 {{ font-family:{FH} !important; font-weight:700 !important;
    color:{TEXT} !important; margin:0 !important; }}

[data-testid="stVerticalBlock"] {{ gap:0.32rem !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:14px !important;
    border-color:{BD} !important; }}

/* Plotly charts — white card */
[data-testid="stPlotlyChart"] {{
    background:{CARD} !important; border-radius:16px !important;
    box-shadow:0 1px 6px rgba(14,92,57,0.07) !important;
    overflow:hidden !important; border:1px solid {BD} !important;
}}

/* Inputs */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"]   label,
div[data-testid="stTextInput"]   label {{
    font-family:{FH} !important; font-size:0.73rem !important; text-transform:none !important;
    color:{MUTED} !important; font-weight:500 !important; letter-spacing:0.01em;
}}
.stNumberInput input,.stTextInput input {{
    background:{CARD} !important; border:1.5px solid {BD} !important; border-radius:10px !important;
    color:{TEXT} !important; font-family:{FM} !important; font-size:0.91rem !important; padding:8px 12px !important;
}}
.stNumberInput input:focus,.stTextInput input:focus {{
    border-color:{PRIMARY} !important; box-shadow:0 0 0 3px rgba(22,121,77,0.11) !important;
    outline:none !important;
}}
.stNumberInput button {{ background:{CARD} !important; border-color:{BD} !important; }}

/* Slider */
[data-testid="stSlider"] label {{ font-family:{FH} !important; font-size:0.73rem !important;
    color:{MUTED} !important; font-weight:500 !important; }}

/* Radio */
div[data-testid="stRadio"] *,[data-testid="stRadio"] label * {{ color:{TEXT} !important; }}
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
    color:{TEXT} !important; font-family:{FH} !important; font-size:0.88rem !important;
    margin:0 !important; line-height:1.4 !important;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label {{
    padding:6px 10px; border-radius:8px; margin-bottom:2px; transition:background .12s; cursor:pointer;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label:hover {{ background:{PRIMARY_BG}; }}
div[data-testid="stRadio"] > label {{ font-family:{FH} !important; font-size:0.73rem !important;
    color:{MUTED} !important; font-weight:500 !important; }}

/* ALL primary buttons */
.stButton > button {{
    background:{PRIMARY} !important; color:#fff !important; border:none !important;
    border-radius:50px !important; font-family:{FH} !important;
    font-size:0.88rem !important; font-weight:600 !important; padding:9px 18px !important;
    box-shadow:0 2px 8px rgba(22,121,77,0.20) !important; transition:all .14s !important; width:100%;
}}
.stButton > button:hover {{ background:{PRIMARY_DK} !important; transform:translateY(-1px) !important; }}

/* Secondary buttons (tier pills, delete, inactive nav) */
button[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondary"] button {{
    background:{CARD} !important; color:{TEXT} !important;
    border:1.5px solid {BD} !important; box-shadow:none !important;
    border-radius:50px !important;
}}
button[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondary"] button:hover {{
    background:{PRIMARY_BG} !important; color:{PRIMARY} !important;
    border-color:{PRIMARY} !important;
}}

/* Nav row container */
.nav-row {{ display:flex; gap:{'5px' if IS_MOBILE else '6px'};
    margin:0 0 1.2rem; padding:5px;
    background:{CARD}; border:1px solid {BD}; border-radius:14px;
    box-shadow:0 2px 8px rgba(14,92,57,0.05); overflow-x:auto; }}
.nav-row .stButton > button {{
    border-radius:10px !important;
    font-size:{'0.87rem' if IS_MOBILE else '0.97rem'} !important;
    padding:{'10px 11px' if IS_MOBILE else '11px 16px'} !important;
    box-shadow:none !important; white-space:nowrap;
}}

/* Download button */
.stDownloadButton > button {{
    background:{PRIMARY} !important; color:#fff !important; border:none !important;
    border-radius:50px !important; font-family:{FH} !important;
    font-size:0.93rem !important; font-weight:700 !important;
    padding:11px 22px !important; box-shadow:0 3px 12px rgba(22,121,77,0.24) !important;
    width:100%;
}}
.stDownloadButton > button:hover {{ background:{PRIMARY_DK} !important; transform:translateY(-1px) !important; }}

/* Selectbox */
.stSelectbox > div > div {{ background:{CARD} !important; border:1.5px solid {BD} !important;
    border-radius:10px !important; font-family:{FH} !important; }}
[role="listbox"] *,[role="option"] {{ background:{CARD} !important; color:{TEXT} !important; }}

/* Expander */
[data-testid="stExpander"] summary {{
    background:{CARD} !important; border-radius:10px !important;
    font-family:{FH} !important; font-weight:600 !important; color:{PRIMARY} !important;
    border:1px solid {BD} !important;
}}

hr {{ border:none; border-top:1px solid {BD}; margin:0.6rem 0; }}

@media (max-width:640px) {{
    .block-container {{ padding-left:0.5rem !important; padding-right:0.5rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# UI HELPERS
# ════════════════════════════════════════════════════════════════
def note(text, kind="info"):
    cfg = {"info":(PRIMARY_BG,PRIMARY),"good":(GREEN_BG,GREEN),
           "warn":(AMBER_BG,AMBER),"alert":(RED_BG,RED)}
    bg,ac = cfg.get(kind,cfg["info"])
    st.markdown(
        f"<div style='background:{bg};border-left:3.5px solid {ac};border-radius:0 10px 10px 0;"
        f"padding:10px 14px;margin:5px 0;font-family:{FH};font-size:0.88rem;color:{TEXT};"
        f"line-height:1.55;'>{text}</div>", unsafe_allow_html=True)

def section(label, color=PRIMARY):
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;margin:18px 0 10px;'>"
        f"<span style='font-family:{FH};font-size:0.72rem;letter-spacing:0.07em;"
        f"text-transform:uppercase;color:{color};white-space:nowrap;font-weight:700;'>{label}</span>"
        f"<div style='flex:1;height:1px;background:{BD};'></div></div>",
        unsafe_allow_html=True)

def metric_card(label, value, sub="", accent=PRIMARY, bg=CARD):
    """Screenshot-matched metric card: white bg, colored top border, clean hierarchy."""
    st.markdown(
        f"<div style='background:{bg};border:1px solid {BD};border-top:3px solid {accent};"
        f"border-radius:0 0 14px 14px;padding:14px 16px;min-width:0;height:100%;"
        f"box-shadow:0 1px 4px rgba(0,0,0,0.04);'>"
        f"<div style='font-family:{FH};font-size:0.68rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.06em;color:{MUTED};margin-bottom:6px;overflow:hidden;"
        f"text-overflow:ellipsis;white-space:nowrap;'>{label}</div>"
        f"<div style='font-family:{FH};font-size:1.55rem;color:{accent};font-weight:800;"
        f"line-height:1.15;word-break:break-word;'>{value}</div>"
        f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};margin-top:4px;"
        f"line-height:1.4;'>{sub}</div></div>",
        unsafe_allow_html=True)

def circular_gauge(score, color):
    """Gauge matching screenshots: large number + 'out of 100' subtitle."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"font":{"size":54,"family":"Plus Jakarta Sans","color":color}},
        gauge={"axis":{"range":[0,100],"tickwidth":1,"tickcolor":DIM,
                       "tickfont":{"size":8,"family":"JetBrains Mono","color":DIM}},
               "bar":{"color":color,"thickness":0.30},
               "bgcolor":"rgba(0,0,0,0)","borderwidth":0,
               "steps":[{"range":[0,25],"color":RED_BG},{"range":[25,45],"color":AMBER_BG},
                        {"range":[45,65],"color":"#FFFBEA"},{"range":[65,80],"color":LGREEN_BG},
                        {"range":[80,100],"color":GREEN_BG}],
               "threshold":{"line":{"color":color,"width":5},"thickness":0.85,"value":score}}))
    fig.add_annotation(x=0.5, y=0.16, text="out of 100", showarrow=False,
                       font=dict(size=13, family="Plus Jakarta Sans", color=MUTED),
                       xanchor="center")
    fig.update_layout(height=250, margin=dict(t=20,b=12,l=24,r=24),
                      paper_bgcolor=CARD, plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Plus Jakarta Sans", color=TEXT),
                      hoverlabel=HOVER_STYLE, dragmode=False)
    return fig

def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.60,
        marker=dict(colors=colors, line=dict(color=CARD, width=2)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        showlegend=True))
    ann = [dict(text=center, x=0.5, y=0.5,
                font=dict(size=14,family="Plus Jakarta Sans",color=TEXT,weight=700),
                showarrow=False)] if center else []
    fig.update_layout(
        height=280, margin=dict(t=8,b=8,l=8,r=8),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18,
                    xanchor="center", x=0.5, font=dict(size=10,family="Plus Jakarta Sans",color=TEXT),
                    bgcolor="rgba(0,0,0,0)", itemsizing="constant"),
        annotations=ann,
        paper_bgcolor=CARD, plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans",color=TEXT), hoverlabel=HOVER_STYLE, dragmode=False)
    return fig

def bar_5030(needs_pct, wants_pct, save_pct):
    fig = go.Figure()
    cats = ["Needs","Wants","Savings"]
    fig.add_trace(go.Bar(name="Your %", x=cats, y=[needs_pct,wants_pct,save_pct],
                         marker_color=PRIMARY, marker_line_width=0,
                         hovertemplate="%{x}: %{y:.0f}%<extra></extra>"))
    fig.add_trace(go.Bar(name="50/30/20 ideal", x=cats, y=[50,30,20],
                         marker_color=DIM, marker_line_width=0,
                         hovertemplate="%{x} ideal: %{y}%<extra></extra>"))
    fig.update_layout(
        barmode="group", height=220, margin=dict(t=8,b=8,l=8,r=8),
        legend=dict(bgcolor="rgba(0,0,0,0)",orientation="h",y=1.12,
                    font=dict(family="JetBrains Mono",size=9,color=MUTED)),
        xaxis=dict(showgrid=False,fixedrange=True,
                   tickfont=dict(family="Plus Jakarta Sans",size=11,color=TEXT)),
        yaxis=dict(showgrid=True,gridcolor=BD,ticksuffix="%",fixedrange=True,
                   tickfont=dict(family="JetBrains Mono",size=8,color=MUTED)),
        bargap=0.3, bargroupgap=0.08, paper_bgcolor=CARD, plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans",color=TEXT), hoverlabel=HOVER_STYLE, dragmode=False)
    return fig

def simulation_chart(base_data, wi_data, years, retire_in, target=None):
    x = list(range(years+1))
    fig = go.Figure()

    def add_band(data, clr, name, dash="solid"):
        p10=np.percentile(data,10,axis=1).tolist()
        p90=np.percentile(data,90,axis=1).tolist()
        p50=np.percentile(data,50,axis=1).tolist()
        r,g,b = int(clr[1:3],16),int(clr[3:5],16),int(clr[5:7],16)
        fig.add_trace(go.Scatter(x=x,y=p90,mode="lines",line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=x,y=p10,mode="lines",fill="tonexty",
            line=dict(color="rgba(0,0,0,0)"),fillcolor=f"rgba({r},{g},{b},0.10)",
            showlegend=False,hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=x,y=p50,mode="lines",
            line=dict(color=clr,width=2.5,dash=dash),name=name,
            hovertemplate=f"Year %{{x}}<br>{name}: $%{{y:,.0f}}<extra></extra>"))

    add_band(base_data, PRIMARY, "Current path")
    if wi_data is not None:
        add_band(wi_data, AMBER, "What-If path", dash="dash")

    if 0 < retire_in <= years:
        p90_max = np.percentile(
            wi_data if wi_data is not None else base_data, 90, axis=1).max()
        fig.add_vline(x=retire_in, line=dict(color=TEAL,width=2,dash="dot"))
        fig.add_annotation(x=retire_in,y=p90_max*1.05,text="Retirement",showarrow=False,
                           bgcolor=TEAL_BG,bordercolor=TEAL,borderpad=4,
                           font=dict(family="Plus Jakarta Sans",size=10,color=TEAL))
    if target and target>0:
        fig.add_hline(y=target, line=dict(color=RED,width=1.5,dash="dot"))
        fig.add_annotation(x=years*0.01,y=target,text=f"Target ${target/1e6:.1f}M",
                           showarrow=False,xanchor="left",bgcolor=RED_BG,bordercolor=RED,
                           borderpad=3,font=dict(family="Plus Jakarta Sans",size=10,color=RED))
    fig.update_layout(
        height=400, margin=dict(t=30,b=55,l=70,r=20),
        legend=dict(orientation="h",y=-0.20,font=dict(size=11,family="Plus Jakarta Sans",color=TEXT)),
        xaxis=dict(title="Years from now",fixedrange=True,
                   tickfont=dict(family="JetBrains Mono",size=9,color=MUTED)),
        yaxis=dict(title="Portfolio value",fixedrange=True,tickprefix="$",tickformat=",.0f",
                   tickfont=dict(family="JetBrains Mono",size=9,color=MUTED),
                   gridcolor=BD,showgrid=True),
        paper_bgcolor=CARD, plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans",color=TEXT), hoverlabel=HOVER_STYLE, dragmode=False)
    return fig

# ════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════
logo_html = (f"<div style='width:{'40px' if IS_MOBILE else '46px'};height:{'40px' if IS_MOBILE else '46px'};"
             f"border-radius:12px;background:rgba(255,255,255,0.18);border:1px solid rgba(255,255,255,0.4);"
             f"display:flex;align-items:center;justify-content:center;font-family:{FH};"
             f"font-size:{'1.25rem' if IS_MOBILE else '1.5rem'};font-weight:800;color:#fff;'>S</div>")
st.markdown(
    f"<div style='background:{PRIMARY};border-radius:0 0 20px 20px;padding:{HERO_PAD};"
    f"margin:0 -{SIDE_PAD} 1.1rem;box-shadow:0 4px 18px rgba(14,92,57,0.18);'>"
    f"<div style='display:flex;align-items:center;gap:12px;'>{logo_html}"
    f"<div><div style='font-family:{FH};font-size:{TITLE_SZ};font-weight:800;color:#fff;"
    f"letter-spacing:-0.025em;line-height:1;'>Seralung Finance</div>"
    f"<div style='font-family:{FH};font-size:{'0.76rem' if IS_MOBILE else '0.88rem'};"
    f"color:rgba(255,255,255,0.88);margin-top:3px;font-weight:500;'>"
    f"Understand Risk. Invest with Confidence.</div></div></div></div>",
    unsafe_allow_html=True)
st.markdown(
    f"<div style='font-family:{FH};font-size:0.75rem;color:{MUTED};padding:0 0 5px;'>"
    f"<span style='background:{PRIMARY_BG};color:{PRIMARY_DK};font-weight:600;"
    f"padding:3px 9px;border-radius:5px;'>Educational only</span>"
    f"&nbsp; Not personal financial advice — consult a licensed adviser before investing.</div>",
    unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# NAVIGATION — button-based (WebSocket, zero-blink)
# ════════════════════════════════════════════════════════════════
PAGES = [("budget","Budget","Budget"),("health","Health","Financial Health"),
         ("portfolio","Portfolio","Investment Portfolio"),
         ("simulator","Simulator","What-If Simulator"),("actions","Plan","Action Plan")]
VALID_KEYS = {p[0] for p in PAGES}
raw = st.query_params.get("page","budget")
current_page = raw if raw in VALID_KEYS else "budget"

st.markdown('<div class="nav-row">', unsafe_allow_html=True)
nav_cols = st.columns(len(PAGES))
for i,(key,short,long) in enumerate(PAGES):
    with nav_cols[i]:
        label = short if IS_MOBILE else long
        if st.button(label, key=f"nav_{key}",
                     type="primary" if key==current_page else "secondary"):
            st.query_params["page"] = key
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ════════════════════════════════════════════════════════════════
def _del_bill(bid):
    st.session_state["bills_list"] = [b for b in st.session_state["bills_list"] if b["id"]!=bid]
    for s in ("_name","_cat","_amt"): st.session_state.pop(f"bill_{bid}{s}",None)

def render_bill_card(bill):
    bid = bill["id"]
    if IS_MOBILE:
        st.text_input("Name", key=f"bill_{bid}_name", label_visibility="collapsed",
                      placeholder="Expense name")
        ra,rb = st.columns([2,1])
        with ra: st.selectbox("Cat", EXPENSE_CATEGORIES, key=f"bill_{bid}_cat",
                               label_visibility="collapsed")
        with rb: st.number_input("$", min_value=0, step=10, key=f"bill_{bid}_amt",
                                  label_visibility="collapsed")
        st.button("Remove", key=f"bill_{bid}_del", type="secondary",
                  on_click=_del_bill, args=(bid,))
    else:
        c1,c2,c3,c4 = st.columns([4,3,2,1], gap="small")
        with c1: st.text_input("Name", key=f"bill_{bid}_name", label_visibility="collapsed",
                                placeholder="Expense name")
        with c2: st.selectbox("Cat", EXPENSE_CATEGORIES, key=f"bill_{bid}_cat",
                               label_visibility="collapsed")
        with c3: st.number_input("$", min_value=0, step=10, key=f"bill_{bid}_amt",
                                  label_visibility="collapsed")
        with c4: st.button("✕", key=f"bill_{bid}_del", type="secondary",
                            on_click=_del_bill, args=(bid,), help="Remove bill")
    st.markdown(f"<div style='height:1px;background:{BD};margin:1px 0;'></div>",
                unsafe_allow_html=True)

def add_bill_form():
    with st.expander("Add a new bill"):
        with st.form("add_bill_form", clear_on_submit=True):
            nn = st.text_input("Expense name", placeholder="e.g. Gym membership")
            nc = st.selectbox("Category", EXPENSE_CATEGORIES)
            na = st.number_input("Amount ($/month)", min_value=0, step=10, value=0)
            if st.form_submit_button("Add bill", use_container_width=True):
                if not nn.strip(): st.warning("Enter a name.")
                elif na<=0:        st.warning("Amount must be > 0.")
                else:
                    nid = f"b{uuid.uuid4().hex[:8]}"
                    st.session_state["bills_list"].append(
                        {"id":nid,"expense":nn.strip(),"category":nc,"amount":int(na)})
                    st.session_state[f"bill_{nid}_name"]=nn.strip()
                    st.session_state[f"bill_{nid}_cat"]=nc
                    st.session_state[f"bill_{nid}_amt"]=int(na)
                    st.rerun()

def bills_to_df():
    rows = [{"Expense":st.session_state.get(f"bill_{b['id']}_name",b["expense"]),
             "Category":st.session_state.get(f"bill_{b['id']}_cat",b["category"]),
             "Amount":st.session_state.get(f"bill_{b['id']}_amt",b["amount"])}
            for b in st.session_state["bills_list"]]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Expense","Category","Amount"])

def tier_selector(session_key, default, rec_name=None):
    """5 visible pill buttons — highlighted with ★ Suggested if matched."""
    if session_key not in st.session_state or st.session_state[session_key] not in TIERS:
        st.session_state[session_key] = default
    tcols = st.columns(5)
    for i,tier in enumerate(TIERS):
        with tcols[i]:
            is_sel = (st.session_state[session_key] == tier)
            is_rec = (tier == rec_name) if rec_name else False
            if is_sel and is_rec:  lbl = f"{tier}  ★ Suggested"
            elif is_sel:           lbl = tier
            else:                  lbl = tier
            if st.button(lbl, key=f"{session_key}_btn_{tier}",
                         type="primary" if is_sel else "secondary"):
                st.session_state[session_key] = tier
                st.rerun()
    return st.session_state[session_key]

def build_summary_text(b, fh, rating, cap_word, tname, rec_name, recs):
    lines = ["SERALUNG FINANCE — PERSONAL FINANCIAL SUMMARY","="*50,"",
             "Educational only. Not personal financial advice.","",
             "FINANCIAL HEALTH","-"*50,
             f"  Score:            {fh}/100",f"  Rating:           {rating}","",
             "MONTHLY CASH FLOW","-"*50,
             f"  Income:           ${b['income']:,.0f}",f"  Expenses:         ${b['expenses']:,.0f}",
             f"  Surplus:          ${b['surplus']:,.0f}",f"  Savings rate:     {b['savings_rate']*100:.1f}%","",
             "EMERGENCY FUND","-"*50,
             f"  Cash savings:     ${b['savings']:,.0f}",f"  Essentials/mo:    ${b['essential']:,.0f}",
             f"  Runway:           {b['runway']:.1f} months","","RISK PROFILE","-"*50,
             f"  Risk tolerance:   {tname}",f"  Risk capacity:    {cap_word}",
             f"  Suggested tier:   {rec_name}","","PRIORITISED ACTIONS","-"*50]
    tag = {"alert":"[DO FIRST] ","warn":"[IMPORTANT] ","info":"[CONSIDER] ","good":"[ON TRACK] "}
    for i,(kind,title,text) in enumerate(recs,1):
        lines.append(f"  {i}. {tag.get(kind,'')}{title}")
        words,current,pad = text.split(),"","     "
        for w in words:
            if len(current)+len(w)+1>68: lines.append(pad+current); current=w
            else: current=(current+" "+w).strip()
        if current: lines.append(pad+current)
        lines.append("")
    lines += ["","Generated by Seralung Finance."]
    return "\n".join(lines)

# ════════════════════════════════════════════════════════════════
# PAGE: BUDGET
# ════════════════════════════════════════════════════════════════
def page_budget():
    note("Enter your income and expenses. Each bill is editable — every metric updates live.", "info")
    section("INCOME & SAVINGS")
    i1,i2,i3 = cols(3,"medium")
    with i1: st.number_input("Monthly primary income ($)", min_value=0, step=250, key="income_primary")
    with i2: st.number_input("Secondary income ($, optional)", min_value=0, step=100, key="income_secondary")
    with i3: st.number_input("Current cash savings ($)", min_value=0, step=1000, key="current_savings")

    income  = int(st.session_state["income_primary"]) + int(st.session_state["income_secondary"])
    savings = int(st.session_state["current_savings"])

    section("YOUR BILLS & EXPENSES")
    st.caption(f"{len(st.session_state['bills_list'])} bill(s)  ·  edit inline  ·  ✕ to remove")
    for bill in list(st.session_state["bills_list"]): render_bill_card(bill)
    add_bill_form()

    bills_df = bills_to_df()
    b = compute_budget(income, bills_df, savings)
    st.session_state["budget"] = b

    if income<=0:
        note("Enter your monthly income above to see your budget analysis.", "warn"); return

    section("BUDGET SUMMARY")
    c1,c2,c3,c4 = cols(4,"small")
    with c1: metric_card("Total Income",   f"${b['income']:,.0f}",    "Per month",      TEXT,  CARD)
    with c2: metric_card("Total Expenses", f"${b['expenses']:,.0f}",  f"{b['expenses']/b['income']*100:.0f}% of income", AMBER, AMBER_BG)
    with c3:
        sc  = GREEN if b["surplus"]>0 else RED; sbg = GREEN_BG if b["surplus"]>0 else RED_BG
        val = f"${b['surplus']:,.0f}" if b["surplus"]>=0 else f"-${abs(b['surplus']):,.0f}"
        metric_card("Monthly Surplus", val, "Income − expenses", sc, sbg)
    with c4:
        sr = b["savings_rate"]
        src  = GREEN if sr>=0.20 else (AMBER if sr>=0.10 else RED)
        srbg = GREEN_BG if sr>=0.20 else (AMBER_BG if sr>=0.10 else RED_BG)
        metric_card("Savings Rate", f"{sr*100:.1f}%", "Surplus / income", src, srbg)

    section("50 / 30 / 20 RULE")
    nr=b["needs"]/b["income"]*100; wr=b["wants"]/b["income"]*100
    sv=max(0,b["surplus"])/b["income"]*100
    cA,cB = cols(2,"large")
    with cA: st.plotly_chart(bar_5030(nr,wr,sv), width="stretch", config=PLOTLY_CFG)
    with cB:
        st.markdown("<div style='padding-top:6px;'></div>", unsafe_allow_html=True)
        for lbl,val,ideal,hint in [
            ("Needs",nr,50,"housing, food, transport, insurance, debt"),
            ("Wants",wr,30,"dining, entertainment, shopping, travel"),
            ("Savings",sv,20,"everything left over")]:
            ok  = (val<=ideal+2) if lbl!="Savings" else (val>=ideal-2)
            clr = GREEN if ok else AMBER
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BD};border-radius:10px;"
                f"padding:10px 13px;margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,0.03);'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<span style='font-family:{FH};font-weight:700;color:{TEXT};font-size:0.9rem;'>{lbl}</span>"
                f"<span style='font-family:{FM};font-weight:700;color:{clr};font-size:0.9rem;'>"
                f"{val:.0f}%<span style='color:{MUTED};font-weight:400;font-size:0.8rem;'> / {ideal}%</span>"
                f"</span></div>"
                f"<div style='font-family:{FH};font-size:0.71rem;color:{MUTED};margin-top:2px;'>{hint}</div></div>",
                unsafe_allow_html=True)

    section("WHERE YOUR MONEY GOES")
    cd,ce = cols(2,"large")
    with cd:
        cats = {k:v for k,v in b["cat_sums"].items() if v>0}
        if cats:
            palette = [PRIMARY,TEAL,AMBER,PURPLE,RED,LGREEN,SLATE,
                       "#0E7C7B","#B7791F","#7C3AED","#3DA968","#C53929","#6B7280","#16794D"]
            st.plotly_chart(
                donut(list(cats.keys()),list(cats.values()),palette[:len(cats)],f"${b['expenses']:,.0f}"),
                width="stretch", config=PLOTLY_CFG)
    with ce:
        st.markdown("<div style='padding-top:6px;'></div>", unsafe_allow_html=True)
        rc  = GREEN if b["runway"]>=6 else (AMBER if b["runway"]>=3 else RED)
        rbg = GREEN_BG if b["runway"]>=6 else (AMBER_BG if b["runway"]>=3 else RED_BG)
        metric_card("Emergency Fund Runway", f"{b['runway']:.1f} months",
                    f"${b['savings']:,.0f} savings ÷ ${b['essential']:,.0f}/mo essentials", rc, rbg)
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        if b["runway"]<3:   note("Below 3 months — build this before investing.", "alert")
        elif b["runway"]<6: note("Aim for 6 months of essentials before investing.", "warn")
        else:               note("Healthy buffer — solid foundation to invest from.", "good")

# ════════════════════════════════════════════════════════════════
# PAGE: FINANCIAL HEALTH
# ════════════════════════════════════════════════════════════════
def page_health():
    # Age input always shown (works without budget data)
    section("YOUR AGE")
    age_col, _ = st.columns([1,2])
    with age_col:
        st.number_input("Your current age", min_value=18, max_value=90, step=1, key="user_age",
                        help="Used in risk analysis and the What-If Simulator")
    age = int(st.session_state["user_age"])

    b = st.session_state.get("budget",{})
    if not b or b.get("income",0)<=0:
        note("Complete the Budget page first — health score comes from your income and expenses.", "info")
        return

    fh, parts = financial_health_score(b)
    rating, hclr, hbg = health_rating(fh)

    section("FINANCIAL HEALTH SCORE")
    g1,g2 = cols(2,"large")
    with g1:
        st.plotly_chart(circular_gauge(fh,hclr), width="stretch", config=PLOTLY_CFG)
        st.markdown(
            f"<div style='text-align:center;margin-top:-6px;margin-bottom:4px;'>"
            f"<span style='background:{hbg};color:{hclr};font-family:{FH};font-weight:700;"
            f"font-size:0.95rem;padding:5px 20px;border-radius:20px;display:inline-block;'>"
            f"{rating}</span></div>", unsafe_allow_html=True)
    with g2:
        st.markdown("<div style='padding-top:8px;'></div>", unsafe_allow_html=True)
        for lbl,(got,mx) in parts.items():
            pct = got/mx*100
            clr = GREEN if pct>=70 else (AMBER if pct>=40 else RED)
            st.markdown(
                f"<div style='margin-bottom:12px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:baseline;"
                f"font-family:{FH};margin-bottom:5px;'>"
                f"<span style='font-size:0.9rem;color:{TEXT};font-weight:500;'>{lbl}</span>"
                f"<span style='font-family:{FM};font-weight:700;font-size:0.88rem;color:{clr};'>"
                f"{got}/{mx}</span></div>"
                f"<div style='height:5px;background:rgba(0,0,0,0.07);border-radius:3px;overflow:hidden;'>"
                f"<div style='width:{pct:.0f}%;height:100%;background:{clr};"
                f"border-radius:3px;transition:width .5s ease;'></div></div></div>",
                unsafe_allow_html=True)

    cap = risk_capacity(b); cap_lvl,cap_word = capacity_level(cap)
    if fh<45:      note("Strengthen savings and emergency fund first — this matters more than any investment choice.", "alert")
    elif cap_lvl>=4: note(f"Strong financial position — capacity to absorb investment volatility is {cap_word.lower()}.", "good")
    else:           note(f"Financial health is {rating.lower()} and risk capacity is {cap_word.lower()}.", "info")

    # Age context
    years_retire = max(0, 65-age)
    life_stage = ("Early career" if age<35 else "Mid career" if age<50
                  else "Pre-retirement" if age<65 else "Retirement")
    age_kind = "good" if age<30 else ("warn" if age>=45 else "info")
    age_msg = (f"At {age}, compounding time works strongly in your favour — time absorbs volatility."
               if age<30 else
               f"At {age}, you're in {life_stage.lower()}. Estimated {years_retire} years to typical retirement.")
    note(age_msg, age_kind)

    section("RISK PROFILE — 10 QUESTIONS", TEAL)
    note("These measure your personal comfort with volatility. Your profile updates live as you answer.", "info")

    for i,(q,opts) in enumerate(QUESTIONS):
        qk = f"q{i+1}"
        if qk not in st.session_state: st.session_state[qk] = 0
        stored = int(st.session_state[qk])
        if stored<0 or stored>=len(opts): stored=0; st.session_state[qk]=0
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;gap:9px;align-items:flex-start;margin-bottom:4px;'>"
                f"<span style='background:{TEAL_BG};color:{TEAL};font-family:{FH};font-size:0.68rem;"
                f"font-weight:700;padding:2px 8px;border-radius:5px;flex-shrink:0;margin-top:2px;'>"
                f"{i+1:02d}/10</span>"
                f"<span style='font-family:{FH};font-size:0.95rem;font-weight:600;color:{TEXT};"
                f"line-height:1.4;'>{q}</span></div>", unsafe_allow_html=True)
            sel = st.radio(q, list(range(len(opts))), format_func=lambda x,o=opts: o[x],
                           index=stored, key=f"radio_q{i+1}", label_visibility="collapsed")
            st.session_state[qk] = int(sel)

    tname,tdata,tscore = tolerance_profile()
    st.session_state.update({"tol_name":tname,"tol_level":tdata["level"],
                              "cap_level":cap_lvl,"cap_word":cap_word,"fh_score":fh})

    section("RISK ANALYSIS", PURPLE)
    # Age panel
    st.markdown(
        f"<div style='background:{CARD};border:1px solid {BD};border-radius:14px;"
        f"padding:12px 16px;margin-bottom:10px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;"
        f"box-shadow:0 1px 4px rgba(0,0,0,0.04);'>"
        f"<div><div style='font-family:{FH};font-size:0.65rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.07em;color:{MUTED};'>Age</div>"
        f"<div style='font-family:{FH};font-size:1.55rem;font-weight:800;color:{TEXT};'>{age}</div></div>"
        f"<div style='width:1px;height:38px;background:{BD};'></div>"
        f"<div><div style='font-family:{FH};font-size:0.65rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.07em;color:{MUTED};'>Years to retirement (est.)</div>"
        f"<div style='font-family:{FH};font-size:1.55rem;font-weight:800;color:{PRIMARY};'>"
        f"{years_retire}</div></div>"
        f"<div style='width:1px;height:38px;background:{BD};'></div>"
        f"<div><div style='font-family:{FH};font-size:0.65rem;font-weight:700;text-transform:uppercase;"
        f"letter-spacing:0.07em;color:{MUTED};'>Life stage</div>"
        f"<div style='font-family:{FH};font-size:1rem;font-weight:700;color:{TEXT};'>"
        f"{life_stage}</div></div></div>", unsafe_allow_html=True)

    ra1,ra2,ra3 = cols(3,"small")
    with ra1: metric_card("Risk Tolerance", tname,    f"Level {tdata['level']}/5 · score {tscore}/40",
                           tdata["clr"], tdata["bg"])
    with ra2:
        cap_clrs=[RED,RED,AMBER,TEAL,GREEN]; cap_bgs=[RED_BG,RED_BG,AMBER_BG,TEAL_BG,GREEN_BG]
        metric_card("Risk Capacity",   cap_word,  f"Level {cap_lvl}/5 · from your budget",
                    cap_clrs[cap_lvl-1], cap_bgs[cap_lvl-1])
    with ra3:
        rec_name,_ = recommended_tier(cap_lvl, tdata["level"])
        metric_card("Suggested Tier",  rec_name,  "Prudent match (lower of the two)",
                    TIER_CLR[rec_name], TIER_BG[rec_name])

    gd = tdata["level"] - cap_lvl
    if gd>=2:   note(f"Appetite ({tname}) exceeds what finances support ({cap_word}). Start at {rec_name}.", "alert")
    elif gd<=-2: note(f"Finances ({cap_word}) can support more risk than current comfort ({tname}). Step up gradually.", "info")
    else:        note("Risk tolerance and capacity are well aligned — strong position to build a plan.", "good")

# ════════════════════════════════════════════════════════════════
# PAGE: INVESTMENT PORTFOLIO
# ════════════════════════════════════════════════════════════════
def page_portfolio():
    note("Five model portfolios from lowest to highest risk. Tap a tier to inspect it.", "info")

    tol_lvl = st.session_state.get("tol_level",3)
    cap_lvl = st.session_state.get("cap_level",3)
    rec_name,_ = recommended_tier(cap_lvl, tol_lvl)
    # Pre-compute to avoid any f-string dict issues
    rec_clr = TIER_CLR.get(rec_name, PRIMARY)

    if "tol_level" not in st.session_state:
        note("Complete the Financial Health page to see your matched tier.", "warn")
    else:
        note(f"Based on your risk capacity and tolerance, your suggested starting tier is "
             f"<strong style='color:{rec_clr};'>{rec_name}</strong>.", "good")

    section("CHOOSE A TIER TO EXPLORE")
    choice = tier_selector("selected_tier", rec_name, rec_name=rec_name)
    m = TIER_METRICS[choice]
    clr = TIER_CLR[choice]; cbg = TIER_BG[choice]

    dl,dr = cols(2,"large")
    with dl:
        w = TIER_WEIGHTS[choice]
        active = [(MPT_ASSETS[i],w[i]) for i in range(len(w)) if w[i]>0]
        apal = [TEAL,"#5A4A7A",PRIMARY,AMBER,LGREEN,PURPLE]
        st.plotly_chart(
            donut([a for a,_ in active],[v for _,v in active],
                  [apal[MPT_ASSETS.index(a)] for a,_ in active], choice),
            width="stretch", config=PLOTLY_CFG)
    with dr:
        is_rec = (choice == rec_name)
        sub_label = f"{choice} · suggested for you" if is_rec else choice
        st.markdown(
            f"<div style='background:{cbg};border:1px solid {BD};border-left:4px solid {clr};"
            f"border-radius:0 14px 14px 0;padding:15px 18px;margin-bottom:10px;"
            f"box-shadow:0 1px 4px rgba(0,0,0,0.04);'>"
            f"<div style='font-family:{FH};font-size:1.5rem;font-weight:800;color:{clr};'>"
            f"{sub_label}</div>"
            f"<div style='font-family:{FH};font-size:0.82rem;color:{MUTED};margin-top:3px;'>"
            f"Expected return <strong style='color:{TEXT};'>{m['ret']*100:.1f}%</strong> p.a."
            f" · Volatility <strong style='color:{TEXT};'>{m['vol']*100:.1f}%</strong>"
            f"</div></div>", unsafe_allow_html=True)
        mm1,mm2 = cols(2,"small")
        with mm1:
            metric_card("Sharpe Ratio",       f"{m['sharpe']:.2f}",      "Return per unit of risk", PRIMARY, PRIMARY_BG)
            metric_card("Value at Risk (95%)", f"{m['var95']*100:.1f}%",  "Worst year in 20 (1-yr)", RED,     RED_BG)
        with mm2:
            metric_card("Diversification",    f"{m['div_ratio']:.2f}×",  "Higher = better spread",  TEAL,    TEAL_BG)
            metric_card("Est. Max Drawdown",   f"{m['max_dd']*100:.0f}%", "Peak-to-trough estimate", AMBER,   AMBER_BG)

    section(f"INVESTMENT OPTIONS FOR {choice.upper()}", clr)
    for opt in TIER_OPTIONS[choice]:
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BD};border-left:3px solid {clr};"
            f"border-radius:0 10px 10px 0;padding:9px 14px;margin-bottom:5px;"
            f"font-family:{FH};font-size:0.88rem;color:{TEXT};'>{opt}</div>",
            unsafe_allow_html=True)

    section("ALL TIERS COMPARED")
    rows = ""
    for i,t in enumerate(TIERS):
        mt = TIER_METRICS[t]
        hl = (f"background:{TIER_BG[t]};" if t==rec_name
              else (f"background:{CARD};" if i%2==0 else f"background:{BG};"))
        star = " ★" if t==rec_name else ""
        tc = TIER_CLR[t]
        rows += (f"<tr style='{hl}'>"
                 f"<td style='padding:9px 11px;font-family:{FH};font-weight:700;color:{tc};"
                 f"border-bottom:1px solid {BD};'>{t}{star}</td>"
                 f"<td style='padding:9px 11px;font-family:{FM};font-size:0.82rem;color:{TEXT};"
                 f"border-bottom:1px solid {BD};'>{mt['ret']*100:.1f}%</td>"
                 f"<td style='padding:9px 11px;font-family:{FM};font-size:0.82rem;color:{TEXT};"
                 f"border-bottom:1px solid {BD};'>{mt['vol']*100:.1f}%</td>"
                 f"<td style='padding:9px 11px;font-family:{FM};font-size:0.82rem;color:{TEXT};"
                 f"border-bottom:1px solid {BD};'>{mt['sharpe']:.2f}</td>"
                 f"<td style='padding:9px 11px;font-family:{FM};font-size:0.82rem;color:{RED};"
                 f"border-bottom:1px solid {BD};'>{mt['var95']*100:.1f}%</td>"
                 f"<td style='padding:9px 11px;font-family:{FM};font-size:0.82rem;color:{AMBER};"
                 f"border-bottom:1px solid {BD};'>{mt['max_dd']*100:.0f}%</td></tr>")
    hdr = "".join(f"<th style='text-align:left;padding:8px 11px;background:{PRIMARY};color:#fff;"
                  f"font-family:{FH};font-size:0.68rem;text-transform:uppercase;"
                  f"letter-spacing:0.05em;font-weight:600;white-space:nowrap;'>{h}</th>"
                  for h in ["Tier","Exp. Return","Volatility","Sharpe","VaR 95%","Max DD"])
    st.markdown(
        f"<div style='border:1px solid {BD};border-radius:12px;overflow:hidden;overflow-x:auto;'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr>{hdr}</tr></thead><tbody>{rows}</tbody></table></div>"
        f"<div style='font-family:{FH};font-size:0.7rem;color:{MUTED};margin-top:6px;line-height:1.5;'>"
        f"<strong>VaR 95%</strong>: worst 1-in-20 year loss. "
        f"<strong>Max DD</strong>: peak-to-trough estimate. "
        f"Long-run MPT assumptions — not forecasts.</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# PAGE: WHAT-IF SIMULATOR
# ════════════════════════════════════════════════════════════════
def page_simulator():
    note("Simulate how your wealth grows over time. Adjust the What-If sliders to see long-term impact.", "info")
    b        = st.session_state.get("budget",{})
    def_sav  = int(st.session_state.get("current_savings",15000))
    def_con  = max(0,int(b.get("surplus",500))) if b else 500
    def_age  = int(st.session_state.get("user_age",30))
    def_tier = st.session_state.get("selected_tier","Balanced")

    section("YOUR CURRENT SITUATION")
    r1a,r1b,r1c = st.columns([1,1,1], gap="medium")
    with r1a:
        sim_age = st.number_input("Your age", min_value=18, max_value=80,
                                   value=def_age, step=1, key="sim_age")
    with r1b:
        ret_age = st.number_input("Retirement age", min_value=int(sim_age)+1, max_value=90,
                                   value=min(90,max(int(sim_age)+5,65)), step=1, key="sim_ret_age")
    with r1c:
        income_goal = st.number_input("Monthly income in retirement ($)",
                                       min_value=0, step=500, value=5000, key="sim_income_goal")
    r2a,r2b = st.columns([1,1], gap="medium")
    with r2a: sim_sav = st.number_input("Current savings ($)", min_value=0, step=1000, value=def_sav, key="sim_sav")
    with r2b: sim_con = st.number_input("Monthly contribution ($)", min_value=0, step=100, value=def_con, key="sim_con")

    section("BASELINE PORTFOLIO")
    base_tier = tier_selector("sim_base_tier", def_tier)

    section("WHAT-IF ADJUSTMENTS", AMBER)
    wi1,wi2 = st.columns([1,1], gap="medium")
    with wi1:
        extra = st.slider("Extra monthly savings ($)", 0, 3000, step=50, value=0, key="sim_extra")
    with wi2:
        if "sim_wi_tier" not in st.session_state: st.session_state["sim_wi_tier"] = base_tier
        wi_tier = st.selectbox("Shift portfolio to", TIERS,
                                index=TIERS.index(st.session_state["sim_wi_tier"])
                                      if st.session_state["sim_wi_tier"] in TIERS else 2,
                                key="sim_wi_tier_sel")
        st.session_state["sim_wi_tier"] = wi_tier

    changed = (extra>0) or (wi_tier!=base_tier)
    if changed:
        parts = []
        if extra>0: parts.append(f"+${extra:,}/mo savings")
        if wi_tier!=base_tier: parts.append(f"portfolio {base_tier} → {wi_tier}")
        note(f"Comparing: {' and '.join(parts)}", "good")

    years_show = 35
    retire_in  = min(max(1,int(ret_age)-int(sim_age)), years_show)
    target     = income_goal*12/0.04 if income_goal>0 else 0

    bm = TIER_METRICS[base_tier]; wm = TIER_METRICS[wi_tier]
    np.random.seed(42)
    base_data = run_simulation(sim_sav, sim_con,       bm["ret"], bm["vol"], years_show)
    np.random.seed(42)
    wi_data   = run_simulation(sim_sav, sim_con+extra, wm["ret"], wm["vol"], years_show)

    section("WEALTH PROJECTION — MONTE CARLO (400 PATHS)")
    st.plotly_chart(
        simulation_chart(base_data, wi_data if changed else None, years_show,
                         retire_in, target if target>0 else None),
        width="stretch", config=PLOTLY_CFG)
    note(f"Shaded bands = 10th–90th percentile range. Solid line = median outcome. "
         f"Returns modelled from long-run MPT assumptions for "
         f"<strong>{base_tier}</strong> — not forecasts.", "info")

    section("AT RETIREMENT SNAPSHOT", TEAL)
    b50  = float(np.median(base_data[retire_in]))
    wi50 = float(np.median(wi_data[retire_in]))
    m1,m2,m3,m4 = cols(4,"small")
    with m1: metric_card("Projected nest egg", f"${b50:,.0f}",  f"Median · {base_tier}", PRIMARY, PRIMARY_BG)
    with m2:
        mo4 = b50*0.04/12; ok4 = mo4>=income_goal
        metric_card("Monthly income (4% rule)", f"${mo4:,.0f}",
                    f"Goal: ${income_goal:,.0f}/mo",
                    GREEN if ok4 else RED, GREEN_BG if ok4 else RED_BG)
    with m3:
        if target>0:
            gap = b50-target
            metric_card("Gap to target", f"+${gap:,.0f}" if gap>=0 else f"-${abs(gap):,.0f}",
                        f"Target ${target:,.0f}",
                        GREEN if gap>=0 else RED, GREEN_BG if gap>=0 else RED_BG)
        else: metric_card("Target","Set income goal →","Enter retirement income above",MUTED,BG)
    with m4:
        if changed: metric_card("What-If uplift", f"+${wi50-b50:,.0f}" if wi50>=b50 else f"${wi50-b50:,.0f}",
                                "vs baseline at retirement", AMBER, AMBER_BG)
        else:       metric_card("What-If","Adjust above →","to see the impact",MUTED,BG)

    if target>0:
        if b50>=target: note(f"On track — {base_tier} path projected to meet ${income_goal:,.0f}/mo goal.", "good")
        else: note(f"Projected ${target-b50:,.0f} short of target. Increasing contributions now makes the biggest difference.", "warn")

    section("YEAR-BY-YEAR MILESTONES")
    snap_yrs = sorted({y for y in [5,10,15,20,25,30,retire_in] if 0<y<=years_show})
    rows = ""
    for y in snap_yrs:
        b50y=float(np.median(base_data[y])); w50y=float(np.median(wi_data[y])); diff=w50y-b50y
        rl = " ← retirement" if y==retire_in else ""
        ds = f"+${diff:,.0f}" if diff>0 else ("—" if diff==0 else f"-${abs(diff):,.0f}")
        dc = GREEN if diff>0 else (RED if diff<0 else MUTED)
        rows += (f"<tr><td style='padding:8px 11px;font-family:{FH};font-weight:600;color:{TEXT};"
                 f"border-bottom:1px solid {BD};'>Year {y}{rl}</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};color:{PRIMARY};border-bottom:1px solid {BD};'>${b50y:,.0f}</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};color:{AMBER if changed else MUTED};border-bottom:1px solid {BD};'>${w50y:,.0f}</td>"
                 f"<td style='padding:8px 11px;font-family:{FM};color:{dc};font-weight:700;border-bottom:1px solid {BD};'>"
                 f"{ds if changed else '—'}</td></tr>")
    hdr_l = ["Milestone",f"Baseline ({base_tier})",f"What-If ({wi_tier})","Difference"]
    hdr_h = "".join(f"<th style='text-align:left;padding:8px 11px;background:{PRIMARY};color:#fff;"
                    f"font-family:{FH};font-size:0.68rem;text-transform:uppercase;font-weight:600;'>{h}</th>"
                    for h in hdr_l)
    st.markdown(
        f"<div style='border:1px solid {BD};border-radius:12px;overflow:hidden;overflow-x:auto;'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr>{hdr_h}</tr></thead><tbody>{rows}</tbody></table></div>",
        unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# PAGE: ACTION PLAN
# ════════════════════════════════════════════════════════════════
def page_actions():
    b = st.session_state.get("budget",{})
    if not b or b.get("income",0)<=0:
        note("Complete the Budget and Financial Health pages to generate your action plan.", "info"); return

    fh       = st.session_state.get("fh_score", financial_health_score(b)[0])
    rating,_,_ = health_rating(fh)
    cap_lvl  = st.session_state.get("cap_level",3)
    cap_word = st.session_state.get("cap_word","Moderate")
    tol_lvl  = st.session_state.get("tol_level",3)
    tname    = st.session_state.get("tol_name","Balanced")
    rec_name,_ = recommended_tier(cap_lvl, tol_lvl)

    recs = []
    if b["runway"]<3:
        target=b["essential"]*6; gap_amt=max(0,target-b["savings"])
        txt = (f"You have {b['runway']:.1f} months saved. Aim for 6 months (~${target:,.0f}). "
               f"At ${b['surplus']:,.0f}/mo surplus, that's ~{gap_amt/b['surplus']:.0f} months away."
               if b["surplus"]>0 else
               f"You have {b['runway']:.1f} months saved and no surplus — free up cash flow first.")
        recs.append(("alert","Build your emergency fund first",txt))
    elif b["runway"]<6:
        recs.append(("warn","Top up your emergency fund",
            f"You have {b['runway']:.1f} months. Building to 6 gives a full buffer before investing."))
    sr = b["savings_rate"]
    if sr<0:
        recs.append(("alert","You are spending more than you earn",
            f"Expenses exceed income by ${abs(b['surplus']):,.0f}/mo. No investment can outrun a monthly deficit."))
    elif sr<0.10:
        recs.append(("warn","Lift your savings rate",
            f"Saving {sr*100:.0f}% of income. Reaching 20% (${b['income']*0.20:,.0f}/mo) accelerates every goal."))
    if b["needs"]/b["income"]>0.55:
        recs.append(("warn","Fixed costs are high",
            f"Needs are {b['needs']/b['income']*100:.0f}% of income (ideal ≤50%). Housing, transport, and insurance are the usual culprits — structural changes here free up the most room."))
    if b["wants"]/b["income"]>0.32:
        recs.append(("info","Discretionary spending is above the guide",
            f"Wants are {b['wants']/b['income']*100:.0f}% (ideal ≤30%). Redirecting part of this to savings compounds fast."))
    if b["dti"]>0.20:
        recs.append(("warn","Debt load is elevated",
            f"Debt repayments are {b['dti']*100:.0f}% of income. Clearing high-interest debt is effectively a guaranteed return."))
    gd = tol_lvl - cap_lvl
    if gd>=2:    recs.append(("alert","Do not invest beyond your capacity",
                    f"Comfort with risk ({tname}) exceeds what finances support ({cap_word}). Start at {rec_name}."))
    elif gd<=-2: recs.append(("info","You can afford more growth when ready",
                    f"Your finances ({cap_word}) could support more risk than current comfort ({tname}). Step up gradually."))
    if fh>=65 and b["runway"]>=6:
        recs.append(("good","You are ready to invest systematically",
            f"Strong foundation. Consider ${max(0,b['surplus']):,.0f}/mo automated into {rec_name} tier."))
    if not any(k in ("alert","warn") for k,_,_ in recs):
        recs.append(("good","Your finances are in good shape",
            "No critical issues. Keep contributing consistently and review quarterly."))

    recs.sort(key=lambda r:{"alert":0,"warn":1,"info":2,"good":3}.get(r[0],4))
    n_alert = sum(1 for r in recs if r[0]=="alert")
    n_warn  = sum(1 for r in recs if r[0]=="warn")
    readiness = max(0,min(100, fh - n_alert*12 - n_warn*5))
    rdg,rclr,rbg = health_rating(readiness)
    rec_clr = TIER_CLR.get(rec_name, PRIMARY)

    section("INVESTMENT READINESS")
    rr1,rr2 = cols(2,"large")
    with rr1: st.plotly_chart(circular_gauge(readiness,rclr), width="stretch", config=PLOTLY_CFG)
    with rr2:
        pad = "8px" if IS_MOBILE else "26px"
        st.markdown(
            f"<div style='background:{rbg};border:1px solid {BD};border-left:4px solid {rclr};"
            f"border-radius:0 14px 14px 0;padding:16px 20px;margin-top:{pad};"
            f"box-shadow:0 1px 4px rgba(0,0,0,0.04);'>"
            f"<div style='font-family:{FH};font-size:0.65rem;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:0.08em;color:{MUTED};margin-bottom:4px;'>Overall</div>"
            f"<div style='font-family:{FH};font-size:1.65rem;font-weight:800;color:{rclr};'>{rdg}</div>"
            f"<div style='font-family:{FH};font-size:0.85rem;color:{MUTED};margin-top:5px;line-height:1.5;'>"
            f"{n_alert} critical item{'s' if n_alert!=1 else ''} and {n_warn} to watch. "
            f"Suggested portfolio: <strong style='color:{rec_clr};'>{rec_name}</strong>.</div></div>",
            unsafe_allow_html=True)

    section("YOUR PRIORITISED ACTIONS", PURPLE)
    cfg_map = {"alert":(RED_BG,RED),"warn":(AMBER_BG,AMBER),
               "info":(PRIMARY_BG,PRIMARY),"good":(GREEN_BG,GREEN)}
    tag_map = {"alert":"Do first","warn":"Important","info":"Consider","good":"On track"}
    for rank,(kind,title,text) in enumerate(recs,1):
        bg2,ac = cfg_map.get(kind,cfg_map["info"])
        tag = tag_map.get(kind,"")
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BD};border-left:3.5px solid {ac};"
            f"border-radius:0 14px 14px 0;padding:13px 16px;margin-bottom:8px;"
            f"box-shadow:0 1px 4px rgba(0,0,0,0.03);'>"
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:5px;flex-wrap:wrap;'>"
            f"<span style='background:{ac};color:#fff;font-family:{FH};font-size:0.78rem;"
            f"font-weight:800;width:24px;height:24px;border-radius:8px;display:inline-flex;"
            f"align-items:center;justify-content:center;flex-shrink:0;'>{rank}</span>"
            f"<span style='background:{bg2};color:{ac};font-family:{FH};font-size:0.6rem;"
            f"font-weight:700;padding:2px 9px;border-radius:20px;text-transform:uppercase;"
            f"letter-spacing:0.05em;'>{tag}</span>"
            f"<span style='font-family:{FH};font-size:0.97rem;font-weight:700;color:{TEXT};'>"
            f"{title}</span></div>"
            f"<div style='font-family:{FH};font-size:0.87rem;color:{MUTED};line-height:1.6;"
            f"padding-left:34px;'>{text}</div></div>",
            unsafe_allow_html=True)

    section("DOWNLOAD YOUR SUMMARY", PURPLE)
    st.download_button(
        "  Download summary (.txt)",
        data=build_summary_text(b,fh,rating,cap_word,tname,rec_name,recs),
        file_name="seralung_finance_summary.txt", mime="text/plain",
        use_container_width=True)
    st.caption("Your score, cash flow, runway, risk profile and action plan — easy to print or share.")

# ════════════════════════════════════════════════════════════════
# PAGE DISPATCH
# ════════════════════════════════════════════════════════════════
{"budget":page_budget,"health":page_health,"portfolio":page_portfolio,
 "simulator":page_simulator,"actions":page_actions}[current_page]()

# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown(
    f"<div style='border-top:1px solid {BD};margin-top:2.5rem;padding:14px 0 6px;"
    f"font-family:{FH};font-size:0.72rem;color:{DIM};text-align:center;'>"
    f"<strong style='color:{PRIMARY};'>Seralung Finance</strong>"
    f" &nbsp;·&nbsp; Understand Risk. Invest with Confidence."
    f"<br><span style='font-size:0.66rem;'>Educational purposes only — not personal "
    f"financial advice — consult a licensed financial adviser before investing.</span></div>",
    unsafe_allow_html=True)
