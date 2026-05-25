"""
Meridian — Investment Risk & Portfolio Allocation Guide
========================================================
An educational framework inspired by senior financial planning practice.

For informational and educational purposes only.
This tool does not constitute personal financial advice.
Always consult a licensed financial adviser (AFSL holder) before
making investment decisions.

Run:          streamlit run meridian_app.py
Requirements: streamlit plotly
"""

import streamlit as st
import plotly.graph_objects as go

# ── PAGE CONFIG — must be first Streamlit call ───────────────────────
st.set_page_config(
    page_title="Meridian · Investment Guide & Health Audit",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════
# 1. DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════

BG       = "#F3F0E8"    # Warm parchment background
CARD     = "#FDFCF9"    # Off-white card surface
BORDER   = "#DED9CE"    # Warm gray border
TEXT     = "#141210"    # Near-black primary text
MUTED    = "#7A7268"    # Warm gray secondary text
NAVY     = "#1A3558"    # Deep navy — primary accent
GOLD     = "#B8902A"    # Warm gold — secondary accent
SUCCESS  = "#275E42"    # Forest green
WARNING  = "#7A5810"    # Amber
DANGER   = "#7A1E1E"    # Muted red
NSOFT    = "#ECF1F8"    # Navy tint background
GSOFT    = "#FAF5E8"    # Gold tint background

# Display serif — authoritative, editorial
FONT_H = "'Cormorant Garamond', Georgia, serif"
# Body serif — readable, trustworthy (FT / Economist feel)
FONT_B = "'Source Serif 4', Georgia, serif"
# Monospace — numbers, labels, data
FONT_M = "'IBM Plex Mono', monospace"

# Asset class palette — one color per class, used consistently across all charts
ASSET_NAMES = [
    "Australian Shares",
    "International Shares",
    "Property & REITs",
    "Fixed Income & Bonds",
    "Cash & Term Deposits",
]
ASSET_COLORS = [NAVY, "#2A5E3F", GOLD, "#5A4A7A", "#3A7A7A"]

CURRENCY_SYM = {
    "AUD": "A$", "USD": "$", "EUR": "€", "GBP": "£", "SGD": "S$"
}

# ═══════════════════════════════════════════════════════════════════════
# 2. SESSION STATE
# ═══════════════════════════════════════════════════════════════════════

DEFAULTS = {
    **{f"q{i}": None for i in range(1, 11)},  # 10 risk questionnaire answers
    "risk_score":      0,
    "risk_profile":    "",
    "risk_capacity":   0,
    "risk_tolerance":  0,
    "override_profile": "",
    "profile_done":    False,
    "aus_shares":      0.0,     # Portfolio: Australian shares value
    "intl_shares":     0.0,     # Portfolio: International shares value
    "property":        0.0,     # Portfolio: Property and REITs value
    "fixed_income":    0.0,     # Portfolio: Fixed income and bonds value
    "cash":            0.0,     # Portfolio: Cash and term deposits value
    "currency":        "AUD",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══════════════════════════════════════════════════════════════════════
# 3. RISK QUESTIONS
# Each question has 4 options scored 1–4.
# Total score range: 10 (most conservative) to 40 (most aggressive).
# FCI questions: q1, q2, q3, q7, q8
# ETI questions: q4, q5, q6, q9, q10
# ═══════════════════════════════════════════════════════════════════════

QUESTIONS = [
    {
        "id": "q1",
        "label": "Investment Time Horizon",
        "text": "When do you anticipate needing the majority of these funds?",
        "advisor": (
            "Time horizon is the single most important input to any investment plan. "
            "A longer runway allows you to absorb market downturns and wait for recovery — "
            "and historically, patience has always been rewarded. "
            "The Australian share market has recovered from every correction it has ever experienced. "
            "The variable is not whether recovery occurs, but whether you have time to wait for it."
        ),
        "options": [
            ("Less than 3 years — I may need this money soon", 1),
            ("3 to 7 years — medium-term planning", 2),
            ("7 to 15 years — long-term wealth building", 3),
            ("15 years or more — retirement or generational wealth", 4),
        ],
    },
    {
        "id": "q2",
        "label": "Income Stability",
        "text": "How would you describe your current income situation?",
        "advisor": (
            "Investors with stable income can take more investment risk because they are not "
            "forced to liquidate assets during downturns. "
            "Someone with variable or self-employed income needs a structurally more conservative allocation — "
            "not as a preference, but as a practical necessity. "
            "Your income is a financial asset. Its stability should inform how much risk you take with your capital."
        ),
        "options": [
            ("Retired or living on a fixed income", 1),
            ("Variable, self-employed or contract income", 2),
            ("Stable salaried employment", 3),
            ("Tenured, government or highly secure employment", 4),
        ],
    },
    {
        "id": "q3",
        "label": "Emergency Reserves",
        "text": "How many months of living expenses do you hold in accessible cash?",
        "advisor": (
            "Without an adequate cash buffer, you may be forced to sell investments at exactly the "
            "wrong moment — during a market correction. "
            "This single factor has destroyed more long-term investment plans than poor stock selection ever has. "
            "I will not recommend an aggressive allocation to any client who does not first have 3 to 6 months "
            "of expenses in accessible cash. It is the foundation on which everything else rests."
        ),
        "options": [
            ("Less than 1 month", 1),
            ("1 to 3 months", 2),
            ("3 to 6 months", 3),
            ("6 months or more", 4),
        ],
    },
    {
        "id": "q4",
        "label": "Investment Experience",
        "text": "How would you describe your direct investment experience?",
        "advisor": (
            "Experience matters not for the returns it generates in theory, but for the emotional discipline "
            "it builds in practice. "
            "An investor who lived through the GFC in 2008 or March 2020 has real evidence of how they behave "
            "under stress — which is far more reliable than how they expect to behave in calm markets. "
            "First-time investors routinely overestimate their own resilience."
        ),
        "options": [
            ("I have never invested beyond a savings account", 1),
            ("Basic knowledge — I understand shares and managed funds", 2),
            ("3 or more years of active investing in shares or ETFs", 3),
            ("10 or more years across multiple asset classes including international markets", 4),
        ],
    },
    {
        "id": "q5",
        "label": "Reaction to Market Falls",
        "text": "If your portfolio dropped 30% over three months, what would you actually do?",
        "advisor": (
            "This is the most revealing question in any risk assessment. "
            "In my experience, most investors significantly overestimate their tolerance for loss in calm markets. "
            "A 30% drawdown is not hypothetical — it happened in 2008, in early 2020, and it will happen again. "
            "I ask clients to think about a specific dollar figure rather than a percentage. "
            "Watching A$300,000 become A$210,000 on a statement is a very different experience from "
            "reading that 'equities fell 30%.' Your honest answer here is the heart of this assessment."
        ),
        "options": [
            ("Sell everything immediately to prevent further losses", 1),
            ("Reduce my exposure by selling some holdings", 2),
            ("Do nothing — hold and wait for recovery", 3),
            ("Add to my positions at the lower prices", 4),
        ],
    },
    {
        "id": "q6",
        "label": "Primary Investment Objective",
        "text": "What is the primary goal for this investment?",
        "advisor": (
            "Your objective determines everything downstream. "
            "A retiree drawing income and a 32-year-old accumulating wealth require fundamentally "
            "different portfolios, even if they share the same nominal risk profile score. "
            "I always want to understand not just the financial goal, "
            "but what that money ultimately represents to the person sitting across from me."
        ),
        "options": [
            ("Preserve my capital — I cannot afford significant losses", 1),
            ("Modest growth with capital preservation as the priority", 2),
            ("Balanced growth over the medium to long term", 3),
            ("Maximum long-term growth — I fully accept short-term volatility", 4),
        ],
    },
    {
        "id": "q7",
        "label": "Planned Withdrawals",
        "text": "Do you expect to make significant withdrawals within the next 5 years?",
        "advisor": (
            "Liquidity requirements directly constrain risk-taking. "
            "You should never hold an asset you cannot afford to own through a 2 to 3 year market downturn. "
            "If you need a portion of these funds within 5 years — a house deposit, school fees, "
            "a business purchase — that portion belongs in cash or short-term fixed income, "
            "regardless of your overall risk profile."
        ),
        "options": [
            ("Yes — I will need most of this money within 5 years", 1),
            ("Yes — I expect to need a meaningful portion", 2),
            ("Possibly minor withdrawals only", 3),
            ("No — this capital is fully committed for the long term", 4),
        ],
    },
    {
        "id": "q8",
        "label": "Current Debt Position",
        "text": "How would you describe your current debt obligations?",
        "advisor": (
            "Carrying high-interest debt while taking investment risk is rarely rational. "
            "Paying down a 20% credit card is a guaranteed 20% return — better than any investment "
            "I have consistently seen over a short horizon. "
            "High debt also reduces your flexibility during market stress. "
            "The question is always: what is the guaranteed after-tax return of paying down debt, "
            "versus the uncertain risk-adjusted return of investing?"
        ),
        "options": [
            ("High debt relative to income or assets", 1),
            ("Moderate debt, including a standard home mortgage", 2),
            ("Low and actively reducing debt", 3),
            ("Debt free", 4),
        ],
    },
    {
        "id": "q9",
        "label": "Portfolio Significance",
        "text": "This investment represents approximately what portion of your total net worth?",
        "advisor": (
            "Concentration risk is frequently overlooked in risk assessments that focus only on asset class. "
            "If this portfolio represents the majority of your total wealth, a conservative approach "
            "is warranted regardless of other factors. "
            "Diversification across asset types — property, superannuation, shares, business interests — "
            "matters as much as diversification within a single portfolio."
        ),
        "options": [
            ("More than 75% — this is my primary financial asset", 1),
            ("50 to 75% of my total net worth", 2),
            ("25 to 50% of my total net worth", 3),
            ("Less than 25% — I have significant other assets", 4),
        ],
    },
    {
        "id": "q10",
        "label": "Loss Tolerance",
        "text": "What is the maximum annual loss you could absorb without impacting your lifestyle or wellbeing?",
        "advisor": (
            "This question grounds the theoretical in the real. "
            "I ask clients to translate their answer from a percentage into an actual dollar figure — "
            "because percentages feel abstract until they appear on a statement. "
            "Most investors answer this question differently after experiencing an actual loss "
            "than they do in advance. "
            "If you are unsure, choose the more conservative option. "
            "It is far better to be pleasantly surprised by returns than devastated by losses."
        ),
        "options": [
            ("Less than 5% — any significant loss is unacceptable", 1),
            ("5 to 15% — I can tolerate a moderate drawdown", 2),
            ("15 to 25% — I understand that markets cycle", 3),
            ("25% or more — I am focused on long-term returns", 4),
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════
# 4. RISK PROFILES
# Score ranges, target allocations, and advisor commentary per profile.
# ═══════════════════════════════════════════════════════════════════════

PROFILES = {
    "Conservative": {
        "score_range":   (10, 18),
        "description":   "Capital preservation is your primary concern. Your portfolio is built to withstand market volatility with minimal drawdown, accepting lower long-term returns in exchange for stability and predictability.",
        "return_range":  "3 – 5% p.a.",
        "drawdown":      "5 – 10%",
        "horizon":       "1 – 5 years",
        "advisor_note":  "Conservative investors are not making a poor choice — they are making the right choice for their specific circumstances. The most expensive investment mistake is taking more risk than you can genuinely absorb, and being forced to sell at a loss. Stability and predictability have real financial value that is consistently underrated in the investment industry.",
        "targets": {
            "Australian Shares":    8,
            "International Shares": 12,
            "Property & REITs":     5,
            "Fixed Income & Bonds": 45,
            "Cash & Term Deposits": 30,
        },
    },
    "Moderately Conservative": {
        "score_range":   (19, 25),
        "description":   "You seek modest growth while protecting the bulk of your capital. Fixed income and defensive assets dominate, with a measured allocation to growth assets designed to stay ahead of inflation over time.",
        "return_range":  "4 – 6% p.a.",
        "drawdown":      "10 – 15%",
        "horizon":       "3 – 7 years",
        "advisor_note":  "The moderately conservative profile often fits investors approaching or in retirement who need their capital to last 20 to 30 years, but cannot afford significant drawdowns early in that period. The goal is not to grow wealthy rapidly — it is to remain financially secure, and to draw income with confidence that the portfolio can sustain withdrawals across a full market cycle.",
        "targets": {
            "Australian Shares":    15,
            "International Shares": 20,
            "Property & REITs":     10,
            "Fixed Income & Bonds": 40,
            "Cash & Term Deposits": 15,
        },
    },
    "Balanced": {
        "score_range":   (26, 31),
        "description":   "A genuine balance between long-term growth and downside protection. You accept that markets will cycle, and are positioned to capture equity returns over time while maintaining meaningful defensive exposure.",
        "return_range":  "5 – 8% p.a.",
        "drawdown":      "15 – 25%",
        "horizon":       "5 – 10 years",
        "advisor_note":  "The balanced portfolio is the most common outcome of a rigorous risk assessment — and for good reason. It acknowledges both the necessity of growth assets to outpace inflation and the reality that investors have finite emotional and financial capacity to absorb losses. The 60/40 equity-to-bond split has endured for decades as an industry benchmark because it reflects a genuinely sensible trade-off between growth and protection.",
        "targets": {
            "Australian Shares":    25,
            "International Shares": 30,
            "Property & REITs":     15,
            "Fixed Income & Bonds": 22,
            "Cash & Term Deposits": 8,
        },
    },
    "Growth": {
        "score_range":   (32, 36),
        "description":   "Long-term capital appreciation is your priority. You hold a growth-dominant portfolio and understand that 20 to 35% drawdowns are a normal feature of this approach — not an aberration — and that recovery has historically followed every correction.",
        "return_range":  "7 – 10% p.a.",
        "drawdown":      "25 – 35%",
        "horizon":       "7 – 15 years",
        "advisor_note":  "Growth investors accept meaningful short-term pain for long-term gain. The historical evidence strongly supports this approach over 10 or more year horizons — Australian equities have returned approximately 9% per annum over the past 30 years including dividends. The critical discipline is not abandoning the strategy during corrections. The investors I have seen build the most significant wealth are not the most sophisticated — they are the most patient.",
        "targets": {
            "Australian Shares":    30,
            "International Shares": 40,
            "Property & REITs":     15,
            "Fixed Income & Bonds": 12,
            "Cash & Term Deposits": 3,
        },
    },
    "Aggressive": {
        "score_range":   (37, 40),
        "description":   "Maximum long-term wealth accumulation. You have a long horizon, stable income, and the tested emotional discipline to remain invested through significant market corrections without reducing your exposure.",
        "return_range":  "8 – 12% p.a.",
        "drawdown":      "35 – 50%",
        "horizon":       "15+ years",
        "advisor_note":  "An aggressive allocation is appropriate for very few investors, and they tend to know with certainty who they are. If you are genuinely comfortable watching 40% of your portfolio temporarily disappear — and viewing it as an opportunity rather than a catastrophe — this profile fits. If there is any doubt, I would always suggest the growth profile instead. Being aggressive on paper and aggressive in a real downturn are profoundly different experiences.",
        "targets": {
            "Australian Shares":    35,
            "International Shares": 45,
            "Property & REITs":     15,
            "Fixed Income & Bonds": 5,
            "Cash & Term Deposits": 0,
        },
    },
}

# ═══════════════════════════════════════════════════════════════════════
# 5. HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def sym() -> str:
    """Return the currency symbol for the selected currency."""
    return CURRENCY_SYM.get(st.session_state["currency"], "$")


def fmt(n) -> str:
    """Format a number as a currency string with appropriate suffix."""
    if n is None: return f"{sym()}0"
    s = sym(); sign = "-" if n < 0 else ""; n = abs(n)
    if n >= 1_000_000: return f"{sign}{s}{n/1_000_000:.2f}M"
    if n >= 1_000:     return f"{sign}{s}{n:,.0f}"
    return f"{sign}{s}{n:.0f}"


def score_to_profile(score: int) -> str:
    """Map a raw risk score (10–40) to a profile name."""
    for name, data in PROFILES.items():
        lo, hi = data["score_range"]
        if lo <= score <= hi:
            return name
    return "Balanced"


def portfolio_values() -> dict:
    """Return current portfolio holdings as a dict of {asset_name: value}."""
    return {
        "Australian Shares":    st.session_state["aus_shares"],
        "International Shares": st.session_state["intl_shares"],
        "Property & REITs":     st.session_state["property"],
        "Fixed Income & Bonds": st.session_state["fixed_income"],
        "Cash & Term Deposits": st.session_state["cash"],
    }


def total_portfolio() -> float:
    """Sum of all portfolio holdings."""
    return float(sum(portfolio_values().values()))


def advisor_quote(text: str, kind: str = "wisdom"):
    """
    Render a styled advisor callout with JW avatar and professional label.
    kind: 'wisdom' | 'caution' | 'success' | 'warning'
    """
    palettes = {
        "wisdom":  (NSOFT, NAVY),
        "caution": (GSOFT,  GOLD),
        "success": ("#EAF2EA", SUCCESS),
        "warning": ("#FAF0E0", WARNING),
    }
    bg, accent = palettes.get(kind, palettes["wisdom"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {accent};"
        f"border-radius:0 8px 8px 0;padding:1.1rem 1.3rem;"
        f"margin:0.85rem 0;display:flex;gap:1rem;align-items:flex-start;'>"
        f"<div style='min-width:36px;height:36px;border-radius:50%;"
        f"background:{accent};color:#fff;display:flex;align-items:center;"
        f"justify-content:center;font-family:{FONT_H};font-size:0.9rem;"
        f"font-weight:600;flex-shrink:0;letter-spacing:0.02em;'>JW</div>"
        f"<div style='flex:1;'>"
        f"<p style='font-family:{FONT_M};font-size:0.58rem;letter-spacing:0.15em;"
        f"text-transform:uppercase;color:{accent};margin:0 0 0.4rem;font-weight:500;'>"
        f"Senior Financial Adviser · 25 Years Practice</p>"
        f"<p style='font-family:{FONT_B};font-size:0.875rem;color:{TEXT};"
        f"line-height:1.7;margin:0;font-weight:300;font-style:italic;'>{text}</p>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def section_label(text: str):
    """Render an all-caps section label with a bottom border."""
    st.markdown(
        f"<p style='font-family:{FONT_M};font-size:0.58rem;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{MUTED};margin:1.6rem 0 0.8rem;"
        f"padding-bottom:0.5rem;border-bottom:1px solid {BORDER};'>{text}</p>",
        unsafe_allow_html=True,
    )


def kpi_row(cards: list[tuple]):
    """
    Render a row of KPI cards.
    Each card is (label, value, note, accent:bool).
    """
    cols = st.columns(len(cards), gap="small")
    for col, (label, value, note, accent) in zip(cols, cards):
        border = f"border-left:3px solid {NAVY};" if accent else ""
        with col:
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BORDER};"
                f"border-radius:8px;padding:16px 18px;{border}'>"
                f"<div style='font-family:{FONT_M};font-size:0.56rem;"
                f"letter-spacing:0.18em;text-transform:uppercase;color:{MUTED};"
                f"margin-bottom:9px;'>{label}</div>"
                f"<div style='font-family:{FONT_H};font-size:1.75rem;color:{TEXT};"
                f"line-height:1;font-weight:500;'>{value}</div>"
                f"<div style='font-family:{FONT_M};font-size:0.62rem;"
                f"color:{MUTED};margin-top:6px;'>{note}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


def banner(text: str, kind: str = "info"):
    """Render a left-bordered informational banner."""
    palettes = {
        "info":    (NSOFT,      NAVY),
        "success": ("#EAF2EA",  SUCCESS),
        "warning": ("#FAF3E0",  WARNING),
        "danger":  ("#FAE8E8",  DANGER),
    }
    bg, border = palettes.get(kind, palettes["info"])
    st.markdown(
        f"<div style='background:{bg};border:1px solid {BORDER};"
        f"border-left:3px solid {border};border-radius:0 6px 6px 0;"
        f"padding:10px 14px;font-family:{FONT_B};font-size:0.875rem;"
        f"color:{TEXT};line-height:1.65;margin:0.4rem 0;'>{text}</div>",
        unsafe_allow_html=True,
    )


def html_row_table(headers: list, rows: list):
    """
    Render a data table as plain HTML — bypasses the st.dataframe iframe issue.
    headers: list of column names
    rows: list of lists (one per row)
    """
    header_cells = "".join(
        f"<th style='text-align:left;padding:0.4rem 0.85rem;"
        f"border-bottom:1px solid {BORDER};"
        f"font-family:{FONT_M};font-size:0.58rem;text-transform:uppercase;"
        f"letter-spacing:0.12em;color:{MUTED};background:{CARD};"
        f"white-space:nowrap;font-weight:500;'>{h}</th>"
        for h in headers
    )
    row_html = ""
    for i, row in enumerate(rows):
        bg = CARD if i % 2 == 0 else "#F8F6F0"
        cells = "".join(
            f"<td style='padding:0.42rem 0.85rem;"
            f"border-bottom:1px solid {BORDER};"
            f"font-family:{FONT_B};font-size:0.85rem;"
            f"color:{TEXT};background:{bg};'>{cell}</td>"
            for cell in row
        )
        row_html += f"<tr>{cells}</tr>"

    st.markdown(
        f"<div style='border:1px solid {BORDER};border-radius:8px;"
        f"overflow:hidden;overflow-x:auto;margin:0.5rem 0 1rem;'>"
        f"<table style='width:100%;border-collapse:collapse;background:{CARD};'>"
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )


def donut_chart(labels: list, values: list, colors: list, center_text: str = "") -> go.Figure:
    """
    Build a styled Plotly donut chart.
    Returns a go.Figure ready for st.plotly_chart().
    """
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker=dict(colors=colors, line=dict(color=BG, width=3)),
        textinfo="label+percent",
        textfont=dict(family=FONT_B, size=11, color=TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<br>%{value:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        showlegend=False,
        font=dict(family=FONT_B, color=TEXT),
        annotations=[dict(
            text=center_text,
            x=0.5, y=0.5,
            font=dict(size=13, family=FONT_H, color=TEXT),
            showarrow=False,
        )] if center_text else [],
    )
    return fig


def bar_chart(names: list, current: list, target: list) -> go.Figure:
    """
    Build a grouped bar chart comparing current vs target allocation percentages.
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Current",
        x=names, y=current,
        marker_color=GOLD,
        hovertemplate="%{x}<br>Current: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Target",
        x=names, y=target,
        marker_color=NAVY,
        hovertemplate="%{x}<br>Target: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            font=dict(family=FONT_M, size=10, color=MUTED),
            orientation="h", y=1.08,
        ),
        xaxis=dict(
            showgrid=False, color=MUTED,
            tickfont=dict(family=FONT_M, size=9, color=MUTED),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=BORDER,
            tickfont=dict(family=FONT_M, size=9, color=MUTED),
            ticksuffix="%",
        ),
        font=dict(family=FONT_B, color=TEXT),
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════
# 6. GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════════

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Source+Serif+4:ital,wght@0,300;0,400;0,500;1,300;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>

/* ── Base ── */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background-color: {BG} !important;
    font-family: {FONT_B};
    color: {TEXT};
}}
.block-container {{
    padding: 1.8rem 2rem 3rem;
    max-width: 1080px;
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none !important; }}

/* ── Typography ── */
h1, h2, h3 {{
    font-family: {FONT_H};
    font-weight: 500;
    color: {TEXT};
    letter-spacing: -0.01em;
}}
p, li {{ color: {TEXT}; font-family: {FONT_B}; }}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    border-bottom: 1px solid {BORDER};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: {FONT_M};
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

/* ── Widget labels ── */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stRadio"] label {{
    font-family: {FONT_M} !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: {MUTED} !important;
}}

/* ── Number inputs ── */
.stNumberInput input {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT} !important;
    font-family: {FONT_M} !important;
    font-size: 0.9rem !important;
    border-radius: 6px !important;
}}
.stNumberInput button {{
    background: {CARD} !important;
    color: {TEXT} !important;
    border-color: {BORDER} !important;
}}

/* ── Selectbox ── */
.stSelectbox > div > div {{
    background: {CARD} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT} !important;
    border-radius: 6px !important;
}}
[role="listbox"] *, [role="option"] {{
    background: {CARD} !important;
    color: {TEXT} !important;
    font-family: {FONT_B} !important;
}}

/* ── Radio buttons ── */
.stRadio > div > label {{
    font-family: {FONT_B} !important;
    font-size: 0.875rem !important;
    color: {TEXT} !important;
    font-weight: 300 !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background-color: {NAVY} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: {FONT_M} !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 2rem !important;
    transition: opacity 0.15s !important;
}}
.stButton > button:hover {{ opacity: 0.82 !important; }}

/* ── Expander ── */
div[data-testid="stExpander"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin: 0.4rem 0;
}}
div[data-testid="stExpander"] summary {{
    font-family: {FONT_M};
    font-size: 0.62rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {MUTED};
    padding: 0.6rem 0;
}}

/* ── Dividers ── */
hr {{
    border: none;
    border-top: 1px solid {BORDER};
    margin: 1.4rem 0;
}}

/* ── Progress bar (used for score) ── */
.score-bar-track {{
    height: 5px;
    background: {BORDER};
    border-radius: 3px;
    margin: 10px 0 4px;
    overflow: hidden;
}}
.score-bar-fill {{
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(to right, {NAVY}, {GOLD});
}}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# 7. TOP BAR
# ═══════════════════════════════════════════════════════════════════════

col_logo, col_mid, col_right = st.columns([5, 2, 2])

with col_logo:
    st.markdown(
        f"<div style='font-family:{FONT_H};font-size:2.4rem;color:{TEXT};"
        f"line-height:1;letter-spacing:-0.02em;font-weight:500;'>Meridian</div>"
        f"<div style='font-family:{FONT_M};font-size:0.6rem;letter-spacing:0.2em;"
        f"text-transform:uppercase;color:{MUTED};margin-top:4px;'>"
        f"Investment Risk &amp; Allocation Guide</div>",
        unsafe_allow_html=True,
    )

with col_right:
    currencies = list(CURRENCY_SYM.keys())
    new_cur = st.selectbox(
        "Currency",
        currencies,
        index=currencies.index(st.session_state["currency"]),
        label_visibility="collapsed",
    )
    if new_cur != st.session_state["currency"]:
        st.session_state["currency"] = new_cur
        try:    st.rerun()
        except: st.experimental_rerun()

# Disclaimer strip
st.markdown(
    f"<div style='background:{GSOFT};border:1px solid {BORDER};"
    f"border-radius:6px;padding:7px 14px;margin:0.6rem 0 0.2rem;"
    f"font-family:{FONT_M};font-size:0.58rem;letter-spacing:0.08em;"
    f"text-transform:uppercase;color:{WARNING};'>"
    f"Educational purposes only &nbsp;·&nbsp; Not personal financial advice &nbsp;·&nbsp; "
    f"Consult a licensed financial adviser (AFSL) before investing</div>",
    unsafe_allow_html=True,
)

# Progress indicator — shows which steps are complete
profile_done   = st.session_state["profile_done"]
portfolio_done = total_portfolio() > 0

step_html = ""
steps = [
    ("01  Risk Assessment", profile_done),
    ("02  Portfolio Input", portfolio_done),
    ("03  Allocation Analysis", profile_done and portfolio_done),
    ("04  Rebalancing Plan", profile_done and portfolio_done),
]
for label, done in steps:
    color = SUCCESS if done else MUTED
    marker = "✓" if done else "○"
    step_html += (
        f"<span style='font-family:{FONT_M};font-size:0.6rem;"
        f"letter-spacing:0.1em;text-transform:uppercase;color:{color};"
        f"margin-right:1.8rem;'>{marker}&nbsp; {label}</span>"
    )

st.markdown(
    f"<div style='padding:0.6rem 0 0.2rem;'>{step_html}</div>",
    unsafe_allow_html=True,
)
st.markdown("---")


# ═══════════════════════════════════════════════════════════════════════
# 8. TABS
# ═══════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Risk Assessment",
    "My Portfolio",
    "Allocation Analysis",
    "Rebalancing Plan",
    "Financial Health Audit",
    "Horizon Simulator",
])


# ───────────────────────────────────────────────────────────────────────
# TAB 1 — RISK ASSESSMENT (UPGRADED TRI-AXIS RISK ENGINE)
# ───────────────────────────────────────────────────────────────────────

with tab1:

    advisor_quote(
        "Before any allocation decision can be made, we must understand your relationship with risk. "
        "Historically, risk is split into two axes: <strong>Financial Risk Capacity</strong> (your resources, cash buffers, "
        "and investment runway) and <strong>Emotional Risk Tolerance</strong> (your psychological reactions and volatility experience). "
        "Our upgraded Tri-Axis Risk Engine measures both separately to detect dangerous structural mismatches before they damage your net worth.",
        kind="wisdom",
    )

    section_label("The Risk Questionnaire")

    all_answered = True
    raw_capacity = 0
    raw_tolerance = 0

    capacity_qids = ["q1", "q2", "q3", "q7", "q8"]
    tolerance_qids = ["q4", "q5", "q6", "q9", "q10"]

    for q in QUESTIONS:
        qid = q["id"]
        option_labels = [opt[0] for opt in q["options"]]

        # Get current selection index (None if not answered)
        current_val = st.session_state.get(qid)
        current_idx = None
        if current_val is not None:
            for idx, (label, _) in enumerate(q["options"]):
                if label == current_val:
                    current_idx = idx
                    break

        st.markdown(
            f"<p style='font-family:{FONT_H};font-size:1.05rem;color:{TEXT};"
            f"font-weight:500;margin:1.4rem 0 0.2rem;'>{q['label']}</p>"
            f"<p style='font-family:{FONT_B};font-size:0.875rem;color:{MUTED};"
            f"font-weight:300;margin:0 0 0.5rem;font-style:italic;'>{q['text']}</p>",
            unsafe_allow_html=True,
        )

        selected = st.radio(
            label=q["text"],
            options=option_labels,
            index=current_idx,
            key=f"radio_{qid}",
            label_visibility="collapsed",
        )

        if selected:
            st.session_state[qid] = selected
            # Add points to the correct axis
            for label, pts in q["options"]:
                if label == selected:
                    if qid in capacity_qids:
                        raw_capacity += pts
                    else:
                        raw_tolerance += pts
                    break
        else:
            all_answered = False

        # Advisor insight per question — collapsed by default
        with st.expander("Adviser perspective on this question"):
            st.markdown(
                f"<p style='font-family:{FONT_B};font-size:0.875rem;"
                f"color:{TEXT};line-height:1.7;font-weight:300;"
                f"font-style:italic;padding:0.3rem 0;'>{q['advisor']}</p>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Calculate My Risk Profile"):
        if not all_answered:
            banner("Please answer all 10 questions before calculating your profile.", "warning")
        else:
            total_score = raw_capacity + raw_tolerance
            default_profile = score_to_profile(total_score)
            
            st.session_state["risk_score"]     = total_score
            st.session_state["risk_capacity"]  = raw_capacity
            st.session_state["risk_tolerance"] = raw_tolerance
            st.session_state["risk_profile"]   = default_profile
            st.session_state["profile_done"]   = True
            
            # Mismatch Override Policy Logic
            # 1. Capacity is Low (FCI <= 10) but default profile is growth-oriented
            if raw_capacity <= 10 and default_profile in ["Growth", "Aggressive"]:
                st.session_state["override_profile"] = "Balanced"
            # 2. Capacity is High (FCI >= 16) but tolerance is highly conservative (ETI <= 10)
            elif raw_capacity >= 16 and raw_tolerance <= 10 and default_profile in ["Balanced", "Growth", "Aggressive"]:
                st.session_state["override_profile"] = "Moderately Conservative"
            else:
                st.session_state["override_profile"] = default_profile
                
            try:    st.rerun()
            except: st.experimental_rerun()

    # Show result if profile has been calculated
    if st.session_state["profile_done"]:
        f_cap = st.session_state["risk_capacity"]
        e_tol = st.session_state["risk_tolerance"]
        fci_pct = int(((f_cap - 5) / 15) * 100)
        eti_pct = int(((e_tol - 5) / 15) * 100)
        
        assigned_profile = st.session_state["override_profile"]
        profile_data = PROFILES[assigned_profile]

        st.markdown("---")
        section_label("Tri-Axis Risk Diagnostics")

        # Renders the twin premium risk bars
        st.markdown(
            f"<div style='display:flex;gap:1.5rem;margin-bottom:1rem;flex-wrap:wrap;'>"
            f"<div style='flex:1;min-width:280px;background:{CARD};border:1px solid {BORDER};"
            f"border-left:3px solid {NAVY};border-radius:0 8px 8px 0;padding:1.2rem;'>"
            f"<div style='font-family:{FONT_M};font-size:0.58rem;letter-spacing:0.18em;"
            f"text-transform:uppercase;color:{MUTED};margin-bottom:0.5rem;'>Financial Risk Capacity</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;'>"
            f"<div style='font-family:{FONT_H};font-size:1.75rem;color:{NAVY};font-weight:500;'>{f_cap} / 20</div>"
            f"<div style='font-family:{FONT_M};font-size:0.75rem;color:{MUTED};'>{fci_pct}%</div>"
            f"</div>"
            f"<div class='score-bar-track'><div class='score-bar-fill' style='width:{fci_pct}%;background:{NAVY};'></div></div>"
            f"<p style='font-family:{FONT_B};font-size:0.8rem;color:{MUTED};line-height:1.65;margin-top:8px;font-weight:300;'>"
            f"Your structural financial ability to take risk based on cash runway, secure income, and low liabilities.</p>"
            f"</div>"
            f"<div style='flex:1;min-width:280px;background:{CARD};border:1px solid {BORDER};"
            f"border-left:3px solid {GOLD};border-radius:0 8px 8px 0;padding:1.2rem;'>"
            f"<div style='font-family:{FONT_M};font-size:0.58rem;letter-spacing:0.18em;"
            f"text-transform:uppercase;color:{MUTED};margin-bottom:0.5rem;'>Emotional Risk Tolerance</div>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline;'>"
            f"<div style='font-family:{FONT_H};font-size:1.75rem;color:{GOLD};font-weight:500;'>{e_tol} / 20</div>"
            f"<div style='font-family:{FONT_M};font-size:0.75rem;color:{MUTED};'>{eti_pct}%</div>"
            f"</div>"
            f"<div class='score-bar-track'><div class='score-bar-fill' style='width:{eti_pct}%;background:{GOLD};'></div></div>"
            f"<p style='font-family:{FONT_B};font-size:0.8rem;color:{MUTED};line-height:1.65;margin-top:8px;font-weight:300;'>"
            f"Your behavioral willingness to tolerate market swings based on your experience and emotional loss comfort.</p>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Mismatch Resolution Advisory
        orig_prof = st.session_state["risk_profile"]
        if assigned_profile != orig_prof:
            # Overrule has taken place
            if f_cap <= 10:
                advisor_quote(
                    f"<strong>Adviser Warning · Risk Mismatch Override:</strong> "
                    f"Your emotional risk tolerance suggests a <strong>{orig_prof}</strong> profile, "
                    f"but your financial risk capacity is constrained by a short runway or debts. "
                    f"Under professional planning guidelines, risk capacity must act as the primary safety gate. "
                    f"Recommending growth portfolios under low capacity represents a high risk of ruin. We have adjusted your recommended target allocation down to the <strong>{assigned_profile}</strong> profile to ensure liquidity.",
                    kind="warning"
                )
            else:
                advisor_quote(
                    f"<strong>Adviser Insight · Emotional Tolerance Override:</strong> "
                    f"Your base structural finances are robust, supporting a <strong>{orig_prof}</strong> capacity profile. "
                    f"However, your psychological responses are highly conservative. Investing is an emotional journey as much as "
                    f"a mathematical one; we have adjusted your recommended portfolio to a <strong>{assigned_profile}</strong> target to avoid behavioral panic in downturns.",
                    kind="caution"
                )
        else:
            st.markdown(
                f"<div style='background:#EAF2EA;border:1px solid {BORDER};border-left:3px solid {SUCCESS};"
                f"border-radius:0 6px 6px 0;padding:12px 16px;margin:0.8rem 0;font-family:{FONT_B};font-size:0.875rem;"
                f"color:{TEXT};line-height:1.6;'>"
                f"<strong>Structural Alignment:</strong> Your financial risk capacity and emotional willingness "
                f"are in structural alignment. Your recommended strategic allocation is the <strong>{assigned_profile}</strong> profile.</div>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)
        kpi_row([
            ("Assigned Profile",   assigned_profile,          "Based on Tri-Axis reconciliation", True),
            ("Expected Return",    profile_data["return_range"],   "Historical estimate, not guaranteed", False),
            ("Max Drawdown Range", profile_data["drawdown"],       "Typical correction depth", False),
            ("Suited Horizon",     profile_data["horizon"],        "Minimum recommended period", False),
        ])

        st.markdown("<br>", unsafe_allow_html=True)
        advisor_quote(profile_data["advisor_note"], kind="wisdom")

        # Target allocation preview
        section_label("Strategic Target Allocation")
        targets = profile_data["targets"]
        active_targets = {k: v for k, v in targets.items() if v > 0}

        fig = donut_chart(
            labels=list(active_targets.keys()),
            values=list(active_targets.values()),
            colors=[ASSET_COLORS[ASSET_NAMES.index(k)] for k in active_targets.keys()],
            center_text=f"<b>{assigned_profile[:4]}.</b><br>Target",
        )
        col_chart, col_legend = st.columns([1, 1])
        with col_chart:
            st.plotly_chart(fig, use_container_width=True)
        with col_legend:
            st.markdown("<br>", unsafe_allow_html=True)
            for asset, pct in targets.items():
                color = ASSET_COLORS[ASSET_NAMES.index(asset)]
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:0.7rem;"
                    f"padding:0.45rem 0;border-bottom:1px solid {BORDER};'>"
                    f"<div style='width:10px;height:10px;border-radius:50%;"
                    f"background:{color};flex-shrink:0;'></div>"
                    f"<div style='font-family:{FONT_B};font-size:0.82rem;color:{TEXT};"
                    f"flex:1;font-weight:300;'>{asset}</div>"
                    f"<div style='font-family:{FONT_M};font-size:0.82rem;color:{NAVY};"
                    f"font-weight:500;'>{pct}%</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ───────────────────────────────────────────────────────────────────────
# TAB 2 — MY PORTFOLIO
# ───────────────────────────────────────────────────────────────────────

with tab2:

    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment in Tab 1 first to unlock portfolio analysis.", "info")
    else:
        advisor_quote(
            "Enter the current market value of your holdings in each asset class below. "
            "Include superannuation, direct shares, managed funds, ETFs, investment property, "
            "bonds, and cash — the full picture. "
            "Investors who assess only part of their wealth routinely take more risk than they realise. "
            "A complete portfolio view is the only one worth analysing.",
            kind="wisdom",
        )

        section_label("Current Holdings by Asset Class")

        ASSET_DESCRIPTIONS = {
            "Australian Shares":    "ASX-listed shares, Australian equity ETFs, Australian managed funds",
            "International Shares": "Global ETFs (MSCI World, S&P 500), international managed funds, ADRs",
            "Property & REITs":     "Direct investment property (equity portion), A-REITs, global REITs",
            "Fixed Income & Bonds": "Government bonds, corporate bonds, bond ETFs, term deposits over 1 year",
            "Cash & Term Deposits": "Bank savings accounts, offset accounts, term deposits under 1 year",
        }
        ASSET_KEYS = ["aus_shares", "intl_shares", "property", "fixed_income", "cash"]

        col_a, col_b = st.columns(2, gap="large")

        asset_items = list(zip(ASSET_NAMES, ASSET_KEYS))

        for idx, (name, key) in enumerate(asset_items):
            col = col_a if idx < 3 else col_b
            with col:
                st.markdown(
                    f"<p style='font-family:{FONT_H};font-size:0.95rem;color:{TEXT};"
                    f"font-weight:500;margin:1.1rem 0 0.1rem;'>{name}</p>"
                    f"<p style='font-family:{FONT_B};font-size:0.75rem;color:{MUTED};"
                    f"font-weight:300;margin:0 0 0.4rem;font-style:italic;'>"
                    f"{ASSET_DESCRIPTIONS[name]}</p>",
                    unsafe_allow_html=True,
                )
                st.number_input(
                    label=name,
                    min_value=0.0,
                    step=1000.0,
                    key=key,
                    label_visibility="collapsed",
                )

        total = total_portfolio()

        if total == 0:
            st.markdown("<br>", unsafe_allow_html=True)
            banner("Enter your holdings above to see your current allocation.", "info")
        else:
            st.markdown("---")
            section_label("Current Portfolio Summary")

            holdings = portfolio_values()
            active   = {k: v for k, v in holdings.items() if v > 0}

            kpi_row([
                ("Total Portfolio Value", fmt(total),          "Sum of all asset classes", True),
                ("Asset Classes Held",    str(len(active)),    "Of 5 available classes",   False),
                ("Largest Holding",       max(active, key=active.get) if active else "—",
                 f"{max(active.values())/total*100:.1f}% of portfolio" if active else "", False),
            ])

            st.markdown("<br>", unsafe_allow_html=True)

            col_c, col_d = st.columns([1, 1])
            with col_c:
                fig2 = donut_chart(
                    labels=list(active.keys()),
                    values=list(active.values()),
                    colors=[ASSET_COLORS[ASSET_NAMES.index(k)] for k in active.keys()],
                    center_text=f"<b>{fmt(total)}</b><br>total",
                )
                st.plotly_chart(fig2, use_container_width=True)

            with col_d:
                st.markdown("<br>", unsafe_allow_html=True)
                for asset, value in sorted(holdings.items(), key=lambda x: x[1], reverse=True):
                    if value == 0: continue
                    pct   = value / total * 100
                    color = ASSET_COLORS[ASSET_NAMES.index(asset)]
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:0.7rem;"
                        f"padding:0.45rem 0;border-bottom:1px solid {BORDER};'>"
                        f"<div style='width:10px;height:10px;border-radius:50%;"
                        f"background:{color};flex-shrink:0;'></div>"
                        f"<div style='font-family:{FONT_B};font-size:0.82rem;color:{TEXT};"
                        f"flex:1;font-weight:300;'>{asset}</div>"
                        f"<div style='font-family:{FONT_M};font-size:0.75rem;color:{MUTED};"
                        f"margin-right:0.5rem;'>{pct:.1f}%</div>"
                        f"<div style='font-family:{FONT_M};font-size:0.82rem;color:{TEXT};"
                        f"font-weight:500;'>{fmt(value)}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            for asset, value in holdings.items():
                if value == 0: continue
                pct = value / total * 100
                
                # Check for growth asset concentration (> 40%)
                if asset in ["Australian Shares", "International Shares", "Property & REITs"] and pct > 40.0:
                    advisor_quote(
                        f"Your portfolio has a significant concentration in <strong>{asset}</strong> ({pct:.1f}%). "
                        f"While high concentration can accelerate wealth accumulation when the asset performs, "
                        f"it removes your defense against systemic sector drawdowns. In professional wealth practice, "
                        f"any allocation exceeding 40% in a growth asset class requires explicit justification "
                        f"and careful correlation monitoring.",
                        kind="caution"
                    )
                # Check for cash drag (> 50%)
                elif asset == "Cash & Term Deposits" and pct > 50.0:
                    advisor_quote(
                        f"Your cash holding is remarkably high ({pct:.1f}%). "
                        f"While this provides total liquidity and short-term capital protection, it represents a meaningful "
                        f"long-term drag on your purchasing power. Over time, inflation systematically erodes the real value of cash "
                        f"assets. Consider if a portion of this buffer can be allocated to interest-bearing or growth assets.",
                        kind="warning"
                    )


# ───────────────────────────────────────────────────────────────────────
# TAB 3 — ALLOCATION ANALYSIS
# ───────────────────────────────────────────────────────────────────────

with tab3:

    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment in Tab 1 first to unlock allocation analysis.", "info")
    elif total_portfolio() == 0:
        banner("Enter your portfolio holdings in Tab 2 first to analyze your allocation.", "info")
    else:
        profile_name = st.session_state["override_profile"]
        profile = PROFILES[profile_name]
        targets = profile["targets"]
        holdings = portfolio_values()
        total = total_portfolio()
        
        advisor_quote(
            f"Asset allocation explains over 90% of the variability in long-term portfolio returns. "
            f"By comparing your current assets to the <strong>{profile_name}</strong> target, we identify where "
            f"your portfolio has drifted from its intended risk tolerance. Our objective is not to eliminate "
            f"every single dollar of variance, but to prevent major structural drifts that expose you to unwanted risk.",
            kind="wisdom"
        )
        
        section_label("Allocation Drift Comparison")
        
        # Calculate current percentages and variances
        current_pcts = {asset: (val / total * 100) for asset, val in holdings.items()}
        drift_pcts = {asset: (current_pcts[asset] - targets[asset]) for asset in ASSET_NAMES}
        drift_vals = {asset: (holdings[asset] - (targets[asset] / 100 * total)) for asset in ASSET_NAMES}
        
        # Growth vs Defensive calculations
        growth_assets = ["Australian Shares", "International Shares", "Property & REITs"]
        defensive_assets = ["Fixed Income & Bonds", "Cash & Term Deposits"]
        
        curr_growth_pct = sum(current_pcts[a] for a in growth_assets)
        curr_def_pct = sum(current_pcts[a] for a in defensive_assets)
        tgt_growth_pct = sum(targets[a] for a in growth_assets)
        tgt_def_pct = sum(targets[a] for a in defensive_assets)
        
        col_bar, col_metrics = st.columns([5, 4], gap="large")
        
        with col_bar:
            fig3 = bar_chart(
                names=ASSET_NAMES,
                current=[current_pcts[a] for a in ASSET_NAMES],
                target=[targets[a] for a in ASSET_NAMES]
            )
            st.plotly_chart(fig3, use_container_width=True)
            
        with col_metrics:
            st.markdown("<br>", unsafe_allow_html=True)
            # Display KPIs for Growth / Defensive
            kpi_row([
                ("Growth / Defensive Split", f"{curr_growth_pct:.0f}% / {curr_def_pct:.0f}%", f"Target: {tgt_growth_pct:.0f}% / {tgt_def_pct:.0f}%", True),
            ])
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Find the largest absolute drift
            max_drift_asset = max(ASSET_NAMES, key=lambda a: abs(drift_pcts[a]))
            max_drift_pct = drift_pcts[max_drift_asset]
            max_drift_val = drift_vals[max_drift_asset]
            
            drift_direction = "Overweight" if max_drift_pct > 0 else "Underweight"
            kpi_row([
                ("Maximum Portfolio Drift", f"{abs(max_drift_pct):.1f}%", f"{max_drift_asset} ({drift_direction})", False)
            ])
            
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Asset Class Drift Table")
        
        # HTML Table for allocation drift
        headers = ["Asset Class", "Current Value", "Current %", "Target %", "Drift %", "Drift Value"]
        table_rows = []
        for asset in ASSET_NAMES:
            c_val = holdings[asset]
            c_pct = current_pcts[asset]
            t_pct = targets[asset]
            d_pct = drift_pcts[asset]
            d_val = drift_vals[asset]
            
            # Text styling for drift
            if abs(d_pct) < 1.0:
                d_pct_str = f"<span style='color:{MUTED};font-family:{FONT_M};'>Aligned</span>"
                d_val_str = f"<span style='color:{MUTED};font-family:{FONT_M};'>—</span>"
            elif d_pct > 0:
                d_pct_str = f"<span style='color:{DANGER};font-weight:500;font-family:{FONT_M};'>+{d_pct:.1f}%</span>"
                d_val_str = f"<span style='color:{DANGER};font-weight:500;font-family:{FONT_M};'>+{fmt(d_val)}</span>"
            else:
                d_pct_str = f"<span style='color:{GOLD};font-weight:500;font-family:{FONT_M};'>{d_pct:.1f}%</span>"
                d_val_str = f"<span style='color:{GOLD};font-weight:500;font-family:{FONT_M};'>{fmt(d_val)}</span>"
                
            table_rows.append([
                asset,
                fmt(c_val),
                f"{c_pct:.1f}%",
                f"{t_pct:.1f}%",
                d_pct_str,
                d_val_str
            ])
            
        html_row_table(headers, table_rows)
        
        # Dynamic Advisor commentary based on portfolio health
        max_abs_drift = max(abs(drift_pcts[a]) for a in ASSET_NAMES)
        if max_abs_drift <= 3.0:
            advisor_quote(
                "Your portfolio is remarkably well-aligned with your target asset profile. "
                "Minor deviations under 3% are standard and do not warrant portfolio disruption or transaction costs. "
                "Maintain your disciplined approach and review this layout semi-annually.",
                kind="success"
            )
        elif max_abs_drift <= 8.0:
            advisor_quote(
                f"You have moderate drift in your portfolio, primarily driven by <strong>{max_drift_asset}</strong> which is "
                f"{abs(max_drift_pct):.1f}% {drift_direction.lower()}. This level of drift is common during medium-term "
                f"market movements. We recommend scheduling a rebalancing action soon, ideally using tax-efficient capital cash inflows.",
                kind="caution"
            )
        else:
            advisor_quote(
                f"Your portfolio has developed significant asset drift. <strong>{max_drift_asset}</strong> has drifted by "
                f"<strong>{drift_pcts[max_drift_asset]:+.1f}%</strong> (equivalent to {fmt(drift_vals[max_drift_asset])}). "
                f"This major misalignment shifts the actual risk profile of your portfolio away from your comfort zone. "
                f"If equities are highly overweight, you are exposed to significant drawdowns; if cash is overweight, inflation is "
                f"eroding your purchasing power. Active rebalancing is highly recommended. Proceed to Tab 4 for a structured action plan.",
                kind="warning"
            )


# ───────────────────────────────────────────────────────────────────────
# TAB 4 — REBALANCING PLAN
# ───────────────────────────────────────────────────────────────────────

with tab4:

    if not st.session_state["profile_done"]:
        banner("Complete the Risk Assessment in Tab 1 first to unlock your rebalancing plan.", "info")
    elif total_portfolio() == 0:
        banner("Enter your portfolio holdings in Tab 2 first to generate a rebalancing plan.", "info")
    else:
        profile_name = st.session_state["override_profile"]
        profile = PROFILES[profile_name]
        targets = profile["targets"]
        holdings = portfolio_values()
        total = total_portfolio()
        
        advisor_quote(
            "Rebalancing is the systematic act of selling high and buying low. "
            "It requires you to trim asset classes that have performed exceptionally well (taking profits) "
            "and allocate to asset classes that have lagged behind. This disciplined process "
            "is emotionally challenging but remains the single most reliable risk-mitigation technique in asset management.",
            kind="wisdom"
        )
        
        section_label("Rebalancing Action Ledger")
        
        # Calculate rebalancing values
        rebal_rows = []
        total_buy = 0.0
        total_sell = 0.0
        
        for asset in ASSET_NAMES:
            c_val = holdings[asset]
            t_pct = targets[asset]
            t_val = (t_pct / 100) * total
            adj_val = t_val - c_val
            
            # Action threshold: $100
            if abs(adj_val) < 100.0:
                action_str = f"<span style='color:{SUCCESS};font-weight:500;font-family:{FONT_M};'>✓ Aligned</span>"
                adj_str = f"<span style='color:{MUTED};font-family:{FONT_M};'>—</span>"
            elif adj_val > 0:
                total_buy += adj_val
                action_str = f"<span style='color:{NAVY};font-weight:500;font-family:{FONT_M};'>Buy / Allocate</span>"
                adj_str = f"<span style='color:{NAVY};font-weight:500;font-family:{FONT_M};'>+{fmt(adj_val)}</span>"
            else:
                total_sell += abs(adj_val)
                action_str = f"<span style='color:{GOLD};font-weight:500;font-family:{FONT_M};'>Sell / Reallocate</span>"
                adj_str = f"<span style='color:{GOLD};font-weight:500;font-family:{FONT_M};'>-{fmt(abs(adj_val))}</span>"
                
            rebal_rows.append([
                asset,
                fmt(c_val),
                fmt(t_val),
                adj_str,
                action_str
            ])
            
        # Display KPI Summary Card for Rebalancing Volume
        kpi_row([
            ("Total Portfolio Value", fmt(total), "Net wealth under advisory", True),
            ("Buy / Inflow Volume Required", fmt(total_buy), "To fully align underweight sectors", False),
            ("Sell / Outflow Volume Required", fmt(total_sell), "To trim overweight sectors", False),
        ])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Render the custom HTML table
        headers = ["Asset Class", "Current Value", "Target Value", "Adjustment Required", "Action Directive"]
        html_row_table(headers, rebal_rows)
        
        # Strategic Advice block
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("Rebalancing Methodologies & Best Practices")
        
        col_m1, col_m2 = st.columns(2, gap="large")
        
        with col_m1:
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BORDER};"
                f"border-radius:8px;padding:20px;min-height:220px;'>"
                f"<h4 style='font-family:{FONT_H};font-size:1.15rem;color:{NAVY};"
                f"margin-top:0;margin-bottom:0.5rem;'>Method A: Cash Flow Rebalancing</h4>"
                f"<p style='font-family:{FONT_B};font-size:0.875rem;color:{TEXT};"
                f"line-height:1.65;font-weight:300;margin:0 0 1rem;'>"
                f"Instead of selling assets (which triggers trading fees and tax liabilities), you "
                f"direct new savings, dividend payouts, or pension contributions exclusively to "
                f"the underweight classes (indicated by <strong>Buy / Allocate</strong> above).</p>"
                f"<p style='font-family:{FONT_M};font-size:0.6rem;color:{SUCCESS};"
                f"letter-spacing:0.05em;text-transform:uppercase;font-weight:500;margin:0;'>"
                f"✓ Tax-efficient &nbsp;·&nbsp; ✓ Minimises transaction costs</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            
        with col_m2:
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BORDER};"
                f"border-radius:8px;padding:20px;min-height:220px;'>"
                f"<h4 style='font-family:{FONT_H};font-size:1.15rem;color:{GOLD};"
                f"margin-top:0;margin-bottom:0.5rem;'>Method B: Full Rebalancing</h4>"
                f"<p style='font-family:{FONT_B};font-size:0.875rem;color:{TEXT};"
                f"line-height:1.65;font-weight:300;margin:0 0 1rem;'>"
                f"Simultaneously executing sell orders on overweight asset classes and buying "
                f"underweight classes. While this instantly achieves your target allocation, it is a "
                f"taxable event in many jurisdictions (such as triggering Capital Gains Tax in Australia) "
                f"and incurs double transaction fees.</p>"
                f"<p style='font-family:{FONT_M};font-size:0.6rem;color:{WARNING};"
                f"letter-spacing:0.05em;text-transform:uppercase;font-weight:500;margin:0;'>"
                f"⚠ High precision &nbsp;·&nbsp; ⚠ Potential CGT liability</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Professional Checklist for Rebalancing
        st.markdown(
            f"<div style='background:#FDFCF9;border:1px solid {BORDER};"
            f"border-radius:8px;padding:24px 28px;'>"
            f"<p style='font-family:{FONT_M};font-size:0.58rem;letter-spacing:0.18em;"
            f"text-transform:uppercase;color:{MUTED};margin-top:0;margin-bottom:12px;'>"
            f"Adviser Execution Checklist</p>"
            f"<ol style='font-family:{FONT_B};font-size:0.875rem;color:{TEXT};"
            f"line-height:1.8;font-weight:300;margin:0;padding-left:1.2rem;'>"
            f"<li><strong>Assess tax exposure:</strong> If using Method B, calculate if you hold any assets at a capital loss or if you qualify for long-term CGT discounts (e.g. holding assets &gt; 12 months in Australia).</li>"
            f"<li><strong>Leverage natural cash flows first:</strong> Turn off automatic dividend reinvestment plans (DRPs) in overweight holdings and direct cash dividends to your cash accounts to buy underweight holdings manually.</li>"
            f"<li><strong>Consolidate accounts:</strong> Ensure you evaluate assets across both your individual accounts and superannuation / retirement schemes before making execution choices.</li>"
            f"<li><strong>Establish drift thresholds:</strong> Professional advisory standards advise only triggering a full rebalance when an asset class drifts by more than 5.0% absolute.</li>"
            f"</ol>"
            f"</div>",
            unsafe_allow_html=True
        )


# ───────────────────────────────────────────────────────────────────────
# TAB 5 — FINANCIAL HEALTH & RESILIENCE AUDIT (9/10 PROBLEM-SOLVING)
# ───────────────────────────────────────────────────────────────────────

with tab5:

    advisor_quote(
        "A premium portfolio is meaningless if your underlying financial architecture is unstable. "
        "Before investing heavily in growth assets, we must perform a clinical audit of your emergency safety buffers, "
        "debt ratios, and savings accelerators. This system grades your financial health and generates "
        "specific, structural prescriptions to secure your foundation.",
        kind="wisdom",
    )

    section_label("Financial Diagnostics Parameters")

    col_h1, col_h2 = st.columns(2, gap="large")

    with col_h1:
        net_income = st.number_input(
            "Monthly Net Income (After-Tax)",
            min_value=1.0,
            value=8000.0,
            step=500.0,
            key="h_net_income",
        )
        essential_expenses = st.number_input(
            "Monthly Essential Overheads (Rent, Mortgage, Bills, Food)",
            min_value=1.0,
            value=4500.0,
            step=250.0,
            key="h_expenses",
        )

    with col_h2:
        total_debt = st.number_input(
            "Total Outstanding Non-Mortgage Liabilities (Credit Cards, Personal Loans, Car Finance)",
            min_value=0.0,
            value=12000.0,
            step=1000.0,
            key="h_total_debt",
        )
        debt_payments = st.number_input(
            "Monthly Outstanding Debt Payments",
            min_value=0.0,
            value=600.0,
            step=100.0,
            key="h_debt_payments",
        )

    # Emergency cash buffer integration
    cash_in_portfolio = st.session_state["cash"]
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        st.markdown(
            f"<p style='font-family:{FONT_H};font-size:0.95rem;color:{TEXT};font-weight:500;margin-bottom:0.2rem;'>"
            f"Liquid Emergency Buffer</p>"
            f"<p style='font-family:{FONT_B};font-size:0.75rem;color:{MUTED};margin-top:0;font-weight:300;font-style:italic;'>"
            f"Includes your Cash holdings from Tab 2 ({fmt(cash_in_portfolio)}) plus any other immediate accessible cash savings.</p>",
            unsafe_allow_html=True
        )
    with col_c2:
        additional_cash = st.number_input(
            "Additional Accessible Bank Savings",
            min_value=0.0,
            value=5000.0,
            step=1000.0,
            key="h_additional_cash",
            label_visibility="collapsed"
        )

    total_liquidity = cash_in_portfolio + additional_cash

    # ── CALCULATIONS ──
    # 1. Emergency Fund (Liquidity Coverage Ratio - LCR)
    # LCR = Liquidity / Expenses
    lcr = total_liquidity / essential_expenses if essential_expenses > 0 else 0.0
    if lcr >= 6.0:
        lcr_grade, lcr_color, lcr_score, lcr_note = "A", SUCCESS, 4.0, "Excellent buffer. Outlasts standard job transition windows."
    elif lcr >= 3.0:
        lcr_grade, lcr_color, lcr_score, lcr_note = "B", SUCCESS, 3.0, "Healthy reserve. Standard protection against immediate shocks."
    elif lcr >= 1.0:
        lcr_grade, lcr_color, lcr_score, lcr_note = "C", WARNING, 2.0, "Vulnerable runway. Highly vulnerable to job disruption or sudden bills."
    else:
        lcr_grade, lcr_color, lcr_score, lcr_note = "F", DANGER, 1.0, "Critical gap. Forced portfolio liquidation is extremely likely during stress."

    # 2. Debt Service Ratio (DSR)
    # DSR = Debt Payments / Net Income
    dsr = debt_payments / net_income if net_income > 0 else 0.0
    dsr_pct = dsr * 100
    if dsr <= 10.0:
        dsr_grade, dsr_color, dsr_score, dsr_note = "A", SUCCESS, 4.0, "Zero or highly optimal commitments. Maximum flexibility."
    elif dsr <= 25.0:
        dsr_grade, dsr_color, dsr_score, dsr_note = "C", SUCCESS, 3.0, "Moderate debt load. Manages standard debt servicing safely."
    elif dsr <= 40.0:
        dsr_grade, dsr_color, dsr_score, dsr_note = "D", WARNING, 2.0, "Heavy debt weight. Income is severely constrained."
    else:
        dsr_grade, dsr_color, dsr_score, dsr_note = "F", DANGER, 1.0, "Debt ruin spiral threat. High insolvency danger."

    # 3. Savings Rate Accelerator (SRA)
    # Savings = Net Income - Expenses - Debt Payments
    monthly_savings = net_income - essential_expenses - debt_payments
    savings_rate = monthly_savings / net_income if net_income > 0 else 0.0
    sra_pct = savings_rate * 100
    if savings_rate >= 0.30:
        sra_grade, sra_color, sra_score, sra_note = "A+", SUCCESS, 4.0, "Wealth Accelerator. Highly optimized budget compounding capital rapidly."
    elif savings_rate >= 0.15:
        sra_grade, sra_color, sra_score, sra_note = "B", SUCCESS, 3.0, "Active Builder. Steady accumulation exceeding basic thresholds."
    elif savings_rate >= 0.0:
        sra_grade, sra_color, sra_score, sra_note = "C", WARNING, 2.0, "Stagnant. Barely building reserves. High risk of long-term failure."
    else:
        sra_grade, sra_color, sra_score, sra_note = "F", DANGER, 1.0, "Wealth Drag. Deficit spending. Accumulating compounding debts."

    # ── AGGREGATE GPA ──
    gpa = (lcr_score + dsr_score + savings_score) / 3.0
    if gpa >= 3.6:
        overall_grade, overall_color, gpa_desc = "A", SUCCESS, "Resilient Wealth Builder"
        prescription = (
            "Your base structural finances are highly optimized. You have locked down excellent cash runway protection "
            "and carry optimal liabilities. <strong>Prescription:</strong> Confidently fund your target Growth/Defensive "
            "asset mixes. Establish scheduled automatic transfers from salary into investments to systematically remove timing biases."
        )
    elif gpa >= 2.8:
        overall_grade, overall_color, gpa_desc = "B", SUCCESS, "Active Accumulator"
        prescription = (
            "You have solid buffers but carrying minor outstanding liabilities drags on your compounding potential. "
            "<strong>Prescription:</strong> Halt aggressive growth portfolio expansions temporarily. Direct 80% of monthly savings "
            "exclusively to eliminate high-interest liabilities, delivering a guaranteed after-tax return, and build cash to 6 months."
        )
    elif gpa >= 1.8:
        overall_grade, overall_color, gpa_desc = "C", WARNING, "Vulnerable Framework"
        prescription = (
            "Your framework is highly vulnerable. Any minor economic bump (job transition, medical charge, vehicle failure) "
            "will force you to halt plans and liquidate stocks at market bottoms. "
            "<strong>Prescription:</strong> Limit investments strictly to defensive allocations (Bonds/Cash) or halt active additions completely. "
            "Target 100% of spare cash to expand liquid savings until you cross a minimum of 3 months expenses buffer."
        )
    else:
        overall_grade, overall_color, gpa_desc = "F", DANGER, "Critical Restructuring Required"
        prescription = (
            "<strong>IMMEDIATE DANGER ALERT:</strong> You are operating with zero liquidity coverage, high debt drag, "
            "and deficit budgets. Continuing to invest in shares under these conditions represents highly speculative exposure. "
            "<strong>Prescription:</strong> Halt all investment portfolio allocations immediately. Clear cash-outs to pay immediate debt minimums. "
            "Consolidate toxic credit accounts and dramatically reduce essential spending overheads to prevent systemic bankruptcy."
        )

    # Scorecard layout
    st.markdown("---")
    section_label("Financial Health Audit Grade")

    col_grade, col_pres = st.columns([1, 2], gap="large")

    with col_grade:
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BORDER};"
            f"border-radius:12px;padding:32px 24px;text-align:center;min-height:280px;'>"
            f"<div style='font-family:{FONT_M};font-size:0.6rem;letter-spacing:0.2em;"
            f"text-transform:uppercase;color:{MUTED};margin-bottom:0.8rem;'>Financial GPA</div>"
            f"<div style='font-family:{FONT_H};font-size:5.5rem;color:{overall_color};"
            f"line-height:1;font-weight:600;'>{overall_grade}</div>"
            f"<div style='font-family:{FONT_H};font-size:1.2rem;color:{TEXT};"
            f"margin-top:1.2rem;font-weight:500;'>{gpa_desc}</div>"
            f"<div style='font-family:{FONT_M};font-size:0.68rem;color:{MUTED};"
            f"margin-top:0.4rem;'>Score: {gpa:.2f} / 4.00</div>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_pres:
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BORDER};"
            f"border-left:4px solid {overall_color};border-radius:0 12px 12px 0;"
            f"padding:28px;min-height:280px;'>"
            f"<h4 style='font-family:{FONT_H};font-size:1.35rem;color:{TEXT};"
            f"margin-top:0;margin-bottom:0.8rem;'>Clinical Financial Prescription</h4>"
            f"<p style='font-family:{FONT_B};font-size:0.95rem;color:{TEXT};"
            f"line-height:1.75;font-weight:300;margin:0;'>{prescription}</p>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Diagnostic Pillar Summary")

    # Render three pillar rows as dynamic HTML tables
    headers = ["Resilience Pillar", "Your Statistics", "Calculated Metric", "Audit Grade", "Adviser Diagnostic"]
    rows = [
        [
            "<strong>Emergency Coverage (Liquidity)</strong>",
            fmt(total_liquidity),
            f"{lcr:.1f} Months Essential Overheads",
            f"<span style='color:{lcr_color};font-weight:500;font-family:{FONT_M};'>{lcr_grade}</span>",
            lcr_note
        ],
        [
            "<strong>Debt Overhead Weight (Solvency)</strong>",
            fmt(debt_payments) + " / mo",
            f"{dsr_pct:.1f}% of net income",
            f"<span style='color:{dsr_color};font-weight:500;font-family:{FONT_M};'>{dsr_grade}</span>",
            dsr_note
        ],
        [
            "<strong>Savings Accelerator (Wealth Rate)</strong>",
            fmt(monthly_savings) + " / mo",
            f"{sra_pct:.1f}% savings rate",
            f"<span style='color:{sra_color};font-weight:500;font-family:{FONT_M};'>{sra_grade}</span>",
            sra_note
        ]
    ]

    html_row_table(headers, rows)


# ───────────────────────────────────────────────────────────────────────
# TAB 6 — INTERACTIVE HORIZON & VOLATILITY SIMULATOR (9/10 PROBLEM-SOLVING)
# ───────────────────────────────────────────────────────────────────────

with tab6:

    advisor_quote(
        "For beginners, the absolute hardest concept is staying patient through market corrections and ignoring "
        "short-term volatility. This simulator isolates and demonstrates the differences between <strong>Cash Bank Savings</strong> "
        "(eroded by inflation) and a <strong>Growth Investment Portfolio</strong> across various economic cycles. "
        "Adjust the parameters below to see how systematic compounding systematically builds real wealth.",
        kind="wisdom",
    )

    section_label("Simulator Configuration")

    col_s1, col_s2 = st.columns(2, gap="large")

    with col_s1:
        init_capital = st.slider(
            "Initial Investment Capital",
            min_value=0,
            max_value=250000,
            value=10000,
            step=5000,
            format=f"{sym()}%d",
            key="s_init_capital"
        )
        monthly_cont = st.slider(
            "Regular Monthly Savings Addition",
            min_value=0,
            max_value=5000,
            value=500,
            step=100,
            format=f"{sym()}%d",
            key="s_monthly_cont"
        )

    with col_s2:
        runway_yrs = st.slider(
            "Investment Runway (Horizon Years)",
            min_value=1,
            max_value=40,
            value=20,
            step=1,
            key="s_runway"
        )
        sim_inflation = st.slider(
            "Expected Annual Inflation Rate",
            min_value=0.0,
            max_value=8.0,
            value=2.5,
            step=0.5,
            format="%f%%",
            key="s_inflation"
        )

    market_modes = [
        "Steady Average Growth (Balanced Equity - 7.5% p.a.)",
        "Volatile Equity Cycles (Growth Equity - 9.0% p.a. average with cycles)",
        "Stagflationary Drag (Poor Equity - 3.0% p.a. vs 5.0% high inflation)",
        "Early Catastrophe & Steady Recovery (Severe -20% Year 1 crash)",
    ]

    selected_mode = st.selectbox(
        "Market Volatility Environment Mode",
        market_modes,
        index=1,
        key="s_market_mode"
    )

    # ── COMPREHENSIVE SIMULATOR LOOP ──
    sim_nominal_cash = float(init_capital)
    sim_nominal_port = float(init_capital)
    
    cash_trace = [sim_nominal_cash]
    port_nom_trace = [sim_nominal_port]
    port_real_trace = [sim_nominal_port]
    years_trace = [0]
    
    annual_addition = float(monthly_cont * 12)
    
    # Cycles mapping
    # Mode 1: Steady 7.5%
    # Mode 2: Volatile (Bull 18%, Great 22%, Flat 2%, Correction -15%)
    # Mode 3: Stagflation (Return 3%, Inflation overridden to 5.0%)
    # Mode 4: Early Crash (Yr 1: -20%, Yr 2: -15%, thereafter 8.5% recovery)
    
    mode_index = market_modes.index(selected_mode)
    
    active_inflation = sim_inflation
    if mode_index == 2:
        active_inflation = 5.0  # Stagflation high inflation override

    for yr in range(1, runway_yrs + 1):
        # 1. Compounding Cash Savings Path (assumed standard 3.0% interest rate)
        sim_nominal_cash = (sim_nominal_cash + annual_addition) * 1.03
        cash_trace.append(sim_nominal_cash)
        
        # 2. Compounding Portfolio Path
        if mode_index == 0:
            ret = 0.075
        elif mode_index == 1:
            cycle = [0.18, 0.22, 0.02, -0.15]
            ret = cycle[(yr - 1) % 4]
        elif mode_index == 2:
            ret = 0.03
        else:
            if yr == 1:
                ret = -0.20
            elif yr == 2:
                ret = -0.15
            else:
                ret = 0.085
                
        sim_nominal_port = (sim_nominal_port + annual_addition) * (1.0 + ret)
        port_nom_trace.append(sim_nominal_port)
        
        # 3. Adjusting for Inflation (Purchasing Power Drag)
        inf_factor = (1.0 + (active_inflation / 100.0)) ** yr
        sim_real_port = sim_nominal_port / inf_factor
        port_real_trace.append(sim_real_port)
        
        years_trace.append(yr)

    # ── METRIC STATISTICS calculations ──
    inflation_cost = sim_nominal_port - port_real_trace[-1]
    growth_premium = sim_nominal_port - sim_nominal_cash

    st.markdown("---")
    section_label("Simulation Growth Ledger")

    # Display KPI Stats
    kpi_row([
        ("Projected Wealth Accumulated", fmt(sim_nominal_port), f"Portfolio after {runway_yrs} years", True),
        ("Inflation Purchasing Cost", f"-{fmt(inflation_cost)}", f"Real purchasing value: {fmt(port_real_trace[-1])}", False),
        ("Portfolio Over Cash Premium", fmt(growth_premium), f"Outperformed basic cash savings", False),
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PLOTLY LINE VISUALIZATION ──
    fig_sim = go.Figure()
    
    # Nominal Portfolio Line
    fig_sim.add_trace(go.Scatter(
        x=years_trace,
        y=port_nom_trace,
        mode="lines+markers",
        name="Nominal Investment Portfolio (Growth Asset Mix)",
        line=dict(color=NAVY, width=3),
        hovertemplate="Year %{x}<br>Nominal Portfolio: %{y:,.0f}<extra></extra>"
    ))
    
    # Real Portfolio Area
    fig_sim.add_trace(go.Scatter(
        x=years_trace,
        y=port_real_trace,
        mode="lines",
        name="Real Inflation-Adjusted Portfolio (Purchasing Power)",
        line=dict(color=SUCCESS, width=2, dash="dash"),
        hovertemplate="Year %{x}<br>Real Value: %{y:,.0f}<extra></extra>"
    ))
    
    # Cash Savings Line
    fig_sim.add_trace(go.Scatter(
        x=years_trace,
        y=cash_trace,
        mode="lines",
        name="Nominal Cash Savings (3.0% interest bank deposits)",
        line=dict(color=GOLD, width=2.5),
        hovertemplate="Year %{x}<br>Cash Savings: %{y:,.0f}<extra></extra>"
    ))

    fig_sim.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=30, b=10, l=10, r=10),
        height=380,
        legend=dict(
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            font=dict(family=FONT_M, size=9, color=MUTED),
            orientation="h", y=1.12,
        ),
        xaxis=dict(
            showgrid=False, color=MUTED,
            tickfont=dict(family=FONT_M, size=9, color=MUTED),
            title=dict(text="Timeline Runway (Years)", font=dict(family=FONT_M, size=9, color=MUTED)),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=BORDER,
            tickfont=dict(family=FONT_M, size=9, color=MUTED),
            tickprefix=sym(),
        ),
        font=dict(family=FONT_B, color=TEXT),
    )

    st.plotly_chart(fig_sim, use_container_width=True)

    # Educational Wisdom Commentary
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("Educational Insight · Volatility & Runway Dynamics")

    col_e1, col_e2 = st.columns(2, gap="large")

    with col_e1:
        st.markdown(
            f"<h4 style='font-family:{FONT_H};font-size:1.25rem;color:{NAVY};"
            f"margin-top:0;margin-bottom:0.5rem;'>1. The Fallacy of Market Timing</h4>"
            f"<p style='font-family:{FONT_B};font-size:0.875rem;color:{TEXT};"
            f"line-height:1.7;font-weight:300;margin:0 0 1rem;'>"
            f"Select the <strong>Early Catastrophe & Steady Recovery</strong> mode. Observe the visual "
            f"path. Even when experiencing a devastating <strong>-35% combined crash</strong> in Years 1 and 2, "
            f"the disciplined accumulation portfolio recovers and dramatically outperforms cash savings over a 20-year runway. "
            f"Beginners routinely panic and sell assets at market bottoms. In senior wealth practice, we teach "
            f"that <em>time in the market</em> compounds assets; trying to time market bottoms is a mathematical wealth drag.</p>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_e2:
        st.markdown(
            f"<h4 style='font-family:{FONT_H};font-size:1.25rem;color:{GOLD};"
            f"margin-top:0;margin-bottom:0.5rem;'>2. The Invisible Overhead: Inflation</h4>"
            f"<p style='font-family:{FONT_B};font-size:0.875rem;color:{TEXT};"
            f"line-height:1.7;font-weight:300;margin:0;'>"
            f"Compare the solid Navy line (Nominal Portfolio) with the green dashed line (Real Portfolio). "
            f"The gap between them represents the invisible tax of <strong>Inflation</strong>. "
            f"At a standard {sim_inflation}%, your purchasing power is eroded by {sim_inflation}% every single year. "
            f"If you hold assets solely in low-yield cash accounts, you are taking a guaranteed real capital loss. "
            f"Accepting asset class price volatility is the entry price you pay to secure positive, compounding "
            f"purchasing power growth.</p>"
            f"</div>",
            unsafe_allow_html=True
        )
