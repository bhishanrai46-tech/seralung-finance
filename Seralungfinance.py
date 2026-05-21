import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import io
import csv
import math
from datetime import datetime

# =====================================================================
# 1. PAGE & THEME CONFIGURATION
# =====================================================================
st.set_page_config(page_title="Seralung Unified Finance", layout="wide", initial_sidebar_state="collapsed")

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

# Inject styling variables
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
""", unsafe_with_html=True)

# =====================================================================
# 2. EMBEDDED CORE FINANCIAL ALGORITHMS (NATIVE PYTHON)
# =====================================================================

def calculate_au_tax(income: float) -> dict:
    """Computes progressive Australian income tax and Medicare levy thresholds."""
    brackets = [
        (190000, 0.45, 51638),
        (135000, 0.37, 31288),
        (45000,  0.30, 4288),
        (18200,  0.16, 0)
    ]
    base_tax = 0.0
    for threshold, rate, cumulative in brackets:
        if income > threshold:
            base_tax = cumulative + (income - threshold) * rate
            break
            
    medicare_levy = income * 0.02 if income > 26000 else 0.0
    total_liability = base_tax + medicare_levy
    net_pay = income - total_liability
    effective_rate = (total_liability / income * 100) if income > 0 else 0.0
    
    return {
        "taxable_income": income,
        "income_tax": round(base_tax, 2),
        "medicare_levy": round(medicare_levy, 2),
        "total_tax_liability": round(total_liability, 2),
        "net_take_home": round(net_pay, 2),
        "effective_tax_rate": round(effective_rate, 2)
    }

def generate_asset_allocation(amount: float, profile: str) -> dict:
    """Calculates specific asset weights based on the risk tier matrix."""
    matrix = {
        "Conservative": {
            "ETFs": (0.60, "Broad multi-asset defensive indexes, sovereign bonds, and fixed income hedges."),
            "Stocks": (0.25, "High-yielding blue-chip defensive equities with robust cash flows and franked dividends."),
            "Gold": (0.13, "Physical allocation acting as a macro inflation hedge and portfolio insurance."),
            "Crypto": (0.02, "Minimal blueprint isolated into core blue chips (BTC/ETH) to eliminate tail ruin.")
        },
        "Moderate": {
            "ETFs": (0.50, "Core baseline globally diversified broad market equity indexes (e.g., VGS, IVV)."),
            "Stocks": (0.35, "Blended mixture of industrial growth leaders and defensive value components."),
            "Gold": (0.10, "Systemic protection buffer to minimize total portfolio drawdown correlation."),
            "Crypto": (0.05, "Asymmetric alpha position focused on established digital stores of value.")
        },
        "Growth": {
            "Stocks": (0.45, "Long-term growth assets via technology, healthcare, and resource innovators."),
            "ETFs": (0.40, "High-beta specialized sectors, megatrend vehicles, and international index allocations."),
            "Crypto": (0.10, "Aggressive digital asset exposure aimed at outperforming nominal benchmarks."),
            "Gold": (0.05, "Reduced core insurance floor holding minimal liquid baseline protection.")
        },
        "Aggressive": {
            "Stocks": (0.50, "Direct deployment into high-conviction mid/small-cap tech disruptions and alpha engines."),
            "ETFs": (0.25, "Geared index tracking structures or highly specialized volatile sector funds."),
            "Crypto": (0.20, "Venture-tier allocation capturing generational infrastructure shifts across web3."),
            "Gold": (0.05, "Minimal residual safety cash buffer preserved for drawdown liquidity options.")
        }
    }
    
    allocations_out = {}
    profile_rules = matrix[profile]
    for asset, (weight, note) in profile_rules.items():
        allocations_out[asset] = {
            "percentage": weight * 100,
            "amount": round(amount * weight, 2),
            "strategy_note": note
        }
    return {"total_invested": amount, "risk_profile": profile, "allocations": allocations_out}

def run_monte_carlo(initial_capital, monthly_contribution, years, expected_return, volatility, simulations=500) -> pd.DataFrame:
    """Simulates monthly asset tracking intervals using a vectorized log-normal distribution model."""
    months = years * 12
    mu_mo = expected_return / 12
    sigma_mo = volatility / math.sqrt(12)
    
    res = np.zeros((simulations, months + 1))
    res[:, 0] = initial_capital
    
    for t in range(1, months + 1):
        shocks = np.random.normal(mu_mo, sigma_mo, simulations)
        res[:, t] = res[:, t-1] * (1 + shocks) + monthly_contribution
        
    trajectory_list = []
    for y in range(years + 1):
        m_idx = y * 12
        slice_data = res[:, m_idx]
        trajectory_list.append({
            "year": y,
            "p10": round(float(np.percentile(slice_data, 10)), 2),
            "p50": round(float(np.percentile(slice_data, 50)), 2),
            "p90": round(float(np.percentile(slice_data, 90)), 2)
        })
    return pd.DataFrame(trajectory_list)

def calculate_health_telemetry(savings_rate, debt_to_income, runway_months, net_worth_positive, budget_overrun, has_goals) -> dict:
    """Aggregates subcomponent rules into an operational financial strength telemetry matrix."""
    s1 = min(25.0, (savings_rate / 20.0) * 25.0) if savings_rate > 0 else 0
    s2 = min(20.0, (runway_months / 6.0) * 20.0)
    s3 = max(0.0, 20.0 - (debt_to_income * 0.5))
    s4 = 15.0 if net_worth_positive else 0.0
    s5 = max(0.0, 10.0 - (budget_overrun / 100.0))
    s6 = 10.0 if has_goals else 0.0
    
    total_score = int(round(s1 + s2 + s3 + s4 + s5 + s6))
    tier = "Elite" if total_score >= 80 else "Good" if total_score >= 65 else "Fair" if total_score >= 50 else "Critical"
    
    breakdown = {
        "Savings Rate": {"score": round(s1, 1), "max": 25, "ok": savings_rate >= 20, "desc": f"{savings_rate:.1f}% (Target: >20%)"},
        "Emergency Fund": {"score": round(s2, 1), "max": 20, "ok": runway_months >= 6, "desc": f"{runway_months:.1f} months (Target: 6)"},
        "Debt Control": {"score": round(s3, 1), "max": 20, "ok": debt_to_income <= 36, "desc": f"{debt_to_income:.1f}% Debt Ratio (Target: <36%)"},
        "Net Worth": {"score": round(s4, 1), "max": 15, "ok": net_worth_positive, "desc": "Positive" if net_worth_positive else "Negative Structure"},
        "Budget Control": {"score": round(s5, 1), "max": 10, "ok": budget_overrun == 0, "desc": f"${budget_overrun:,.0f} overspent bounds"},
        "Goal Progress": {"score": round(s6, 1), "max": 10, "ok": has_goals, "desc": "Active structural targets set"}
    }
    return {"score": total_score, "tier": tier, "breakdown": breakdown}

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
# 3. INTERFACE COMPILATION & VISUAL COMPUTATION
# =====================================================================

# App Layout Header Banner
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("Seralung Unified Financial Architecture")
    st.caption("Consolidated Single-File Execution Pipeline (Embedded Matrix Logic Engine)")
with col_t2:
    st.session_state.active_theme = st.selectbox("Interface Visual Theme Profile", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.active_theme))

st.write("---")

# Process Calculations Natively (No HTTP Networking Latency)
total_gross_monthly = st.session_state.primary_income + st.session_state.other_income
annualized_gross = total_gross_monthly * 12

tax_res = calculate_au_tax(annualized_gross)
monthly_tax = tax_res["total_tax_liability"] / 12
net_monthly_income = total_gross_monthly - monthly_tax

total_monthly_expenses = sum(e["amount"] for e in st.session_state.expenses)
monthly_cash_surplus = net_monthly_income - total_monthly_expenses
calculated_savings_rate = (monthly_cash_surplus / net_monthly_income * 100) if net_monthly_income > 0 else 0

total_assets = sum(a["value"] for a in st.session_state.assets)
total_liabilities = sum(l["balance"] for l in st.session_state.liabilities)
net_worth = total_assets - total_liabilities

cash_reserves = sum(a["value"] for a in st.session_state.assets if a["type"] in ["Cash", "Savings"])
runway_months = (cash_reserves / total_monthly_expenses) if total_monthly_expenses > 0 else 0
debt_to_income_ratio = (total_liabilities / annualized_gross * 100) if annualized_gross > 0 else 0
overspend = sum(max(0, e["amount"] - e["budget"]) for e in st.session_state.expenses)

health_data = calculate_health_telemetry(
    calculated_savings_rate, debt_to_income_ratio, runway_months, net_worth > 0, overspend, len(st.session_state.goals) > 0
)

# Render Score Metrics Dashboard Header Row
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

# Workspace Component Navigation Tabs
tab_telemetry, tab_allocation, tab_projections = st.tabs([
    "📊 Core Telemetry & Operations", 
    "📈 Refined Asset Allocations", 
    "🔮 Vectorized Trajectory Forecasting"
])

with tab_telemetry:
    col_g1, col_g2 = st.columns([1, 2])
    with col_g1:
        st.markdown("<h4 style='text-align: center;'>Algorithmic Strength Telemetry</h4>", unsafe_with_html=True)
        st.markdown(render_svg_gauge(health_data["score"], health_data["tier"]), unsafe_with_html=True)
        st.write("##")
        st.metric(label="Calculated ATO Income Tax Drag (Annual)", value=fmt(tax_res["total_tax_liability"]), delta=f"Effective Drag: {tax_res['effective_tax_rate']}%")
        
    with col_g2:
        st.markdown("<h4>Telemetry Matrix Subcomponent Ratings Breakdown</h4>", unsafe_with_html=True)
        breakdown_df = pd.DataFrame.from_dict(health_data["breakdown"], orient="index")
        st.dataframe(breakdown_df[["score", "max", "desc", "ok"]], use_container_width=True)

with tab_allocation:
    st.subheader("Algorithmic Asset Allocation Pipeline Model")
    col_alloc_in, col_alloc_graph = st.columns([1, 2])
    
    with col_alloc_in:
        alloc_capital = st.number_input("Target Investment Allocation Deployment Capital ($)", min_value=1000.0, value=st.session_state.invest_capital, step=5000.0)
        alloc_risk = st.selectbox("Strategic Risk Tolerance Setting", ["Conservative", "Moderate", "Growth", "Aggressive"], index=1)
        
        alloc_res = generate_asset_allocation(alloc_capital, alloc_risk)
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
        with c2: st.markdown(f"<span style='color:{theme['accent']}; font-weight:700;'>{fmt(details['amount'])}</span>", unsafe_with_html=True)
        with c3: st.caption(details["strategy_note"])

with tab_projections:
    st.subheader("Vectorized Asset Baseline Path Estimator Engine")
    col_p1, col_p2 = st.columns([1, 2])
    
    with col_p1:
        sim_years = st.slider("Target Planning Phase Investment Duration Runway (Years)", 5, 40, 25)
        expected_mu = st.slider("Target Portfolio Mean Compound Return Scale (Nominal Annual)", 0.02, 0.18, 0.075, step=0.005)
        expected_sigma = st.slider("Target Volatility Standard Deviation Envelope Setting", 0.05, 0.30, 0.14, step=0.01)
        
        traj_df = run_monte_carlo(
            initial_capital=total_assets,
            monthly_contribution=max(0.0, monthly_cash_surplus),
            years=sim_years,
            expected_return=expected_mu,
            volatility=expected_sigma
        )
        
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
