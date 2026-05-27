"""
Meridian — Investment Risk & Allocation  v6  (Light Green Theme)
Run:  streamlit run meridian_app.py
Deps: streamlit plotly
"""
import math, random
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Meridian", layout="wide",
                   initial_sidebar_state="collapsed")

# ── PALETTE (light green) ─────────────────────────────────────
BG         = "#E6F4EA"
CARD       = "#FFFFFF"
BD         = "#CFE3D5"
TEXT       = "#15231B"
MUTED      = "#5E7167"
DIM        = "#9CB0A3"

PRIMARY    = "#1E8E54"
PRIMARY_BG = "#E4F4EA"
PRIMARY_DK = "#15703F"

GREEN      = "#1E8E54"
GREEN_BG   = "#E4F4EA"
LGREEN     = "#3DA968"
LGREEN_BG  = "#EAF6EE"
AMBER      = "#B7791F"
AMBER_BG   = "#FBF3E2"
RED        = "#C53929"
RED_BG     = "#FBEAE7"
PURPLE     = "#6D4AB8"
PURPLE_BG  = "#F0EBFA"
TEAL       = "#0E7C7B"
TEAL_BG    = "#E0F2F1"
BLUE       = "#2E6FB0"
BLUE_BG    = "#E9F0F8"

FH = "'Plus Jakarta Sans', system-ui, sans-serif"
FM = "'JetBrains Mono', 'Fira Code', monospace"

ASSET_NAMES = ["Australian Shares", "International Shares", "Property & REITs",
               "Fixed Income & Bonds", "Cash & Term Deposits"]
ASSET_KEYS  = ["aus_shares", "intl_shares", "property_reits", "fixed_income", "cash_td"]
ASSET_CLR   = [PRIMARY, TEAL, AMBER, PURPLE, BLUE]

PROFILE_CLR = {
    "Conservative":            TEAL,
    "Moderately Conservative": LGREEN,
    "Balanced":                PRIMARY,
    "Growth":                  PURPLE,
    "Aggressive":              RED,
}
PROFILE_BG = {
    "Conservative":            TEAL_BG,
    "Moderately Conservative": LGREEN_BG,
    "Balanced":                PRIMARY_BG,
    "Growth":                  PURPLE_BG,
    "Aggressive":              RED_BG,
}

CUR_SYM = {"AUD": "A$", "USD": "$", "EUR": "€", "GBP": "£", "SGD": "S$"}

# ── SESSION ───────────────────────────────────────────────────
_defaults = {
    **{f"q{i}": 0 for i in range(1, 11)},
    "risk_score": 0, "risk_profile": "", "profile_done": False,
    "aus_shares": 0, "intl_shares": 0, "property_reits": 0,
    "fixed_income": 0, "cash_td": 0, "currency": "AUD",
    "goal_amount": 1_000_000, "goal_years": 20,
    "monthly_contrib": 2_000, "cgt_rate": 32, "cost_base_pct": 60,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── QUESTIONS ─────────────────────────────────────────────────
QUESTIONS = [
    ("When do you expect to need this money?",
     ["Under 3 years — I may need it soon",
      "3–7 years — medium-term plan",
      "7–15 years — long-term wealth building",
      "15+ years — retirement or generational wealth"],
     "Longer timelines let you ride out downturns. Short timelines demand caution — markets don't always cooperate with your schedule."),
    ("How stable is your income?",
     ["Retired or on a fixed income",
      "Variable — self-employed or contract work",
      "Stable salaried employment",
      "Very secure — government or tenured role"],
     "Stable income means you can hold through a crash without being forced to sell. Variable income may force you to liquidate at the worst moment."),
    ("How many months of expenses do you have in accessible cash?",
     ["Less than 1 month",
      "1–3 months",
      "3–6 months",
      "6 months or more"],
     "Without a cash buffer you risk selling investments in emergencies. This single gap has derailed more portfolios than poor stock selection."),
    ("How would you describe your investment experience?",
     ["None — mostly savings accounts",
      "Basic — I understand shares and managed funds",
      "3+ years of active investing in shares or ETFs",
      "10+ years across multiple asset classes"],
     "Experience builds discipline. Knowing how you actually behaved in 2008 or March 2020 is more reliable than how you think you'd behave."),
    ("If your portfolio fell 30% in 3 months, you would:",
     ["Sell everything to stop the bleeding",
      "Sell part of it to reduce exposure",
      "Hold on and wait for recovery",
      "Add to positions at the lower prices"],
     "Be honest. A 30% drop happened in 2008 and 2020 — it will happen again. What you actually do in that moment determines your long-term outcome."),
    ("What is the primary goal for this investment?",
     ["Protect capital — safety is everything",
      "Modest growth with capital protection as backup",
      "Balanced growth over the medium to long term",
      "Maximum long-term growth — volatility is fine"],
     "Your goal shapes the entire strategy. A retiree drawing income and a 30-year-old accumulating wealth need fundamentally different portfolios."),
    ("Do you expect significant withdrawals within the next 5 years?",
     ["Yes — most of it within 5 years",
      "Yes — a meaningful portion",
      "Possibly — small amounts only",
      "No — capital is fully committed long-term"],
     "Money you need within 5 years should not be in equities. A crash right before withdrawal is the scenario that hurts most."),
    ("How would you describe your current debt?",
     ["High debt relative to income or assets",
      "Moderate — standard mortgage",
      "Low — actively paying it down",
      "Debt free"],
     "Paying off a 20% credit card is a guaranteed 20% return. High-interest debt usually beats any investment return short-term."),
    ("This portfolio is what share of your total net worth?",
     ["Over 75% — this is most of what I own",
      "50–75% of total net worth",
      "25–50% of total net worth",
      "Under 25% — I have significant other assets"],
     "If this is most of your wealth, caution is warranted regardless of other answers. Concentration risk applies across your whole balance sheet."),
    ("Maximum annual loss you could absorb without impacting lifestyle?",
     ["Under 5% — any significant loss is unacceptable",
      "5–15% — moderate drawdown is manageable",
      "15–25% — I understand markets cycle",
      "25% or more — I focus on long-term returns"],
     "Translate this to a dollar figure before answering. Percentages are abstract; a number on your statement is not. When unsure, choose the safer option."),
]

# ── PROFILES ──────────────────────────────────────────────────
PROFILES = {
    "Conservative": {
        "range": (10, 18), "ret": "3–5% p.a.", "ret_mid": 0.04,
        "draw": "5–10%", "draw_mid": 0.075, "horizon": "1–5 years", "vol": 0.05,
        "headline": "Capital preservation. Safety over returns.",
        "desc": "Predominantly bonds and cash with a small equity allocation. Minimal drawdown risk, lower return ceiling. Right for short horizons or low risk tolerance.",
        "targets": {"Australian Shares": 8, "International Shares": 12,
                    "Property & REITs": 5, "Fixed Income & Bonds": 45, "Cash & Term Deposits": 30}},
    "Moderately Conservative": {
        "range": (19, 25), "ret": "4–6% p.a.", "ret_mid": 0.05,
        "draw": "10–15%", "draw_mid": 0.125, "horizon": "3–7 years", "vol": 0.08,
        "headline": "Steady growth with a strong defensive base.",
        "desc": "Fixed income dominates. A measured equity allocation adds inflation-beating returns without significant downside risk.",
        "targets": {"Australian Shares": 15, "International Shares": 20,
                    "Property & REITs": 10, "Fixed Income & Bonds": 40, "Cash & Term Deposits": 15}},
    "Balanced": {
        "range": (26, 31), "ret": "5–8% p.a.", "ret_mid": 0.065,
        "draw": "15–25%", "draw_mid": 0.20, "horizon": "5–10 years", "vol": 0.11,
        "headline": "Equal weight on growth and protection.",
        "desc": "The 60/40 model — equities drive returns, bonds cushion corrections. Accepts short-term volatility for long-term gains.",
        "targets": {"Australian Shares": 25, "International Shares": 30,
                    "Property & REITs": 15, "Fixed Income & Bonds": 22, "Cash & Term Deposits": 8}},
    "Growth": {
        "range": (32, 36), "ret": "7–10% p.a.", "ret_mid": 0.08,
        "draw": "25–35%", "draw_mid": 0.30, "horizon": "7–15 years", "vol": 0.15,
        "headline": "Long-term wealth accumulation. Volatility accepted.",
        "desc": "Equity-heavy with a small defensive buffer. Drawdowns of 25–35% are expected and temporary. Requires patience and a long runway.",
        "targets": {"Australian Shares": 30, "International Shares": 40,
                    "Property & REITs": 15, "Fixed Income & Bonds": 12, "Cash & Term Deposits": 3}},
    "Aggressive": {
        "range": (37, 40), "ret": "8–12% p.a.", "ret_mid": 0.09,
        "draw": "35–50%", "draw_mid": 0.425, "horizon": "15+ years", "vol": 0.19,
        "headline": "Maximum long-term growth. High tolerance required.",
        "desc": "Near-full equity exposure. Suitable for very long horizons, stable income, and investors who can hold through severe corrections without panic.",
        "targets": {"Australian Shares": 35, "International Shares": 45,
                    "Property & REITs": 15, "Fixed Income & Bonds": 5, "Cash & Term Deposits": 0}},
}

STRESS = {
    "Correction  -15%": {
        "label": "-15%  Market Correction",
        "desc": "Typical pullback. Occurs every 3–5 years on average. Markets have historically recovered within 6–18 months.",
        "rec": 1.0,
        "shocks": {"Australian Shares": -0.18, "International Shares": -0.16,
                   "Property & REITs": -0.11, "Fixed Income & Bonds": +0.03, "Cash & Term Deposits": 0.0}},
    "Bear Market  -30%": {
        "label": "-30%  Bear Market",
        "desc": "COVID March 2020 / 2022 rate-shock level. Recovery typically 1–3 years. Defensive assets absorb meaningful impact.",
        "rec": 2.5,
        "shocks": {"Australian Shares": -0.33, "International Shares": -0.30,
                   "Property & REITs": -0.22, "Fixed Income & Bonds": +0.06, "Cash & Term Deposits": 0.0}},
    "GFC Crash  -50%": {
        "label": "-50%  GFC-Level Crash",
        "desc": "2008–09 scenario. ASX fell 54% peak-to-trough; full recovery took ~5 years. Rare but within historical range.",
        "rec": 5.0,
        "shocks": {"Australian Shares": -0.54, "International Shares": -0.50,
                   "Property & REITs": -0.42, "Fixed Income & Bonds": +0.09, "Cash & Term Deposits": 0.0}},
}

# ── PURE FUNCTIONS ────────────────────────────────────────────
def sym():
    return CUR_SYM.get(st.session_state["currency"], "$")

def pv():
    return {n: st.session_state[k] for n, k in zip(ASSET_NAMES, ASSET_KEYS)}

def tpv():
    return sum(st.session_state[k] for k in ASSET_KEYS)

def gprof(s):
    for name, d in PROFILES.items():
        if d["range"][0] <= s <= d["range"][1]:
            return name
    return "Balanced"

def fmt(n):
    if n is None:
        return sym() + "0"
    s = sym()
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{sign}{s}{n / 1e6:.2f}M"
    if n >= 1_000:
        return f"{sign}{s}{n:,.0f}"
    return f"{sign}{s}{n:.0f}"

def calc_health(h, t, total):
    if not total:
        return 0, 0, 0, 0
    gaps = [abs(h.get(a, 0) / total * 100 - t.get(a, 0)) for a in ASSET_NAMES]
    align = max(0.0, 40.0 - sum(gaps) / len(gaps) * 2.2)
    pcts = [h.get(a, 0) / total * 100 for a in ASSET_NAMES]
    nm = sum(1 for p in pcts if p >= 2)
    divers = max(0.0, min(30.0, nm * 6.0) - max(0.0, (max(pcts) - 50) * 0.55))
    cd = (h.get("Cash & Term Deposits", 0) + h.get("Fixed Income & Bonds", 0)) / total * 100
    td = t.get("Cash & Term Deposits", 0) + t.get("Fixed Income & Bonds", 0)
    liq = max(0.0, 30.0 - abs(cd - td) * 1.4)
    return round(align + divers + liq), round(align), round(divers), round(liq)

def run_stress(h, total, sc):
    new_total = 0.0
    breakdown = {}
    for a in ASSET_NAMES:
        v = h.get(a, 0)
        sv = v * (1 + sc["shocks"].get(a, 0))
        new_total += sv
        breakdown[a] = sv - v
    return new_total, new_total - total, breakdown

def run_mc(cur, mo, yrs, pname, n=1000):
    P = {
        "Conservative": (0.040, 0.050),
        "Moderately Conservative": (0.050, 0.080),
        "Balanced": (0.065, 0.110),
        "Growth": (0.080, 0.150),
        "Aggressive": (0.090, 0.190),
    }
    mu, sig = P.get(pname, (0.065, 0.110))
    mm = mu / 12
    ms = sig / math.sqrt(12)
    random.seed(42)
    ydata = [[float(cur)] * n for _ in range(yrs + 1)]
    for s in range(n):
        v = float(cur)
        for yr in range(1, yrs + 1):
            for _ in range(12):
                v = max(0.0, v * (1 + random.gauss(mm, ms)) + mo)
            ydata[yr][s] = v
    finals = sorted(ydata[yrs])

    def pct(x):
        return finals[max(0, int(x * n) - 1)]

    ym   = {y: sorted(ydata[y])[n // 2] for y in range(yrs + 1)}
    yp10 = {y: sorted(ydata[y])[max(0, int(0.1 * n) - 1)] for y in range(yrs + 1)}
    yp90 = {y: sorted(ydata[y])[min(n - 1, int(0.9 * n))] for y in range(yrs + 1)}
    return pct(0.10), pct(0.25), pct(0.50), pct(0.75), pct(0.90), ym, yp10, yp90

def smart_alloc(money, h, t, total):
    pt = total + money
    needs = {}
    for a in ASSET_NAMES:
        g = pt * t.get(a, 0) / 100 - h.get(a, 0)
        if g > 0:
            needs[a] = g
    if not needs:
        return {a: 0 for a in ASSET_NAMES}
    tn = sum(needs.values())
    res = {}
    running = 0
    items = list(needs.items())
    for i, (a, g) in enumerate(items):
        if i == len(items) - 1:
            res[a] = money - running
        else:
            al = round(money * g / tn / 100) * 100
            res[a] = al
            running += al
    return res

def cgt_estimate(sell, cb_pct, rate):
    gain = max(0.0, sell - sell * cb_pct / 100)
    return gain * 0.5 * rate / 100

# ── CSS ───────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: {BG} !important;
    font-family: {FH};
    color: {TEXT} !important;
}}
/* Default text dark everywhere (beats a dark theme config). Inline-styled spans
   and the white button text keep their own colours because those use inline styles. */
.stApp, .stApp p, .stApp label, .stApp li,
[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {{
    color: {TEXT};
}}
.block-container {{ padding: 1rem 1.6rem 3rem; max-width: 1100px; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}
* {{ box-sizing: border-box; }}

h1, h2, h3, h4 {{ font-family: {FH} !important; font-weight: 700 !important; color: {TEXT} !important; margin: 0 !important; }}

/* Tighten vertical gaps */
[data-testid="stVerticalBlock"] {{ gap: 0.5rem !important; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 10px !important; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 0; border-bottom: 1px solid {BD}; background: transparent; padding: 0; }}
.stTabs [data-baseweb="tab"] {{
    font-family: {FM}; font-size: 0.65rem; letter-spacing: 0.07em; text-transform: uppercase;
    color: {MUTED}; background: transparent; border: none;
    border-bottom: 2px solid transparent; padding: 9px 16px; margin: 0;
}}
.stTabs [aria-selected="true"] {{
    color: {PRIMARY} !important; border-bottom: 2px solid {PRIMARY} !important;
    background: transparent !important; font-weight: 600 !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 1rem; background: transparent; }}

/* Inputs */
div[data-testid="stNumberInput"] label, div[data-testid="stSelectbox"] label {{
    font-family: {FM} !important; font-size: 0.6rem !important;
    letter-spacing: 0.09em !important; text-transform: uppercase !important; color: {MUTED} !important;
}}
.stNumberInput input {{
    background: {CARD} !important; border: 1px solid {BD} !important; border-radius: 6px !important;
    color: {TEXT} !important; font-family: {FM} !important; font-size: 0.88rem !important;
    padding: 6px 10px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}}
.stNumberInput input:focus {{
    border-color: {PRIMARY} !important; box-shadow: 0 0 0 3px rgba(30,142,84,0.14) !important; outline: none !important;
}}
.stNumberInput button {{ background: {CARD} !important; border-color: {BD} !important; border-radius: 4px !important; }}
.stSelectbox > div > div {{
    background: {CARD} !important; border: 1px solid {BD} !important; border-radius: 6px !important;
    font-family: {FH} !important; font-size: 0.85rem !important; box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}}
[role="listbox"] *, [role="option"] {{ background: {CARD} !important; color: {TEXT} !important; font-family: {FH} !important; }}

/* RADIO — force every text node inside the radio to be dark, no matter how Streamlit nests it.
   The radio circle uses border/background (not color), so this wildcard is safe. */
div[data-testid="stRadio"] *,
[data-testid="stRadio"] label *,
[data-testid="stRadio"] [role="radiogroup"] * {{
    color: {TEXT} !important;
}}
div[data-testid="stRadio"] label p,
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
    color: {TEXT} !important;
    font-family: {FH} !important;
    font-size: 0.875rem !important;
    font-weight: 400 !important;
    margin: 0 !important;
    line-height: 1.45 !important;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label {{
    padding: 7px 10px;
    border-radius: 7px;
    margin-bottom: 2px;
    transition: background 0.12s ease;
    cursor: pointer;
}}
div[data-testid="stRadio"] [role="radiogroup"] > label:hover {{
    background: {PRIMARY_BG};
}}
/* the group's own (collapsed) label */
div[data-testid="stRadio"] > label {{
    font-family: {FM} !important; font-size: 0.58rem !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important; color: {MUTED} !important;
}}

/* Button */
.stButton > button {{
    background: {PRIMARY} !important; color: #ffffff !important; border: none !important;
    border-radius: 7px !important; font-family: {FH} !important; font-size: 0.9rem !important;
    font-weight: 600 !important; padding: 9px 24px !important;
    box-shadow: 0 2px 10px rgba(30,142,84,0.30) !important; transition: all 0.15s !important;
}}
.stButton > button:hover {{ background: {PRIMARY_DK} !important; transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(30,142,84,0.38) !important; }}

/* Slider */
.stSlider label {{
    font-family: {FM} !important; font-size: 0.6rem !important;
    letter-spacing: 0.09em !important; text-transform: uppercase !important; color: {MUTED} !important;
}}
.stSlider [data-baseweb="slider"] [role="slider"] {{ background: {PRIMARY} !important; }}

hr {{ border: none; border-top: 1px solid {BD}; margin: 0.8rem 0; }}
</style>
""", unsafe_allow_html=True)


# ── UI HELPERS ────────────────────────────────────────────────
def note(text, kind="info"):
    cfg = {
        "info":  (PRIMARY_BG, PRIMARY),
        "good":  (GREEN_BG,   GREEN),
        "warn":  (AMBER_BG,   AMBER),
        "alert": (RED_BG,     RED),
    }
    bg, ac = cfg.get(kind, cfg["info"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {ac};border-radius:0 6px 6px 0;"
        f"padding:8px 12px;margin:5px 0;font-family:{FH};font-size:0.85rem;"
        f"color:{TEXT};line-height:1.55;'>{text}</div>",
        unsafe_allow_html=True,
    )


def sec(label, color=PRIMARY):
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;margin:14px 0 7px;'>"
        f"<span style='font-family:{FM};font-size:0.58rem;letter-spacing:0.12em;"
        f"text-transform:uppercase;color:{color};white-space:nowrap;font-weight:500;'>{label}</span>"
        f"<div style='flex:1;height:1px;background:{BD};'></div></div>",
        unsafe_allow_html=True,
    )


def kpis(cards):
    cols = st.columns(len(cards), gap="small")
    for col, (lbl, val, sub, ac, bg) in zip(cols, cards):
        with col:
            st.markdown(
                f"<div style='background:{bg};border:1px solid {BD};border-top:3px solid {ac};"
                f"border-radius:0 0 8px 8px;padding:10px 12px;min-width:0;'>"
                f"<div style='font-family:{FM};font-size:0.56rem;letter-spacing:0.1em;"
                f"text-transform:uppercase;color:{MUTED};margin-bottom:3px;"
                f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{lbl}</div>"
                f"<div style='font-family:{FM};font-size:1.1rem;color:{ac};font-weight:600;"
                f"line-height:1.25;word-break:break-word;'>{val}</div>"
                f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};margin-top:2px;"
                f"line-height:1.35;overflow-wrap:break-word;'>{sub}</div></div>",
                unsafe_allow_html=True,
            )


def tbl(headers, rows):
    hdr = "".join(
        f"<th style='text-align:left;padding:6px 10px;background:{BG};font-family:{FM};"
        f"font-size:0.56rem;text-transform:uppercase;letter-spacing:0.09em;color:{MUTED};"
        f"font-weight:500;white-space:nowrap;border-bottom:1px solid {BD};'>{h}</th>"
        for h in headers
    )
    body = ""
    for i, row in enumerate(rows):
        rbg = CARD if i % 2 == 0 else BG
        cells = "".join(
            f"<td style='padding:7px 10px;font-family:{FH};font-size:0.82rem;color:{TEXT};"
            f"background:{rbg};border-bottom:1px solid {BD};word-break:break-word;"
            f"overflow-wrap:break-word;max-width:180px;'>{c}</td>"
            for c in row
        )
        body += f"<tr>{cells}</tr>"
    st.markdown(
        f"<div style='border:1px solid {BD};border-radius:8px;overflow:hidden;overflow-x:auto;"
        f"margin:5px 0 12px;box-shadow:0 1px 4px rgba(0,0,0,0.05);'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.64,
        marker=dict(colors=colors, line=dict(color="#fff", width=2)),
        textinfo="label+percent",
        textfont=dict(family="Plus Jakarta Sans, sans-serif", size=10, color=TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    ))
    ann = [dict(text=center, x=0.5, y=0.5,
                font=dict(size=11, family="JetBrains Mono", color=TEXT),
                showarrow=False)] if center else []
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=8, b=8, l=8, r=8), height=240, showlegend=False, annotations=ann,
    )
    return fig


def bar_pair(x, y_cur, y_tgt):
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Current", x=x, y=y_cur, marker_color=AMBER, marker_line_width=0,
                         hovertemplate="%{x}<br>Current: %{y:.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(name="Target", x=x, y=y_tgt, marker_color=PRIMARY, marker_line_width=0,
                         hovertemplate="%{x}<br>Target: %{y:.1f}%<extra></extra>"))
    fig.update_layout(
        barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=8, b=8, l=8, r=8), height=240,
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, orientation="h", y=1.1,
                    font=dict(family="JetBrains Mono", size=9, color=MUTED)),
        xaxis=dict(showgrid=False, tickfont=dict(family="JetBrains Mono", size=8, color=MUTED)),
        yaxis=dict(showgrid=True, gridcolor=BD,
                   tickfont=dict(family="JetBrains Mono", size=8, color=MUTED), ticksuffix="%"),
        bargap=0.22, bargroupgap=0.06,
    )
    return fig


def action_card(title, amount_str, cur_pct, tgt_pct, kind, priority, extra=""):
    ac   = RED if kind == "sell" else GREEN
    bg   = RED_BG if kind == "sell" else GREEN_BG
    verb = "Sell" if kind == "sell" else "Buy"
    pri_html = (
        f"<span style='font-family:{FM};font-size:0.56rem;letter-spacing:0.09em;"
        f"text-transform:uppercase;color:{ac};margin-top:3px;display:block;'>{priority}</span>"
        if priority else ""
    )
    extra_html = f"<span style='color:{MUTED};'> &nbsp;|&nbsp; {extra}</span>" if extra else ""
    st.markdown(
        f"<div style='background:{CARD};border:1px solid {BD};border-radius:8px;"
        f"border-left:3px solid {ac};padding:10px 14px;margin-bottom:6px;"
        f"box-shadow:0 1px 4px rgba(0,0,0,0.05);'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;'>"
        f"<span style='font-family:{FH};font-size:0.9rem;font-weight:600;color:{TEXT};"
        f"min-width:0;overflow-wrap:break-word;'>{title}</span>"
        f"<span style='background:{bg};color:{ac};font-family:{FM};font-size:0.82rem;"
        f"font-weight:600;padding:2px 10px;border-radius:4px;white-space:nowrap;'>{verb} {amount_str}</span></div>"
        f"<div style='font-family:{FM};font-size:0.7rem;color:{MUTED};margin-top:4px;'>"
        f"{cur_pct:.1f}% &rarr; {tgt_pct:.0f}%{extra_html}</div>{pri_html}</div>",
        unsafe_allow_html=True,
    )


# ── HEADER ────────────────────────────────────────────────────
p_done = st.session_state["profile_done"]
h_done = tpv() > 0

hl, hr = st.columns([7, 1], gap="small")
with hl:
    st.markdown(
        f"<div style='padding:12px 0 6px;border-bottom:2px solid {PRIMARY};margin-bottom:10px;'>"
        f"<div style='display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;'>"
        f"<span style='font-family:{FM};font-size:1.05rem;font-weight:600;color:{PRIMARY};"
        f"letter-spacing:-0.01em;'>Meridian</span>"
        f"<span style='font-family:{FM};font-size:0.62rem;color:{MUTED};letter-spacing:0.06em;'>"
        f"Investment Risk &amp; Allocation &nbsp;·&nbsp; v6 green</span></div>"
        f"<div style='display:flex;flex-wrap:wrap;gap:5px;margin-top:7px;'>"
        + "".join(
            f"<span style='font-family:{FM};font-size:0.58rem;letter-spacing:0.06em;"
            f"text-transform:uppercase;padding:2px 8px;border-radius:3px;"
            f"background:{(PRIMARY if done else BD)};color:{('#fff' if done else MUTED)};'>"
            f"{'+ ' if done else ''}{lbl}</span>"
            for lbl, done in [
                ("Profile", p_done), ("Portfolio", h_done),
                ("Analysis", p_done and h_done), ("Rebalancing", p_done and h_done),
                ("Stress Test", p_done and h_done), ("Goals", p_done and h_done),
            ]
        )
        + "</div></div>",
        unsafe_allow_html=True,
    )
with hr:
    cur_list = list(CUR_SYM.keys())
    st.markdown("<div style='padding-top:12px;'>", unsafe_allow_html=True)
    st.selectbox("currency", cur_list, index=cur_list.index(st.session_state["currency"]),
                 key="currency", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    f"<div style='font-family:{FM};font-size:0.58rem;color:{DIM};padding:3px 0 8px;"
    f"border-bottom:1px solid {BD};margin-bottom:4px;'>"
    f"Educational purposes only — not personal financial advice — consult a licensed adviser (AFSL)</div>",
    unsafe_allow_html=True,
)

# ── TABS ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Risk Assessment", "Portfolio", "Analysis", "Rebalancing", "Stress Test", "Goal Projections",
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — RISK ASSESSMENT
# ══════════════════════════════════════════════════════════════
with tab1:
    note("Answer all 10 questions honestly. Your provisional profile updates live as you go — accuracy here determines the quality of everything that follows.", "info")

    total_score = 0
    for i, (q, opts, insight) in enumerate(QUESTIONS):
        qk = f"q{i + 1}"
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;gap:9px;align-items:flex-start;'>"
                f"<span style='background:{PRIMARY_BG};color:{PRIMARY};font-family:{FM};"
                f"font-size:0.6rem;font-weight:700;padding:2px 7px;border-radius:4px;"
                f"flex-shrink:0;margin-top:2px;'>{i + 1:02d}/{len(QUESTIONS)}</span>"
                f"<span style='font-family:{FH};font-size:0.95rem;font-weight:600;"
                f"color:{TEXT};line-height:1.4;'>{q}</span></div>",
                unsafe_allow_html=True,
            )
            idx = st.radio(
                q, list(range(len(opts))),
                format_func=lambda x, o=opts: o[x],
                index=st.session_state[qk], key=f"r_{qk}",
                label_visibility="collapsed",
            )
            st.session_state[qk] = idx
            total_score += idx + 1
            st.markdown(
                f"<div style='font-family:{FH};font-size:0.78rem;color:{MUTED};line-height:1.5;"
                f"border-top:1px solid {BD};padding-top:7px;'>"
                f"<strong style='color:{PRIMARY};'>Why this matters &mdash;</strong> {insight}</div>",
                unsafe_allow_html=True,
            )

    # Live provisional profile preview
    prov = gprof(total_score)
    prov_clr = PROFILE_CLR[prov]
    prov_bg  = PROFILE_BG[prov]
    prov_pct = ((total_score - 10) / 30) * 100
    st.markdown(
        f"<div style='background:{prov_bg};border:1px solid {BD};border-left:4px solid {prov_clr};"
        f"border-radius:0 10px 10px 0;padding:12px 16px;margin:10px 0;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;'>"
        f"<div>"
        f"<div style='font-family:{FM};font-size:0.56rem;letter-spacing:0.1em;"
        f"text-transform:uppercase;color:{MUTED};'>Live preview &mdash; updates as you answer</div>"
        f"<div style='font-family:{FH};font-size:1.3rem;font-weight:700;color:{prov_clr};'>{prov}</div>"
        f"</div>"
        f"<div style='font-family:{FM};font-size:0.85rem;color:{MUTED};white-space:nowrap;'>"
        f"{total_score}/40</div></div>"
        f"<div style='height:6px;background:rgba(0,0,0,0.07);border-radius:3px;margin-top:8px;overflow:hidden;'>"
        f"<div style='width:{prov_pct:.0f}%;height:100%;background:{prov_clr};border-radius:3px;'></div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    col_b, _ = st.columns([2, 5])
    with col_b:
        if st.button("Lock in my profile"):
            st.session_state["risk_score"]   = total_score
            st.session_state["risk_profile"] = prov
            st.session_state["profile_done"] = True
            st.rerun()

    if p_done:
        pname = st.session_state["risk_profile"]
        prof  = PROFILES[pname]
        pac   = PROFILE_CLR[pname]
        pbg   = PROFILE_BG[pname]
        score = st.session_state["risk_score"]
        pct   = ((score - 10) / 30) * 100
        tgts  = prof["targets"]
        tv    = tpv()

        sec("LOCKED PROFILE", pac)
        st.markdown(
            f"<div style='background:{pbg};border:1px solid {BD};border-left:4px solid {pac};"
            f"border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:8px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;"
            f"gap:8px;flex-wrap:wrap;margin-bottom:5px;'><div>"
            f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;"
            f"text-transform:uppercase;color:{MUTED};margin-bottom:3px;'>Risk Profile</div>"
            f"<div style='font-family:{FH};font-size:1.5rem;font-weight:700;color:{pac};"
            f"line-height:1.2;'>{pname}</div>"
            f"<div style='font-family:{FH};font-size:0.82rem;color:{MUTED};margin-top:2px;'>"
            f"{prof['headline']}</div></div>"
            f"<span style='font-family:{FM};font-size:0.75rem;color:{MUTED};white-space:nowrap;'>"
            f"Score: {score}/40</span></div>"
            f"<div style='height:4px;background:rgba(0,0,0,0.08);border-radius:2px;overflow:hidden;margin-bottom:8px;'>"
            f"<div style='width:{pct:.0f}%;height:100%;background:{pac};'></div></div>"
            f"<div style='font-family:{FH};font-size:0.83rem;color:{TEXT};line-height:1.55;opacity:0.85;'>"
            f"{prof['desc']}</div></div>",
            unsafe_allow_html=True,
        )

        if tv > 0:
            kpis([
                ("Expected return", prof["ret"], "Historical p.a.", pac, pbg),
                ("Max drawdown", prof["draw"], "Typical correction", RED, RED_BG),
                ("Dollar drawdown", fmt(tv * prof["draw_mid"]), "At current value", RED, RED_BG),
                ("Min horizon", prof["horizon"], "Recommended", MUTED, BG),
            ])
        else:
            kpis([
                ("Expected return", prof["ret"], "Historical p.a.", pac, pbg),
                ("Max drawdown", prof["draw"], "Typical correction", RED, RED_BG),
                ("Min horizon", prof["horizon"], "Recommended", MUTED, BG),
            ])

        sec("TARGET ALLOCATION", pac)
        at = {k: v for k, v in tgts.items() if v > 0}
        c1, c2 = st.columns(2, gap="small")
        with c1:
            st.plotly_chart(donut(list(at.keys()), list(at.values()),
                                  [ASSET_CLR[ASSET_NAMES.index(k)] for k in at]),
                            use_container_width=True)
        with c2:
            for an, pv2 in tgts.items():
                clr = ASSET_CLR[ASSET_NAMES.index(an)]
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px;padding:5px 0;"
                    f"border-bottom:1px solid {BD};min-width:0;'>"
                    f"<div style='width:8px;height:8px;border-radius:50%;background:{clr};flex-shrink:0;'></div>"
                    f"<div style='font-family:{FH};font-size:0.82rem;color:{TEXT};flex:1;min-width:0;"
                    f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{an}</div>"
                    f"<div style='background:{clr}22;color:{clr};font-family:{FM};font-size:0.78rem;"
                    f"font-weight:600;padding:2px 8px;border-radius:3px;flex-shrink:0;'>{pv2}%</div></div>",
                    unsafe_allow_html=True,
                )


# ══════════════════════════════════════════════════════════════
# TAB 2 — PORTFOLIO
# ══════════════════════════════════════════════════════════════
with tab2:
    if not p_done:
        note("Complete the Risk Assessment first.", "info")
    else:
        note("Enter current market value for each asset class — super, direct shares, ETFs, property equity, bonds, and cash. Partial inputs will skew the analysis.", "info")
        sec("HOLDINGS")
        descs = [
            "ASX shares, AU equity ETFs, managed funds",
            "Global ETFs (S&P 500, MSCI World), international funds",
            "Investment property equity, A-REITs, global REITs",
            "Govt & corp bonds, bond ETFs, term deposits 1yr+",
            "Savings accounts, term deposits under 1yr, offset accounts",
        ]
        cbgs = [PRIMARY_BG, TEAL_BG, AMBER_BG, PURPLE_BG, BLUE_BG]
        ca, cb = st.columns(2, gap="large")
        for i, (an, key, desc) in enumerate(zip(ASSET_NAMES, ASSET_KEYS, descs)):
            col = ca if i < 3 else cb
            with col:
                clr = ASSET_CLR[i]
                st.markdown(
                    f"<div style='background:{cbgs[i]};border-left:3px solid {clr};"
                    f"border-radius:0 6px 6px 0;padding:7px 10px;margin-bottom:3px;'>"
                    f"<div style='font-family:{FH};font-size:0.85rem;font-weight:600;color:{TEXT};'>{an}</div>"
                    f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};'>{desc}</div></div>",
                    unsafe_allow_html=True,
                )
                st.number_input(an, min_value=0, step=1000, key=key, label_visibility="collapsed")

        total = tpv()
        if not total:
            note("Enter holdings above to see your allocation breakdown.", "info")
        else:
            holdings = pv()
            active   = {k: v for k, v in holdings.items() if v > 0}
            pname    = st.session_state["risk_profile"]
            tgts     = PROFILES[pname]["targets"]
            hs, ha, hd, hl = calc_health(holdings, tgts, total)

            sec("PORTFOLIO HEALTH")
            hclr = GREEN if hs >= 75 else (AMBER if hs >= 50 else RED)
            hbg  = GREEN_BG if hs >= 75 else (AMBER_BG if hs >= 50 else RED_BG)
            hlbl = "On track" if hs >= 75 else ("Needs attention" if hs >= 50 else "Action required")

            h1, h2 = st.columns([1, 2], gap="small")
            with h1:
                st.markdown(
                    f"<div style='background:{hbg};border:1px solid {BD};border-radius:10px;"
                    f"padding:14px;text-align:center;'>"
                    f"<div style='font-family:{FM};font-size:0.56rem;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{MUTED};margin-bottom:6px;'>Health Score</div>"
                    f"<div style='font-family:{FM};font-size:2.8rem;font-weight:600;color:{hclr};line-height:1;'>{hs}</div>"
                    f"<div style='font-family:{FM};font-size:0.6rem;color:{MUTED};'>/100</div>"
                    f"<div style='background:{hclr};color:#fff;font-family:{FH};font-size:0.75rem;"
                    f"font-weight:600;padding:3px 12px;border-radius:3px;margin-top:8px;display:inline-block;'>{hlbl}</div>"
                    f"<div style='height:4px;background:rgba(0,0,0,0.08);border-radius:2px;margin-top:10px;overflow:hidden;'>"
                    f"<div style='width:{hs}%;height:100%;background:{hclr};'></div></div></div>",
                    unsafe_allow_html=True,
                )
            with h2:
                for lbl, scv, tot, tip_txt in [
                    ("Alignment", ha, 40, f"{ha}/40 — gap vs {pname} target"),
                    ("Diversification", hd, 30, f"{hd}/30 — spread across asset classes"),
                    ("Defensive buffer", hl, 30, f"{hl}/30 — cash & bonds vs target"),
                ]:
                    bar = scv / tot * 100
                    c2  = GREEN if bar >= 70 else (AMBER if bar >= 40 else RED)
                    c2bg = GREEN_BG if bar >= 70 else (AMBER_BG if bar >= 40 else RED_BG)
                    st.markdown(
                        f"<div style='background:{c2bg};border:1px solid {BD};border-radius:8px;"
                        f"padding:8px 12px;margin-bottom:5px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;gap:8px;'>"
                        f"<span style='font-family:{FH};font-size:0.83rem;font-weight:600;color:{TEXT};'>{lbl}</span>"
                        f"<span style='background:{c2};color:#fff;font-family:{FM};font-size:0.68rem;"
                        f"font-weight:600;padding:1px 7px;border-radius:3px;white-space:nowrap;'>{scv}/{tot}</span></div>"
                        f"<div style='height:4px;background:rgba(0,0,0,0.08);border-radius:2px;overflow:hidden;margin-bottom:4px;'>"
                        f"<div style='width:{bar:.0f}%;height:100%;background:{c2};'></div></div>"
                        f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};'>{tip_txt}</div></div>",
                        unsafe_allow_html=True,
                    )

            if hs >= 75:
                note("Portfolio is well-aligned to your risk profile. Review quarterly to maintain balance.", "good")
            elif ha < 20:
                note(f"Significant deviation from {pname} target allocation. See the Rebalancing tab for specific actions.", "alert")
            elif hd < 15:
                note("High concentration in a single asset class. A sharp correction has outsized impact on total wealth.", "warn")
            else:
                note("Some gaps to close. The Rebalancing tab shows the most tax-efficient path.", "warn")

            sec("CURRENT ALLOCATION")
            kpis([
                ("Total portfolio", fmt(total), "All asset classes", TEXT, BG),
                ("Asset classes", str(len(active)), "of 5 held", PRIMARY, PRIMARY_BG),
                ("Largest position", max(active, key=active.get)[:14], f"{max(active.values()) / total * 100:.0f}%", AMBER, AMBER_BG),
                ("Health score", f"{hs}/100", "Alignment · Spread", hclr, hbg),
            ])
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2, gap="small")
            with c1:
                st.plotly_chart(donut(list(active.keys()), list(active.values()),
                                      [ASSET_CLR[ASSET_NAMES.index(k)] for k in active], fmt(total)),
                                use_container_width=True)
            with c2:
                for an in sorted(holdings, key=lambda x: holdings[x], reverse=True):
                    v = holdings[an]
                    if not v:
                        continue
                    pct2 = v / total * 100
                    clr  = ASSET_CLR[ASSET_NAMES.index(an)]
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:8px;padding:5px 0;"
                        f"border-bottom:1px solid {BD};min-width:0;'>"
                        f"<div style='width:8px;height:8px;border-radius:50%;background:{clr};flex-shrink:0;'></div>"
                        f"<div style='font-family:{FH};font-size:0.82rem;color:{TEXT};flex:1;min-width:0;"
                        f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{an}</div>"
                        f"<div style='font-family:{FM};font-size:0.7rem;color:{MUTED};flex-shrink:0;margin-right:5px;'>{pct2:.1f}%</div>"
                        f"<div style='font-family:{FM};font-size:0.8rem;font-weight:600;color:{TEXT};flex-shrink:0;'>{fmt(v)}</div></div>",
                        unsafe_allow_html=True,
                    )

            for an, v in holdings.items():
                if v and v / total * 100 > 60:
                    note(f"{an} is {v / total * 100:.0f}% of your portfolio. See the Stress Test tab for dollar-impact analysis.", "warn")
                    break


# ══════════════════════════════════════════════════════════════
# TAB 3 — ANALYSIS
# ══════════════════════════════════════════════════════════════
with tab3:
    if not p_done:
        note("Complete the Risk Assessment first.", "info")
    elif not tpv():
        note("Enter holdings in the Portfolio tab first.", "info")
    else:
        pname    = st.session_state["risk_profile"]
        tgts     = PROFILES[pname]["targets"]
        holdings = pv()
        total    = tpv()
        pac      = PROFILE_CLR[pname]
        pbg      = PROFILE_BG[pname]

        st.markdown(
            f"<div style='background:{pbg};border-left:3px solid {pac};border-radius:0 6px 6px 0;"
            f"padding:8px 12px;margin-bottom:6px;'>"
            f"<span style='font-family:{FH};font-size:0.85rem;color:{TEXT};'>"
            f"Profile: <strong style='color:{pac};'>{pname}</strong> — comparing your current allocation to target.</span></div>",
            unsafe_allow_html=True,
        )

        sec("CURRENT VS TARGET")
        short = [a.split("&")[0].strip()[:12] for a in ASSET_NAMES]
        st.plotly_chart(bar_pair(short,
                                 [holdings.get(a, 0) / total * 100 for a in ASSET_NAMES],
                                 [tgts.get(a, 0) for a in ASSET_NAMES]),
                        use_container_width=True)

        sec("GAP ANALYSIS")
        rows, overs, unders = [], [], []
        for an in ASSET_NAMES:
            cp  = holdings.get(an, 0) / total * 100
            tp  = tgts.get(an, 0)
            gap = cp - tp
            cv  = holdings.get(an, 0)
            tv2 = total * tp / 100
            if gap > 5:
                st2 = f"<span style='color:{RED};font-family:{FM};font-size:0.75rem;font-weight:600;'>+{gap:.1f}% over</span>"
                overs.append((an, gap))
            elif gap < -5:
                st2 = f"<span style='color:{AMBER};font-family:{FM};font-size:0.75rem;font-weight:600;'>{gap:.1f}% under</span>"
                unders.append((an, gap))
            else:
                st2 = f"<span style='color:{GREEN};font-family:{FM};font-size:0.75rem;font-weight:600;'>on target</span>"
            rows.append([an, f"{cp:.1f}%", f"{tp:.0f}%", st2, fmt(cv), fmt(tv2), fmt(cv - tv2)])
        tbl(["Asset", "Current", "Target", "Status", "Value", "Target Value", "Gap"], rows)

        if overs:
            b = max(overs, key=lambda x: x[1])
            note(f"Largest overweight: {b[0]} at +{b[1]:.1f}%. Common when high-performing assets drift up without rebalancing. See Rebalancing tab.", "warn")
        if unders:
            b = min(unders, key=lambda x: x[1])
            note(f"Largest underweight: {b[0]} at {abs(b[1]):.1f}% below target. Defensive underweights increase drawdown risk. Prioritise new contributions here.", "warn")
        if not overs and not unders:
            note("Portfolio is well-aligned to your risk profile. Review quarterly.", "good")

        sec("VISUAL COMPARISON")
        cl, cr = st.columns(2, gap="small")
        with cl:
            st.markdown(f"<div style='font-family:{FM};font-size:0.56rem;letter-spacing:0.1em;"
                        f"text-transform:uppercase;color:{MUTED};text-align:center;margin-bottom:4px;'>Current</div>",
                        unsafe_allow_html=True)
            a_a = {k: v for k, v in holdings.items() if v > 0}
            st.plotly_chart(donut(list(a_a.keys()), list(a_a.values()),
                                  [ASSET_CLR[ASSET_NAMES.index(k)] for k in a_a], "Current"),
                            use_container_width=True)
        with cr:
            st.markdown(f"<div style='font-family:{FM};font-size:0.56rem;letter-spacing:0.1em;"
                        f"text-transform:uppercase;color:{MUTED};text-align:center;margin-bottom:4px;'>Target — {pname}</div>",
                        unsafe_allow_html=True)
            t_a = {k: v for k, v in tgts.items() if v > 0}
            st.plotly_chart(donut(list(t_a.keys()), list(t_a.values()),
                                  [ASSET_CLR[ASSET_NAMES.index(k)] for k in t_a], pname[:4] + "."),
                            use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 4 — REBALANCING
# ══════════════════════════════════════════════════════════════
with tab4:
    if not p_done:
        note("Complete the Risk Assessment first.", "info")
    elif not tpv():
        note("Enter holdings in the Portfolio tab first.", "info")
    else:
        pname    = st.session_state["risk_profile"]
        tgts     = PROFILES[pname]["targets"]
        holdings = pv()
        total    = tpv()

        note("Rebalancing: sell what has drifted overweight, buy what is underweight. Prioritise super first (no CGT). Use new contributions where possible to avoid taxable events.", "info")

        sec("TAX SETTINGS", AMBER)
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.session_state["cgt_rate"] = st.slider("Marginal tax rate (%)", 0, 47, int(st.session_state["cgt_rate"]), 1)
        with c2:
            st.session_state["cost_base_pct"] = st.slider("Cost base as % of current value", 20, 100,
                                                          int(st.session_state["cost_base_pct"]), 5,
                                                          help="e.g. bought at $50k, now worth $100k → set to 50%")

        sells, buys, holds = [], [], []
        for an in ASSET_NAMES:
            cv   = holdings.get(an, 0)
            cp   = cv / total * 100
            tp   = tgts.get(an, 0)
            tv2  = total * tp / 100
            diff = cv - tv2
            gap  = cp - tp
            if gap > 2:
                sells.append((an, diff, cp, tp))
            elif gap < -2:
                buys.append((an, abs(diff), cp, tp))
            else:
                holds.append((an, cp, tp))
        sells.sort(key=lambda x: x[1], reverse=True)
        buys.sort(key=lambda x: x[1], reverse=True)

        if sells:
            sec("REDUCE — OVERWEIGHT", RED)
            for i, (an, amt, cp, tp) in enumerate(sells):
                cgt_e = cgt_estimate(amt, st.session_state["cost_base_pct"], st.session_state["cgt_rate"])
                action_card(an, fmt(amt), cp, tp, "sell",
                            "High priority" if i == 0 else "",
                            f"Est. CGT: {fmt(cgt_e)}  |  Net: {fmt(amt - cgt_e)}")

        if buys:
            sec("INCREASE — UNDERWEIGHT", GREEN)
            for i, (an, amt, cp, tp) in enumerate(buys):
                action_card(an, fmt(amt), cp, tp, "buy", "High priority" if i == 0 else "")

        if holds:
            sec("HOLD — ON TARGET", MUTED)
            hold_html = "  &middot;  ".join(
                f"<span style='color:{GREEN};font-weight:600;'>&#10003;</span> {a} ({c:.1f}%)"
                for a, c, _ in holds
            )
            st.markdown(f"<div style='font-family:{FH};font-size:0.83rem;color:{MUTED};padding:4px 0;'>{hold_html}</div>",
                        unsafe_allow_html=True)

        sec("SMART CONTRIBUTION ALLOCATOR", GREEN)
        note("Direct new contributions into underweight assets — no selling, no CGT, maximum efficiency.", "good")
        new_money = st.number_input("New amount to invest", min_value=0, step=500, value=10000)
        if new_money > 0:
            allocs = smart_alloc(new_money, holdings, tgts, total)
            alloc_rows = [[an, fmt(amt), f"{amt / new_money * 100:.0f}%", "Closes underweight gap"]
                          for an, amt in allocs.items() if amt > 0]
            if alloc_rows:
                tbl(["Asset", "Allocate", "% of New Money", "Rationale"], alloc_rows)
                note(f"Investing {fmt(new_money)} this way reduces gap to target with no capital gains event.", "good")
            else:
                note("Portfolio is already on target — contribute proportionally to target weights.", "good")

        sec("FULL SUMMARY")
        total_cgt = 0
        srows = []
        for an in ASSET_NAMES:
            cv   = holdings.get(an, 0)
            cp   = cv / total * 100
            tp   = tgts.get(an, 0)
            tv2  = total * tp / 100
            diff = tv2 - cv
            if diff > 500:
                act = f"<span style='color:{GREEN};font-family:{FM};font-size:0.8rem;font-weight:600;'>Buy {fmt(diff)}</span>"
                cgt_cell = "—"
            elif diff < -500:
                cgt_e = cgt_estimate(abs(diff), st.session_state["cost_base_pct"], st.session_state["cgt_rate"])
                total_cgt += cgt_e
                act = f"<span style='color:{RED};font-family:{FM};font-size:0.8rem;font-weight:600;'>Sell {fmt(abs(diff))}</span>"
                cgt_cell = f"<span style='color:{AMBER};font-family:{FM};'>{fmt(cgt_e)}</span>"
            else:
                act = f"<span style='color:{MUTED};font-family:{FM};font-size:0.8rem;'>Hold</span>"
                cgt_cell = "—"
            srows.append([an, f"{cp:.1f}%", fmt(cv), f"{tp:.0f}%", fmt(tv2), act, cgt_cell])
        tbl(["Asset", "Current %", "Value", "Target %", "Target Value", "Action", "Est. CGT"], srows)
        if total_cgt > 0:
            note(f"Total estimated CGT on these sells: {fmt(total_cgt)} (50% discount applied for assets held 12+ months). Confirm with your accountant.", "warn")

        sec("EXECUTION NOTES", MUTED)
        exec_cfg = {"good": (GREEN_BG, GREEN), "warn": (AMBER_BG, AMBER), "info": (PRIMARY_BG, PRIMARY)}
        for title, txt, kind in [
            ("Super first", "No CGT on sales inside an accumulation-phase super fund. Always rebalance within super before acting on non-super assets.", "good"),
            ("Use contributions", "Directing new money into underweights avoids selling and CGT entirely. Most efficient method over a 12–24 month horizon.", "good"),
            ("CGT timing", "Assets held under 12 months: full gain is taxed. Over 12 months: 50% discount applies. Consider timing sells around the 12-month mark.", "warn"),
            ("Review frequency", "Annual review is sufficient for most investors. More frequent rebalancing generates friction without proportional benefit.", "info"),
        ]:
            ebg, eac = exec_cfg.get(kind, exec_cfg["info"])
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BD};border-left:3px solid {eac};"
                f"border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:5px;'>"
                f"<div style='font-family:{FH};font-size:0.83rem;font-weight:600;color:{eac};margin-bottom:2px;'>{title}</div>"
                f"<div style='font-family:{FH};font-size:0.8rem;color:{MUTED};line-height:1.5;'>{txt}</div></div>",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════
# TAB 5 — STRESS TEST
# ══════════════════════════════════════════════════════════════
with tab5:
    if not p_done:
        note("Complete the Risk Assessment first.", "info")
    elif not tpv():
        note("Enter holdings in the Portfolio tab first.", "info")
    else:
        holdings = pv()
        total    = tpv()
        pname    = st.session_state["risk_profile"]
        prof     = PROFILES[pname]

        note("Stress testing converts abstract percentage declines into actual dollar impacts on your specific portfolio. These are calibrated historical scenarios, not predictions.", "info")

        sec("SCENARIO", RED)
        scen_name = st.radio("Scenario", list(STRESS.keys()), horizontal=True, label_visibility="collapsed")
        sc = STRESS[scen_name]
        nt, net_loss, bd = run_stress(holdings, total, sc)
        pct_loss = abs(net_loss) / total * 100

        st.markdown(
            f"<div style='background:{RED_BG};border:1px solid #F2C9C3;border-left:3px solid {RED};"
            f"border-radius:0 8px 8px 0;padding:10px 14px;margin:6px 0;'>"
            f"<div style='font-family:{FM};font-size:0.78rem;font-weight:600;color:{RED};margin-bottom:3px;'>{sc['label']}</div>"
            f"<div style='font-family:{FH};font-size:0.83rem;color:{TEXT};line-height:1.5;'>{sc['desc']}</div></div>",
            unsafe_allow_html=True,
        )

        kpis([
            ("Before", fmt(total), "Current value", TEXT, BG),
            ("Estimated loss", fmt(net_loss), f"-{pct_loss:.1f}%", RED, RED_BG),
            ("Portfolio after", fmt(nt), "Post-crash estimate", AMBER, AMBER_BG),
            ("Recovery est.", f"~{sc['rec']:.0f} yr", f"At {prof['ret_mid'] * 100:.0f}% p.a.", GREEN, GREEN_BG),
        ])

        sec("ASSET IMPACT", RED)
        imp_rows = []
        bx, bv, bc = [], [], []
        for an in ASSET_NAMES:
            v = holdings.get(an, 0)
            if not v:
                continue
            delta = bd.get(an, 0)
            shock = sc["shocks"].get(an, 0)
            ds = (f"<span style='color:{RED};font-family:{FM};font-weight:600;'>{fmt(delta)}</span>"
                  if delta < 0 else
                  f"<span style='color:{GREEN};font-family:{FM};font-weight:600;'>+{fmt(delta)}</span>")
            imp_rows.append([an, fmt(v), f"{shock * 100:+.0f}%", fmt(v + delta), ds])
            bx.append(an.split("&")[0].strip()[:10])
            bv.append(delta)
            bc.append(RED if delta < 0 else GREEN)
        tbl(["Asset", "Before", "Shock", "After", "Change"], imp_rows)

        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=bx, y=bv, marker_color=bc, marker_line_width=0,
                               hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
        fig_b.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            margin=dict(t=4, b=4, l=4, r=4), height=200, showlegend=False,
                            xaxis=dict(showgrid=False, tickfont=dict(family="JetBrains Mono", size=8, color=MUTED)),
                            yaxis=dict(showgrid=True, gridcolor=BD,
                                       tickfont=dict(family="JetBrains Mono", size=8, color=MUTED), tickprefix=sym()))
        st.plotly_chart(fig_b, use_container_width=True)

        sec("RECOVERY TIMELINE", GREEN)
        yrs = list(range(16))
        fig_r = go.Figure()
        fig_r.add_hline(y=total, line_dash="dash", line_color=PRIMARY, line_width=1.5,
                        annotation_text="Current value",
                        annotation_font=dict(family="JetBrains Mono", size=9, color=PRIMARY))
        rec_colors = [GREEN, AMBER, RED]
        for (sn, s_), rc in zip(STRESS.items(), rec_colors):
            sl   = sum(holdings.get(a, 0) * s_["shocks"].get(a, 0) for a in ASSET_NAMES)
            vals = [(total + sl) * (1 + prof["ret_mid"]) ** y for y in yrs]
            fig_r.add_trace(go.Scatter(x=yrs, y=vals, mode="lines", name=s_["label"].split("  ")[0],
                                       line=dict(color=rc, width=1.8),
                                       hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
        fig_r.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            margin=dict(t=8, b=8, l=8, r=8), height=240,
                            legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, orientation="h", y=1.12,
                                        font=dict(family="JetBrains Mono", size=9, color=MUTED)),
                            xaxis=dict(title="Years post-crash", showgrid=False,
                                       tickfont=dict(family="JetBrains Mono", size=8, color=MUTED)),
                            yaxis=dict(showgrid=True, gridcolor=BD,
                                       tickfont=dict(family="JetBrains Mono", size=8, color=MUTED), tickprefix=sym()))
        st.plotly_chart(fig_r, use_container_width=True)

        if pct_loss > prof["draw_mid"] * 100 * 1.3:
            note(f"Your {pct_loss:.1f}% drawdown in this scenario exceeds the typical {prof['draw']} range for a {pname} portfolio. Your current allocation carries more risk than your profile implies.", "alert")
        elif pct_loss < prof["draw_mid"] * 100 * 0.7:
            note(f"Defensive holdings absorb the shock well. Your {pct_loss:.1f}% drawdown is below the typical {prof['draw']} for a {pname} investor — bonds and cash working as intended.", "good")
        else:
            note(f"Estimated loss of {fmt(abs(net_loss))} ({pct_loss:.1f}%) is consistent with a {pname} portfolio. Recovery at {prof['ret_mid'] * 100:.0f}% p.a.: approximately {sc['rec']:.0f} year(s).", "info")


# ══════════════════════════════════════════════════════════════
# TAB 6 — GOAL PROJECTIONS
# ══════════════════════════════════════════════════════════════
with tab6:
    if not p_done:
        note("Complete the Risk Assessment first.", "info")
    else:
        pname = st.session_state["risk_profile"]
        prof  = PROFILES[pname]
        total = tpv()
        pac   = PROFILE_CLR[pname]
        pbg   = PROFILE_BG[pname]

        note("Monte Carlo simulation — 1,000 independent paths using your profile's historical return and volatility. Outcome probabilities, not point predictions.", "info")

        sec("INPUTS", PURPLE)
        g1, g2, g3 = st.columns(3, gap="large")
        with g1:
            ga = st.number_input("Target portfolio value", min_value=0, step=50_000,
                                 value=int(st.session_state["goal_amount"]))
            st.session_state["goal_amount"] = ga
        with g2:
            gy = st.slider("Time horizon (years)", 1, 40, int(st.session_state["goal_years"]), 1)
            st.session_state["goal_years"] = gy
        with g3:
            mc = st.number_input("Monthly contributions", min_value=0, step=250,
                                 value=int(st.session_state["monthly_contrib"]))
            st.session_state["monthly_contrib"] = mc

        start = float(total) if total > 0 else 0.0
        if not start and not mc:
            note("Enter your portfolio value (Portfolio tab) or a monthly contribution to run projections.", "info")
        else:
            with st.spinner("Running 1,000 simulations..."):
                p10, p25, p50, p75, p90, ym, yp10, yp90 = run_mc(start, mc, gy, pname, 1000)

            if   p90 < ga: prob, pc = "< 10%",  RED
            elif p75 < ga: prob, pc = "10–25%", RED
            elif p50 < ga: prob, pc = "25–50%", AMBER
            elif p25 < ga: prob, pc = "50–75%", GREEN
            elif p10 < ga: prob, pc = "75–90%", GREEN
            else:          prob, pc = "> 90%",  GREEN
            pcbg = RED_BG if pc == RED else (AMBER_BG if pc == AMBER else GREEN_BG)

            ti = start + mc * gy * 12
            sec("RESULTS", PURPLE)
            kpis([
                ("Starting value", fmt(start), "Current portfolio", TEXT, BG),
                ("Total contributed", fmt(ti), f"{fmt(mc)}/mo x {gy}yr", MUTED, BG),
                ("Median outcome", fmt(p50), "50th percentile", pac, pbg),
                ("Probability of goal", prob, f"Reaching {fmt(ga)}", pc, pcbg),
            ])

            sec("PROJECTION CHART", PURPLE)
            yrsx = list(range(gy + 1))
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=yrsx + yrsx[::-1],
                                        y=[yp90[y] for y in yrsx] + [yp10[y] for y in yrsx][::-1],
                                        fill="toself", fillcolor="rgba(30,142,84,0.10)",
                                        line=dict(color="rgba(0,0,0,0)"), name="10th–90th band", hoverinfo="skip"))
            fig_mc.add_trace(go.Scatter(x=yrsx, y=[ym[y] for y in yrsx], mode="lines", name="Median",
                                        line=dict(color=PRIMARY, width=2.5),
                                        hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
            fig_mc.add_trace(go.Scatter(x=yrsx, y=[yp10[y] for y in yrsx], mode="lines", name="10th pct",
                                        line=dict(color=RED, width=1.2, dash="dot"),
                                        hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
            fig_mc.add_trace(go.Scatter(x=yrsx, y=[yp90[y] for y in yrsx], mode="lines", name="90th pct",
                                        line=dict(color=TEAL, width=1.2, dash="dot"),
                                        hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
            if ga > 0:
                fig_mc.add_hline(y=ga, line_dash="dash", line_color=PURPLE, line_width=1.5,
                                 annotation_text=f"Goal {fmt(ga)}",
                                 annotation_font=dict(family="JetBrains Mono", size=9, color=PURPLE))
            fig_mc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 margin=dict(t=8, b=8, l=8, r=8), height=320,
                                 legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0, orientation="h", y=1.1,
                                             font=dict(family="JetBrains Mono", size=9, color=MUTED)),
                                 xaxis=dict(title="Years", showgrid=False,
                                            tickfont=dict(family="JetBrains Mono", size=8, color=MUTED)),
                                 yaxis=dict(showgrid=True, gridcolor=BD,
                                            tickfont=dict(family="JetBrains Mono", size=8, color=MUTED), tickprefix=sym()))
            st.plotly_chart(fig_mc, use_container_width=True)

            sec(f"OUTCOME DISTRIBUTION — YEAR {gy}", PURPLE)
            tbl(["Percentile", "Value", "Interpretation"], [
                ["90th (optimistic)", fmt(p90), "Only 10% of simulations exceed this"],
                ["75th", fmt(p75), "Better than 3 in 4 paths"],
                ["50th (median)", fmt(p50), "Central estimate"],
                ["25th", fmt(p25), "Worse than 3 in 4 paths"],
                ["10th (pessimistic)", fmt(p10), "Only 10% of paths fall below this"],
            ])

            sec("CONTRIBUTION SENSITIVITY", PURPLE)
            note("Increasing monthly contributions typically has more impact than chasing higher returns.", "info")
            sr = []
            for ex in [0, 500, 1000, 2000, 3000]:
                _, _, sp50, _, _, _, _, _ = run_mc(start, mc + ex, gy, pname, 500)
                hit  = sp50 >= ga
                clr2 = GREEN if hit else RED
                sr.append(["Current" if ex == 0 else f"+{fmt(ex)}/mo",
                           fmt(mc + ex) + "/mo", fmt(sp50),
                           f"<span style='color:{clr2};font-family:{FM};font-size:0.8rem;font-weight:600;'>"
                           f"{'Reaches' if hit else 'Misses'} goal</span>"])
            tbl(["Scenario", "Monthly", "Median Outcome", "Goal"], sr)

            if pc == GREEN:
                note("On track. Consistency matters more than optimising returns. Stay invested through downturns.", "good")
            elif pc == AMBER:
                gap2  = ga - p50
                extra = gap2 / (gy * 12) if gy else 0
                note(f"Median outcome is {fmt(p50)} — {fmt(gap2)} short of goal. An additional {fmt(extra)}/month would close most of that gap.", "warn")
            else:
                note(f"Low probability of reaching {fmt(ga)} in {gy} years at current settings. Consider higher contributions, a longer timeline, or revisiting your risk profile.", "alert")

            note("Simulations use historical parameters and do not account for inflation, fees, taxes, or sequence-of-returns risk. Use as a planning range, not a guarantee.", "warn")


# ── FOOTER ────────────────────────────────────────────────────
st.markdown(
    f"<div style='border-top:1px solid {BD};margin-top:2rem;padding:12px 0 6px;font-family:{FM};"
    f"font-size:0.58rem;letter-spacing:0.06em;text-transform:uppercase;color:{DIM};text-align:center;'>"
    f"Meridian — Educational purposes only — Not personal financial advice — Consult a licensed financial adviser (AFSL)</div>",
    unsafe_allow_html=True,
)
