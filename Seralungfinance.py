"""
Meridian — Investment Risk & Portfolio Allocation Guide  (Enhanced v2)
=======================================================================
New in v2:
  · Portfolio Health Score  (alignment + diversification + liquidity)
  · Stress Test — dollar impact of -15%, -30%, -50% scenarios
  · Goal Projections — Monte Carlo simulation, 1 000 paths
  · Smart Contribution Planner — allocate new money optimally
  · CGT Estimator — approx. tax cost of each rebalancing trade
  · Recovery Timeline — years to recover after each crash scenario
  · Drawdown $ impact shown on profile result
  · Improved adviser insights throughout

Run:  streamlit run meridian_app.py
Needs: streamlit plotly
"""

import math
import random
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Meridian",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════

BG     = "#F3F0E8"
CARD   = "#FDFCF9"
BORDER = "#DED9CE"
TEXT   = "#141210"
MUTED  = "#7A7268"
NAVY   = "#1A3558"
GOLD   = "#B8902A"
GREEN  = "#275E42"
AMBER  = "#7A5810"
RED    = "#7A1E1E"
NSOFT  = "#ECF1F8"
GSOFT  = "#FAF5E8"
RSOFT  = "#FAF0F0"

FH = "'Cormorant Garamond', Georgia, serif"
FB = "'Source Serif 4', Georgia, serif"
FM = "'IBM Plex Mono', monospace"

ASSET_NAMES  = ["Australian Shares", "International Shares", "Property & REITs",
                "Fixed Income & Bonds", "Cash & Term Deposits"]
ASSET_COLORS = [NAVY, "#2A5E3F", GOLD, "#5A4A7A", "#3A7A7A"]
ASSET_KEYS   = ["aus_shares", "intl_shares", "property_reits", "fixed_income", "cash_td"]
ASSET_BETA   = [1.0, 0.95, 0.70, -0.15, 0.0]   # sensitivity to broad market shock

CUR_SYM = {"AUD": "A$", "USD": "$", "EUR": "€", "GBP": "£", "SGD": "S$"}

# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

_defaults = {
    **{f"q{i}": 0 for i in range(1, 11)},
    "risk_score": 0, "risk_profile": "", "profile_done": False,
    "aus_shares": 0, "intl_shares": 0, "property_reits": 0,
    "fixed_income": 0, "cash_td": 0, "currency": "AUD",
    "goal_amount": 1_000_000, "goal_years": 20,
    "monthly_contrib": 2_000, "cgt_rate": 22.5,
    "cost_base_pct": 60,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════
# RISK QUESTIONS (unchanged)
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
        "range": (10, 18), "ret": "3–5% p.a.", "ret_mid": 0.04,
        "draw": "5–10%", "draw_mid": 0.075, "horizon": "1–5 years", "vol": 0.05,
        "desc": "Capital preservation is your primary concern. Your portfolio is built to withstand volatility with minimal drawdown, accepting lower returns for stability.",
        "note": "Conservative investors are not making a poor choice — they are making the right choice for their circumstances. The worst investment decision is one that forces you to sell at a loss because you took more risk than you could absorb.",
        "targets": {"Australian Shares": 8, "International Shares": 12, "Property & REITs": 5,
                    "Fixed Income & Bonds": 45, "Cash & Term Deposits": 30},
    },
    "Moderately Conservative": {
        "range": (19, 25), "ret": "4–6% p.a.", "ret_mid": 0.05,
        "draw": "10–15%", "draw_mid": 0.125, "horizon": "3–7 years", "vol": 0.08,
        "desc": "You seek modest growth while protecting capital. Fixed income dominates with a measured allocation to growth assets to stay ahead of inflation.",
        "note": "This profile often fits investors near retirement who need capital to last 20–30 years but cannot afford significant early drawdowns. The goal is not to grow wealthy — it is to remain wealthy.",
        "targets": {"Australian Shares": 15, "International Shares": 20, "Property & REITs": 10,
                    "Fixed Income & Bonds": 40, "Cash & Term Deposits": 15},
    },
    "Balanced": {
        "range": (26, 31), "ret": "5–8% p.a.", "ret_mid": 0.065,
        "draw": "15–25%", "draw_mid": 0.20, "horizon": "5–10 years", "vol": 0.11,
        "desc": "A genuine balance between growth and protection. You accept that markets cycle and are positioned to capture equity returns while maintaining meaningful defensive exposure.",
        "note": "The balanced portfolio is the most common outcome of a rigorous risk assessment. The 60/40 equity-to-bond split has endured for decades because it reflects a genuinely sensible trade-off between growth and protection.",
        "targets": {"Australian Shares": 25, "International Shares": 30, "Property & REITs": 15,
                    "Fixed Income & Bonds": 22, "Cash & Term Deposits": 8},
    },
    "Growth": {
        "range": (32, 36), "ret": "7–10% p.a.", "ret_mid": 0.08,
        "draw": "25–35%", "draw_mid": 0.30, "horizon": "7–15 years", "vol": 0.15,
        "desc": "Long-term capital appreciation is your priority. You understand that 20–35% drawdowns are normal, not aberrations, and recovery has historically followed every correction.",
        "note": "The historical evidence strongly supports this approach over 10+ year horizons. Australian equities have returned approximately 9% p.a. over the past 30 years including dividends. The investors who build the most wealth are not the most sophisticated — they are the most patient.",
        "targets": {"Australian Shares": 30, "International Shares": 40, "Property & REITs": 15,
                    "Fixed Income & Bonds": 12, "Cash & Term Deposits": 3},
    },
    "Aggressive": {
        "range": (37, 40), "ret": "8–12% p.a.", "ret_mid": 0.09,
        "draw": "35–50%", "draw_mid": 0.425, "horizon": "15+ years", "vol": 0.19,
        "desc": "Maximum long-term wealth accumulation. You have a long horizon, stable income, and the tested discipline to remain invested through significant corrections.",
        "note": "An aggressive allocation is appropriate for very few investors. If you are comfortable watching 40% of your portfolio temporarily disappear and viewing it as opportunity — this fits. If there is any doubt, consider the growth profile instead.",
        "targets": {"Australian Shares": 35, "International Shares": 45, "Property & REITs": 15,
                    "Fixed Income & Bonds": 5, "Cash & Term Deposits": 0},
    },
}

STRESS_SCENARIOS = {
    "Correction  −15%": {
        "headline": "−15%  Market Correction",
        "desc": "A typical market pullback. Occurs roughly every 3–5 years. Equity markets have historically recovered within 6–18 months. This is the noise of normal investing.",
        "recovery_years": 1.0,
        "shocks": {"Australian Shares": -0.18, "International Shares": -0.16,
                   "Property & REITs": -0.11, "Fixed Income & Bonds": +0.03,
                   "Cash & Term Deposits": 0.00},
    },
    "Bear Market  −30%": {
        "headline": "−30%  Bear Market",
        "desc": "Comparable to the 2022 rate-shock sell-off or the March 2020 COVID crash. Recovery typically 1–3 years. Defensive assets act as a meaningful cushion.",
        "recovery_years": 2.5,
        "shocks": {"Australian Shares": -0.33, "International Shares": -0.30,
                   "Property & REITs": -0.22, "Fixed Income & Bonds": +0.06,
                   "Cash & Term Deposits": 0.00},
    },
    "GFC Crash  −50%": {
        "headline": "−50%  GFC-Level Crash",
        "desc": "A 2008-style systemic event. The ASX 200 fell 54% peak-to-trough and required nearly 5 years for full recovery. A portfolio with meaningful defensive holdings cushions this materially.",
        "recovery_years": 5.0,
        "shocks": {"Australian Shares": -0.54, "International Shares": -0.50,
                   "Property & REITs": -0.42, "Fixed Income & Bonds": +0.09,
                   "Cash & Term Deposits": 0.00},
    },
}

# ═══════════════════════════════════════════════════════════════
# HELPERS — FORMATTING
# ═══════════════════════════════════════════════════════════════

def sym():
    return CUR_SYM.get(st.session_state["currency"], "$")

def fmt(n):
    if n is None:
        return f"{sym()}0"
    s = sym()
    sign = "−" if n < 0 else ""
    n = abs(n)
    if n >= 1_000_000:
        return f"{sign}{s}{n/1e6:.2f}M"
    if n >= 1_000:
        return f"{sign}{s}{n:,.0f}"
    return f"{sign}{s}{n:.0f}"

def pv():
    return {n: st.session_state[k] for n, k in zip(ASSET_NAMES, ASSET_KEYS)}

def total_pv():
    return sum(st.session_state[k] for k in ASSET_KEYS)

def get_profile(score):
    for name, data in PROFILES.items():
        lo, hi = data["range"]
        if lo <= score <= hi:
            return name
    return "Balanced"

# ═══════════════════════════════════════════════════════════════
# HELPERS — ANALYTICS
# ═══════════════════════════════════════════════════════════════

def portfolio_health_score(holdings, tgts, total):
    """Return (total, alignment, diversification, liquidity) — each component /100 proportional."""
    if total == 0:
        return 0, 0, 0, 0

    # Alignment (0–40 pts): penalise average percentage gap from target
    gaps = [abs(holdings.get(a, 0) / total * 100 - tgts.get(a, 0)) for a in ASSET_NAMES]
    avg_gap = sum(gaps) / len(gaps)
    align = max(0.0, 40.0 - avg_gap * 2.2)

    # Diversification (0–30 pts): number of meaningful holdings minus high concentration penalty
    pcts = [holdings.get(a, 0) / total * 100 for a in ASSET_NAMES]
    n_meaningful = sum(1 for p in pcts if p >= 2)
    max_pct = max(pcts) if pcts else 100
    divers = min(30.0, n_meaningful * 6.0) - max(0.0, (max_pct - 50) * 0.55)
    divers = max(0.0, divers)

    # Liquidity buffer (0–30 pts): proximity of defensive weighting to target
    cur_def = (holdings.get("Cash & Term Deposits", 0) + holdings.get("Fixed Income & Bonds", 0)) / total * 100
    tgt_def = tgts.get("Cash & Term Deposits", 0) + tgts.get("Fixed Income & Bonds", 0)
    liq_gap = abs(cur_def - tgt_def)
    liq = max(0.0, 30.0 - liq_gap * 1.4)

    total_score = align + divers + liq
    return round(total_score), round(align), round(divers), round(liq)

def stress_test(holdings, total, scenario):
    """Return (new_total, dollar_loss, asset_breakdown)."""
    shocks = scenario["shocks"]
    new_total = 0.0
    breakdown = {}
    for asset in ASSET_NAMES:
        val = holdings.get(asset, 0)
        shocked = val * (1 + shocks.get(asset, 0))
        new_total += shocked
        breakdown[asset] = shocked - val
    return new_total, new_total - total, breakdown

def monte_carlo(current_value, monthly_contrib, years, profile_name, n_sims=1000):
    """Return (p10, p25, p50, p75, p90, sample_year_medians)."""
    params = {
        "Conservative":          (0.040, 0.050),
        "Moderately Conservative":(0.050, 0.080),
        "Balanced":              (0.065, 0.110),
        "Growth":                (0.080, 0.150),
        "Aggressive":            (0.090, 0.190),
    }
    mu_a, sig_a = params.get(profile_name, (0.065, 0.110))
    months = years * 12
    m_mu   = mu_a  / 12
    m_sig  = sig_a / math.sqrt(12)

    random.seed(42)
    finals = []
    yearly_all = [[] for _ in range(years + 1)]
    yearly_all[0] = [current_value] * n_sims

    for sim in range(n_sims):
        val = float(current_value)
        for yr in range(1, years + 1):
            for _ in range(12):
                r = random.gauss(m_mu, m_sig)
                val = max(0.0, val * (1 + r) + monthly_contrib)
            yearly_all[yr].append(val)
        finals.append(val)

    finals.sort()
    pct = lambda p: finals[max(0, int(p * n_sims) - 1)]
    p10, p25, p50, p75, p90 = pct(0.10), pct(0.25), pct(0.50), pct(0.75), pct(0.90)

    # Median by year for fan chart
    year_medians = {}
    year_p10     = {}
    year_p90     = {}
    for yr in range(years + 1):
        s = sorted(yearly_all[yr])
        n = len(s)
        year_medians[yr] = s[n // 2]
        year_p10[yr]     = s[max(0, int(0.10 * n) - 1)]
        year_p90[yr]     = s[min(n - 1, int(0.90 * n))]

    return p10, p25, p50, p75, p90, year_medians, year_p10, year_p90

def smart_allocate(new_money, holdings, tgts, total):
    """Allocate new_money to minimise distance from target; return {asset: amount}."""
    projected_total = total + new_money
    needs = {}
    for asset in ASSET_NAMES:
        target_val = projected_total * tgts.get(asset, 0) / 100
        current_val = holdings.get(asset, 0)
        gap = target_val - current_val
        if gap > 0:
            needs[asset] = gap
    if not needs:
        return {a: 0 for a in ASSET_NAMES}
    total_need = sum(needs.values())
    result = {}
    running = 0
    items = list(needs.items())
    for i, (asset, gap) in enumerate(items):
        if i == len(items) - 1:
            result[asset] = new_money - running
        else:
            alloc = round(new_money * gap / total_need / 100) * 100
            result[asset] = alloc
            running += alloc
    return result

def cgt_cost(sell_amount, cost_base_pct, marginal_rate, held_over_12m=True):
    """Approximate CGT liability."""
    cost_base = sell_amount * cost_base_pct / 100
    gross_gain = max(0.0, sell_amount - cost_base)
    if held_over_12m:
        taxable_gain = gross_gain * 0.50  # 50% CGT discount
    else:
        taxable_gain = gross_gain
    return taxable_gain * marginal_rate / 100

def recovery_years(loss_pct, annual_return):
    """Years to recover from a loss_pct loss given annual_return."""
    if annual_return <= 0 or loss_pct <= 0:
        return None
    # Solve: (1 - loss_pct) * (1 + r)^n = 1
    if loss_pct >= 1:
        return None
    return math.log(1 / (1 - loss_pct)) / math.log(1 + annual_return)

# ═══════════════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════════════

def advisor(text, kind="wisdom"):
    pal = {
        "wisdom":  (NSOFT, NAVY),
        "caution": (GSOFT, GOLD),
        "good":    ("#EAF2EA", GREEN),
        "warn":    ("#FAF0E0", AMBER),
        "alert":   (RSOFT, RED),
    }
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
        f"</div></div>",
        unsafe_allow_html=True,
    )

def slabel(text):
    st.markdown(
        f"<p style='font-family:{FM};font-size:0.56rem;letter-spacing:0.22em;"
        f"text-transform:uppercase;color:{MUTED};margin:1.6rem 0 0.8rem;"
        f"padding-bottom:0.5rem;border-bottom:1px solid {BORDER};'>{text}</p>",
        unsafe_allow_html=True,
    )

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
                f"margin-top:6px;'>{note}</div></div>",
                unsafe_allow_html=True,
            )

def banner(text, kind="info"):
    pal = {"info": (NSOFT, NAVY), "good": ("#EAF2EA", GREEN),
           "warn": (GSOFT, AMBER), "bad": (RSOFT, RED)}
    bg, bdr = pal.get(kind, pal["info"])
    st.markdown(
        f"<div style='background:{bg};border:1px solid {BORDER};border-left:3px solid {bdr};"
        f"border-radius:0 6px 6px 0;padding:10px 14px;font-family:{FB};"
        f"font-size:0.875rem;color:{TEXT};line-height:1.65;margin:0.4rem 0;'>{text}</div>",
        unsafe_allow_html=True,
    )

def htable(headers, rows):
    hdr = "".join(
        f"<th style='text-align:left;padding:0.4rem 0.8rem;border-bottom:1px solid {BORDER};"
        f"font-family:{FM};font-size:0.56rem;text-transform:uppercase;letter-spacing:0.12em;"
        f"color:{MUTED};background:{CARD};white-space:nowrap;font-weight:500;'>{h}</th>"
        for h in headers
    )
    body = ""
    for i, row in enumerate(rows):
        bg = CARD if i % 2 == 0 else "#F8F6F0"
        cells = "".join(
            f"<td style='padding:0.4rem 0.8rem;border-bottom:1px solid {BORDER};"
            f"font-family:{FB};font-size:0.82rem;color:{TEXT};background:{bg};'>{c}</td>"
            for c in row
        )
        body += f"<tr>{cells}</tr>"
    st.markdown(
        f"<div style='border:1px solid {BORDER};border-radius:8px;overflow:hidden;"
        f"overflow-x:auto;margin:0.5rem 0 1rem;'>"
        f"<table style='width:100%;border-collapse:collapse;background:{CARD};'>"
        f"<thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )

def donut(labels, values, colors, center=""):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.62,
        marker=dict(colors=colors, line=dict(color=BG, width=3)),
        textinfo="label+percent",
        textfont=dict(family="Source Serif 4, serif", size=11, color=TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<br>%{value:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10), height=260, showlegend=False,
        font=dict(family="Source Serif 4, serif", color=TEXT),
        annotations=[dict(
            text=center, x=0.5, y=0.5,
            font=dict(size=13, family="Cormorant Garamond, serif", color=TEXT),
            showarrow=False,
        )] if center else [],
    )
    return fig

def health_gauge(score):
    """Render a colour-coded health score widget."""
    if score >= 75:
        clr, label = GREEN, "Healthy"
    elif score >= 50:
        clr, label = GOLD, "Needs Attention"
    else:
        clr, label = RED, "Significant Gaps"
    pct = score  # already 0-100
    st.markdown(
        f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:8px;"
        f"padding:18px 20px;border-left:3px solid {clr};'>"
        f"<div style='font-family:{FM};font-size:0.54rem;letter-spacing:0.18em;"
        f"text-transform:uppercase;color:{MUTED};margin-bottom:8px;'>Portfolio Health Score</div>"
        f"<div style='display:flex;align-items:baseline;gap:0.5rem;'>"
        f"<div style='font-family:{FH};font-size:2.8rem;color:{clr};font-weight:500;line-height:1;'>{score}</div>"
        f"<div style='font-family:{FM};font-size:0.72rem;color:{MUTED};'>/100</div>"
        f"<div style='font-family:{FM};font-size:0.65rem;letter-spacing:0.12em;"
        f"text-transform:uppercase;color:{clr};margin-left:0.5rem;'>{label}</div>"
        f"</div>"
        f"<div style='height:5px;background:{BORDER};border-radius:3px;margin:10px 0 0;overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;background:{clr};border-radius:3px;'></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Source+Serif+4:ital,wght@0,300;0,400;0,500;1,300;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background-color: {BG} !important;
    font-family: {FB};
    color: {TEXT};
}}
.block-container {{ padding: 1.8rem 2rem 3rem; max-width: 1100px; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}

h1, h2, h3, h4 {{ font-family: {FH} !important; font-weight: 500 !important; color: {TEXT} !important; }}
p, span, li {{ color: {TEXT} !important; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 0; border-bottom: 1px solid {BORDER}; background: transparent; }}
.stTabs [data-baseweb="tab"] {{
    font-family: {FM}; font-size: 0.60rem; letter-spacing: 0.14em;
    text-transform: uppercase; color: {MUTED}; background: transparent;
    border: none; border-bottom: 2px solid transparent; padding: 13px 20px;
}}
.stTabs [aria-selected="true"] {{
    color: {NAVY} !important; border-bottom: 2px solid {NAVY} !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {NAVY} !important; height: 2px !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 1.5rem; background: transparent; }}

div[data-testid="stNumberInput"] label, div[data-testid="stSelectbox"] label {{
    font-family: {FM} !important; font-size: 0.58rem !important;
    letter-spacing: 0.16em !important; text-transform: uppercase !important; color: {MUTED} !important;
}}
.stNumberInput input {{
    background: {CARD} !important; border: 1px solid {BORDER} !important;
    color: {TEXT} !important; font-family: {FM} !important;
    font-size: 0.9rem !important; border-radius: 6px !important;
}}
.stNumberInput button {{ background: {CARD} !important; color: {TEXT} !important; border-color: {BORDER} !important; }}
.stSelectbox > div > div {{ background: {CARD} !important; border: 1px solid {BORDER} !important; color: {TEXT} !important; border-radius: 6px !important; }}
[role="listbox"] *, [role="option"] {{ background: {CARD} !important; color: {TEXT} !important; font-family: {FB} !important; }}
.stRadio > div > label {{ font-family: {FB} !important; font-size: 0.875rem !important; color: {TEXT} !important; font-weight: 300 !important; }}
div[data-testid="stRadio"] > label {{ font-family: {FM} !important; font-size: 0.58rem !important; letter-spacing: 0.16em !important; text-transform: uppercase !important; color: {MUTED} !important; }}
.stSlider label {{ font-family: {FM} !important; font-size: 0.58rem !important; letter-spacing: 0.16em !important; text-transform: uppercase !important; color: {MUTED} !important; }}
.stButton > button {{
    background-color: {NAVY} !important; color: #FFFFFF !important;
    border: none !important; border-radius: 6px !important;
    font-family: {FM} !important; font-size: 0.68rem !important;
    letter-spacing: 0.14em !important; text-transform: uppercase !important;
    padding: 0.65rem 2rem !important;
}}
.stButton > button:hover {{ opacity: 0.82 !important; }}
div[data-testid="stExpander"] {{ background: {CARD} !important; border: 1px solid {BORDER} !important; border-radius: 8px !important; }}
div[data-testid="stExpander"] summary, div[data-testid="stExpander"] summary span {{
    font-family: {FM} !important; font-size: 0.62rem !important;
    letter-spacing: 0.14em !important; text-transform: uppercase !important; color: {MUTED} !important;
}}
hr {{ border: none; border-top: 1px solid {BORDER}; margin: 1.4rem 0; }}
.score-track {{ height: 5px; background: {BORDER}; border-radius: 3px; margin: 10px 0 4px; overflow: hidden; }}
.score-fill {{ height: 100%; border-radius: 3px; background: linear-gradient(to right, {NAVY}, {GOLD}); }}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TOP BAR
# ═══════════════════════════════════════════════════════════════

c1, _, c3 = st.columns([5, 2, 2])
with c1:
    st.markdown(
        f"<div style='font-family:{FH};font-size:2.4rem;color:{TEXT};line-height:1;font-weight:500;'>Meridian</div>"
        f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.22em;text-transform:uppercase;"
        f"color:{MUTED};margin-top:4px;'>Investment Risk &amp; Allocation Guide — Enhanced Edition</div>",
        unsafe_allow_html=True,
    )

with c3:
    cur_list = list(CUR_SYM.keys())
    st.selectbox("Currency", cur_list,
                 index=cur_list.index(st.session_state["currency"]),
                 key="currency", label_visibility="collapsed")

st.markdown(
    f"<div style='background:{GSOFT};border:1px solid {BORDER};border-radius:6px;"
    f"padding:7px 14px;margin:0.5rem 0 0.2rem;font-family:{FM};font-size:0.56rem;"
    f"letter-spacing:0.08em;text-transform:uppercase;color:{AMBER};'>"
    f"Educational purposes only · Not personal financial advice · "
    f"Consult a licensed financial adviser (AFSL) before investing</div>",
    unsafe_allow_html=True,
)

p_done = st.session_state["profile_done"]
h_done = total_pv() > 0
steps = [
    ("01  Risk Profile", p_done), ("02  Portfolio", h_done),
    ("03  Analysis", p_done and h_done), ("04  Rebalancing", p_done and h_done),
    ("05  Stress Test", p_done and h_done), ("06  Goal Projections", p_done and h_done),
]
step_html = ""
for label, done in steps:
    clr = GREEN if done else MUTED
    mark = "✓" if done else "○"
    step_html += (
        f"<span style='font-family:{FM};font-size:0.57rem;letter-spacing:0.1em;"
        f"text-transform:uppercase;color:{clr};margin-right:1.5rem;'>{mark}&nbsp; {label}</span>"
    )
st.markdown(f"<div style='padding:0.6rem 0;'>{step_html}</div>", unsafe_allow_html=True)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Risk Assessment", "My Portfolio",
    "Allocation Analysis", "Rebalancing Plan",
    "Stress Test", "Goal Projections",
])

# ──────────────────────────────────────────────────────────────
# TAB 1 — RISK ASSESSMENT
# ──────────────────────────────────────────────────────────────

with tab1:
    advisor(
        "Before any allocation decision, we must understand your genuine relationship with risk. "
        "The ten questions below are drawn from decades of client practice. "
        "Answer each honestly — the accuracy of everything that follows depends on it.",
        kind="wisdom",
    )
    slabel("The Risk Questionnaire")

    total_score = 0
    for i, (title, question, insight, options) in enumerate(QUESTIONS):
        qkey = f"q{i+1}"
        st.markdown(
            f"<p style='font-family:{FH};font-size:1.05rem;color:{TEXT};font-weight:500;"
            f"margin:1.4rem 0 0.15rem;'>{title}</p>"
            f"<p style='font-family:{FB};font-size:0.85rem;color:{MUTED};font-weight:300;"
            f"margin:0 0 0.5rem;font-style:italic;'>{question}</p>",
            unsafe_allow_html=True,
        )
        selected_idx = st.radio(
            label=title,
            options=list(range(len(options))),
            format_func=lambda x, opts=options: opts[x],
            index=st.session_state[qkey],
            key=f"radio_{qkey}",
            label_visibility="collapsed",
        )
        st.session_state[qkey] = selected_idx
        total_score += selected_idx + 1
        with st.expander("Adviser perspective"):
            st.markdown(
                f"<p style='font-family:{FB};font-size:0.875rem;color:{TEXT};"
                f"line-height:1.7;font-weight:300;font-style:italic;padding:0.3rem 0;'>{insight}</p>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Calculate My Risk Profile"):
        profile_name = get_profile(total_score)
        st.session_state["risk_score"]   = total_score
        st.session_state["risk_profile"] = profile_name
        st.session_state["profile_done"] = True
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

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
            unsafe_allow_html=True,
        )

        # Drawdown $ estimate (needs portfolio value)
        total_val = total_pv()
        if total_val > 0:
            draw_est = total_val * prof["draw_mid"]
            kpi([
                ("Expected Return",     prof["ret"],     "Historical estimate p.a.", True),
                ("Max Drawdown Range",  prof["draw"],    "Typical correction depth", False),
                ("Est. $ Drawdown",     fmt(draw_est),   "At your current portfolio", False),
                ("Suited Horizon",      prof["horizon"], "Minimum recommended", False),
            ])
        else:
            kpi([
                ("Expected Return",    prof["ret"],     "Historical estimate p.a.", True),
                ("Max Drawdown Range", prof["draw"],    "Typical correction depth", False),
                ("Suited Horizon",     prof["horizon"], "Minimum recommended", False),
            ])

        st.markdown("<br>", unsafe_allow_html=True)
        advisor(prof["note"], kind="wisdom")

        slabel("Indicative Target Allocation")
        tgts = prof["targets"]
        active_t = {k: v for k, v in tgts.items() if v > 0}
        col_ch, col_lg = st.columns([1, 1])
        with col_ch:
            fig = donut(
                list(active_t.keys()), list(active_t.values()),
                [ASSET_COLORS[ASSET_NAMES.index(k)] for k in active_t],
                f"<b>{pname[:4]}.</b>",
            )
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
                    f"<div style='font-family:{FB};font-size:0.82rem;color:{TEXT};flex:1;font-weight:300;'>{asset}</div>"
                    f"<div style='font-family:{FM};font-size:0.82rem;color:{NAVY};font-weight:500;'>{pctv}%</div></div>",
                    unsafe_allow_html=True,
                )


# ──────────────────────────────────────────────────────────────
# TAB 2 — MY PORTFOLIO  (+ Health Score)
# ──────────────────────────────────────────────────────────────

with tab2:
    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment first.", "info")
    else:
        advisor(
            "Enter the current market value of each asset class — super, shares, ETFs, "
            "investment property, bonds, and cash. The full picture. "
            "Investors who assess only part of their wealth routinely take more risk than they realise.",
            kind="wisdom",
        )
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
                    unsafe_allow_html=True,
                )
                st.number_input(name, min_value=0, step=1000, key=key, label_visibility="collapsed")

        total = total_pv()
        if total == 0:
            st.markdown("<br>", unsafe_allow_html=True)
            banner("Enter your holdings above to see allocation.", "info")
        else:
            st.markdown("---")
            holdings = pv()
            active = {k: v for k, v in holdings.items() if v > 0}
            pname   = st.session_state["risk_profile"]
            tgts    = PROFILES[pname]["targets"]

            # ── Portfolio Health Score ──────────────────────────
            slabel("Portfolio Health Score")
            hs, ha, hd, hl = portfolio_health_score(holdings, tgts, total)
            hcol1, hcol2 = st.columns([1, 2], gap="large")
            with hcol1:
                health_gauge(hs)
            with hcol2:
                st.markdown(
                    f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem;margin-top:0.2rem;'>",
                    unsafe_allow_html=True,
                )
                for label, score, total_pts, tip in [
                    ("Alignment",      ha, 40, "How closely your holdings match your target profile"),
                    ("Diversification", hd, 30, "Spread across asset classes — avoids concentration risk"),
                    ("Liquidity Buffer", hl, 30, "Defensive asset weighting vs target"),
                ]:
                    bar_pct = score / total_pts * 100
                    clr = GREEN if bar_pct >= 70 else (GOLD if bar_pct >= 40 else RED)
                    st.markdown(
                        f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:8px;"
                        f"padding:14px 16px;'>"
                        f"<div style='font-family:{FM};font-size:0.53rem;letter-spacing:0.16em;"
                        f"text-transform:uppercase;color:{MUTED};margin-bottom:6px;'>{label}</div>"
                        f"<div style='font-family:{FH};font-size:1.5rem;color:{clr};line-height:1;'>"
                        f"{score}<span style='font-size:0.9rem;color:{MUTED};'>/{total_pts}</span></div>"
                        f"<div style='height:4px;background:{BORDER};border-radius:2px;margin:8px 0 6px;overflow:hidden;'>"
                        f"<div style='width:{bar_pct:.0f}%;height:100%;background:{clr};border-radius:2px;'></div></div>"
                        f"<div style='font-family:{FB};font-size:0.68rem;color:{MUTED};font-style:italic;'>{tip}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

            # Contextual health advice
            if hs >= 75:
                advisor("Your portfolio is well-structured. The primary task now is maintaining this alignment as markets drift — review quarterly and after large contributions.", kind="good")
            elif ha < 20:
                advisor("Your allocation differs significantly from your risk profile. This is the highest-priority item in your financial plan. The Rebalancing Plan tab has specific actions.", kind="alert")
            elif hd < 15:
                advisor("High concentration in one or two asset classes is your primary risk. A market shock in your dominant asset class has an outsized impact on your total wealth.", kind="caution")
            else:
                advisor("Some gaps exist between your current allocation and your target. These are manageable — the Rebalancing Plan tab shows the most tax-efficient path to close them.", kind="warn")

            # ── Allocation overview ─────────────────────────────
            st.markdown("---")
            slabel("Current Allocation")
            kpi([
                ("Total Portfolio",   fmt(total),          "All asset classes combined", True),
                ("Asset Classes",     str(len(active)),    "of 5 held (≥ 1%)", False),
                ("Largest Position",  max(active, key=active.get),
                 f"{max(active.values())/total*100:.0f}% of portfolio", False),
                ("Health Score",      f"{hs}/100",         "Alignment · Divers. · Liquidity", False),
            ])
            st.markdown("<br>", unsafe_allow_html=True)
            col_c, col_d = st.columns([1, 1])
            with col_c:
                fig2 = donut(
                    list(active.keys()), list(active.values()),
                    [ASSET_COLORS[ASSET_NAMES.index(k)] for k in active],
                    f"<b>{fmt(total)}</b>",
                )
                st.plotly_chart(fig2, use_container_width=True)
            with col_d:
                st.markdown("<br>", unsafe_allow_html=True)
                for asset in sorted(holdings, key=lambda x: holdings[x], reverse=True):
                    val = holdings[asset]
                    if val == 0:
                        continue
                    pctv = val / total * 100
                    clr  = ASSET_COLORS[ASSET_NAMES.index(asset)]
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:0.7rem;"
                        f"padding:0.45rem 0;border-bottom:1px solid {BORDER};'>"
                        f"<div style='width:10px;height:10px;border-radius:50%;background:{clr};flex-shrink:0;'></div>"
                        f"<div style='font-family:{FB};font-size:0.82rem;color:{TEXT};flex:1;font-weight:300;'>{asset}</div>"
                        f"<div style='font-family:{FM};font-size:0.72rem;color:{MUTED};margin-right:0.5rem;'>{pctv:.1f}%</div>"
                        f"<div style='font-family:{FM};font-size:0.82rem;color:{TEXT};font-weight:500;'>{fmt(val)}</div></div>",
                        unsafe_allow_html=True,
                    )

            for asset, val in holdings.items():
                if val and val / total * 100 > 60:
                    st.markdown("<br>", unsafe_allow_html=True)
                    advisor(
                        f"{asset} represents {val/total*100:.0f}% of your portfolio. "
                        "Even excellent asset classes experience prolonged downturns — the Stress Test tab "
                        "shows the specific dollar impact if this asset corrects sharply.",
                        kind="caution",
                    )
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
        pname    = st.session_state["risk_profile"]
        tgts     = PROFILES[pname]["targets"]
        holdings = pv()
        total    = total_pv()

        advisor(
            f"Your risk profile is <strong>{pname}</strong>. Below is a comparison between "
            "your current allocation and the target for this profile. The gaps are where "
            "the actionable decisions live.",
            kind="wisdom",
        )
        slabel("Current vs Target")

        cur_pcts = [holdings.get(a, 0) / total * 100 for a in ASSET_NAMES]
        tgt_pcts = [tgts.get(a, 0) for a in ASSET_NAMES]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="Current", x=ASSET_NAMES, y=cur_pcts, marker_color=GOLD,
            hovertemplate="%{x}<br>Current: %{y:.1f}%<extra></extra>",
        ))
        fig3.add_trace(go.Bar(
            name="Target", x=ASSET_NAMES, y=tgt_pcts, marker_color=NAVY,
            hovertemplate="%{x}<br>Target: %{y:.1f}%<extra></extra>",
        ))
        fig3.update_layout(
            barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10), height=280,
            legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                        font=dict(family="IBM Plex Mono", size=10, color=MUTED),
                        orientation="h", y=1.08),
            xaxis=dict(showgrid=False, color=MUTED,
                       tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED)),
            yaxis=dict(showgrid=True, gridcolor=BORDER,
                       tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED),
                       ticksuffix="%"),
            font=dict(family="Source Serif 4, serif", color=TEXT),
        )
        st.plotly_chart(fig3, use_container_width=True)

        slabel("Gap Analysis")
        rows = []
        overs, unders = [], []
        for asset in ASSET_NAMES:
            cp  = holdings.get(asset, 0) / total * 100
            tp  = tgts.get(asset, 0)
            gap = cp - tp
            cv  = holdings.get(asset, 0)
            tv  = total * tp / 100
            dv  = cv - tv
            if gap > 5:
                status = f"<span style='color:{RED};font-weight:500;'>Overweight +{gap:.1f}%</span>"
                overs.append((asset, gap))
            elif gap < -5:
                status = f"<span style='color:{AMBER};font-weight:500;'>Underweight {gap:.1f}%</span>"
                unders.append((asset, gap))
            else:
                status = f"<span style='color:{GREEN};'>On target ({gap:+.1f}%)</span>"
            rows.append([asset, f"{cp:.1f}%", f"{tp:.0f}%", status,
                         fmt(cv), fmt(tv), fmt(dv)])

        htable(["Asset Class", "Current %", "Target %", "Status",
                "Current Value", "Target Value", "Difference"], rows)

        if overs:
            b = max(overs, key=lambda x: x[1])
            advisor(
                f"Your largest overweight is {b[0]} at +{b[1]:.1f}% above target. "
                "This commonly develops as strong-performing assets drift upward without rebalancing. "
                "See the Rebalancing Plan for tax-efficient reduction strategies.",
                kind="caution",
            )
        if unders:
            b = min(unders, key=lambda x: x[1])
            advisor(
                f"Your most notable underweight is {b[0]}, {abs(b[1]):.1f}% below target. "
                "Underweights in defensive assets leave the portfolio more exposed to downturns "
                "than your risk profile would suggest — direct new contributions here first.",
                kind="caution",
            )
        if not overs and not unders:
            advisor(
                "Your portfolio is well-aligned with your risk profile. "
                "The primary task is maintaining this alignment as markets drift — review quarterly.",
                kind="good",
            )

        slabel("Visual Comparison")
        col_l, col_r = st.columns(2, gap="large")
        with col_l:
            st.markdown(
                f"<p style='font-family:{FM};font-size:0.58rem;letter-spacing:0.14em;"
                f"text-transform:uppercase;color:{MUTED};text-align:center;'>Current</p>",
                unsafe_allow_html=True,
            )
            a_act = {k: v for k, v in holdings.items() if v > 0}
            st.plotly_chart(
                donut(list(a_act.keys()), list(a_act.values()),
                      [ASSET_COLORS[ASSET_NAMES.index(k)] for k in a_act], "Current"),
                use_container_width=True,
            )
        with col_r:
            st.markdown(
                f"<p style='font-family:{FM};font-size:0.58rem;letter-spacing:0.14em;"
                f"text-transform:uppercase;color:{MUTED};text-align:center;'>Target — {pname}</p>",
                unsafe_allow_html=True,
            )
            t_act = {k: v for k, v in tgts.items() if v > 0}
            st.plotly_chart(
                donut(list(t_act.keys()), list(t_act.values()),
                      [ASSET_COLORS[ASSET_NAMES.index(k)] for k in t_act], pname[:4] + "."),
                use_container_width=True,
            )


# ──────────────────────────────────────────────────────────────
# TAB 4 — REBALANCING PLAN  (+ CGT estimator + Smart Contributions)
# ──────────────────────────────────────────────────────────────

with tab4:
    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment first.", "info")
    elif total_pv() == 0:
        banner("Enter your holdings in the My Portfolio tab.", "info")
    else:
        pname    = st.session_state["risk_profile"]
        tgts     = PROFILES[pname]["targets"]
        holdings = pv()
        total    = total_pv()

        advisor(
            "Rebalancing is the discipline of systematically selling what has done well "
            "and buying what has done poorly — without emotion or prediction. "
            "Consider capital gains tax before executing any sale, particularly for assets held "
            "outside superannuation.",
            kind="wisdom",
        )

        # ── CGT Settings ────────────────────────────────────────
        slabel("Tax Settings  (used for CGT estimates below)")
        cgt_col1, cgt_col2 = st.columns(2, gap="large")
        with cgt_col1:
            st.session_state["cgt_rate"] = st.slider(
                "Marginal tax rate (%)", 0, 47, int(st.session_state["cgt_rate"]), 1,
                help="Your marginal income tax rate. The CGT discount (50%) is applied automatically for assets held >12 months.",
            )
        with cgt_col2:
            st.session_state["cost_base_pct"] = st.slider(
                "Average cost base (% of current value)", 20, 100,
                int(st.session_state["cost_base_pct"]), 5,
                help="If your holdings have doubled in value, set this to ~50%. This estimates your embedded capital gain.",
            )

        # ── Rebalancing Actions ─────────────────────────────────
        slabel("Rebalancing Actions")
        sells, buys, holds_list = [], [], []
        for asset in ASSET_NAMES:
            cv  = holdings.get(asset, 0)
            cp  = cv / total * 100
            tp  = tgts.get(asset, 0)
            tv  = total * tp / 100
            diff = cv - tv
            gap  = cp - tp
            if gap > 2:
                sells.append((asset, diff, cp, tp))
            elif gap < -2:
                buys.append((asset, abs(diff), cp, tp))
            else:
                holds_list.append((asset, cp, tp))
        sells.sort(key=lambda x: x[1], reverse=True)
        buys.sort(key=lambda x: x[1], reverse=True)

        if sells:
            st.markdown(
                f"<p style='font-family:{FH};font-size:1.1rem;color:{RED};"
                f"font-weight:500;margin:0.5rem 0 0.8rem;'>Reduce — Overweight Positions</p>",
                unsafe_allow_html=True,
            )
            for i, (asset, amount, cp, tp) in enumerate(sells):
                cgt_est = cgt_cost(amount, st.session_state["cost_base_pct"],
                                   st.session_state["cgt_rate"])
                net_proceeds = amount - cgt_est
                pri = "High priority" if i == 0 else "Secondary"
                st.markdown(
                    f"<div style='background:{CARD};border:1px solid {BORDER};"
                    f"border-left:3px solid {RED};border-radius:0 8px 8px 0;"
                    f"padding:1rem 1.3rem;margin-bottom:0.75rem;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;'>"
                    f"<span style='font-family:{FH};font-size:0.95rem;color:{TEXT};font-weight:500;'>Reduce {asset}</span>"
                    f"<span style='font-family:{FM};font-size:0.9rem;color:{RED};font-weight:500;'>Sell {fmt(amount)}</span></div>"
                    f"<p style='font-family:{FB};font-size:0.82rem;color:{MUTED};font-weight:300;margin:0 0 0.25rem;'>"
                    f"Currently {cp:.1f}% → Target {tp:.0f}%</p>"
                    f"<div style='display:flex;gap:1.5rem;'>"
                    f"<span style='font-family:{FM};font-size:0.62rem;color:{AMBER};'>"
                    f"Est. CGT liability: {fmt(cgt_est)} (50% discount applied)</span>"
                    f"<span style='font-family:{FM};font-size:0.62rem;color:{MUTED};'>"
                    f"Net after tax: {fmt(net_proceeds)}</span>"
                    f"</div>"
                    f"<p style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;"
                    f"text-transform:uppercase;color:{RED};margin:0.4rem 0 0;'>{pri}</p></div>",
                    unsafe_allow_html=True,
                )

        if buys:
            st.markdown(
                f"<p style='font-family:{FH};font-size:1.1rem;color:{GREEN};"
                f"font-weight:500;margin:1.2rem 0 0.8rem;'>Increase — Underweight Positions</p>",
                unsafe_allow_html=True,
            )
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
                    unsafe_allow_html=True,
                )

        if holds_list:
            slabel("Hold — On Target")
            ht = " &nbsp;·&nbsp; ".join(
                f"<span style='color:{GREEN};font-weight:500;'>✓</span> {a} ({c:.1f}%)"
                for a, c, _ in holds_list
            )
            st.markdown(
                f"<p style='font-family:{FB};font-size:0.875rem;color:{MUTED};font-weight:300;'>{ht}</p>",
                unsafe_allow_html=True,
            )

        # ── Smart Contribution Planner ──────────────────────────
        st.markdown("---")
        slabel("Smart Contribution Planner")
        advisor(
            "The most tax-efficient rebalancing method is directing new contributions into underweight "
            "asset classes — no CGT is triggered, and the portfolio drifts toward target naturally. "
            "Enter an amount you plan to invest and I will allocate it optimally.",
            kind="wisdom",
        )
        contrib_amount = st.number_input(
            "New investment amount to allocate", min_value=0, step=500,
            value=10000, key="contrib_input",
        )
        if contrib_amount > 0:
            allocs = smart_allocate(contrib_amount, holdings, tgts, total)
            alloc_rows = []
            for asset, amount in allocs.items():
                if amount > 0:
                    clr = ASSET_COLORS[ASSET_NAMES.index(asset)]
                    pct_of_contrib = amount / contrib_amount * 100
                    alloc_rows.append([
                        f"<span style='color:{clr};'>●</span> {asset}",
                        fmt(amount),
                        f"{pct_of_contrib:.0f}%",
                        "Closes underweight gap",
                    ])
            if alloc_rows:
                htable(["Asset Class", "Allocate", "% of New Money", "Reason"], alloc_rows)
                advisor(
                    f"Directing {fmt(contrib_amount)} this way achieves rebalancing progress "
                    "with zero CGT liability. After this contribution, run the analysis tab to see "
                    "your updated gap.",
                    kind="good",
                )
            else:
                banner("Your portfolio is already aligned — new contributions can be spread proportionally to target weights.", "good")

        # ── Full Summary Table ──────────────────────────────────
        slabel("Full Rebalancing Summary")
        srows = []
        total_cgt = 0
        for asset in ASSET_NAMES:
            cv = holdings.get(asset, 0)
            cp = cv / total * 100
            tp = tgts.get(asset, 0)
            tv = total * tp / 100
            diff = tv - cv
            if diff > 500:
                act = f"<span style='color:{GREEN};font-weight:500;'>Buy {fmt(diff)}</span>"
                cgt_cell = "—"
            elif diff < -500:
                cgt_e = cgt_cost(abs(diff), st.session_state["cost_base_pct"],
                                 st.session_state["cgt_rate"])
                total_cgt += cgt_e
                act = f"<span style='color:{RED};font-weight:500;'>Sell {fmt(abs(diff))}</span>"
                cgt_cell = f"<span style='color:{AMBER};'>{fmt(cgt_e)}</span>"
            else:
                act = f"<span style='color:{MUTED};'>Hold</span>"
                cgt_cell = "—"
            srows.append([asset, f"{cp:.1f}%", fmt(cv), f"{tp:.0f}%", fmt(tv), act, cgt_cell])
        htable(["Asset Class", "Current %", "Current Value", "Target %",
                "Target Value", "Action", "Est. CGT"], srows)

        if total_cgt > 0:
            advisor(
                f"Total estimated CGT liability for this rebalance: {fmt(total_cgt)}. "
                "This assumes 50% CGT discount (held >12 months). Consider rebalancing within "
                "super first, and using new contributions outside super to reduce taxable events.",
                kind="caution",
            )

        slabel("Before You Act")
        for title, text, kind in [
            ("Superannuation First",
             "Rebalancing within super is typically the most tax-efficient first step — no CGT on asset sales inside an accumulation-phase super fund. Confirm with your fund's rules.",
             "wisdom"),
            ("Use New Contributions",
             "Direct new contributions into underweight classes rather than selling overweight ones. This achieves gradual rebalancing without any tax events — the lowest-friction long-term approach.",
             "good"),
            ("Capital Gains Tax",
             "Selling appreciated assets outside super may trigger CGT. If held 12+ months, the 50% discount applies. The CGT estimates above use your inputs but are indicative only — consult your accountant.",
             "caution"),
            ("Review Annually",
             "Set a calendar reminder to review once per year, or whenever any class drifts 10+ percentage points from target. Over-frequent rebalancing generates costs without proportional benefit.",
             "wisdom"),
        ]:
            with st.expander(title):
                advisor(text, kind=kind)

        st.markdown("<br>", unsafe_allow_html=True)
        advisor(
            "This plan gives you a clear, evidence-based framework. The harder part — and where a "
            "licensed adviser adds the most value — is executing in the most tax-efficient sequence "
            "for your specific circumstances. Use this as a starting point for that conversation.",
            kind="wisdom",
        )


# ──────────────────────────────────────────────────────────────
# TAB 5 — STRESS TEST
# ──────────────────────────────────────────────────────────────

with tab5:
    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment first.", "info")
    elif total_pv() == 0:
        banner("Enter your holdings in the My Portfolio tab.", "info")
    else:
        holdings = pv()
        total    = total_pv()
        pname    = st.session_state["risk_profile"]
        prof     = PROFILES[pname]

        advisor(
            "Stress testing translates abstract percentage declines into actual dollar impacts "
            "on your specific portfolio. The numbers below are not predictions — they are "
            "calibrated historical scenarios that have occurred before and will occur again. "
            "The question is not whether markets will fall, but whether your portfolio can absorb it.",
            kind="wisdom",
        )

        slabel("Scenario Selector")
        scenario_name = st.radio(
            "Select scenario", list(STRESS_SCENARIOS.keys()),
            horizontal=True, label_visibility="collapsed",
        )
        scenario = STRESS_SCENARIOS[scenario_name]

        new_total, net_loss, breakdown = stress_test(holdings, total, scenario)
        pct_loss = abs(net_loss) / total * 100 if total > 0 else 0

        st.markdown(
            f"<div style='background:{RSOFT};border:1px solid {BORDER};"
            f"border-left:3px solid {RED};border-radius:0 8px 8px 0;"
            f"padding:1.2rem 1.5rem;margin:1rem 0;'>"
            f"<div style='font-family:{FH};font-size:1.3rem;color:{RED};font-weight:500;"
            f"margin-bottom:0.3rem;'>{scenario['headline']}</div>"
            f"<p style='font-family:{FB};font-size:0.875rem;color:{TEXT};font-weight:300;"
            f"line-height:1.65;margin:0;'>{scenario['desc']}</p></div>",
            unsafe_allow_html=True,
        )

        kpi([
            ("Portfolio Before",   fmt(total),            "Current value", True),
            ("Estimated Loss",     fmt(net_loss),         f"−{pct_loss:.1f}% of portfolio", False),
            ("Portfolio After",    fmt(new_total),        "Approximate post-crash value", False),
            ("Recovery Period",    f"~{scenario['recovery_years']:.0f}y",
             f"Historical avg at {prof['ret_mid']*100:.0f}% p.a. return", False),
        ])

        # Asset-by-asset impact
        slabel("Impact by Asset Class")
        impact_rows = []
        fig_bar = go.Figure()
        bar_assets, bar_losses, bar_colors = [], [], []
        for asset in ASSET_NAMES:
            val      = holdings.get(asset, 0)
            delta    = breakdown.get(asset, 0)
            shock    = scenario["shocks"].get(asset, 0)
            new_val  = val + delta
            if val == 0:
                continue
            clr = RED if delta < 0 else GREEN
            delta_str = (
                f"<span style='color:{RED};font-weight:500;'>{fmt(delta)}</span>"
                if delta < 0 else
                f"<span style='color:{GREEN};font-weight:500;'>+{fmt(delta)}</span>"
            )
            impact_rows.append([
                asset, fmt(val), f"{shock*100:+.0f}%", fmt(new_val), delta_str,
            ])
            bar_assets.append(asset.split(" ")[0])
            bar_losses.append(delta)
            bar_colors.append(RED if delta < 0 else GREEN)

        htable(["Asset Class", "Current Value", "Scenario Shock", "New Value", "P&L"], impact_rows)

        fig_bar.add_trace(go.Bar(
            x=bar_assets, y=bar_losses,
            marker_color=bar_colors,
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>",
        ))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10), height=220,
            xaxis=dict(showgrid=False, color=MUTED,
                       tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED)),
            yaxis=dict(showgrid=True, gridcolor=BORDER,
                       tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED),
                       tickprefix=sym()),
            font=dict(family="Source Serif 4, serif", color=TEXT),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Recovery timeline
        slabel("Recovery Timeline")
        ret_mid = prof["ret_mid"]
        rec_data = []
        years_range = list(range(0, 16))
        for sc_name, sc in STRESS_SCENARIOS.items():
            # After crash, value grows back at profile return rate
            shock_loss = sum(
                holdings.get(a, 0) * sc["shocks"].get(a, 0) for a in ASSET_NAMES
            )
            crashed = total + shock_loss
            vals = [crashed * (1 + ret_mid) ** y for y in years_range]
            rec_data.append((sc_name, vals))

        fig_rec = go.Figure()
        fig_rec.add_hline(y=total, line_dash="dash", line_color=NAVY, line_width=1.5,
                          annotation_text="Current Portfolio Value",
                          annotation_font=dict(family="IBM Plex Mono", size=9, color=NAVY))
        rec_colors = [GOLD, AMBER, RED]
        for (sc_name, vals), clr in zip(rec_data, rec_colors):
            fig_rec.add_trace(go.Scatter(
                x=years_range, y=vals, mode="lines", name=sc_name.split("  ")[0],
                line=dict(color=clr, width=2),
                hovertemplate="Year %{x}<br>%{y:,.0f}<extra></extra>",
            ))
        fig_rec.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10), height=280,
            legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                        font=dict(family="IBM Plex Mono", size=9, color=MUTED),
                        orientation="h", y=1.1),
            xaxis=dict(title="Years post-crash", showgrid=False, color=MUTED,
                       tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED)),
            yaxis=dict(showgrid=True, gridcolor=BORDER,
                       tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED),
                       tickprefix=sym()),
            font=dict(family="Source Serif 4, serif", color=TEXT),
        )
        st.plotly_chart(fig_rec, use_container_width=True)

        # Contextual commentary
        if pct_loss > prof["draw_mid"] * 100 * 1.3:
            advisor(
                f"In the {scenario_name.strip()} scenario, your portfolio could lose "
                f"{fmt(abs(net_loss))} — materially worse than the typical drawdown for a "
                f"{pname} investor. This suggests your current allocation carries more risk "
                f"than your profile implies. Review the Rebalancing Plan.",
                kind="alert",
            )
        elif pct_loss < prof["draw_mid"] * 100 * 0.7:
            advisor(
                f"Your defensive holdings cushion the impact well. In this scenario, your "
                f"estimated loss is {fmt(abs(net_loss))} — less than the typical {pname} "
                f"drawdown. This is what well-constructed defensive exposure is designed to do.",
                kind="good",
            )
        else:
            advisor(
                f"Your estimated {scenario_name.strip().lower()} loss of {fmt(abs(net_loss))} "
                f"is consistent with the expected drawdown for a {pname} portfolio. "
                f"Recovery to current value is projected in approximately {scenario['recovery_years']:.0f} years "
                f"at {ret_mid*100:.0f}% p.a. — assuming no additional contributions.",
                kind="wisdom",
            )


# ──────────────────────────────────────────────────────────────
# TAB 6 — GOAL PROJECTIONS  (Monte Carlo)
# ──────────────────────────────────────────────────────────────

with tab6:
    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment first.", "info")
    else:
        pname = st.session_state["risk_profile"]
        prof  = PROFILES[pname]
        total = total_pv()

        advisor(
            "Goal projections use a Monte Carlo simulation — 1 000 independent paths, each with "
            "random monthly returns drawn from your profile's historical distribution. "
            "The result is a probability band, not a prediction. Markets are not deterministic, "
            "but the distribution of outcomes over long horizons is remarkably stable.",
            kind="wisdom",
        )

        slabel("Projection Inputs")
        gc1, gc2, gc3 = st.columns(3, gap="large")
        with gc1:
            goal_amount = st.number_input(
                "Target Portfolio Value", min_value=0, step=50_000,
                value=int(st.session_state["goal_amount"]), key="goal_input",
            )
            st.session_state["goal_amount"] = goal_amount
        with gc2:
            goal_years = st.slider(
                "Investment Horizon (years)", 1, 40,
                int(st.session_state["goal_years"]), 1, key="goal_years_input",
            )
            st.session_state["goal_years"] = goal_years
        with gc3:
            monthly_contrib = st.number_input(
                "Monthly Contributions", min_value=0, step=250,
                value=int(st.session_state["monthly_contrib"]), key="contrib_monthly",
            )
            st.session_state["monthly_contrib"] = monthly_contrib

        start_value = total if total > 0 else 0
        if start_value == 0 and monthly_contrib == 0:
            banner("Enter either your current portfolio (My Portfolio tab) or a monthly contribution to run projections.", "info")
        else:
            with st.spinner("Running 1 000 Monte Carlo simulations…"):
                p10, p25, p50, p75, p90, yr_med, yr_p10, yr_p90 = monte_carlo(
                    start_value, monthly_contrib, goal_years, pname, n_sims=1000,
                )

            # Probability of reaching goal
            # Approximate: if p50 > goal → >50% chance; interpolate
            if p90 < goal_amount:
                prob_txt = "< 10%"
                prob_color = RED
            elif p75 < goal_amount:
                prob_txt = "10 – 25%"
                prob_color = AMBER
            elif p50 < goal_amount:
                prob_txt = "25 – 50%"
                prob_color = GOLD
            elif p25 < goal_amount:
                prob_txt = "50 – 75%"
                prob_color = GREEN
            elif p10 < goal_amount:
                prob_txt = "75 – 90%"
                prob_color = GREEN
            else:
                prob_txt = "> 90%"
                prob_color = GREEN

            total_contributed = start_value + monthly_contrib * goal_years * 12

            kpi([
                ("Starting Value",       fmt(start_value),        "Current portfolio", True),
                ("Total Contributed",    fmt(total_contributed),  f"{fmt(monthly_contrib)}/mo × {goal_years}y", False),
                ("Median Outcome",       fmt(p50),                "50th percentile (1 in 2 chance)", False),
                ("Probability of Goal",  prob_txt,
                 f"Reaching {fmt(goal_amount)}", False),
            ])

            # Fan chart
            slabel("Projection Fan Chart")
            years_x = list(range(goal_years + 1))
            med_y   = [yr_med[y] for y in years_x]
            p10_y   = [yr_p10[y] for y in years_x]
            p90_y   = [yr_p90[y] for y in years_x]

            fig_mc = go.Figure()

            # Shaded band p10-p90
            fig_mc.add_trace(go.Scatter(
                x=years_x + years_x[::-1],
                y=p90_y + p10_y[::-1],
                fill="toself",
                fillcolor=f"rgba(26,53,88,0.10)",
                line=dict(color="rgba(0,0,0,0)"),
                name="10th – 90th percentile",
                hoverinfo="skip",
            ))

            # Median line
            fig_mc.add_trace(go.Scatter(
                x=years_x, y=med_y,
                mode="lines", name="Median outcome",
                line=dict(color=NAVY, width=2.5),
                hovertemplate="Year %{x}<br>Median: %{y:,.0f}<extra></extra>",
            ))

            # p10 pessimistic
            fig_mc.add_trace(go.Scatter(
                x=years_x, y=p10_y, mode="lines", name="Pessimistic (10th)",
                line=dict(color=RED, width=1, dash="dot"),
                hovertemplate="Year %{x}<br>10th pct: %{y:,.0f}<extra></extra>",
            ))

            # p90 optimistic
            fig_mc.add_trace(go.Scatter(
                x=years_x, y=p90_y, mode="lines", name="Optimistic (90th)",
                line=dict(color=GREEN, width=1, dash="dot"),
                hovertemplate="Year %{x}<br>90th pct: %{y:,.0f}<extra></extra>",
            ))

            # Goal line
            if goal_amount > 0:
                fig_mc.add_hline(
                    y=goal_amount, line_dash="dash", line_color=GOLD, line_width=1.5,
                    annotation_text=f"Goal: {fmt(goal_amount)}",
                    annotation_font=dict(family="IBM Plex Mono", size=9, color=GOLD),
                )

            fig_mc.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10), height=340,
                legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0,
                            font=dict(family="IBM Plex Mono", size=9, color=MUTED),
                            orientation="h", y=1.08),
                xaxis=dict(title="Years", showgrid=False, color=MUTED,
                           tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED)),
                yaxis=dict(showgrid=True, gridcolor=BORDER,
                           tickfont=dict(family="IBM Plex Mono", size=9, color=MUTED),
                           tickprefix=sym()),
                font=dict(family="Source Serif 4, serif", color=TEXT),
            )
            st.plotly_chart(fig_mc, use_container_width=True)

            # Percentile table
            slabel("Outcome Distribution at Year " + str(goal_years))
            htable(
                ["Percentile", "Portfolio Value", "Interpretation"],
                [
                    ["90th (Optimistic)",  fmt(p90), "Only 10% of simulations exceed this"],
                    ["75th",               fmt(p75), "Better than 3 in 4 scenarios"],
                    ["50th (Median)",      fmt(p50), "The most likely single outcome"],
                    ["25th",               fmt(p25), "Worse than 3 in 4 scenarios"],
                    ["10th (Pessimistic)", fmt(p10), "Only 10% of simulations fall below this"],
                ],
            )

            # Contribution sensitivity
            slabel("What If I Contributed More?")
            sens_rows = []
            for extra in [0, 500, 1000, 2000, 3000]:
                _, _, s_p50, _, _ , _, _, _ = monte_carlo(
                    start_value, monthly_contrib + extra, goal_years, pname, n_sims=500,
                )
                hit = "✓" if s_p50 >= goal_amount else "✗"
                clr = GREEN if s_p50 >= goal_amount else MUTED
                sens_rows.append([
                    f"{fmt(monthly_contrib + extra)}/mo" if extra == 0 else f"+{fmt(extra)}/mo",
                    fmt(monthly_contrib * 12 * goal_years + extra * 12 * goal_years + start_value),
                    fmt(s_p50),
                    f"<span style='color:{clr};'>{hit} {'Reaches' if s_p50 >= goal_amount else 'Misses'} goal (median)</span>",
                ])
            htable(["Monthly Contribution", "Total Invested", "Median Outcome", "Goal Status"], sens_rows)

            # Contextual advice
            if prob_txt in ("> 90%", "75 – 90%"):
                advisor(
                    f"Your current plan has a strong probability of reaching {fmt(goal_amount)} "
                    f"over {goal_years} years. Consistency of contributions is more important "
                    "than return optimisation at this stage. Do not attempt to time markets — "
                    "every year out of the market compounds against you.",
                    kind="good",
                )
            elif prob_txt in ("50 – 75%", "25 – 50%"):
                gap_median = goal_amount - p50
                extra_needed = gap_median / (goal_years * 12) if goal_years > 0 else 0
                advisor(
                    f"Your median outcome is {fmt(p50)} — {fmt(gap_median)} short of your goal. "
                    f"An additional {fmt(extra_needed)}/month in contributions would close most of this gap. "
                    "Alternatively, extending your horizon by 2–3 years can significantly improve outcomes.",
                    kind="warn",
                )
            else:
                advisor(
                    f"The probability of reaching {fmt(goal_amount)} in {goal_years} years is low "
                    "under your current plan. Consider: increasing monthly contributions, extending "
                    "the timeline, or — if genuinely appropriate — reviewing whether a slightly higher "
                    "risk profile is warranted given your circumstances.",
                    kind="alert",
                )

            st.markdown("<br>", unsafe_allow_html=True)
            advisor(
                "Monte Carlo simulations use historical return and volatility parameters. "
                "They do not predict actual outcomes and do not account for sequence-of-returns risk, "
                "inflation, tax, or fees. Treat these as planning ranges, not guarantees. "
                "A licensed adviser can build a more precise cash-flow model for your situation.",
                kind="caution",
            )

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    f"<div style='font-family:{FM};font-size:0.56rem;color:{MUTED};"
    f"letter-spacing:0.1em;text-transform:uppercase;text-align:center;"
    f"padding-bottom:1.5rem;line-height:1.8;'>"
    f"Meridian · Investment Risk &amp; Allocation Guide — Enhanced Edition<br>"
    f"For educational purposes only · Not personal financial advice<br>"
    f"Consult a licensed financial adviser (AFSL) before investing</div>",
    unsafe_allow_html=True,
)
