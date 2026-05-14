import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

# Page config
st.set_page_config(
    page_title="Seralung Finance",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Themes
THEMES = {
    "Slate (Default)": {
        "bg": "#0F1117",
        "surface": "#1A1D27",
        "surface2": "#22263A",
        "border": "#2E3350",
        "accent": "#6C8EF5",
        "accent2": "#4ECDC4",
        "text": "#E8EAF6",
        "muted": "#8B90B0",
        "green": "#43D9A2",
        "red": "#FF6B6B",
        "amber": "#FFB347",
        "chart_colors": ["#6C8EF5", "#4ECDC4", "#FF6B6B", "#FFB347", "#43D9A2", "#C084FC"],
    },
    "Ivory (Light)": {
        "bg": "#FAFAF8",
        "surface": "#FFFFFF",
        "surface2": "#F4F3F0",
        "border": "#E5E3DC",
        "accent": "#3D5A80",
        "accent2": "#98C1D9",
        "text": "#1A1A1A",
        "muted": "#6B6B6B",
        "green": "#2D6A4F",
        "red": "#C1121F",
        "amber": "#E76F51",
        "chart_colors": ["#3D5A80", "#98C1D9", "#E76F51", "#2D6A4F", "#E9C46A", "#8B5CF6"],
    },
    "Forest (Earthy)": {
        "bg": "#1A2018",
        "surface": "#232C20",
        "surface2": "#2C3828",
        "border": "#3D5C36",
        "accent": "#7EC850",
        "accent2": "#A8D878",
        "text": "#E6F0E0",
        "muted": "#8AA880",
        "green": "#7EC850",
        "red": "#E8685A",
        "amber": "#F0B840",
        "chart_colors": ["#7EC850", "#A8D878", "#F0B840", "#E8685A", "#5BC8AF", "#C4A0DC"],
    },
    "Sand (Minimal)": {
        "bg": "#F5F0E8",
        "surface": "#FFFFFF",
        "surface2": "#EDE8DC",
        "border": "#D4CBBA",
        "accent": "#8B7355",
        "accent2": "#C4A882",
        "text": "#2C2416",
        "muted": "#7A6E60",
        "green": "#4A7C59",
        "red": "#C0392B",
        "amber": "#D4883A",
        "chart_colors": ["#8B7355", "#C4A882", "#4A7C59", "#D4883A", "#5B8DB8", "#9B59B6"],
    },
    "Midnight (Deep Blue)": {
        "bg": "#060B18",
        "surface": "#0D1526",
        "surface2": "#142035",
        "border": "#1E3050",
        "accent": "#4FC3F7",
        "accent2": "#29B6F6",
        "text": "#E1F0FF",
        "muted": "#6A8BAA",
        "green": "#26C6DA",
        "red": "#EF5350",
        "amber": "#FFA726",
        "chart_colors": ["#4FC3F7", "#26C6DA", "#EF5350", "#FFA726", "#AB47BC", "#66BB6A"],
    },
    "Rose (Warm Pink)": {
        "bg": "#FDF6F0",
        "surface": "#FFFFFF",
        "surface2": "#FAF0EC",
        "border": "#F0D8D0",
        "accent": "#C2666A",
        "accent2": "#E8958A",
        "text": "#2D1A1A",
        "muted": "#8A6060",
        "green": "#5B8A6A",
        "red": "#C2403A",
        "amber": "#D4883A",
        "chart_colors": ["#C2666A", "#E8958A", "#5B8A6A", "#D4883A", "#5B78B8", "#8B5CF6"],
    },
}

# Sidebar
with st.sidebar:
    st.markdown("## Seralung Finance")
    st.markdown("---")
    theme_name = st.selectbox("Theme", list(THEMES.keys()))
    T = THEMES[theme_name]
    st.markdown("---")

# Global CSS
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: {T['bg']};
    color: {T['text']};
}}
.stApp {{ background-color: {T['bg']}; }}
[data-testid="stSidebar"] {{
    background-color: {T['surface']};
    border-right: 1px solid {T['border']};
}}
[data-testid="stSidebar"] * {{ color: {T['text']} !important; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}

[data-testid="metric-container"] {{
    background: {T['surface']};
    border: 1px solid {T['border']};
    border-radius: 12px;
    padding: 1rem 1.25rem;
}}
[data-testid="metric-container"] label {{ color: {T['muted']} !important; font-size: 0.75rem !important; }}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{ color: {T['text']} !important; font-weight: 600; }}

[data-testid="stTabs"] [role="tab"] {{
    background: {T['surface2']};
    border: 1px solid {T['border']};
    border-radius: 8px;
    color: {T['muted']};
    font-size: 0.85rem;
    font-weight: 500;
    padding: 0.4rem 1rem;
    margin-right: 4px;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: {T['accent']};
    color: #fff;
    border-color: {T['accent']};
}}
[data-testid="stTabs"] [role="tablist"] {{ border-bottom: 1px solid {T['border']}; padding-bottom: 0.5rem; }}

[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
textarea {{
    background: {T['surface2']} !important;
    border: 1px solid {T['border']} !important;
    border-radius: 8px !important;
    color: {T['text']} !important;
    font-family: 'DM Sans', sans-serif !important;
}}

[data-testid="stSelectbox"] > div > div {{
    background: {T['surface2']} !important;
    border: 1px solid {T['border']} !important;
    color: {T['text']} !important;
    border-radius: 8px !important;
}}

[data-testid="baseButton-primary"], .stButton > button {{
    background: {T['accent']} !important;
    border: none !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
}}
.stButton > button:hover {{
    opacity: 0.88 !important;
    transform: translateY(-1px);
}}

hr {{ border-color: {T['border']}; }}
h1, h2, h3 {{ color: {T['text']} !important; font-weight: 600; }}

.sf-card {{
    background: {T['surface']};
    border: 1px solid {T['border']};
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}}
.sf-card-title {{
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {T['muted']};
    margin-bottom: 1rem;
}}
.sf-badge-green {{
    background: {T['green']}22;
    color: {T['green']};
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-block;
}}
.sf-badge-red {{
    background: {T['red']}22;
    color: {T['red']};
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-block;
}}
.sf-badge-amber {{
    background: {T['amber']}22;
    color: {T['amber']};
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-block;
}}
.sf-tip {{
    background: {T['accent']}18;
    border-left: 3px solid {T['accent']};
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: {T['text']};
    margin-bottom: 1rem;
    line-height: 1.5;
}}
.sf-proj-row {{
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid {T['border']};
    font-size: 0.875rem;
    color: {T['text']};
}}
.sf-proj-row:last-child {{ border-bottom: none; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)


# Plotly layout helper
def plot_layout(title="", height=280):
    return dict(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=T["muted"], size=11),
        height=height,
        margin=dict(l=10, r=10, t=30 if title else 10, b=10),
        legend=dict(
            font=dict(color=T["muted"], size=11),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        xaxis=dict(gridcolor=T["border"], linecolor=T["border"], showgrid=True),
        yaxis=dict(gridcolor=T["border"], linecolor=T["border"], showgrid=True),
    )


# Session state defaults
def _init(key, val):
    if key not in st.session_state:
        st.session_state[key] = val


_init("expenses", [
    {"name": "Rent / Mortgage", "amount": 1500.0},
    {"name": "Groceries", "amount": 400.0},
    {"name": "Transport", "amount": 200.0},
    {"name": "Dining & Entertainment", "amount": 300.0},
    {"name": "Subscriptions", "amount": 80.0},
])
_init("goals", [])
_init("risk_profile", "Moderate")
_init("needs_pct", 50)
_init("wants_pct", 30)
_init("invest_pct", 20)
_init("em_pct", 30)
_init("idx_pct", 40)
_init("stk_pct", 20)
_init("cry_pct", 10)

# Header
col_logo, col_sub = st.columns([3, 1])
with col_logo:
    st.markdown(
        "<h1 style='margin:0; font-size:1.8rem; letter-spacing:-0.02em;'>Seralung Finance</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{T['muted']}; font-size:0.85rem; margin-top:2px; margin-bottom:1.5rem;'>"
        "Your personal financial command centre</p>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# Sidebar income inputs
with st.sidebar:
    st.markdown(
        f"<p style='color:{T['muted']}; font-size:0.75rem; font-weight:600; "
        "letter-spacing:0.08em; text-transform:uppercase;'>Monthly Income</p>",
        unsafe_allow_html=True,
    )
    primary_income = st.number_input(
        "Primary salary (after tax)", min_value=0.0, value=5000.0, step=100.0, format="%.0f"
    )
    other_income = st.number_input(
        "Other income", min_value=0.0, value=0.0, step=50.0, format="%.0f"
    )
    total_income = primary_income + other_income

    st.markdown("---")
    st.markdown(
        f"<p style='color:{T['muted']}; font-size:0.75rem; font-weight:600; "
        "letter-spacing:0.08em; text-transform:uppercase;'>Budget Rule</p>",
        unsafe_allow_html=True,
    )
    needs_pct = st.slider("Needs %", 0, 100, st.session_state.needs_pct, 1)
    wants_pct = st.slider("Wants %", 0, 100, st.session_state.wants_pct, 1)
    invest_pct = st.slider("Invest/Save %", 0, 100, st.session_state.invest_pct, 1)
    total_pct = needs_pct + wants_pct + invest_pct
    if total_pct != 100:
        st.warning(f"Allocations sum to {total_pct}% (must be 100%)")
    st.session_state.needs_pct = needs_pct
    st.session_state.wants_pct = wants_pct
    st.session_state.invest_pct = invest_pct

    st.markdown("---")
    st.markdown(
        f"<p style='color:{T['muted']}; font-size:0.75rem; font-weight:600; "
        "letter-spacing:0.08em; text-transform:uppercase;'>About</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='color:{T['muted']}; font-size:0.75rem; line-height:1.5;'>"
        "Seralung Finance is for educational purposes only. Not financial advice.</p>",
        unsafe_allow_html=True,
    )

# Derived values
total_expenses = sum(e["amount"] for e in st.session_state.expenses)
investable = total_income * invest_pct / 100
left_over = total_income - total_expenses
needs_budget = total_income * needs_pct / 100
wants_budget = total_income * wants_pct / 100

# Summary metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Monthly Income", f"${total_income:,.0f}")
m2.metric(
    "Total Expenses",
    f"${total_expenses:,.0f}",
    delta=f"${total_expenses - total_income:,.0f}" if total_expenses > total_income else None,
    delta_color="inverse",
)
m3.metric("Investable (target)", f"${investable:,.0f}", f"{invest_pct}% of income")
m4.metric(
    "Left Over",
    f"${left_over:,.0f}",
    delta="Surplus" if left_over >= 0 else "Deficit",
    delta_color="normal" if left_over >= 0 else "inverse",
)

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# Tabs
tab_budget, tab_invest, tab_risk, tab_goals, tab_tax = st.tabs(
    ["Budget", "Invest", "Risk", "Goals", "Tax & FIRE"]
)

# =============================================================================
# TAB 1 — BUDGET
# =============================================================================
with tab_budget:
    col_exp, col_charts = st.columns([1, 1], gap="large")

    with col_exp:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Monthly Expenses</div>", unsafe_allow_html=True)

        to_delete = None
        for i, exp in enumerate(st.session_state.expenses):
            c1, c2, c3 = st.columns([3, 2, 0.5])
            with c1:
                new_name = st.text_input(
                    f"name_{i}", value=exp["name"], label_visibility="collapsed", key=f"ename_{i}"
                )
                st.session_state.expenses[i]["name"] = new_name
            with c2:
                new_amt = st.number_input(
                    f"amt_{i}",
                    value=float(exp["amount"]),
                    min_value=0.0,
                    step=10.0,
                    label_visibility="collapsed",
                    key=f"eamt_{i}",
                    format="%.0f",
                )
                st.session_state.expenses[i]["amount"] = new_amt
            with c3:
                if st.button("X", key=f"del_{i}", help="Remove"):
                    to_delete = i

        if to_delete is not None:
            st.session_state.expenses.pop(to_delete)
            st.rerun()

        col_an, col_aa = st.columns(2)
        with col_an:
            new_exp_name = st.text_input("New category name", placeholder="e.g. Gym", key="new_exp_name")
        with col_aa:
            new_exp_amt = st.number_input("Amount ($)", min_value=0.0, step=10.0, key="new_exp_amt", format="%.0f")
        if st.button("+ Add expense", use_container_width=True):
            if new_exp_name:
                st.session_state.expenses.append({"name": new_exp_name, "amount": float(new_exp_amt)})
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with col_charts:
        if st.session_state.expenses:
            df_exp = pd.DataFrame(st.session_state.expenses)
            df_exp = df_exp[df_exp["amount"] > 0].sort_values("amount", ascending=True)
            colors = (T["chart_colors"] * math.ceil(len(df_exp) / len(T["chart_colors"])))[:len(df_exp)]
            fig_exp = go.Figure(go.Bar(
                x=df_exp["amount"],
                y=df_exp["name"],
                orientation="h",
                marker_color=colors,
                text=[f"${v:,.0f}" for v in df_exp["amount"]],
                textposition="outside",
                textfont=dict(color=T["muted"], size=11),
            ))
            fig_exp.update_layout(**plot_layout("Spending by category", height=260))
            st.plotly_chart(fig_exp, use_container_width=True)

        # Budget rule breakdown
        st.markdown(
            f"<div class='sf-card'><div class='sf-card-title'>"
            f"{needs_pct}/{wants_pct}/{invest_pct} Rule Snapshot</div>",
            unsafe_allow_html=True,
        )
        rows = [
            ("Needs", needs_budget, T["accent"]),
            ("Wants", wants_budget, T["accent2"]),
            ("Invest / Save", investable, T["green"]),
        ]
        for label, budget, color in rows:
            if label == "Invest / Save":
                actual = investable
            elif label == "Needs":
                actual = total_expenses * 0.6
            else:
                actual = total_expenses * 0.4
            pct = min(100, round(actual / budget * 100)) if budget > 0 else 0
            badge_color = "green" if pct <= 80 else "amber" if pct <= 100 else "red"
            badge_text = "On track" if pct <= 80 else "Near limit" if pct <= 100 else "Over"
            badge = f"<span class='sf-badge-{badge_color}'>{badge_text}</span>"
            bar_color = T["red"] if pct > 100 else color
            st.markdown(
                f"""<div style='margin-bottom:10px;'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:4px;
                              font-size:0.8rem;color:{T["muted"]};'>
                    <span>{label} — ${actual:,.0f} / ${budget:,.0f}</span>{badge}
                  </div>
                  <div style='background:{T["surface2"]};border-radius:6px;height:7px;overflow:hidden;'>
                    <div style='width:{pct}%;height:100%;background:{bar_color};
                                border-radius:6px;transition:width 0.4s;'></div>
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Donut
        if st.session_state.expenses:
            df_donut = pd.DataFrame(st.session_state.expenses)
            df_donut = df_donut[df_donut["amount"] > 0]
            donut_colors = (T["chart_colors"] * math.ceil(len(df_donut) / len(T["chart_colors"])))[:len(df_donut)]
            fig_donut = go.Figure(go.Pie(
                labels=df_donut["name"],
                values=df_donut["amount"],
                hole=0.55,
                marker=dict(colors=donut_colors, line=dict(color=T["bg"], width=2)),
                textfont=dict(size=11, color=T["muted"]),
                hovertemplate="%{label}<br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_donut.update_layout(**plot_layout("Expense distribution", height=260))
            st.plotly_chart(fig_donut, use_container_width=True)

# =============================================================================
# TAB 2 — INVEST
# =============================================================================
with tab_invest:
    st.markdown(
        f"<div class='sf-tip'>Based on your {invest_pct}% savings rate, you have "
        f"<strong>${investable:,.0f}/month</strong> to invest. Adjust your allocation below.</div>",
        unsafe_allow_html=True,
    )

    col_split, col_proj = st.columns([1, 1], gap="large")

    with col_split:
        st.markdown("<div class='sf-card'><div class='sf-card-title'>Investment split</div>", unsafe_allow_html=True)
        em_pct = st.slider("Emergency fund", 0, 100, st.session_state.em_pct, 1)
        idx_pct = st.slider("Index funds (ETFs)", 0, 100, st.session_state.idx_pct, 1)
        stk_pct = st.slider("Individual stocks", 0, 100, st.session_state.stk_pct, 1)
        cry_pct = st.slider("Crypto", 0, 100, st.session_state.cry_pct, 1)
        isum = em_pct + idx_pct + stk_pct + cry_pct
        if isum != 100:
            st.warning(f"Investment splits sum to {isum}% (must be 100%)")
        st.session_state.em_pct = em_pct
        st.session_state.idx_pct = idx_pct
        st.session_state.stk_pct = stk_pct
        st.session_state.cry_pct = cry_pct
        st.markdown("</div>", unsafe_allow_html=True)

        labels = ["Emergency", "Index funds", "Stocks", "Crypto"]
        values = [em_pct, idx_pct, stk_pct, cry_pct]
        amounts = [investable * v / 100 for v in values]
        fig_inv_donut = go.Figure(go.Pie(
            labels=[f"{l} ${a:,.0f}/mo" for l, a in zip(labels, amounts)],
            values=values,
            hole=0.55,
            marker=dict(
                colors=[T["accent"], T["green"], T["amber"], T["red"]],
                line=dict(color=T["bg"], width=2),
            ),
            textfont=dict(size=11, color=T["muted"]),
        ))
        fig_inv_donut.update_layout(**plot_layout("Monthly allocation", height=260))
        st.plotly_chart(fig_inv_donut, use_container_width=True)

    with col_proj:
        years = list(range(0, 11))

        def compound(rate):
            v, result = 0, []
            for _ in years:
                result.append(round(v))
                v = (v + investable * 12) * (1 + rate)
            return result

        c_proj = compound(0.04)
        m_proj = compound(0.07)
        a_proj = compound(0.12)

        fig_proj = go.Figure()
        for proj, label, color, dash in [
            (c_proj, "Conservative (4%)", T["accent"], "dot"),
            (m_proj, "Moderate (7%)", T["green"], "solid"),
            (a_proj, "Aggressive (12%)", T["amber"], "dash"),
        ]:
            fig_proj.add_trace(go.Scatter(
                x=years,
                y=proj,
                name=label,
                mode="lines",
                line=dict(color=color, width=2, dash=dash),
                hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>",
            ))
        fig_proj.update_layout(**plot_layout("10-year growth projection", height=300))
        fig_proj.update_yaxes(tickprefix="$", tickformat=",.0f")
        fig_proj.update_xaxes(title_text="Year", tickvals=years)
        st.plotly_chart(fig_proj, use_container_width=True)

        st.markdown("<div class='sf-card'><div class='sf-card-title'>Year-by-year summary</div>", unsafe_allow_html=True)
        for yr in [1, 3, 5, 10]:
            st.markdown(
                f"""<div class='sf-proj-row'>
                  <span>Year {yr}</span>
                  <span style='color:{T["accent"]}'>${c_proj[yr]:,}</span>
                  <span style='color:{T["green"]}'>${m_proj[yr]:,}</span>
                  <span style='color:{T["amber"]}'>${a_proj[yr]:,}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;font-size:0.7rem;"
            f"color:{T['muted']};padding-top:6px;'>"
            "<span></span><span>Conservative</span><span>Moderate</span><span>Aggressive</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# TAB 3 — RISK
# =============================================================================
with tab_risk:
    risk_profiles = {
        "Conservative": {
            "desc": "Capital preservation. Low volatility, stable returns. Suited to short time horizons or risk-averse investors.",
            "alloc": {"Government bonds": 40, "Blue-chip stocks": 30, "REITs": 20, "Cash": 10},
            "ret": (3, 5),
            "scenarios": (-5, 3, 8),
            "colors": [T["accent"], T["green"], T["accent2"], T["muted"]],
        },
        "Moderate": {
            "desc": "Balanced growth. Mix of equities and fixed income. Suited to medium-term goals (5-15 years).",
            "alloc": {"Index funds": 50, "Growth stocks": 25, "Bonds": 15, "Crypto": 10},
            "ret": (6, 9),
            "scenarios": (-15, 7, 18),
            "colors": [T["green"], T["amber"], T["accent"], T["red"]],
        },
        "Aggressive": {
            "desc": "Maximum growth. High volatility, high potential. Suited to long time horizons (15+ years) with risk tolerance.",
            "alloc": {"Growth stocks": 40, "Crypto": 25, "Emerging markets": 20, "Options/Alts": 15},
            "ret": (10, 20),
            "scenarios": (-35, 12, 45),
            "colors": [T["amber"], T["red"], T["accent2"], T["muted"]],
        },
    }

    r1, r2, r3 = st.columns(3)
    for col, rname in zip([r1, r2, r3], risk_profiles.keys()):
        with col:
            rp = risk_profiles[rname]
            selected = st.session_state.risk_profile == rname
            border_style = f"2px solid {T['accent']}" if selected else f"1px solid {T['border']}"
            bg_style = T["surface2"] if selected else T["surface"]
            st.markdown(
                f"""<div style='background:{bg_style};border:{border_style};border-radius:12px;
                               padding:1rem;'>
                  <div style='font-weight:600;font-size:0.95rem;color:{T["text"]};margin-bottom:6px;'>{rname}</div>
                  <div style='font-size:0.78rem;color:{T["muted"]};line-height:1.5;'>{rp["desc"]}</div>
                  <div style='margin-top:10px;font-size:0.78rem;color:{T["accent"]};font-weight:600;'>
                    Expected: {rp["ret"][0]}-{rp["ret"][1]}% p.a.
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(f"Select {rname}", key=f"risk_{rname}", use_container_width=True):
                st.session_state.risk_profile = rname
                st.rerun()

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
    rp = risk_profiles[st.session_state.risk_profile]

    col_alloc, col_scen = st.columns([1, 1], gap="large")

    with col_alloc:
        st.markdown(
            f"<div class='sf-card'><div class='sf-card-title'>Portfolio: {st.session_state.risk_profile}</div>",
            unsafe_allow_html=True,
        )
        asset_keys = list(rp["alloc"].keys())
        for idx_a, (asset, pct) in enumerate(rp["alloc"].items()):
            amt = investable * pct / 100
            bar_color = rp["colors"][idx_a]
            st.markdown(
                f"""<div style='margin-bottom:10px;'>
                  <div style='display:flex;justify-content:space-between;font-size:0.8rem;
                              color:{T["muted"]};margin-bottom:4px;'>
                    <span>{asset}</span><span>{pct}% - ${amt:,.0f}/mo</span>
                  </div>
                  <div style='background:{T["surface2"]};border-radius:5px;height:6px;'>
                    <div style='width:{pct}%;height:100%;background:{bar_color};border-radius:5px;'></div>
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        fig_r_donut = go.Figure(go.Pie(
            labels=list(rp["alloc"].keys()),
            values=list(rp["alloc"].values()),
            hole=0.55,
            marker=dict(colors=rp["colors"], line=dict(color=T["bg"], width=2)),
            textfont=dict(size=11, color=T["muted"]),
        ))
        fig_r_donut.update_layout(**plot_layout("Allocation breakdown", height=240))
        st.plotly_chart(fig_r_donut, use_container_width=True)

    with col_scen:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>Scenario analysis (10-year)</div>",
            unsafe_allow_html=True,
        )
        base = investable * 12 * 10
        scen_data = [
            ("Bear market", rp["scenarios"][0], T["red"], "red"),
            ("Average", rp["scenarios"][1], T["amber"], "amber"),
            ("Bull market", rp["scenarios"][2], T["green"], "green"),
        ]
        for label, ret, color, badge_type in scen_data:
            est = base * (1 + ret / 100)
            st.markdown(
                f"""<div class='sf-proj-row'>
                  <span>{label}</span>
                  <span class='sf-badge-{badge_type}'>{ret:+}%</span>
                  <span style='color:{color};font-weight:600;'>${est:,.0f}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        bubble_data = [
            {"asset": "Cash/Bonds", "risk": 5, "return": 2.5, "size": 16},
            {"asset": "Index funds", "risk": 28, "return": 7, "size": 24},
            {"asset": "Growth stocks", "risk": 52, "return": 12, "size": 20},
            {"asset": "Crypto", "risk": 80, "return": 22, "size": 14},
            {"asset": "REITs", "risk": 35, "return": 8, "size": 18},
        ]
        fig_bubble = go.Figure()
        for i, d in enumerate(bubble_data):
            fig_bubble.add_trace(go.Scatter(
                x=[d["risk"]],
                y=[d["return"]],
                mode="markers+text",
                name=d["asset"],
                text=[d["asset"]],
                textposition="top center",
                textfont=dict(size=10, color=T["muted"]),
                marker=dict(
                    size=d["size"] * 2,
                    color=T["chart_colors"][i % len(T["chart_colors"])],
                    opacity=0.8,
                ),
            ))
        fig_bubble.update_layout(**plot_layout("Risk vs. expected return", height=300))
        fig_bubble.update_xaxes(title_text="Risk (volatility %)", range=[-5, 100])
        fig_bubble.update_yaxes(title_text="Expected return %", ticksuffix="%", range=[-2, 30])
        st.plotly_chart(fig_bubble, use_container_width=True)

# =============================================================================
# TAB 4 — GOALS
# =============================================================================
with tab_goals:
    g1, g2, g3 = st.columns(3)
    g1.metric("Monthly investable", f"${investable:,.0f}")
    g2.metric("1-year savings", f"${investable * 12:,.0f}")
    if investable > 0:
        five_year = investable * 12 * ((pow(1 + 0.07 / 12, 60) - 1) / (0.07 / 12))
    else:
        five_year = 0
    g3.metric("5-year (7% growth)", f"${five_year:,.0f}")

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

    with st.expander("+ Add a financial goal", expanded=not st.session_state.goals):
        gc1, gc2, gc3 = st.columns([2, 1, 1])
        with gc1:
            goal_name = st.text_input("Goal name", placeholder="House deposit, Car, Holiday...")
        with gc2:
            goal_amount = st.number_input("Target ($)", min_value=0.0, step=1000.0, format="%.0f")
        with gc3:
            goal_saved = st.number_input("Already saved ($)", min_value=0.0, step=100.0, format="%.0f")
        if st.button("Add goal", use_container_width=True):
            if goal_name and goal_amount > 0:
                st.session_state.goals.append({"name": goal_name, "amount": goal_amount, "saved": goal_saved})
                st.rerun()

    if st.session_state.goals:
        for i, g in enumerate(st.session_state.goals):
            remaining = max(0, g["amount"] - g["saved"])
            months = math.ceil(remaining / investable) if investable > 0 else 9999
            years_g = months / 12
            pct_g = min(100, round(g["saved"] / g["amount"] * 100)) if g["amount"] > 0 else 0
            col_g, col_del = st.columns([10, 1])
            with col_g:
                st.markdown(
                    f"""<div class='sf-card'>
                      <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                        <span style='font-weight:600;font-size:0.95rem;color:{T["text"]}'>{g["name"]}</span>
                        <span style='font-size:0.8rem;color:{T["muted"]};'>${g["amount"]:,.0f} target</span>
                      </div>
                      <div style='font-size:0.8rem;color:{T["muted"]};margin-bottom:8px;'>
                        ${g["saved"]:,.0f} saved · ${remaining:,.0f} remaining ·
                        <span style='color:{T["accent"]};'>{years_g:.1f} years ({months} months) at current rate</span>
                      </div>
                      <div style='background:{T["surface2"]};border-radius:6px;height:8px;'>
                        <div style='width:{pct_g}%;height:100%;background:{T["green"]};border-radius:6px;'></div>
                      </div>
                      <div style='font-size:0.75rem;color:{T["muted"]};margin-top:4px;'>{pct_g}% complete</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("X", key=f"goal_del_{i}"):
                    st.session_state.goals.pop(i)
                    st.rerun()
    else:
        st.markdown(
            f"<div style='text-align:center;padding:3rem;color:{T['muted']};font-size:0.9rem;'>"
            "No goals yet - add one above to track your progress.</div>",
            unsafe_allow_html=True,
        )

    if st.session_state.goals and investable > 0:
        goal_labels = [g["name"] for g in st.session_state.goals]
        goal_months = [
            math.ceil(max(0, g["amount"] - g["saved"]) / investable)
            for g in st.session_state.goals
        ]
        gl_colors = (T["chart_colors"] * math.ceil(len(goal_labels) / len(T["chart_colors"])))[:len(goal_labels)]
        fig_goals = go.Figure(go.Bar(
            x=goal_months,
            y=goal_labels,
            orientation="h",
            marker_color=gl_colors,
            text=[f"{m} months" for m in goal_months],
            textposition="outside",
            textfont=dict(color=T["muted"], size=11),
        ))
        fig_goals.update_layout(
            **plot_layout("Time to reach each goal (months)", height=max(200, len(goal_labels) * 60))
        )
        fig_goals.update_xaxes(title_text="Months", showgrid=True)
        st.plotly_chart(fig_goals, use_container_width=True)

# =============================================================================
# TAB 5 — TAX & FIRE
# =============================================================================
with tab_tax:
    col_tax, col_fire = st.columns([1, 1], gap="large")

    with col_tax:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>Australian Tax Estimator (FY2024-25)</div>",
            unsafe_allow_html=True,
        )
        gross_income = st.number_input(
            "Annual gross income ($)",
            min_value=0.0,
            value=float(primary_income * 12),
            step=1000.0,
            format="%.0f",
        )
        include_medicare = st.checkbox("Include Medicare levy (2%)", value=True)

        # ATO 2024-25 tax brackets (fixed calculation)
        def calc_tax(income):
            if income <= 18200:
                return 0.0
            elif income <= 45000:
                return (income - 18200) * 0.19
            elif income <= 120000:
                return 5092 + (income - 45000) * 0.325
            elif income <= 180000:
                return 29467 + (income - 120000) * 0.37
            else:
                return 51667 + (income - 180000) * 0.45

        # Low Income Tax Offset (LITO) — still active FY2024-25
        def calc_lito(income):
            if income <= 37500:
                return 700.0
            elif income <= 45000:
                return 700 - (income - 37500) * 0.05
            elif income <= 66667:
                return 325 - (income - 45000) * 0.015
            else:
                return 0.0

        tax = calc_tax(gross_income)
        medicare = gross_income * 0.02 if include_medicare else 0.0
        lito = calc_lito(gross_income)
        total_tax = max(0.0, tax + medicare - lito)
        net = gross_income - total_tax
        eff_rate = (total_tax / gross_income * 100) if gross_income > 0 else 0.0

        tax_items = [
            ("Gross income", f"${gross_income:,.0f}", T["text"]),
            ("Income tax (gross)", f"-${tax:,.0f}", T["red"]),
            ("Medicare levy", f"-${medicare:,.0f}", T["amber"]),
            ("LITO offset", f"+${lito:,.0f}", T["green"]),
            ("Total tax payable", f"-${total_tax:,.0f}", T["red"]),
            ("Net income (annual)", f"${net:,.0f}", T["accent"]),
            ("Net income (monthly)", f"${net / 12:,.0f}", T["accent"]),
            ("Effective tax rate", f"{eff_rate:.1f}%", T["amber"]),
        ]
        for label, value, color in tax_items:
            is_highlight = label in ("Net income (annual)", "Net income (monthly)", "Effective tax rate")
            fw = "font-weight:600;" if is_highlight else ""
            st.markdown(
                f"""<div style='display:flex;justify-content:space-between;padding:6px 0;
                               border-bottom:1px solid {T["border"]};font-size:0.85rem;{fw}'>
                  <span style='color:{T["muted"]}'>{label}</span>
                  <span style='color:{color}'>{value}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_fire:
        st.markdown(
            "<div class='sf-card'><div class='sf-card-title'>FIRE Calculator (Financial Independence)</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size:0.78rem;color:{T['muted']};margin-bottom:1rem;line-height:1.5;'>"
            "FIRE = save 25x your annual expenses. The 4% rule lets you withdraw 4% annually "
            "without depleting your portfolio.</div>",
            unsafe_allow_html=True,
        )

        annual_expenses = st.number_input(
            "Annual living expenses ($)",
            min_value=0.0,
            value=float(total_expenses * 12),
            step=500.0,
            format="%.0f",
            key="fire_exp",
        )
        current_portfolio = st.number_input(
            "Current portfolio value ($)", min_value=0.0, value=0.0, step=1000.0, format="%.0f"
        )
        fire_target = annual_expenses * 25
        gap = max(0, fire_target - current_portfolio)

        fire_items = [
            ("Annual expenses", f"${annual_expenses:,.0f}"),
            ("FIRE number (25x)", f"${fire_target:,.0f}"),
            ("Current portfolio", f"${current_portfolio:,.0f}"),
            ("Gap remaining", f"${gap:,.0f}"),
        ]
        for label, value in fire_items:
            st.markdown(
                f"""<div style='display:flex;justify-content:space-between;padding:6px 0;
                               border-bottom:1px solid {T["border"]};font-size:0.85rem;'>
                  <span style='color:{T["muted"]}'>{label}</span>
                  <span style='color:{T["text"]};font-weight:500;'>{value}</span>
                </div>""",
                unsafe_allow_html=True,
            )

        fire_pct = min(100, round(current_portfolio / fire_target * 100)) if fire_target > 0 else 0
        st.markdown(
            f"""<div style='margin:1rem 0 0.4rem;font-size:0.8rem;color:{T["muted"]};'>
              FIRE progress: {fire_pct}%
            </div>
            <div style='background:{T["surface2"]};border-radius:6px;height:10px;'>
              <div style='width:{fire_pct}%;height:100%;background:{T["green"]};border-radius:6px;'></div>
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if investable > 0 and fire_target > 0:
            years_to_fire = list(range(0, 41))
            portfolio_vals_fire = []
            v = current_portfolio
            yr_target = None
            for yr in years_to_fire:
                portfolio_vals_fire.append(round(v))
                if v >= fire_target and yr_target is None:
                    yr_target = yr
                v = (v + investable * 12) * 1.07

            fig_fire = go.Figure()
            fig_fire.add_trace(go.Scatter(
                x=years_to_fire,
                y=portfolio_vals_fire,
                name="Portfolio (7% growth)",
                mode="lines",
                line=dict(color=T["green"], width=2),
                fill="tozeroy",
                fillcolor=T["green"] + "22",
                hovertemplate="Year %{x}<br>$%{y:,.0f}<extra></extra>",
            ))
            fig_fire.add_hline(
                y=fire_target,
                line_dash="dot",
                line_color=T["amber"],
                annotation_text=f"FIRE target ${fire_target:,.0f}",
                annotation_font_color=T["amber"],
            )
            fig_fire.update_layout(**plot_layout("Path to FIRE", height=280))
            fig_fire.update_yaxes(tickprefix="$", tickformat=",.0f")
            fig_fire.update_xaxes(title_text="Years from now")
            st.plotly_chart(fig_fire, use_container_width=True)

            if yr_target is not None:
                st.markdown(
                    f"<div class='sf-tip'>At your current savings rate, you could reach FIRE in "
                    f"approximately <strong>{yr_target} years</strong>.</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='sf-tip'>At your current rate, you may not reach FIRE within "
                    "40 years. Try increasing your savings rate above.</div>",
                    unsafe_allow_html=True,
                )

# Footer
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:{T['muted']};font-size:0.72rem;'>"
    "Seralung Finance — Educational purposes only. Not financial advice. "
    "Always consult a qualified financial adviser.</p>",
    unsafe_allow_html=True,
)
