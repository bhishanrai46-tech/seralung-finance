"""
Meridian — Investment Risk & Portfolio Allocation Guide
========================================================
Educational framework. For informational purposes only.
Not personal financial advice. Consult a licensed adviser.
Run:  streamlit run meridian_app.py
Needs: streamlit plotly
"""

import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Meridian", page_icon=None, layout="wide",
                   initial_sidebar_state="collapsed")

# ═══════════════════════════════════════════════════════════════
# TOKENS
# ═══════════════════════════════════════════════════════════════

BG      = "#F3F0E8"
CARD    = "#FDFCF9"
BORDER  = "#DED9CE"
TEXT    = "#141210"
MUTED   = "#7A7268"
NAVY    = "#1A3558"
GOLD    = "#B8902A"
GREEN   = "#275E42"
AMBER   = "#7A5810"
RED     = "#7A1E1E"
NSOFT   = "#ECF1F8"
GSOFT   = "#FAF5E8"

FH = "'Cormorant Garamond', Georgia, serif"
FB = "'Source Serif 4', Georgia, serif"
FM = "'IBM Plex Mono', monospace"

ASSET_NAMES  = ["Australian Shares","International Shares","Property & REITs",
                "Fixed Income & Bonds","Cash & Term Deposits"]
ASSET_COLORS = [NAVY, "#2A5E3F", GOLD, "#5A4A7A", "#3A7A7A"]
ASSET_KEYS   = ["aus_shares","intl_shares","property_reits","fixed_income","cash_td"]

CUR_SYM = {"AUD":"A$","USD":"$","EUR":"€","GBP":"£","SGD":"S$"}

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

for k, v in {
    **{f"q{i}": 0 for i in range(1, 11)},
    "risk_score": 0, "risk_profile": "", "profile_done": False,
    "aus_shares": 0, "intl_shares": 0, "property_reits": 0,
    "fixed_income": 0, "cash_td": 0, "currency": "AUD",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════
# QUESTIONS — 10 questions, 4 options each scored 1–4
# ═══════════════════════════════════════════════════════════════

QUESTIONS = [
    ("Investment Time Horizon",
     "When do you anticipate needing the majority of these funds?",
     "Time horizon is the single most important input. A longer runway allows you to absorb market downturns and wait for recovery. The Australian share market has recovered from every correction it has ever experienced — the variable is whether you have time to wait.",
     ["Less than 3 years — I may need this money soon",
      "3 to 7 years — medium-term planning",
      "7 to 15 years — long-term wealth building",
      "15 years or more — retirement or generational wealth"]),
    ("Income Stability",
     "How would you describe your current income situation?",
     "Investors with stable income can take more risk because they are not forced to liquidate during downturns. Variable income requires a structurally more conservative allocation — not as a preference, but as a practical necessity.",
     ["Retired or living on a fixed income",
      "Variable, self-employed or contract income",
      "Stable salaried employment",
      "Tenured, government or highly secure employment"]),
    ("Emergency Reserves",
     "How many months of living expenses do you hold in accessible cash?",
     "Without an adequate cash buffer, you may be forced to sell investments at exactly the wrong moment. This single factor has destroyed more long-term investment plans than poor stock selection ever has.",
     ["Less than 1 month",
      "1 to 3 months",
      "3 to 6 months",
      "6 months or more"]),
    ("Investment Experience",
     "How would you describe your direct investment experience?",
     "Experience matters for the emotional discipline it builds. An investor who lived through the GFC in 2008 or March 2020 has real evidence of how they behave under stress — far more reliable than how they expect to behave.",
     ["I have never invested beyond a savings account",
      "Basic knowledge — I understand shares and managed funds",
      "3 or more years of active investing in shares or ETFs",
      "10 or more years across multiple asset classes"]),
    ("Reaction to Market Falls",
     "If your portfolio dropped 30% over three months, what would you actually do?",
     "This is the most revealing question. Most investors overestimate their loss tolerance during calm markets. A 30% drawdown is not hypothetical — it happened in 2008, in early 2020, and it will happen again.",
     ["Sell everything immediately to prevent further losses",
      "Reduce my exposure by selling some holdings",
      "Do nothing — hold and wait for recovery",
      "Add to my positions at the lower prices"]),
    ("Primary Objective",
     "What is the primary goal for this investment?",
     "Your objective determines everything downstream. A retiree drawing income and a 32-year-old accumulating wealth require fundamentally different portfolios, even if they share the same risk score.",
     ["Preserve my capital — I cannot afford significant losses",
      "Modest growth with capital preservation as priority",
      "Balanced growth over the medium to long term",
      "Maximum long-term growth — I accept significant volatility"]),
    ("Planned Withdrawals",
     "Do you expect to make significant withdrawals within the next 5 years?",
     "Liquidity requirements directly constrain risk-taking. You should never hold an asset you cannot afford to own through a 2 to 3 year downturn. If you need funds in 5 years, that portion should not be in equities.",
     ["Yes — I will need most of this money within 5 years",
      "Yes — I expect to need a meaningful portion",
      "Possibly minor withdrawals only",
      "No — this capital is fully committed for the long term"]),
    ("Debt Position",
     "How would you describe your current debt obligations?",
     "Carrying high-interest debt while taking investment risk is rarely rational. Paying down a 20% credit card is a guaranteed 20% return — better than any investment over a short horizon.",
     ["High debt relative to income or assets",
      "Moderate debt including a standard mortgage",
      "Low and actively reducing debt",
      "Debt free"]),
    ("Portfolio Significance",
     "This investment represents what portion of your total net worth?",
     "If this portfolio represents the majority of your wealth, a conservative approach is warranted regardless of other factors. Concentration risk across asset types matters as much as within a single portfolio.",
     ["More than 75% — this is my primary financial asset",
      "50 to 75% of my total net worth",
      "25 to 50% of my total net worth",
      "Less than 25% — I have significant other assets"]),
    ("Loss Tolerance",
     "What is the maximum annual loss you could absorb without impacting your lifestyle?",
     "I ask clients to translate their answer into a dollar figure — because percentages feel abstract until they appear on a statement. If unsure, choose the more conservative option.",
     ["Less than 5% — any significant loss is unacceptable",
      "5 to 15% — I can tolerate a moderate drawdown",
      "15 to 25% — I understand that markets cycle",
      "25% or more — I am focused on long-term returns"]),
]

# ═══════════════════════════════════════════════════════════════
# PROFILES
# ═══════════════════════════════════════════════════════════════

PROFILES = {
    "Conservative": {
        "range": (10,18), "ret": "3–5% p.a.", "draw": "5–10%", "horizon": "1–5 years",
        "desc": "Capital preservation is your primary concern. Your portfolio is built to withstand volatility with minimal drawdown, accepting lower returns for stability.",
        "note": "Conservative investors are not making a poor choice — they are making the right choice for their circumstances. The worst investment decision is one that forces you to sell at a loss because you took more risk than you could absorb.",
        "targets": {"Australian Shares":8,"International Shares":12,"Property & REITs":5,"Fixed Income & Bonds":45,"Cash & Term Deposits":30},
    },
    "Moderately Conservative": {
        "range": (19,25), "ret": "4–6% p.a.", "draw": "10–15%", "horizon": "3–7 years",
        "desc": "You seek modest growth while protecting capital. Fixed income dominates with a measured allocation to growth assets to stay ahead of inflation.",
        "note": "This profile often fits investors near retirement who need capital to last 20–30 years but cannot afford significant early drawdowns. The goal is not to grow wealthy — it is to remain wealthy.",
        "targets": {"Australian Shares":15,"International Shares":20,"Property & REITs":10,"Fixed Income & Bonds":40,"Cash & Term Deposits":15},
    },
    "Balanced": {
        "range": (26,31), "ret": "5–8% p.a.", "draw": "15–25%", "horizon": "5–10 years",
        "desc": "A genuine balance between growth and protection. You accept that markets cycle and are positioned to capture equity returns while maintaining meaningful defensive exposure.",
        "note": "The balanced portfolio is the most common outcome of a rigorous risk assessment. The 60/40 equity-to-bond split has endured for decades because it reflects a genuinely sensible trade-off between growth and protection.",
        "targets": {"Australian Shares":25,"International Shares":30,"Property & REITs":15,"Fixed Income & Bonds":22,"Cash & Term Deposits":8},
    },
    "Growth": {
        "range": (32,36), "ret": "7–10% p.a.", "draw": "25–35%", "horizon": "7–15 years",
        "desc": "Long-term capital appreciation is your priority. You understand that 20–35% drawdowns are normal, not aberrations, and recovery has historically followed every correction.",
        "note": "The historical evidence strongly supports this approach over 10+ year horizons. Australian equities have returned approximately 9% p.a. over the past 30 years including dividends. The investors who build the most wealth are not the most sophisticated — they are the most patient.",
        "targets": {"Australian Shares":30,"International Shares":40,"Property & REITs":15,"Fixed Income & Bonds":12,"Cash & Term Deposits":3},
    },
    "Aggressive": {
        "range": (37,40), "ret": "8–12% p.a.", "draw": "35–50%", "horizon": "15+ years",
        "desc": "Maximum long-term wealth accumulation. You have a long horizon, stable income, and the tested discipline to remain invested through significant corrections.",
        "note": "An aggressive allocation is appropriate for very few investors. If you are comfortable watching 40% of your portfolio temporarily disappear and viewing it as opportunity — this fits. If there is any doubt, consider the growth profile instead.",
        "targets": {"Australian Shares":35,"International Shares":45,"Property & REITs":15,"Fixed Income & Bonds":5,"Cash & Term Deposits":0},
    },
}

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def sym(): return CUR_SYM.get(st.session_state["currency"],"$")

def fmt(n):
    if n is None: return f"{sym()}0"
    s=sym(); sign="-" if n<0 else ""; n=abs(n)
    if n>=1_000_000: return f"{sign}{s}{n/1e6:.2f}M"
    if n>=1_000: return f"{sign}{s}{n:,.0f}"
    return f"{sign}{s}{n:.0f}"

def get_profile(score):
    for name, data in PROFILES.items():
        lo, hi = data["range"]
        if lo <= score <= hi: return name
    return "Balanced"

def pv():
    return {n: st.session_state[k] for n, k in zip(ASSET_NAMES, ASSET_KEYS)}

def total_pv():
    return sum(st.session_state[k] for k in ASSET_KEYS)

def advisor(text, kind="wisdom"):
    pal = {"wisdom":(NSOFT,NAVY),"caution":(GSOFT,GOLD),"good":("#EAF2EA",GREEN),"warn":("#FAF0E0",AMBER)}
    bg, ac = pal.get(kind, pal["wisdom"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {ac};border-radius:0 8px 8px 0;"
        f"padding:1.1rem 1.3rem;margin:0.85rem 0;display:flex;gap:1rem;align-items:flex-start;'>"
        f"<div style='min-width:36px;height:36px;border-radius:50%;background:{ac};color:#fff;"
        f"display:flex;align-items:center;justify-content:center;font-family:{FH};"
        f"font-size:0.9rem;font-weight:600;flex-shrink:0;'>JW</div>"
        f"<div style='flex:1;'>"
        f"<p style='font-family:{FM};font-size:0.56rem;letter-spacing:0.16em;"
        f"text-transform:uppercase;color:{ac};margin:0 0 0.4rem;font-weight:500;'>"
        f"Senior Financial Adviser · 25 Years Practice</p>"
        f"<p style='font-family:{FB};font-size:0.875rem;color:{TEXT};"
        f"line-height:1.7;margin:0;font-weight:300;font-style:italic;'>{text}</p>"
        f"</div></div>", unsafe_allow_html=True)

def slabel(text):
    st.markdown(
        f"<p style='font-family:{FM};font-size:0.56rem;letter-spacing:0.22em;"
        f"text-transform:uppercase;color:{MUTED};margin:1.6rem 0 0.8rem;"
        f"padding-bottom:0.5rem;border-bottom:1px solid {BORDER};'>{text}</p>",
        unsafe_allow_html=True)

def kpi(cards):
    cols = st.columns(len(cards), gap="small")
    for col, (lbl, val, note, hi) in zip(cols, cards):
        bdr = f"border-left:3px solid {NAVY};" if hi else ""
        with col:
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BORDER};"
                f"border-radius:8px;padding:16px 18px;{bdr}'>"
                f"<div style='font-family:{FM};font-size:0.54rem;letter-spacing:0.18em;"
                f"text-transform:uppercase;color:{MUTED};margin-bottom:9px;'>{lbl}</div>"
                f"<div style='font-family:{FH};font-size:1.7rem;color:{TEXT};"
                f"line-height:1;font-weight:500;'>{val}</div>"
                f"<div style='font-family:{FM};font-size:0.6rem;color:{MUTED};"
                f"margin-top:6px;'>{note}</div></div>", unsafe_allow_html=True)

def banner(text, kind="info"):
    pal = {"info":(NSOFT,NAVY),"good":("#EAF2EA",GREEN),"warn":(GSOFT,AMBER),"bad":("#FAE8E8",RED)}
    bg, bdr = pal.get(kind, pal["info"])
    st.markdown(
        f"<div style='background:{bg};border:1px solid {BORDER};border-left:3px solid {bdr};"
        f"border-radius:0 6px 6px 0;padding:10px 14px;font-family:{FB};"
        f"font-size:0.875rem;color:{TEXT};line-height:1.65;margin:0.4rem 0;'>{text}</div>",
        unsafe_allow_html=True)

def htable(headers, rows):
    hdr = "".join(
        f"<th style='text-align:left;padding:0.4rem 0.8rem;border-bottom:1px solid {BORDER};"
        f"font-family:{FM};font-size:0.56rem;text-transform:uppercase;letter-spacing:0.12em;"
        f"color:{MUTED};background:{CARD};white-space:nowrap;font-weight:500;'>{h}</th>"
        for h in headers)
    body = ""
    for i, row in enumerate(rows):
        bg = CARD if i%2==0 else "#F8F6F0"
        cells = "".join(
            f"<td style='padding:0.4rem 0.8rem;border-bottom:1px solid {BORDER};"
            f"font-family:{FB};font-size:0.82rem;color:{TEXT};background:{bg};'>{c}</td>"
            for c in row)
        body += f"<tr>{cells}</tr>"
    st.markdown(
        f"<div style='border:1px solid {BORDER};border-radius:8px;overflow:hidden;"
        f"overflow-x:auto;margin:0.5rem 0 1rem;'>"
        f"<table style='width:100%;border-collapse:collapse;background:{CARD};'>"
        f"<thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True)

def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color=BG, width=3)),
        textinfo="label+percent",
        textfont=dict(family="Source Serif 4, serif", size=11, color=TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<br>%{value:,.0f}<extra></extra>"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10,b=10,l=10,r=10), height=260, showlegend=False,
        font=dict(family="Source Serif 4, serif", color=TEXT),
        annotations=[dict(text=center,x=0.5,y=0.5,font=dict(size=13,family="Cormorant Garamond, serif",color=TEXT),showarrow=False)] if center else [])
    return fig

# ═══════════════════════════════════════════════════════════════
# CSS — @import for fonts (not <link>), all inside <style>
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Source+Serif+4:ital,wght@0,300;0,400;0,500;1,300;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background-color: {BG} !important;
    font-family: {FB};
    color: {TEXT};
}}
.block-container {{
    padding: 1.8rem 2rem 3rem;
    max-width: 1080px;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}

h1, h2, h3, h4 {{
    font-family: {FH} !important;
    font-weight: 500 !important;
    color: {TEXT} !important;
}}
p, span, li {{
    color: {TEXT} !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {BORDER};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: {FM};
    font-size: 0.62rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {MUTED};
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 13px 24px;
}}
.stTabs [aria-selected="true"] {{
    color: {NAVY} !important;
    border-bottom: 2px solid {NAVY} !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: {NAVY} !important;
    height: 2px !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1.5rem;
    background: transparent;
}}

div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label {{
    font-family: {FM} !important;
    font-size: 0.58rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: {MUTED} !important;
}}
.stNumberInput input {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT} !important;
    font-family: {FM} !important;
    font-size: 0.9rem !important;
    border-radius: 6px !important;
}}
.stNumberInput button {{
    background: {CARD} !important;
    color: {TEXT} !important;
    border-color: {BORDER} !important;
}}
.stSelectbox > div > div {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT} !important;
    border-radius: 6px !important;
}}
[role="listbox"] *, [role="option"] {{
    background: {CARD} !important;
    color: {TEXT} !important;
    font-family: {FB} !important;
}}
.stRadio > div > label {{
    font-family: {FB} !important;
    font-size: 0.875rem !important;
    color: {TEXT} !important;
    font-weight: 300 !important;
}}
div[data-testid="stRadio"] > label {{
    font-family: {FM} !important;
    font-size: 0.58rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: {MUTED} !important;
}}
.stButton > button {{
    background-color: {NAVY} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: {FM} !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 2rem !important;
}}
.stButton > button:hover {{ opacity: 0.82 !important; }}
div[data-testid="stExpander"] {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 8px !important;
}}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary span {{
    font-family: {FM} !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: {MUTED} !important;
}}
hr {{ border: none; border-top: 1px solid {BORDER}; margin: 1.4rem 0; }}
.score-track {{
    height: 5px; background: {BORDER}; border-radius: 3px;
    margin: 10px 0 4px; overflow: hidden;
}}
.score-fill {{
    height: 100%; border-radius: 3px;
    background: linear-gradient(to right, {NAVY}, {GOLD});
}}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TOP BAR
# ═══════════════════════════════════════════════════════════════

c1, _, c3 = st.columns([5, 2, 2])
with c1:
    st.markdown(
        f"<div style='font-family:{FH};font-size:2.4rem;color:{TEXT};"
        f"line-height:1;font-weight:500;'>Meridian</div>"
        f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.22em;"
        f"text-transform:uppercase;color:{MUTED};margin-top:4px;'>"
        f"Investment Risk &amp; Allocation Guide</div>", unsafe_allow_html=True)

with c3:
    cur_list = list(CUR_SYM.keys())
    st.selectbox("Currency", cur_list,
                 index=cur_list.index(st.session_state["currency"]),
                 key="currency", label_visibility="collapsed")

# Disclaimer
st.markdown(
    f"<div style='background:{GSOFT};border:1px solid {BORDER};border-radius:6px;"
    f"padding:7px 14px;margin:0.5rem 0 0.2rem;font-family:{FM};font-size:0.56rem;"
    f"letter-spacing:0.08em;text-transform:uppercase;color:{AMBER};'>"
    f"Educational purposes only · Not personal financial advice · "
    f"Consult a licensed financial adviser before investing</div>",
    unsafe_allow_html=True)

# Progress
p_done = st.session_state["profile_done"]
h_done = total_pv() > 0
steps = [("01  Risk Profile", p_done), ("02  Portfolio", h_done),
         ("03  Analysis", p_done and h_done), ("04  Rebalancing", p_done and h_done)]
step_html = ""
for label, done in steps:
    clr = GREEN if done else MUTED
    mark = "✓" if done else "○"
    step_html += (f"<span style='font-family:{FM};font-size:0.58rem;"
                  f"letter-spacing:0.1em;text-transform:uppercase;color:{clr};"
                  f"margin-right:2rem;'>{mark}&nbsp; {label}</span>")
st.markdown(f"<div style='padding:0.6rem 0;'>{step_html}</div>", unsafe_allow_html=True)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["Risk Assessment","My Portfolio",
                                   "Allocation Analysis","Rebalancing Plan"])

# ──────────────────────────────────────────────────────────────
# TAB 1 — RISK ASSESSMENT
# ──────────────────────────────────────────────────────────────

with tab1:
    advisor(
        "Before any allocation decision, we must understand your genuine relationship with risk. "
        "The ten questions below are drawn from decades of client practice. "
        "Answer each honestly — the accuracy of everything that follows depends on it.",
        kind="wisdom")

    slabel("The Risk Questionnaire")

    total_score = 0
    for i, (title, question, insight, options) in enumerate(QUESTIONS):
        qkey = f"q{i+1}"
        st.markdown(
            f"<p style='font-family:{FH};font-size:1.05rem;color:{TEXT};"
            f"font-weight:500;margin:1.4rem 0 0.15rem;'>{title}</p>"
            f"<p style='font-family:{FB};font-size:0.85rem;color:{MUTED};"
            f"font-weight:300;margin:0 0 0.5rem;font-style:italic;'>{question}</p>",
            unsafe_allow_html=True)

        # Radio — index from session state (default 0 = most conservative)
        selected_idx = st.radio(
            label=title,
            options=list(range(len(options))),
            format_func=lambda x, opts=options: opts[x],
            index=st.session_state[qkey],
            key=f"radio_{qkey}",
            label_visibility="collapsed")

        st.session_state[qkey] = selected_idx
        total_score += selected_idx + 1  # options scored 1–4

        with st.expander("Adviser perspective"):
            st.markdown(
                f"<p style='font-family:{FB};font-size:0.875rem;color:{TEXT};"
                f"line-height:1.7;font-weight:300;font-style:italic;"
                f"padding:0.3rem 0;'>{insight}</p>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Calculate My Risk Profile"):
        profile_name = get_profile(total_score)
        st.session_state["risk_score"]   = total_score
        st.session_state["risk_profile"] = profile_name
        st.session_state["profile_done"] = True
        try: st.rerun()
        except: st.experimental_rerun()

    # Show result
    if st.session_state["profile_done"]:
        pname = st.session_state["risk_profile"]
        prof  = PROFILES[pname]
        pct   = ((st.session_state["risk_score"] - 10) / 30) * 100

        st.markdown("---")
        slabel("Your Risk Profile")

        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BORDER};"
            f"border-left:3px solid {NAVY};border-radius:0 8px 8px 0;"
            f"padding:1.4rem 1.6rem;margin-bottom:1rem;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;'>"
            f"<div style='font-family:{FH};font-size:1.8rem;color:{TEXT};font-weight:500;'>{pname}</div>"
            f"<div style='font-family:{FM};font-size:0.8rem;color:{MUTED};'>"
            f"Score: {st.session_state['risk_score']} / 40</div></div>"
            f"<div class='score-track'><div class='score-fill' style='width:{pct:.0f}%'></div></div>"
            f"<p style='font-family:{FB};font-size:0.875rem;color:{MUTED};"
            f"line-height:1.65;margin:0.8rem 0 0;font-weight:300;'>{prof['desc']}</p></div>",
            unsafe_allow_html=True)

        kpi([
            ("Expected Return",    prof["ret"],     "Historical estimate", True),
            ("Max Drawdown Range", prof["draw"],    "Typical correction depth", False),
            ("Suited Horizon",     prof["horizon"], "Minimum recommended", False),
        ])

        st.markdown("<br>", unsafe_allow_html=True)
        advisor(prof["note"], kind="wisdom")

        # Target allocation preview
        slabel("Indicative Target Allocation")
        tgts = prof["targets"]
        active_t = {k: v for k, v in tgts.items() if v > 0}

        col_ch, col_lg = st.columns([1, 1])
        with col_ch:
            fig = donut(list(active_t.keys()), list(active_t.values()),
                        [ASSET_COLORS[ASSET_NAMES.index(k)] for k in active_t], f"<b>{pname[:4]}.</b>")
            st.plotly_chart(fig, use_container_width=True)
        with col_lg:
            st.markdown("<br>", unsafe_allow_html=True)
            for asset, pctv in tgts.items():
                clr = ASSET_COLORS[ASSET_NAMES.index(asset)]
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:0.7rem;"
                    f"padding:0.45rem 0;border-bottom:1px solid {BORDER};'>"
                    f"<div style='width:10px;height:10px;border-radius:50%;"
                    f"background:{clr};flex-shrink:0;'></div>"
                    f"<div style='font-family:{FB};font-size:0.82rem;color:{TEXT};"
                    f"flex:1;font-weight:300;'>{asset}</div>"
                    f"<div style='font-family:{FM};font-size:0.82rem;color:{NAVY};"
                    f"font-weight:500;'>{pctv}%</div></div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# TAB 2 — MY PORTFOLIO
# ──────────────────────────────────────────────────────────────

with tab2:
    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment first.", "info")
    else:
        advisor(
            "Enter the current market value of each asset class — super, shares, ETFs, "
            "investment property, bonds, and cash. The full picture. "
            "Investors who assess only part of their wealth routinely take more risk than they realise.",
            kind="wisdom")

        slabel("Current Holdings")
        descs = [
            "ASX-listed shares, Australian equity ETFs, managed funds",
            "Global ETFs (MSCI World, S&P 500), international managed funds",
            "Direct investment property equity, A-REITs, global REITs",
            "Government and corporate bonds, bond ETFs, term deposits over 1 year",
            "Bank savings, offset accounts, term deposits under 1 year",
        ]
        ca, cb = st.columns(2, gap="large")
        for idx, (name, key, desc) in enumerate(zip(ASSET_NAMES, ASSET_KEYS, descs)):
            col = ca if idx < 3 else cb
            with col:
                st.markdown(
                    f"<p style='font-family:{FH};font-size:0.95rem;color:{TEXT};"
                    f"font-weight:500;margin:1rem 0 0.1rem;'>{name}</p>"
                    f"<p style='font-family:{FB};font-size:0.72rem;color:{MUTED};"
                    f"font-weight:300;font-style:italic;margin:0 0 0.3rem;'>{desc}</p>",
                    unsafe_allow_html=True)
                st.number_input(name, min_value=0, step=1000, key=key,
                                label_visibility="collapsed")

        total = total_pv()
        if total == 0:
            st.markdown("<br>", unsafe_allow_html=True)
            banner("Enter your holdings above to see allocation.", "info")
        else:
            st.markdown("---")
            slabel("Current Allocation")
            holdings = pv()
            active = {k: v for k, v in holdings.items() if v > 0}

            kpi([
                ("Total Portfolio", fmt(total), "All asset classes", True),
                ("Asset Classes Held", str(len(active)), "of 5 available", False),
                ("Largest Holding", max(active, key=active.get),
                 f"{max(active.values())/total*100:.0f}% of portfolio", False),
            ])
            st.markdown("<br>", unsafe_allow_html=True)

            col_c, col_d = st.columns([1, 1])
            with col_c:
                fig2 = donut(list(active.keys()), list(active.values()),
                             [ASSET_COLORS[ASSET_NAMES.index(k)] for k in active],
                             f"<b>{fmt(total)}</b>")
                st.plotly_chart(fig2, use_container_width=True)
            with col_d:
                st.markdown("<br>", unsafe_allow_html=True)
                for asset in sorted(holdings.keys(), key=lambda x: holdings[x], reverse=True):
                    val = holdings[asset]
                    if val == 0: continue
                    pctv = val/total*100
                    clr = ASSET_COLORS[ASSET_NAMES.index(asset)]
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:0.7rem;"
                        f"padding:0.45rem 0;border-bottom:1px solid {BORDER};'>"
                        f"<div style='width:10px;height:10px;border-radius:50%;"
                        f"background:{clr};flex-shrink:0;'></div>"
                        f"<div style='font-family:{FB};font-size:0.82rem;color:{TEXT};"
                        f"flex:1;font-weight:300;'>{asset}</div>"
                        f"<div style='font-family:{FM};font-size:0.72rem;color:{MUTED};"
                        f"margin-right:0.5rem;'>{pctv:.1f}%</div>"
                        f"<div style='font-family:{FM};font-size:0.82rem;color:{TEXT};"
                        f"font-weight:500;'>{fmt(val)}</div></div>", unsafe_allow_html=True)

            # Concentration warning
            for asset, val in holdings.items():
                if val == 0: continue
                if val/total*100 > 60:
                    st.markdown("<br>", unsafe_allow_html=True)
                    advisor(f"{asset} represents {val/total*100:.0f}% of your portfolio — a significant "
                            f"concentration. Even excellent asset classes experience prolonged downturns. "
                            f"Review the analysis tab for specific guidance.", kind="caution")
                    break


# ──────────────────────────────────────────────────────────────
# TAB 3 — ALLOCATION ANALYSIS
# ──────────────────────────────────────────────────────────────

with tab3:
    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment first.", "info")
    elif total_pv() == 0:
        banner("Enter your holdings in the My Portfolio tab.", "info")
    else:
        pname = st.session_state["risk_profile"]
        tgts  = PROFILES[pname]["targets"]
        holdings = pv()
        total = total_pv()

        advisor(f"Your risk profile is <strong>{pname}</strong>. Below is a comparison between "
                f"your current allocation and the target for this profile. The gaps are where "
                f"the actionable decisions live.", kind="wisdom")

        slabel("Current vs Target")

        # Grouped bar
        cur_pcts = [holdings.get(a,0)/total*100 for a in ASSET_NAMES]
        tgt_pcts = [tgts.get(a,0) for a in ASSET_NAMES]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Current", x=ASSET_NAMES, y=cur_pcts, marker_color=GOLD,
                              hovertemplate="%{x}<br>Current: %{y:.1f}%<extra></extra>"))
        fig3.add_trace(go.Bar(name="Target", x=ASSET_NAMES, y=tgt_pcts, marker_color=NAVY,
                              hovertemplate="%{x}<br>Target: %{y:.1f}%<extra></extra>"))
        fig3.update_layout(barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=10,b=10,l=10,r=10), height=280,
                           legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                                       font=dict(family="IBM Plex Mono", size=10, color=MUTED),
                                       orientation="h", y=1.08),
                           xaxis=dict(showgrid=False, color=MUTED,
                                      tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED)),
                           yaxis=dict(showgrid=True, gridcolor=BORDER,
                                      tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED),
                                      ticksuffix="%"),
                           font=dict(family="Source Serif 4, serif", color=TEXT))
        st.plotly_chart(fig3, use_container_width=True)

        # Gap table
        slabel("Gap Analysis")
        rows = []
        overs = []
        unders = []
        for asset in ASSET_NAMES:
            cp = holdings.get(asset,0)/total*100
            tp = tgts.get(asset,0)
            gap = cp - tp
            cv = holdings.get(asset,0)
            tv = total * tp / 100
            dv = cv - tv
            if gap > 5:
                status = f"<span style='color:{RED};font-weight:500;'>Overweight +{gap:.1f}%</span>"
                overs.append((asset, gap))
            elif gap < -5:
                status = f"<span style='color:{AMBER};font-weight:500;'>Underweight {gap:.1f}%</span>"
                unders.append((asset, gap))
            else:
                status = f"<span style='color:{GREEN};'>On target ({gap:+.1f}%)</span>"
            rows.append([asset, f"{cp:.1f}%", f"{tp:.0f}%", status, fmt(cv), fmt(tv), fmt(dv)])

        htable(["Asset Class","Current %","Target %","Status","Current Value","Target Value","Difference"], rows)

        if overs:
            biggest = max(overs, key=lambda x: x[1])
            advisor(f"Your most significant overweight is {biggest[0]} at {biggest[1]:.1f}% above target. "
                    f"This commonly develops as strong-performing assets drift upward without rebalancing. "
                    f"See the Rebalancing Plan for specific actions.", kind="caution")
        if unders:
            biggest = min(unders, key=lambda x: x[1])
            advisor(f"Your most notable underweight is {biggest[0]}, {abs(biggest[1]):.1f}% below target. "
                    f"Underweights in defensive assets leave the portfolio more exposed to downturns "
                    f"than your risk profile suggests.", kind="caution")
        if not overs and not unders:
            advisor("Your portfolio is well-aligned with your risk profile. The primary task now is "
                    "maintaining this alignment as markets move — review quarterly.", kind="good")

        # Side-by-side donuts
        slabel("Visual Comparison")
        col_l, col_r = st.columns(2, gap="large")
        with col_l:
            st.markdown(f"<p style='font-family:{FM};font-size:0.58rem;letter-spacing:0.14em;"
                        f"text-transform:uppercase;color:{MUTED};text-align:center;'>Current</p>",
                        unsafe_allow_html=True)
            a = {k:v for k,v in holdings.items() if v>0}
            st.plotly_chart(donut(list(a.keys()),list(a.values()),
                                 [ASSET_COLORS[ASSET_NAMES.index(k)] for k in a],"Current"),
                           use_container_width=True)
        with col_r:
            st.markdown(f"<p style='font-family:{FM};font-size:0.58rem;letter-spacing:0.14em;"
                        f"text-transform:uppercase;color:{MUTED};text-align:center;'>Target</p>",
                        unsafe_allow_html=True)
            t = {k:v for k,v in tgts.items() if v>0}
            st.plotly_chart(donut(list(t.keys()),list(t.values()),
                                 [ASSET_COLORS[ASSET_NAMES.index(k)] for k in t],pname[:4]+"."),
                           use_container_width=True)


# ──────────────────────────────────────────────────────────────
# TAB 4 — REBALANCING PLAN
# ──────────────────────────────────────────────────────────────

with tab4:
    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment first.", "info")
    elif total_pv() == 0:
        banner("Enter your holdings in the My Portfolio tab.", "info")
    else:
        pname = st.session_state["risk_profile"]
        tgts  = PROFILES[pname]["targets"]
        holdings = pv()
        total = total_pv()

        advisor("Rebalancing is the discipline of systematically selling what has done well "
                "and buying what has done poorly — without emotion or prediction. "
                "Always consider capital gains tax before executing any sale, "
                "particularly for assets outside superannuation.", kind="wisdom")

        slabel("Rebalancing Actions")

        sells, buys, holds_list = [], [], []
        for asset in ASSET_NAMES:
            cv = holdings.get(asset,0)
            cp = cv/total*100
            tp = tgts.get(asset,0)
            tv = total*tp/100
            diff = cv - tv
            gap  = cp - tp
            if gap > 2:   sells.append((asset, diff, cp, tp))
            elif gap < -2: buys.append((asset, abs(diff), cp, tp))
            else:          holds_list.append((asset, cp, tp))
        sells.sort(key=lambda x: x[1], reverse=True)
        buys.sort(key=lambda x: x[1], reverse=True)

        if sells:
            st.markdown(f"<p style='font-family:{FH};font-size:1.1rem;color:{RED};"
                        f"font-weight:500;margin:0.5rem 0 0.8rem;'>Reduce — Overweight Positions</p>",
                        unsafe_allow_html=True)
            for i, (asset, amount, cp, tp) in enumerate(sells):
                pri = "High priority" if i == 0 else "Secondary"
                st.markdown(
                    f"<div style='background:{CARD};border:1px solid {BORDER};"
                    f"border-left:3px solid {RED};border-radius:0 8px 8px 0;"
                    f"padding:1rem 1.3rem;margin-bottom:0.75rem;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;'>"
                    f"<span style='font-family:{FH};font-size:0.95rem;color:{TEXT};font-weight:500;'>Reduce {asset}</span>"
                    f"<span style='font-family:{FM};font-size:0.9rem;color:{RED};font-weight:500;'>Sell {fmt(amount)}</span></div>"
                    f"<p style='font-family:{FB};font-size:0.82rem;color:{MUTED};font-weight:300;margin:0 0 0.3rem;'>"
                    f"Currently {cp:.1f}% → Target {tp:.0f}%</p>"
                    f"<p style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{RED};margin:0;'>{pri}</p></div>",
                    unsafe_allow_html=True)

        if buys:
            st.markdown(f"<p style='font-family:{FH};font-size:1.1rem;color:{GREEN};"
                        f"font-weight:500;margin:1.2rem 0 0.8rem;'>Increase — Underweight Positions</p>",
                        unsafe_allow_html=True)
            for i, (asset, amount, cp, tp) in enumerate(buys):
                pri = "High priority" if i == 0 else "Secondary"
                st.markdown(
                    f"<div style='background:{CARD};border:1px solid {BORDER};"
                    f"border-left:3px solid {GREEN};border-radius:0 8px 8px 0;"
                    f"padding:1rem 1.3rem;margin-bottom:0.75rem;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;'>"
                    f"<span style='font-family:{FH};font-size:0.95rem;color:{TEXT};font-weight:500;'>Increase {asset}</span>"
                    f"<span style='font-family:{FM};font-size:0.9rem;color:{GREEN};font-weight:500;'>Buy {fmt(amount)}</span></div>"
                    f"<p style='font-family:{FB};font-size:0.82rem;color:{MUTED};font-weight:300;margin:0 0 0.3rem;'>"
                    f"Currently {cp:.1f}% → Target {tp:.0f}%</p>"
                    f"<p style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{GREEN};margin:0;'>{pri}</p></div>",
                    unsafe_allow_html=True)

        if holds_list:
            slabel("Hold — On Target")
            ht = " &nbsp;·&nbsp; ".join(
                f"<span style='color:{GREEN};font-weight:500;'>✓</span> {a} ({c:.1f}%)"
                for a, c, _ in holds_list)
            st.markdown(f"<p style='font-family:{FB};font-size:0.875rem;color:{MUTED};"
                        f"font-weight:300;'>{ht}</p>", unsafe_allow_html=True)

        # Summary table
        slabel("Full Rebalancing Summary")
        srows = []
        for asset in ASSET_NAMES:
            cv = holdings.get(asset,0); cp = cv/total*100
            tp = tgts.get(asset,0); tv = total*tp/100; diff = tv - cv
            if diff > 500:   act = f"<span style='color:{GREEN};font-weight:500;'>Buy {fmt(diff)}</span>"
            elif diff < -500: act = f"<span style='color:{RED};font-weight:500;'>Sell {fmt(abs(diff))}</span>"
            else:             act = f"<span style='color:{MUTED};'>Hold</span>"
            srows.append([asset, f"{cp:.1f}%", fmt(cv), f"{tp:.0f}%", fmt(tv), act])
        htable(["Asset Class","Current %","Current Value","Target %","Target Value","Action"], srows)

        # Considerations
        slabel("Before You Act")
        for title, text, kind in [
            ("Capital Gains Tax",
             "Selling appreciated assets outside super may trigger CGT. If held 12+ months, the 50% discount applies. Consider the after-tax cost of rebalancing vs remaining slightly misaligned.",
             "caution"),
            ("Superannuation First",
             "Rebalancing within super is typically more tax-efficient — no CGT on asset sales inside a super fund in accumulation phase. Start with super adjustments where possible.",
             "wisdom"),
            ("Use New Contributions",
             "Direct new contributions into underweight classes rather than selling overweight ones. This achieves gradual rebalancing without tax events — the most frictionless long-term approach.",
             "good"),
            ("Review Annually",
             "Set a calendar reminder to review once per year, or when any class drifts 10+ percentage points from target. Over-frequent rebalancing generates costs without proportional benefit.",
             "wisdom"),
        ]:
            with st.expander(title):
                advisor(text, kind=kind)

        st.markdown("<br>", unsafe_allow_html=True)
        advisor("This plan gives you a clear, evidence-based framework. The harder part — "
                "and where a licensed adviser adds the most value — is executing the rebalancing "
                "in the most tax-efficient sequence for your specific circumstances. "
                "Use this as a starting point for that conversation.", kind="wisdom")

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    f"<div style='font-family:{FM};font-size:0.56rem;color:{MUTED};"
    f"letter-spacing:0.1em;text-transform:uppercase;text-align:center;"
    f"padding-bottom:1.5rem;line-height:1.8;'>"
    f"Meridian · Investment Risk &amp; Allocation Guide<br>"
    f"For educational purposes only · Not personal financial advice<br>"
    f"Consult a licensed financial adviser (AFSL) before investing</div>",
    unsafe_allow_html=True)
