import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import io
import csv
import math
from datetime import datetime

# =====================================================================
# 1. PAGE & THEME CONFIGURATION
# =====================================================================
st.set_page_config(page_title="Seralung Unified Finance", layout="wide", initial_sidebar_state="collapsed")

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

THEMES = {
    "Dark Modern": {
        "bg":"#0F1117","surface":"#1A1D27","surface2":"#22263A","border":"#2E3350","accent":"#10B981","text":"#F1F5F9","muted":"#94A3B8","track":"#22263A","dark": True
    },
    "Light Emerald": {
        "bg":"#F9FAFB","surface":"#FFFFFF","surface2":"#F3F4F6","border":"#E5E7EB","accent":"#059669","text":"#111827","muted":"#6B7280","track":"#E9EAEC","dark": False
    }
}

# Global State Initializer
def _init_state(k, v):
    if k not in st.session_state: 
        st.session_state[k] = v

_init_state("primary_income", 7500.0)
_init_state("other_income", 800.0)
_init_state("risk_profile", "Moderate")
_init_state("invest_capital", 30000.0)
_init_state("active_theme", "Dark Modern")
_init_state("expenses", [
    {"name":"Rent", "amount":2100.0, "budget":2200.0, "category":"Housing"},
    {"name":"Groceries", "amount":550.0, "budget":600.0, "category":"Food"},
    {"name":"Transport", "amount":280.0, "budget":300.0, "category":"Transport"},
    {"name":"Streaming Services", "amount":65.0, "budget":65.0, "category":"Entertainment"}
])
_init_state("assets", [
    {"name":"Savings Maximiser", "type":"Cash", "value":15500.0},
    {"name":"Core ETF Long", "type":"Investments", "value":22000.0}
])
_init_state("liabilities", [
    {"name":"Car Loan", "type":"Loan", "balance":11000.0},
    {"name":"Credit Card Bal", "type":"Credit", "balance":1200.0}
])
_init_state("goals", [{"name":"Emergency Lock", "target":15000.0, "saved":15000.0}])

theme = THEMES[st.session_state.active_theme]

# LINE 53: Fixed by replacing unsafe_with_html with unsafe_allow_html
st.markdown(f"""
<style>
    .stApp {{ background-color: {theme['bg']}; color: {theme['text']}; }}
    .metric-card {{
        background-color: {theme['surface']};
        padding: 24px; border-radius: 12px;
        border: 1px solid {theme['border']};
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }}
</style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. HELPER VISUAL FUNCTIONS
# =====================================================================

def render_svg_gauge(score, tier):
    r = 76; cx, cy = 100, 100
    circ = 2 * math.pi * r; half = circ / 2
    stroke_len = half * score / 100
    color = theme['accent'] if score >= 70 else "#D97706" if score >= 50 else "#DC2626"
    return f"""
    <svg viewBox="0 0 200 110" style="width:100%; max-width:220px; display:block; margin:0 auto;">
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{theme['track']}" stroke-width="14" stroke-dasharray="{half} {half}" transform="rotate(-180 {cx} {cy})" stroke-linecap="round"/>
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="14" stroke-dasharray="{stroke_len} {circ - stroke_len}" transform="rotate(-180 {cx} {cy})" stroke-linecap="round"/>
        <text x="{cx}" y="75" text-anchor="middle" font-size="36" font-weight="700" fill="{color}" font-family="sans-serif">{score}</text>
        <text x="{cx}" y="96" text-anchor="middle" font-size="11" fill="{theme['muted']}" font-family="sans-serif" letter-spacing="0.05em">{tier.upper()}</text>
    </svg>
    """

def fmt(n): return f"${n:,.0f}"

# =====================================================================
# 3. INTERFACE COMPILATION & API INTERACTION
# =====================================================================

col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("Seralung Financial Architecture")
    st.caption("Distributed Client Pipeline (FastAPI Network Logic Core)")
with col_t2:
    st.session_state.active_theme = st.selectbox("Interface Visual Theme Profile", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.active_theme))

st.write("---")

# Calculate local aggregations to send to API
total_gross_monthly = st.session_state.primary_income + st.session_state.other_income
annualized_gross = total_gross_monthly * 12

total_monthly_expenses = sum(e["amount"] for e in st.session_state.expenses)
total_assets = sum(a["value"] for a in st.session_state.assets)
total_liabilities = sum(l["balance"] for l in st.session_state.liabilities)
net_worth = total_assets - total_liabilities
cash_reserves = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash", "Savings"])
overspend = sum(max(0, e["amount"] - e["budget"]) for e in st.session_state.expenses)

# Fetch calculations from FastAPI Backend endpoints
try:
    tax_res = requests.get(f"{API_BASE_URL}/tax?income={annualized_gross}").json()
    monthly_tax = tax_res["total_tax_liability"] / 12
    net_monthly_income = total_gross_monthly - monthly_tax
    monthly_cash_surplus = net_monthly_income - total_monthly_expenses
    calculated_savings_rate = (monthly_cash_surplus / net_monthly_income * 100) if net_monthly_income > 0 else 0
    runway_months = (cash_reserves / total_monthly_expenses) if total_monthly_expenses > 0 else 0
    debt_to_income_ratio = (total_liabilities / annualized_gross * 100) if annualized_gross > 0 else 0

    telemetry_payload = {
        "savings_rate": calculated_savings_rate,
        "debt_to_income": debt_to_income_ratio,
        "runway_months": runway_months,
        "net_worth_positive": net_worth > 0,
        "budget_overrun": overspend,
        "has_goals": len(st.session_state.goals) > 0
    }
    health_data = requests.post(f"{API_BASE_URL}/telemetry", json=telemetry_payload).json()

    # Render Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.markdown(f'<div class="metric-card"><h5>Net Monthly Disposable</h5><h2>{fmt(net_monthly_income)}</h2><small style="color:{theme["muted"]}">Gross: {fmt(total_gross_monthly)}/mo</small></div>', unsafe_with_html=True)
    with m_col2:
        st.markdown(f'<div class="metric-card"><h5>Monthly Expenditures</h5><h2>{fmt(total_monthly_expenses)}</h2><small style="color:{theme["muted"]}">Overrun Flag: {fmt(overspend)}</small></div>', unsafe_with_html=True)
    with m_col3:
        st.markdown(f'<div class="metric-card"><h5>Net Operational Wealth</h5><h2>{fmt(net_worth)}</h2><small style="color:{theme["accent"]}">Liquid Safety Cushion: {fmt(cash_reserves)}</small></div>', unsafe_with_html=True)
    with m_col4:
        st.markdown(f'<div class="metric-card"><h5>Calculated Cash Flow</h5><h2>{fmt(monthly_cash_surplus)}</h2><small style="color:{theme["accent"]}">Velocity: {calculated_savings_rate:.1f}% Rate</small></div>', unsafe_with_html=True)

    st.write("##")

    tab_telemetry, tab_allocation, tab_projections = st.tabs([
        "📊 Core Telemetry & Operations", 
        "📈 Refined Asset Allocations", 
        "🔮 Vectorized Trajectory Forecasting"
    ])

    with tab_telemetry:
        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            st.markdown("<h4 style='text-align: center;'>Algorithmic Strength Telemetry</h4>", unsafe_allow_html=True)
            st.markdown(render_svg_gauge(health_data["score"], health_data["tier"]), unsafe_allow_html=True)
            st.write("##")
            st.metric(label="Calculated ATO Income Tax Drag (Annual)", value=fmt(tax_res["total_tax_liability"]), delta=f"Effective Drag: {tax_res['effective_tax_rate']}%")
            
        with col_g2:
            st.markdown("<h4>Telemetry Matrix Subcomponent Ratings Breakdown</h4>", unsafe_allow_html=True)
            breakdown_df = pd.DataFrame.from_dict(health_data["breakdown"], orient="index")
            st.dataframe(breakdown_df[["score", "max", "desc", "ok"]], use_container_width=True)

    with tab_allocation:
        st.subheader("Algorithmic Asset Allocation Pipeline Model")
        col_alloc_in, col_alloc_graph = st.columns([1, 2])
        
        with col_alloc_in:
            alloc_capital = st.number_input("Target Investment Allocation Deployment Capital ($)", min_value=1000.0, value=st.session_state.invest_capital, step=5000.0)
            alloc_risk = st.selectbox("Strategic Risk Tolerance Setting", ["Conservative", "Moderate", "Growth", "Aggressive"], index=1)
            
            alloc_res = requests.post(f"{API_BASE_URL}/allocation", json={"amount": alloc_capital, "profile": alloc_risk}).json()
            st.success(f"Dynamic Structural Weights Extracted for: **{alloc_res['risk_profile']} Portfolio Paradigm**")
            
        with col_alloc_graph:
            labels = list(alloc_res["allocations"].keys())
            values = [details["amount"] for details in alloc_res["allocations"].values()]
            
            fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=["#10B981","#3B82F6","#F59E0B","#EF4444"]))])
            fig_pie.update_layout(template="plotly_dark" if theme["dark"] else "plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=20, r=20), height=240)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        st.write("### Specific Tactical Sub-Deployment Targets Blueprint")
        for asset_name, details in alloc_res["allocations"].items():
            c1, c2, c3 = st.columns([1, 1, 3])
            with c1: st.markdown(f"**{asset_name} ({details['percentage']:.0f}%)**")
            with c2: st.markdown(f"<span style='color:{theme['accent']}; font-weight:700;'>{fmt(details['amount'])}</span>", unsafe_allow_html=True)
            with c3: st.caption(details["strategy_note"])

    with tab_projections:
        st.subheader("Vectorized Asset Baseline Path Estimator Engine")
        col_p1, col_p2 = st.columns([1, 2])
        
        with col_p1:
            sim_years = st.slider("Target Planning Phase Investment Duration Runway (Years)", 5, 40, 25)
            expected_mu = st.slider("Target Portfolio Mean Compound Return Scale (Nominal Annual)", 0.02, 0.18, 0.075, step=0.005)
            expected_sigma = st.slider("Target Volatility Standard Deviation Envelope Setting", 0.05, 0.30, 0.14, step=0.01)
            
            projection_payload = {
                "initial_capital": total_assets,
                "monthly_contribution": max(0.0, monthly_cash_surplus),
                "years": sim_years,
                "expected_return": expected_mu,
                "volatility": expected_sigma
            }
            traj_data = requests.post(f"{API_BASE_URL}/projections", json=projection_payload).json()
            traj_df = pd.DataFrame(traj_data)
            
        with col_p2:
            fig_mc = go.Figure()
            fig_mc.add_trace(go.Scatter(x=traj_df["year"], y=traj_df["p90"], name="Optimistic Threshold (P90)", line=dict(color=theme["accent"], width=1.5, dash="dash")))
            fig_mc.add_trace(go.Scatter(x=traj_df["year"], y=traj_df["p50"], name="Median Vector Path (P50)", line=dict(color="#3B82F6", width=2.5)))
            fig_mc.add_trace(go.Scatter(x=traj_df["year"], y=traj_df["p10"], name="Risk Drawdown Pathway (P10)", line=dict(color="#EF4444", width=1.5, dash="dot")))
            
            fig_mc.update_layout(template="plotly_dark" if theme["dark"] else "plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=20, r=20), height=350, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_mc, use_container_width=True)

    # Data Log Export Engine Tool
    st.write("---")
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["Seralung Unified Data Extraction Export Log"])
    w.writerow(["Execution Timestamp", datetime.now().isoformat()])
    w.writerow(["Algorithmic Operational Health Score", health_data["score"]])
    w.writerow(["Net Worth Base Value Evaluation", net_worth])
    csv_data = buf.getvalue().encode("utf-8")

    st.download_button(label="📥 Export Engine Telemetry Logs to CSV", data=csv_data, file_name=f"seralung_telemetry_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

except requests.exceptions.ConnectionError:
    st.error("⚠️ Unable to connect to the FastAPI backend core. Please verify your Uvicorn server is running at http://127.0.0.1:8000")
