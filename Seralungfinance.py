"""
Meridian — Personal Investment Risk & Financial Intelligence  v7
================================================================
3-tab SaaS architecture:
  1. Portfolio Intelligence — allocation scoring (risk, diversification, concentration, defensive)
  2. Financial Health       — income & expenses → capacity rating + 10-q tolerance assessment
  3. Insights Engine        — cross-reference: portfolio risk vs capacity vs tolerance

Run:  streamlit run Seralungfinance.py
Deps: streamlit plotly
"""
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Meridian", layout="wide",
                   initial_sidebar_state="collapsed")

# ════════════════════════════════════════════════════════════════
# PALETTE  (light green theme)
# ════════════════════════════════════════════════════════════════
BG         = "#EAF5EC"
CARD       = "#FFFFFF"
BD         = "#CBE2D2"
TEXT       = "#10241A"
MUTED      = "#54695E"
DIM        = "#95AC9E"

PRIMARY    = "#16794D"
PRIMARY_BG = "#E0F2E7"
PRIMARY_DK = "#0E5C39"
LGREEN     = "#3DA968"
LGREEN_BG  = "#EAF6EE"

GREEN      = PRIMARY
GREEN_BG   = PRIMARY_BG
AMBER      = "#B7791F"
AMBER_BG   = "#FBF3E2"
RED        = "#C53929"
RED_BG     = "#FBEAE7"
PURPLE     = "#7C3AED"
PURPLE_BG  = "#F1ECFC"
TEAL       = "#0E7C7B"
TEAL_BG    = "#DFF2F1"
SLATE      = "#6B7280"
SLATE_BG   = "#F2F4F7"

FH = "'Plus Jakarta Sans', system-ui, sans-serif"
FM = "'JetBrains Mono', 'Fira Code', monospace"

# ════════════════════════════════════════════════════════════════
# ASSET MODEL  (5 categories, retail-friendly)
# ════════════════════════════════════════════════════════════════
ASSET_NAMES = ["Cash", "ETFs / Index Funds", "Individual Stocks", "Crypto", "Other"]
ASSET_KEYS  = ["alloc_cash", "alloc_etfs", "alloc_stocks", "alloc_crypto", "alloc_other"]
ASSET_CLR   = [TEAL, PRIMARY, AMBER, PURPLE, SLATE]
ASSET_BG    = [TEAL_BG, PRIMARY_BG, AMBER_BG, PURPLE_BG, SLATE_BG]

# Risk points contributed per asset class (0-100 scale)
ASSET_RISK_PTS = {
    "Cash":               0,
    "ETFs / Index Funds": 35,
    "Individual Stocks":  65,
    "Crypto":             100,
    "Other":              45,
}
# Annualized volatility estimates (for display only)
ASSET_VOL = {
    "Cash":               0.005,
    "ETFs / Index Funds": 0.16,
    "Individual Stocks":  0.25,
    "Crypto":             0.75,
    "Other":              0.20,
}
# Defensive contribution weights
ASSET_DEFENSIVE = {
    "Cash":               1.00,
    "ETFs / Index Funds": 0.35,
    "Individual Stocks":  0.00,
    "Crypto":             0.00,
    "Other":              0.15,
}
# Growth contribution weights
ASSET_GROWTH = {
    "Cash":               0.00,
    "ETFs / Index Funds": 0.65,
    "Individual Stocks":  1.00,
    "Crypto":             1.00,
    "Other":              0.40,
}
# Asset descriptions (one-liners)
ASSET_DESC = [
    "Savings, term deposits, money in offset",
    "Broad-market funds (S&P 500, VAS, MSCI World)",
    "Direct shares — single companies",
    "Bitcoin, Ethereum, altcoins",
    "Property, bonds, commodities, collectibles",
]

# ════════════════════════════════════════════════════════════════
# RISK TOLERANCE QUIZ  (10 questions; produces Tolerance Profile)
# ════════════════════════════════════════════════════════════════
QUESTIONS = [
    ("When do you expect to need this money?",
     ["Under 3 years — I may need it soon",
      "3–7 years — medium-term plan",
      "7–15 years — long-term wealth building",
      "15+ years — retirement or generational wealth"]),
    ("How stable is your income?",
     ["Retired or on a fixed income",
      "Variable — self-employed or contract work",
      "Stable salaried employment",
      "Very secure — government or tenured role"]),
    ("How many months of expenses do you have in accessible cash?",
     ["Less than 1 month", "1–3 months", "3–6 months", "6 months or more"]),
    ("How would you describe your investment experience?",
     ["None — mostly savings accounts",
      "Basic — I understand shares and managed funds",
      "3+ years of active investing in shares or ETFs",
      "10+ years across multiple asset classes"]),
    ("If your portfolio fell 30% in 3 months, you would:",
     ["Sell everything to stop the bleeding",
      "Sell part of it to reduce exposure",
      "Hold on and wait for recovery",
      "Add to positions at the lower prices"]),
    ("What is your primary investment goal?",
     ["Protect capital — safety is everything",
      "Modest growth with capital protection",
      "Balanced growth over the medium term",
      "Maximum long-term growth — volatility is fine"]),
    ("Do you expect significant withdrawals within the next 5 years?",
     ["Yes — most of it within 5 years",
      "Yes — a meaningful portion",
      "Possibly — small amounts only",
      "No — capital is fully committed long-term"]),
    ("How would you describe your current debt?",
     ["High debt relative to income or assets",
      "Moderate — standard mortgage",
      "Low — actively paying it down",
      "Debt free"]),
    ("This portfolio is what share of your total net worth?",
     ["Over 75% — this is most of what I own",
      "50–75% of total net worth",
      "25–50% of total net worth",
      "Under 25% — I have significant other assets"]),
    ("Maximum annual loss you could absorb without impacting lifestyle?",
     ["Under 5% — any significant loss is unacceptable",
      "5–15% — moderate drawdown is manageable",
      "15–25% — I understand markets cycle",
      "25% or more — I focus on long-term returns"]),
]

# Tolerance profile (from quiz total score 10-40)
TOLERANCE_PROFILES = {
    "Conservative":             {"range": (10, 18), "level": 1, "clr": GREEN,   "bg": GREEN_BG},
    "Moderately Conservative":  {"range": (19, 25), "level": 2, "clr": TEAL,    "bg": TEAL_BG},
    "Balanced":                 {"range": (26, 31), "level": 3, "clr": PRIMARY, "bg": PRIMARY_BG},
    "Growth":                   {"range": (32, 36), "level": 4, "clr": AMBER,   "bg": AMBER_BG},
    "Aggressive":               {"range": (37, 40), "level": 5, "clr": RED,     "bg": RED_BG},
}

# ════════════════════════════════════════════════════════════════
# SESSION STATE DEFAULTS
# ════════════════════════════════════════════════════════════════
_DEFAULTS = {
    # Portfolio percentages
    "alloc_cash": 0, "alloc_etfs": 0, "alloc_stocks": 0, "alloc_crypto": 0, "alloc_other": 0,
    # Financial health inputs
    "income_primary": 0, "income_secondary": 0, "expenses_monthly": 0,
    # Quiz answers
    **{f"q{i}": 0 for i in range(1, 11)},
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ════════════════════════════════════════════════════════════════
# PURE FUNCTIONS — PORTFOLIO INTELLIGENCE
# ════════════════════════════════════════════════════════════════
def get_allocation():
    """Return dict {asset_name: percent} from session state."""
    return {name: float(st.session_state[k]) for name, k in zip(ASSET_NAMES, ASSET_KEYS)}

def total_allocation():
    return sum(get_allocation().values())

def normalized_allocation():
    """Returns allocation normalized to 100% (handles user input that doesn't quite sum to 100)."""
    alloc = get_allocation()
    s = sum(alloc.values())
    if s <= 0:
        return {n: 0.0 for n in ASSET_NAMES}
    return {n: alloc[n] / s * 100 for n in ASSET_NAMES}

def portfolio_risk_score(alloc):
    """0-100 weighted risk score."""
    return round(sum(alloc[n] * ASSET_RISK_PTS[n] for n in alloc) / 100)

def portfolio_volatility(alloc):
    """Weighted annualized volatility (decimal)."""
    return sum(alloc[n] / 100 * ASSET_VOL[n] for n in alloc)

def diversification_score(alloc):
    """0-100, Herfindahl-based (lower concentration = higher score)."""
    weights = [alloc[n] / 100 for n in alloc]
    if sum(weights) <= 0:
        return 0
    hhi = sum(w * w for w in weights)
    # Min HHI for 5 categories = 0.2; max = 1.0. Map to 0-100.
    return round(max(0, min(100, (1 - hhi) / 0.8 * 100)))

def concentration_pct(alloc):
    """Largest single-category allocation."""
    return max(alloc.values()) if alloc else 0

def defensive_score(alloc):
    """0-100. Higher = stronger downside buffer."""
    pool = sum(alloc[n] * ASSET_DEFENSIVE[n] for n in alloc) / 100
    # 40% effective defensive = full score
    return round(min(100, pool * 2.5))

def growth_share_pct(alloc):
    return round(sum(alloc[n] * ASSET_GROWTH[n] for n in alloc) / 100)

def stability_share_pct(alloc):
    return round(sum(alloc[n] * ASSET_DEFENSIVE[n] for n in alloc) / 100)

def risk_level_label(score):
    """Map portfolio risk score 0-100 to named level + numeric level 1-5."""
    if score <= 20: return ("Very Conservative", 1)
    if score <= 40: return ("Conservative",      2)
    if score <= 60: return ("Moderate",          3)
    if score <= 80: return ("Aggressive",        4)
    return            ("Very Aggressive",        5)


# ════════════════════════════════════════════════════════════════
# PURE FUNCTIONS — FINANCIAL HEALTH
# ════════════════════════════════════════════════════════════════
def total_income():
    return float(st.session_state["income_primary"]) + float(st.session_state["income_secondary"])

def monthly_expenses():
    return float(st.session_state["expenses_monthly"])

def monthly_surplus():
    return total_income() - monthly_expenses()

def savings_rate():
    inc = total_income()
    return monthly_surplus() / inc if inc > 0 else 0

def spending_pressure():
    inc = total_income()
    return monthly_expenses() / inc if inc > 0 else 0

def financial_health_score():
    """0-100, weighted: 40 savings rate, 30 spending pressure, 30 surplus magnitude."""
    inc = total_income()
    exp = monthly_expenses()
    if inc <= 0:
        return 0
    sr  = savings_rate()
    sp  = spending_pressure()
    sur = monthly_surplus()

    # Savings rate (40 pts)
    if   sr >= 0.20: sr_pts = 40
    elif sr >= 0.10: sr_pts = 25 + (sr - 0.10) * 150
    elif sr >  0:    sr_pts = sr * 250
    else:            sr_pts = 0

    # Spending pressure (30 pts) — inverse
    if   sp <= 0.50: pr_pts = 30
    elif sp <= 0.70: pr_pts = 20 + (0.70 - sp) * 50
    elif sp <= 0.90: pr_pts = 10 + (0.90 - sp) * 50
    elif sp <  1.00: pr_pts = (1.00 - sp) * 100
    else:            pr_pts = 0

    # Surplus relative to expenses (30 pts) — each month adds buffer
    if exp > 0:
        ratio = sur / exp
        if   ratio >= 0.30: ab_pts = 30
        elif ratio >  0:    ab_pts = ratio * 100
        else:               ab_pts = 0
    else:
        ab_pts = 30 if sur > 0 else 0

    return round(min(100, sr_pts + pr_pts + ab_pts))

def stability_rating(score):
    if score >= 80: return "Strong",   GREEN,  GREEN_BG
    if score >= 60: return "Stable",   TEAL,   TEAL_BG
    if score >= 40: return "Moderate", AMBER,  AMBER_BG
    if score >= 20: return "At Risk",  RED,    RED_BG
    return            "Weak",          RED,    RED_BG

def risk_capacity_score(fh_score, sr):
    """0-100. Capacity to absorb investment volatility."""
    cap = fh_score
    if sr > 0.30: cap = min(100, cap + 10)
    if sr < 0.05: cap = max(0,   cap - 15)
    return round(cap)

def capacity_rating(cap):
    """Returns (rating, level 1-4, color, bg)."""
    if cap >= 75: return "Strong",   4, GREEN, GREEN_BG
    if cap >= 50: return "Moderate", 3, TEAL,  TEAL_BG
    if cap >= 25: return "Limited",  2, AMBER, AMBER_BG
    return         "Weak",            1, RED,   RED_BG


# ════════════════════════════════════════════════════════════════
# PURE FUNCTIONS — TOLERANCE (from quiz)
# ════════════════════════════════════════════════════════════════
def quiz_total():
    return sum(int(st.session_state[f"q{i}"]) + 1 for i in range(1, 11))

def get_tolerance_profile():
    score = quiz_total()
    for name, data in TOLERANCE_PROFILES.items():
        lo, hi = data["range"]
        if lo <= score <= hi:
            return name, data, score
    return "Balanced", TOLERANCE_PROFILES["Balanced"], score


# ════════════════════════════════════════════════════════════════
# INSIGHTS ENGINE
# ════════════════════════════════════════════════════════════════
def generate_insights(p_state, fh_state, tol_state):
    """
    Cross-reference portfolio, financial health, and tolerance.
    Returns: list of {"kind", "title", "text"} dicts, ranked by severity.
    """
    insights = []
    p_lvl = p_state["risk_level_num"]      # 1-5
    c_lvl = fh_state["capacity_level"]      # 1-4
    t_lvl = tol_state["level"]              # 1-5

    # Map 1-4 capacity onto 1-5 risk scale for fair comparison
    cap_aligned = (c_lvl - 1) * 4 / 3 + 1   # 1->1, 4->5

    # ── Portfolio risk vs financial capacity ────────────────────
    gap = p_lvl - cap_aligned
    if gap >= 2:
        insights.append({"kind": "alert", "priority": 1,
            "title": "Portfolio risk exceeds financial capacity",
            "text": "Your portfolio carries significantly more risk than your current financial position can comfortably absorb. A drawdown may force decisions you'd prefer to avoid."})
    elif gap >= 1:
        insights.append({"kind": "warn", "priority": 2,
            "title": "Mild capacity mismatch",
            "text": "Portfolio risk is moderately above your financial capacity. Worth reviewing — a setback could be uncomfortable."})
    elif gap <= -2:
        insights.append({"kind": "info", "priority": 3,
            "title": "Conservative relative to capacity",
            "text": "Your financial position could support a more growth-oriented allocation. Whether to take that on depends on your personal comfort with volatility."})

    # ── Portfolio risk vs tolerance ─────────────────────────────
    t_gap = p_lvl - t_lvl
    if t_gap >= 2:
        insights.append({"kind": "alert", "priority": 1,
            "title": "Portfolio risk exceeds your comfort level",
            "text": "Based on your assessment answers, your tolerance for volatility is lower than your portfolio's actual risk. Investors in this gap often panic-sell at the wrong time."})
    elif t_gap >= 1:
        insights.append({"kind": "warn", "priority": 3,
            "title": "Portfolio slightly above comfort zone",
            "text": "Your stated comfort with volatility sits slightly below your portfolio's risk level."})
    elif t_gap <= -2:
        insights.append({"kind": "info", "priority": 4,
            "title": "Comfort exceeds current allocation",
            "text": "You indicated comfort with more volatility than your portfolio currently carries."})

    # ── Concentration risk ──────────────────────────────────────
    conc = p_state["concentration"]
    if conc >= 70:
        insights.append({"kind": "alert", "priority": 1,
            "title": "Severe concentration",
            "text": f"Over {conc:.0f}% of your portfolio sits in a single asset category. Single-event risk is amplified disproportionately."})
    elif conc >= 55:
        insights.append({"kind": "warn", "priority": 2,
            "title": "High concentration",
            "text": f"{conc:.0f}% in one category. Concentration amplifies the impact of category-specific shocks."})

    # ── Crypto exposure ─────────────────────────────────────────
    crypto = p_state["alloc"]["Crypto"]
    if crypto >= 40:
        insights.append({"kind": "alert", "priority": 1,
            "title": "Very high crypto exposure",
            "text": f"Crypto at {crypto:.0f}% materially increases portfolio volatility. Historical drawdowns in crypto exceed 70%."})
    elif crypto >= 20:
        insights.append({"kind": "warn", "priority": 2,
            "title": "Elevated crypto exposure",
            "text": f"Crypto at {crypto:.0f}% is above the level seen in typical balanced portfolios."})

    # ── Defensive allocation ────────────────────────────────────
    if p_state["defensive_score"] < 25 and c_lvl <= 2:
        insights.append({"kind": "alert", "priority": 1,
            "title": "Insufficient defensive allocation",
            "text": "Defensive holdings are low relative to your financial capacity. A downturn currently has limited cushion."})
    elif p_state["defensive_score"] < 25:
        insights.append({"kind": "warn", "priority": 3,
            "title": "Limited defensive allocation",
            "text": "Defensive holdings (cash, broad ETFs) are minimal. Acceptable if your capacity is strong, but worth being aware of."})

    # ── Diversification ─────────────────────────────────────────
    if p_state["diversification"] < 30:
        insights.append({"kind": "warn", "priority": 2,
            "title": "Limited diversification",
            "text": f"Diversification score: {p_state['diversification']}/100. Portfolio is concentrated across only one or two categories."})

    # ── Financial health stress flag ────────────────────────────
    if fh_state["health_score"] < 30:
        insights.append({"kind": "alert", "priority": 1,
            "title": "Weak financial foundation",
            "text": "Financial health score is low. Stabilising income, expenses, and emergency reserves usually delivers more impact than portfolio adjustments at this point."})

    # ── Positive signal if nothing fired ───────────────────────
    if not insights:
        insights.append({"kind": "good", "priority": 5,
            "title": "Aligned portfolio profile",
            "text": "Portfolio risk aligns with both your financial capacity and stated comfort. Diversification is balanced; no significant concentration detected."})

    # Rank by priority (1 = most severe)
    insights.sort(key=lambda x: x["priority"])
    return insights

def investment_readiness(p_state, fh_score, insights):
    """0-100 composite — synthesizes everything."""
    base = fh_score
    n_alerts = sum(1 for i in insights if i["kind"] == "alert")
    n_warns  = sum(1 for i in insights if i["kind"] == "warn")
    base -= n_alerts * 15
    base -= n_warns  * 5
    base += (p_state["diversification"] - 50) * 0.2
    return round(max(0, min(100, base)))

def stress_preview(alloc):
    """One-line bear-market preview. Returns (pct_loss, narrative)."""
    # Bear market shocks (-30% scenario, by asset)
    shocks = {"Cash": 0.0, "ETFs / Index Funds": -0.30, "Individual Stocks": -0.35,
              "Crypto": -0.55, "Other": -0.20}
    loss = sum(alloc[n] / 100 * shocks[n] for n in alloc)
    return loss * 100  # percent


# ════════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: {BG} !important;
    font-family: {FH};
    color: {TEXT} !important;
}}
.stApp, .stApp p, .stApp label, .stApp li,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {{
    color: {TEXT};
}}
.block-container {{ padding: 0 1.6rem 3rem; max-width: 1120px; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}
* {{ box-sizing: border-box; }}

h1, h2, h3, h4 {{ font-family: {FH} !important; font-weight: 700 !important; color: {TEXT} !important; margin: 0 !important; }}

[data-testid="stVerticalBlock"] {{ gap: 0.55rem !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 12px !important; }}

/* Tabs — big, professional, website-style nav */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px; border-bottom: 1px solid {BD}; background: transparent; padding: 0;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: {FH}; font-size: 1rem; letter-spacing: 0; text-transform: none;
    color: {MUTED}; background: transparent; border: none; font-weight: 600;
    border-bottom: 3px solid transparent; padding: 13px 22px; margin: 0;
    border-radius: 10px 10px 0 0; transition: all 0.15s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {PRIMARY} !important; background: {PRIMARY_BG} !important;
}}
.stTabs [aria-selected="true"] {{
    color: {PRIMARY} !important; border-bottom: 3px solid {PRIMARY} !important;
    background: {PRIMARY_BG} !important; font-weight: 700 !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.2rem; background: transparent; }}

/* Inputs */
div[data-testid="stNumberInput"] label, div[data-testid="stSelectbox"] label {{
    font-family: {FH} !important; font-size: 0.78rem !important;
    letter-spacing: 0 !important; text-transform: none !important; color: {MUTED} !important;
    font-weight: 500 !important;
}}
.stNumberInput input {{
    background: {CARD} !important; border: 1px solid {BD} !important; border-radius: 7px !important;
    color: {TEXT} !important; font-family: {FM} !important; font-size: 0.92rem !important;
    padding: 7px 11px !important;
}}
.stNumberInput input:focus {{
    border-color: {PRIMARY} !important; box-shadow: 0 0 0 3px rgba(22,121,77,0.15) !important;
    outline: none !important;
}}
.stNumberInput button {{ background: {CARD} !important; border-color: {BD} !important; border-radius: 5px !important; }}

/* RADIO — bulletproof text colour + hover interactivity */
div[data-testid="stRadio"] *,
[data-testid="stRadio"] label * {{ color: {TEXT} !important; }}
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
    color: {TEXT} !important; font-family: {FH} !important;
    font-size: 0.88rem !important; font-weight: 400 !important;
    margin: 0 !important; line-height: 1.45 !important;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label {{
    padding: 7px 10px; border-radius: 7px; margin-bottom: 2px;
    transition: background 0.12s ease; cursor: pointer;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label:hover {{
    background: {PRIMARY_BG};
}}
div[data-testid="stRadio"] > label {{
    font-family: {FH} !important; font-size: 0.78rem !important;
    letter-spacing: 0 !important; text-transform: none !important;
    color: {MUTED} !important; font-weight: 500 !important;
}}

/* Button */
.stButton > button {{
    background: {PRIMARY} !important; color: #ffffff !important; border: none !important;
    border-radius: 8px !important; font-family: {FH} !important; font-size: 0.93rem !important;
    font-weight: 600 !important; padding: 10px 26px !important;
    box-shadow: 0 3px 12px rgba(22,121,77,0.32) !important; transition: all 0.15s !important;
}}
.stButton > button:hover {{
    background: {PRIMARY_DK} !important; transform: translateY(-1px) !important;
    box-shadow: 0 5px 16px rgba(22,121,77,0.40) !important;
}}

hr {{ border: none; border-top: 1px solid {BD}; margin: 0.8rem 0; }}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# UI HELPERS
# ════════════════════════════════════════════════════════════════
def note(text, kind="info"):
    cfg = {
        "info":  (PRIMARY_BG, PRIMARY),
        "good":  (GREEN_BG,   GREEN),
        "warn":  (AMBER_BG,   AMBER),
        "alert": (RED_BG,     RED),
    }
    bg, ac = cfg.get(kind, cfg["info"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {ac};border-radius:0 7px 7px 0;"
        f"padding:9px 13px;margin:5px 0;font-family:{FH};font-size:0.88rem;"
        f"color:{TEXT};line-height:1.55;'>{text}</div>",
        unsafe_allow_html=True,
    )

def section(label, color=PRIMARY):
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;margin:18px 0 9px;'>"
        f"<span style='font-family:{FH};font-size:0.78rem;letter-spacing:0.04em;"
        f"text-transform:uppercase;color:{color};white-space:nowrap;font-weight:700;'>{label}</span>"
        f"<div style='flex:1;height:1px;background:{BD};'></div></div>",
        unsafe_allow_html=True,
    )

def metric_card(label, value, sub="", accent=PRIMARY, bg=CARD):
    st.markdown(
        f"<div style='background:{bg};border:1px solid {BD};border-top:3px solid {accent};"
        f"border-radius:0 0 10px 10px;padding:12px 14px;min-width:0;height:100%;'>"
        f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};font-weight:500;"
        f"margin-bottom:5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{label}</div>"
        f"<div style='font-family:{FH};font-size:1.4rem;color:{accent};font-weight:700;"
        f"line-height:1.2;word-break:break-word;'>{value}</div>"
        f"<div style='font-family:{FH};font-size:0.74rem;color:{MUTED};margin-top:3px;"
        f"line-height:1.4;'>{sub}</div></div>",
        unsafe_allow_html=True,
    )

def score_gauge(label, score, accent=PRIMARY, bg=PRIMARY_BG, sub=""):
    """Big numeric score with horizontal bar."""
    pct = max(0, min(100, score))
    st.markdown(
        f"<div style='background:{bg};border:1px solid {BD};border-radius:12px;"
        f"padding:16px 18px;text-align:left;'>"
        f"<div style='font-family:{FH};font-size:0.78rem;color:{MUTED};font-weight:500;"
        f"margin-bottom:4px;'>{label}</div>"
        f"<div style='display:flex;align-items:baseline;gap:6px;'>"
        f"<span style='font-family:{FH};font-size:2.4rem;font-weight:800;color:{accent};line-height:1;'>{score}</span>"
        f"<span style='font-family:{FM};font-size:0.85rem;color:{MUTED};'>/100</span>"
        f"</div>"
        f"<div style='height:6px;background:rgba(0,0,0,0.08);border-radius:4px;margin-top:10px;overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;background:{accent};border-radius:4px;'></div></div>"
        f"<div style='font-family:{FH};font-size:0.78rem;color:{MUTED};margin-top:7px;'>{sub}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color="#fff", width=2)),
        textinfo="label+percent",
        textfont=dict(family="Plus Jakarta Sans, sans-serif", size=10, color=TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    ))
    ann = [dict(text=center, x=0.5, y=0.5,
                font=dict(size=14, family="Plus Jakarta Sans", color=TEXT),
                showarrow=False)] if center else []
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=8, b=8, l=8, r=8), height=250, showlegend=False, annotations=ann,
    )
    return fig


# ════════════════════════════════════════════════════════════════
# HEADER  (website-style hero)
# ════════════════════════════════════════════════════════════════
st.markdown(
    f"<div style='background:linear-gradient(120deg,{PRIMARY_DK} 0%,{PRIMARY} 55%,{LGREEN} 100%);"
    f"border-radius:0 0 22px 22px;padding:1.7rem 2.1rem 1.5rem;margin:0 -1.6rem 1.2rem;"
    f"box-shadow:0 6px 22px rgba(14,92,57,0.22);'>"
    f"<div style='display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;'>"
    f"<div style='display:flex;align-items:center;gap:14px;'>"
    f"<div style='width:48px;height:48px;border-radius:14px;background:rgba(255,255,255,0.18);"
    f"border:1px solid rgba(255,255,255,0.4);display:flex;align-items:center;justify-content:center;"
    f"font-family:{FH};font-size:1.65rem;font-weight:800;color:#fff;flex-shrink:0;'>M</div>"
    f"<div>"
    f"<div style='font-family:{FH};font-size:1.9rem;font-weight:800;color:#fff;"
    f"letter-spacing:-0.02em;line-height:1;'>Meridian</div>"
    f"<div style='font-family:{FH};font-size:0.85rem;color:rgba(255,255,255,0.85);"
    f"margin-top:3px;font-weight:500;'>Personal Investment Risk &amp; Financial Intelligence</div>"
    f"</div></div>"
    f"<div style='font-family:{FH};font-size:0.72rem;color:rgba(255,255,255,0.78);"
    f"text-align:right;font-weight:600;letter-spacing:0.05em;'>SMART INVESTING&nbsp;·&nbsp;v7</div>"
    f"</div></div>"
    f"<div style='font-family:{FH};font-size:0.78rem;color:{MUTED};padding:4px 0 6px;'>"
    f"<span style='background:{PRIMARY_BG};color:{PRIMARY_DK};font-weight:600;"
    f"padding:3px 9px;border-radius:5px;'>Educational only</span>"
    f"&nbsp; Not personal financial advice — consult a licensed adviser before investing.</div>",
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["Portfolio Intelligence", "Financial Health", "Insights Engine"])

# ════════════════════════════════════════════════════════════════
# TAB 1 — PORTFOLIO INTELLIGENCE
# ════════════════════════════════════════════════════════════════
with tab1:
    note("Enter your portfolio as percentages across the five categories. Total should add to 100%. We'll analyse risk, diversification, concentration, and defensive strength.", "info")

    section("YOUR ALLOCATION")
    ca, cb = st.columns(2, gap="large")
    for i, (name, key, desc) in enumerate(zip(ASSET_NAMES, ASSET_KEYS, ASSET_DESC)):
        col = ca if i < 3 else cb
        with col:
            clr = ASSET_CLR[i]
            bgc = ASSET_BG[i]
            st.markdown(
                f"<div style='background:{bgc};border-left:3px solid {clr};"
                f"border-radius:0 7px 7px 0;padding:7px 12px;margin-bottom:3px;'>"
                f"<div style='font-family:{FH};font-size:0.92rem;font-weight:700;color:{TEXT};'>{name}</div>"
                f"<div style='font-family:{FH};font-size:0.75rem;color:{MUTED};'>{desc}</div></div>",
                unsafe_allow_html=True,
            )
            st.number_input(name, min_value=0, max_value=100, step=5,
                            key=key, label_visibility="collapsed")

    total = total_allocation()
    if total == 0:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        note("Enter your allocation percentages above to see your portfolio intelligence breakdown.", "info")
    else:
        # Total indicator
        if 95 <= total <= 105:
            tot_clr, tot_bg, tot_msg = GREEN, GREEN_BG, "Total adds up correctly"
        else:
            tot_clr, tot_bg, tot_msg = AMBER, AMBER_BG, "Values will be normalised to 100% for analysis"
        st.markdown(
            f"<div style='background:{tot_bg};border:1px solid {BD};border-radius:8px;"
            f"padding:9px 13px;margin:8px 0 6px;display:flex;justify-content:space-between;align-items:center;'>"
            f"<span style='font-family:{FH};font-size:0.85rem;color:{TEXT};font-weight:600;'>Total: "
            f"<span style='color:{tot_clr};'>{total:.0f}%</span></span>"
            f"<span style='font-family:{FH};font-size:0.78rem;color:{MUTED};'>{tot_msg}</span></div>",
            unsafe_allow_html=True,
        )

        alloc = normalized_allocation()
        risk_score = portfolio_risk_score(alloc)
        risk_label, risk_lvl_num = risk_level_label(risk_score)
        div_score  = diversification_score(alloc)
        conc       = concentration_pct(alloc)
        def_score  = defensive_score(alloc)
        vol        = portfolio_volatility(alloc)
        grow       = growth_share_pct(alloc)
        stab       = stability_share_pct(alloc)

        # Risk-level colour
        if   risk_lvl_num <= 2: rclr, rbg = GREEN,   GREEN_BG
        elif risk_lvl_num == 3: rclr, rbg = TEAL,    TEAL_BG
        elif risk_lvl_num == 4: rclr, rbg = AMBER,   AMBER_BG
        else:                   rclr, rbg = RED,     RED_BG

        section("PORTFOLIO SCORES")
        col1, col2, col3 = st.columns(3, gap="small")
        with col1:
            score_gauge("Portfolio Risk Level", risk_score, rclr, rbg, f"{risk_label}  ·  Vol ≈ {vol*100:.1f}%")
        with col2:
            dclr = GREEN if div_score >= 70 else (AMBER if div_score >= 40 else RED)
            dbg  = GREEN_BG if div_score >= 70 else (AMBER_BG if div_score >= 40 else RED_BG)
            score_gauge("Diversification", div_score, dclr, dbg,
                        "Spread across categories" if div_score >= 60 else "Concentrated in few categories")
        with col3:
            defc = GREEN if def_score >= 50 else (AMBER if def_score >= 25 else RED)
            defb = GREEN_BG if def_score >= 50 else (AMBER_BG if def_score >= 25 else RED_BG)
            score_gauge("Defensive Strength", def_score, defc, defb,
                        f"{stab}% stability share")

        section("KEY METRICS")
        m1, m2, m3, m4 = st.columns(4, gap="small")
        with m1:
            cclr = GREEN if conc < 40 else (AMBER if conc < 60 else RED)
            cbg  = GREEN_BG if conc < 40 else (AMBER_BG if conc < 60 else RED_BG)
            metric_card("Concentration Risk", f"{conc:.0f}%",
                        "Largest single category", cclr, cbg)
        with m2:
            metric_card("Volatility Exposure", f"{vol*100:.1f}%",
                        "Estimated annualised", PURPLE, PURPLE_BG)
        with m3:
            metric_card("Growth Share", f"{grow}%",
                        "Stocks + Crypto + most ETFs", AMBER, AMBER_BG)
        with m4:
            metric_card("Stability Share", f"{stab}%",
                        "Cash + some ETFs", TEAL, TEAL_BG)

        section("ALLOCATION VIEW")
        c_chart, c_legend = st.columns([1, 1], gap="small")
        with c_chart:
            active = {n: v for n, v in alloc.items() if v > 0}
            st.plotly_chart(donut(list(active.keys()), list(active.values()),
                                  [ASSET_CLR[ASSET_NAMES.index(n)] for n in active],
                                  risk_label.split()[0]),
                            use_container_width=True)
        with c_legend:
            for n, v in sorted(alloc.items(), key=lambda x: x[1], reverse=True):
                if v <= 0: continue
                clr = ASSET_CLR[ASSET_NAMES.index(n)]
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:9px;padding:6px 0;"
                    f"border-bottom:1px solid {BD};'>"
                    f"<div style='width:9px;height:9px;border-radius:50%;background:{clr};flex-shrink:0;'></div>"
                    f"<div style='flex:1;font-family:{FH};font-size:0.85rem;color:{TEXT};font-weight:500;'>{n}</div>"
                    f"<div style='background:{clr}22;color:{clr};font-family:{FM};font-size:0.82rem;"
                    f"font-weight:700;padding:2px 9px;border-radius:4px;'>{v:.1f}%</div></div>",
                    unsafe_allow_html=True,
                )


# ════════════════════════════════════════════════════════════════
# TAB 2 — FINANCIAL HEALTH
# ════════════════════════════════════════════════════════════════
with tab2:
    note("Your income, expenses, and risk-comfort answers determine whether your financial foundation can support your investment strategy.", "info")

    section("INCOME & EXPENSES")
    ie1, ie2, ie3 = st.columns(3, gap="large")
    with ie1:
        st.number_input("Monthly primary income ($)", min_value=0, step=500,
                        key="income_primary")
    with ie2:
        st.number_input("Secondary income ($, optional)", min_value=0, step=250,
                        key="income_secondary")
    with ie3:
        st.number_input("Monthly expenses ($)", min_value=0, step=500,
                        key="expenses_monthly")

    inc = total_income()
    exp = monthly_expenses()

    if inc <= 0:
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        note("Enter your monthly income to see your financial health analysis.", "info")
    else:
        sur = monthly_surplus()
        sr  = savings_rate()
        sp  = spending_pressure()
        fh  = financial_health_score()
        st_rating, st_clr, st_bg = stability_rating(fh)
        cap = risk_capacity_score(fh, sr)
        cap_rating, cap_lvl, cap_clr, cap_bg = capacity_rating(cap)

        section("FINANCIAL STATS")
        s1, s2, s3, s4 = st.columns(4, gap="small")
        with s1:
            metric_card("Monthly Surplus", f"${sur:,.0f}" if sur >= 0 else f"-${abs(sur):,.0f}",
                        "Income − expenses",
                        GREEN if sur > 0 else RED, GREEN_BG if sur > 0 else RED_BG)
        with s2:
            metric_card("Savings Rate", f"{sr*100:.1f}%", "Of total income",
                        GREEN if sr >= 0.20 else (AMBER if sr >= 0.10 else RED),
                        GREEN_BG if sr >= 0.20 else (AMBER_BG if sr >= 0.10 else RED_BG))
        with s3:
            metric_card("Spending Pressure", f"{sp*100:.0f}%", "Expenses / income",
                        GREEN if sp < 0.60 else (AMBER if sp < 0.85 else RED),
                        GREEN_BG if sp < 0.60 else (AMBER_BG if sp < 0.85 else RED_BG))
        with s4:
            metric_card("Total Income", f"${inc:,.0f}", "Primary + secondary", TEXT, BG)

        section("HEALTH SCORES")
        h1, h2 = st.columns(2, gap="small")
        with h1:
            score_gauge("Financial Health Score", fh, st_clr, st_bg,
                        f"Stability: {st_rating}")
        with h2:
            score_gauge("Risk Capacity", cap, cap_clr, cap_bg,
                        f"{cap_rating} capacity to absorb volatility")

        if fh < 30:
            note("Your financial foundation is currently weak. Stabilising expenses and building a savings buffer typically delivers more impact than portfolio adjustments at this stage.", "alert")
        elif fh < 50:
            note("Your financial foundation is moderate. There is room for some investment risk, but caution with high-volatility assets is warranted.", "warn")
        elif cap_lvl == 4:
            note("Strong financial position. Your finances can comfortably absorb a typical equity drawdown without forcing changes to your investment plan.", "good")
        else:
            note(f"Your financial position is {st_rating.lower()}. Risk capacity is {cap_rating.lower()}.", "info")

    # ──────────────────────────────────────────────────────────
    # RISK COMFORT ASSESSMENT (10 questions)
    # ──────────────────────────────────────────────────────────
    section("RISK COMFORT ASSESSMENT", TEAL)
    note("Ten questions to assess your personal comfort with volatility. Live preview updates as you answer.", "info")

    for i, (q, opts) in enumerate(QUESTIONS):
        qk = f"q{i+1}"
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;gap:9px;align-items:flex-start;'>"
                f"<span style='background:{TEAL_BG};color:{TEAL};font-family:{FH};"
                f"font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:4px;"
                f"flex-shrink:0;margin-top:2px;'>{i+1:02d}/10</span>"
                f"<span style='font-family:{FH};font-size:0.95rem;font-weight:600;"
                f"color:{TEXT};line-height:1.4;'>{q}</span></div>",
                unsafe_allow_html=True,
            )
            idx = st.radio(q, list(range(len(opts))),
                           format_func=lambda x, o=opts: o[x],
                           index=st.session_state[qk], key=f"r_{qk}",
                           label_visibility="collapsed")
            st.session_state[qk] = idx

    # Live tolerance preview
    tname, tdata, tscore = get_tolerance_profile()
    tpct = (tscore - 10) / 30 * 100
    st.markdown(
        f"<div style='background:{tdata['bg']};border:1px solid {BD};"
        f"border-left:4px solid {tdata['clr']};border-radius:0 12px 12px 0;"
        f"padding:14px 18px;margin:10px 0;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;'>"
        f"<div>"
        f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};font-weight:600;"
        f"text-transform:uppercase;letter-spacing:0.04em;'>Risk Tolerance Profile</div>"
        f"<div style='font-family:{FH};font-size:1.5rem;font-weight:800;color:{tdata['clr']};"
        f"line-height:1.2;'>{tname}</div></div>"
        f"<div style='font-family:{FM};font-size:0.88rem;color:{MUTED};'>{tscore}/40</div></div>"
        f"<div style='height:6px;background:rgba(0,0,0,0.08);border-radius:3px;margin-top:8px;overflow:hidden;'>"
        f"<div style='width:{tpct:.0f}%;height:100%;background:{tdata['clr']};border-radius:3px;'></div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# TAB 3 — INSIGHTS ENGINE
# ════════════════════════════════════════════════════════════════
with tab3:
    total_pct = total_allocation()
    inc = total_income()

    if total_pct == 0 and inc <= 0:
        note("Complete Portfolio Intelligence and Financial Health first to see your insights.", "info")
    elif total_pct == 0:
        note("Complete Portfolio Intelligence to see your insights.", "info")
    elif inc <= 0:
        note("Complete Financial Health to see your insights.", "info")
    else:
        # Gather state
        alloc = normalized_allocation()
        risk_score = portfolio_risk_score(alloc)
        risk_label, risk_lvl_num = risk_level_label(risk_score)
        p_state = {
            "alloc": alloc,
            "risk_score": risk_score,
            "risk_label": risk_label,
            "risk_level_num": risk_lvl_num,
            "diversification": diversification_score(alloc),
            "concentration": concentration_pct(alloc),
            "defensive_score": defensive_score(alloc),
        }

        fh_score = financial_health_score()
        sr = savings_rate()
        st_rating, _, _ = stability_rating(fh_score)
        cap = risk_capacity_score(fh_score, sr)
        cap_rating, cap_lvl, cap_clr, cap_bg = capacity_rating(cap)
        fh_state = {
            "health_score": fh_score,
            "stability_rating": st_rating,
            "capacity_score": cap,
            "capacity_rating": cap_rating,
            "capacity_level": cap_lvl,
            "capacity_color": cap_clr,
            "capacity_bg": cap_bg,
        }

        tname, tdata, _ = get_tolerance_profile()
        tol_state = {
            "profile": tname,
            "level": tdata["level"],
            "color": tdata["clr"],
            "bg":    tdata["bg"],
        }

        insights = generate_insights(p_state, fh_state, tol_state)
        readiness = investment_readiness(p_state, fh_score, insights)
        stress_pct = stress_preview(alloc)

        # ── HEADLINE VERDICT ────────────────────────────────────
        section("INVESTMENT READINESS")
        # Headline mismatch logic
        risk_vs_cap = p_state["risk_level_num"] - ((cap_lvl - 1) * 4 / 3 + 1)
        if risk_vs_cap >= 1.5:
            headline = "Portfolio risk exceeds your financial capacity"
            head_clr, head_bg = RED, RED_BG
        elif risk_vs_cap <= -1.5:
            headline = "Portfolio is conservative relative to your capacity"
            head_clr, head_bg = TEAL, TEAL_BG
        else:
            headline = "Portfolio aligned with financial capacity"
            head_clr, head_bg = GREEN, GREEN_BG

        st.markdown(
            f"<div style='background:linear-gradient(120deg,{head_bg},{CARD});"
            f"border:1px solid {BD};border-left:4px solid {head_clr};"
            f"border-radius:0 14px 14px 0;padding:18px 22px;margin-bottom:10px;'>"
            f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.04em;'>Headline verdict</div>"
            f"<div style='font-family:{FH};font-size:1.5rem;font-weight:800;color:{head_clr};"
            f"line-height:1.25;margin-top:3px;'>{headline}</div>"
            f"<div style='font-family:{FH};font-size:0.88rem;color:{MUTED};margin-top:5px;'>"
            f"Investment Readiness Score: <strong style='color:{TEXT};'>{readiness}/100</strong>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        # ── THREE-VECTOR DASHBOARD ──────────────────────────────
        if   risk_lvl_num <= 2: rclr, rbg = GREEN, GREEN_BG
        elif risk_lvl_num == 3: rclr, rbg = TEAL,  TEAL_BG
        elif risk_lvl_num == 4: rclr, rbg = AMBER, AMBER_BG
        else:                   rclr, rbg = RED,   RED_BG

        v1, v2, v3 = st.columns(3, gap="small")
        with v1:
            score_gauge("Portfolio Risk", risk_score, rclr, rbg,
                        f"{risk_label}  ·  Level {risk_lvl_num}/5")
        with v2:
            score_gauge("Financial Capacity", cap, cap_clr, cap_bg,
                        f"{cap_rating}  ·  Level {cap_lvl}/4")
        with v3:
            tpct = (quiz_total() - 10) / 30 * 100
            score_gauge("Risk Tolerance", round(tpct), tol_state["color"], tol_state["bg"],
                        f"{tname}  ·  Level {tol_state['level']}/5")

        # ── INTELLIGENT INSIGHTS ────────────────────────────────
        section("INTELLIGENT INSIGHTS", PURPLE)
        for ins in insights:
            cfg = {"alert": (RED_BG, RED), "warn": (AMBER_BG, AMBER),
                   "info":  (PRIMARY_BG, PRIMARY), "good": (GREEN_BG, GREEN)}
            bg, ac = cfg.get(ins["kind"], cfg["info"])
            severity_label = {"alert": "Critical", "warn": "Attention",
                              "info": "Observation", "good": "Strength"}.get(ins["kind"], "")
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BD};border-left:3px solid {ac};"
                f"border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:7px;'>"
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:3px;'>"
                f"<span style='background:{bg};color:{ac};font-family:{FH};font-size:0.65rem;"
                f"font-weight:700;padding:2px 8px;border-radius:3px;text-transform:uppercase;"
                f"letter-spacing:0.04em;'>{severity_label}</span>"
                f"<span style='font-family:{FH};font-size:0.95rem;font-weight:700;color:{TEXT};'>"
                f"{ins['title']}</span></div>"
                f"<div style='font-family:{FH};font-size:0.86rem;color:{MUTED};line-height:1.5;"
                f"padding-left:0;'>{ins['text']}</div></div>",
                unsafe_allow_html=True,
            )

        # ── DOWNSIDE PREVIEW ────────────────────────────────────
        section("DOWNSIDE PREVIEW", AMBER)
        st.markdown(
            f"<div style='background:{AMBER_BG};border:1px solid {BD};border-left:3px solid {AMBER};"
            f"border-radius:0 10px 10px 0;padding:12px 16px;'>"
            f"<div style='font-family:{FH};font-size:0.78rem;color:{MUTED};font-weight:600;"
            f"text-transform:uppercase;letter-spacing:0.04em;margin-bottom:3px;'>Bear market scenario  ·  −30% broad equities</div>"
            f"<div style='font-family:{FH};font-size:1.05rem;color:{TEXT};line-height:1.5;'>"
            f"In a bear-market scenario, your portfolio would fall by an estimated "
            f"<strong style='color:{RED};'>{stress_pct:.1f}%</strong>. "
            f"Historical recovery from this depth has typically taken 1–3 years for diversified portfolios.</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════
st.markdown(
    f"<div style='border-top:1px solid {BD};margin-top:2rem;padding:14px 0 6px;font-family:{FH};"
    f"font-size:0.72rem;color:{DIM};text-align:center;'>"
    f"<strong style='color:{PRIMARY};'>Meridian</strong> &nbsp;·&nbsp; Personal Investment Risk &amp; Financial Intelligence"
    f"<br><span style='font-size:0.66rem;'>Educational purposes only — not personal financial advice — "
    f"consult a licensed financial adviser (AFSL) before investing</span></div>",
    unsafe_allow_html=True,
)
