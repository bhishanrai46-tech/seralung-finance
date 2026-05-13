"""
FINORA — AI Financial Planner Web App
Run: streamlit run finora_app.py
Share: Deploy to https://streamlit.io/cloud (free)
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime
import math

# ── PAGE CONFIG ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finora — Financial Planner",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS — Premium dark theme ─────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0f0f1a;
    border-right: 1px solid #1e1e2e;
}

/* Cards */
.fin-card {
    background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
    border: 1px solid #2a2a42;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
}
.fin-card:hover { border-color: #4f46e5; }

.metric-card {
    background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
    border: 1px solid #2a2a42;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}
.metric-label {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6b6b8a;
    margin-bottom: 8px;
    font-weight: 500;
}
.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    color: #e8e8f0;
    line-height: 1;
}
.metric-value.positive { color: #34d399; }
.metric-value.negative { color: #f87171; }
.metric-value.accent   { color: #818cf8; }

/* Section headers */
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: #e8e8f0;
    margin: 8px 0 20px;
    border-left: 3px solid #4f46e5;
    padding-left: 12px;
}

/* Insight cards */
.insight-card {
    background: #0f1629;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #4f46e5;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 14px;
    line-height: 1.6;
    color: #c8c8e0;
}
.insight-card.warning { border-left-color: #f59e0b; border-color: #3d2e0f; background: #130f05; }
.insight-card.danger  { border-left-color: #f87171; border-color: #3d1515; background: #130505; }
.insight-card.success { border-left-color: #34d399; border-color: #0f3d2e; background: #051309; }

/* Progress bar */
.prog-wrap { background: #1e1e2e; border-radius: 99px; height: 8px; margin: 6px 0; }
.prog-fill  { height: 8px; border-radius: 99px; background: linear-gradient(90deg,#4f46e5,#818cf8); }
.prog-fill.green { background: linear-gradient(90deg,#059669,#34d399); }
.prog-fill.yellow { background: linear-gradient(90deg,#d97706,#fbbf24); }
.prog-fill.red    { background: linear-gradient(90deg,#dc2626,#f87171); }

/* Score ring */
.score-display {
    text-align: center;
    padding: 20px;
}
.score-number {
    font-family: 'DM Serif Display', serif;
    font-size: 64px;
    line-height: 1;
    background: linear-gradient(135deg, #818cf8, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.score-label { font-size: 13px; color: #6b6b8a; margin-top: 4px; }

/* Logo */
.logo-wrap {
    padding: 20px 0 28px;
    text-align: center;
}
.logo-name {
    font-family: 'DM Serif Display', serif;
    font-size: 26px;
    letter-spacing: 0.02em;
    background: linear-gradient(135deg, #818cf8, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.logo-tag { font-size: 11px; color: #4b4b6a; letter-spacing: 0.1em; margin-top: 2px; }

/* Streamlit overrides */
div[data-testid="metric-container"] {
    background: #13131f;
    border: 1px solid #2a2a42;
    border-radius: 12px;
    padding: 16px;
}
.stSlider > div > div > div { background: #4f46e5 !important; }
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }
.stTabs [data-baseweb="tab"] { color: #6b6b8a; font-size: 14px; }
.stTabs [aria-selected="true"] { color: #818cf8 !important; border-bottom-color: #4f46e5 !important; }
</style>
""", unsafe_allow_html=True)

# ── PLOTLY THEME ─────────────────────────────────────────────────────
PLOT_BG    = "#0a0a0f"
PAPER_BG   = "#13131f"
GRID_COLOR = "#1e1e2e"
TEXT_COLOR = "#9090b0"
ACCENT     = "#818cf8"
GREEN      = "#34d399"
RED        = "#f87171"
YELLOW     = "#fbbf24"

def dark_layout(fig, title="", height=320):
    fig.update_layout(
        title=dict(text=title, font=dict(color="#e8e8f0", size=14, family="DM Serif Display")),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=dict(color=TEXT_COLOR, family="DM Sans"),
        height=height,
        margin=dict(l=20, r=20, t=40 if title else 20, b=20),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12)),
    )
    return fig

# ══════════════════════════════════════════════════════════════════════
# CALCULATION ENGINE  (self-contained, no imports)
# ══════════════════════════════════════════════════════════════════════

ATO_BRACKETS = [
    (18_200, 0.0,   0),
    (45_000, 0.19,  0),
    (120_000,0.325, 5_092),
    (180_000,0.37,  29_467),
    (1e9,    0.45,  51_667),
]
MEDICARE = 0.02
SUPER_SG = 0.115
SWR      = 0.04

def calc_tax(gross):
    tax = 0.0
    prev = 0
    for threshold, rate, base in ATO_BRACKETS:
        if gross <= threshold:
            tax = base + (gross - prev) * rate
            break
        prev = threshold
    lito = 0.0
    if gross <= 37_500:    lito = 700
    elif gross <= 45_000:  lito = 700 - (gross - 37_500) * 0.05
    elif gross <= 66_667:  lito = 325 - (gross - 45_000) * 0.015
    medicare = gross * MEDICARE
    net_tax = max(0, tax - lito) + medicare
    return {
        "income_tax": round(tax, 2),
        "lito": round(lito, 2),
        "medicare": round(medicare, 2),
        "total_tax": round(net_tax, 2),
        "net_annual": round(gross - net_tax, 2),
        "net_monthly": round((gross - net_tax) / 12, 2),
        "eff_rate": round(net_tax / gross * 100, 2) if gross else 0,
    }

def budget_analyse(net_income, expenses: dict, extra_debt=0, extra_invest=0):
    NEEDS  = {"rent","mortgage","groceries","utilities","insurance",
               "transport","phone","internet","childcare","medical"}
    WANTS  = {"dining","entertainment","clothing","subscriptions","gym","travel","hobbies"}
    SAVES  = {"savings","investments","super","emergency"}
    n = w = s = u = 0.0
    for k, v in expenses.items():
        key = k.lower().replace(" ","_")
        if key in NEEDS:  n += v
        elif key in WANTS: w += v
        elif key in SAVES: s += v
        else: u += v
    s += extra_debt + extra_invest
    total = n + w + s + u
    return {
        "needs": n, "wants": w, "savings": s, "uncategorized": u,
        "total": total,
        "surplus": net_income - total,
        "savings_rate": s / net_income * 100 if net_income else 0,
        "targets": {"needs": net_income*.5, "wants": net_income*.3, "savings": net_income*.2},
    }

def invest_project(current, annual_contrib, rate, years):
    rows = []
    bal = current
    for yr in range(1, years+1):
        bal = bal * (1 + rate) + annual_contrib
        rows.append({"year": yr, "balance": round(bal,2),
                      "contributed": round(annual_contrib*yr,2),
                      "growth": round(bal - current - annual_contrib*yr, 2)})
    return rows

def risk_score(age, income, total_debt, timeline, experience, tolerance, has_ef, deps):
    s = 0
    if age < 25:   s += 20
    elif age < 35: s += 17
    elif age < 45: s += 13
    elif age < 55: s += 9
    elif age < 65: s += 5
    else:          s += 2
    dti = total_debt / income if income else 1
    if dti < 0.15:   s += 15
    elif dti < 0.30: s += 10
    elif dti < 0.50: s += 5
    if timeline >= 20: s += 20
    elif timeline >= 10: s += 15
    elif timeline >= 5: s += 10
    elif timeline >= 2: s += 5
    s += (experience - 1) * 4
    s += (tolerance - 1) * 5
    s += 5 if has_ef else 0
    s -= deps * 3
    return max(0, min(100, s))

def debt_payoff(debts, extra=0):
    def sim(sorted_d):
        ds = [dict(d) for d in sorted_d]
        interest = 0.0
        months = 0
        while any(d["balance"] > 0 for d in ds):
            months += 1
            if months > 600: break
            for d in ds:
                if d["balance"] <= 0: continue
                i = d["balance"] * d["rate"] / 12
                interest += i
                d["balance"] += i - d["min"]
                if d["balance"] < 0: d["balance"] = 0
            rem = extra
            for d in ds:
                if d["balance"] > 0 and rem > 0:
                    pay = min(rem, d["balance"])
                    d["balance"] -= pay; rem -= pay; break
        return months, round(interest, 2)
    av_sorted = sorted(debts, key=lambda x: -x["rate"])
    sn_sorted = sorted(debts, key=lambda x:  x["balance"])
    av_m, av_i = sim(av_sorted)
    sn_m, sn_i = sim(sn_sorted)
    return {"avalanche": {"months": av_m, "interest": av_i},
            "snowball":  {"months": sn_m, "interest": sn_i}}

def goal_calc(target, saved, monthly_contrib, target_date, return_rate=0.05):
    today = date.today()
    months_left = max(1, (target_date.year - today.year)*12 + (target_date.month - today.month))
    shortfall = max(0, target - saved)
    r = return_rate / 12
    if r > 0:
        req_monthly = shortfall * r / ((1+r)**months_left - 1)
    else:
        req_monthly = shortfall / months_left
    # simulate to find actual completion
    bal = saved
    months_to_goal = None
    for m in range(1, 601):
        bal = bal * (1+r) + monthly_contrib
        if bal >= target:
            months_to_goal = m; break
    proj = None
    if months_to_goal:
        yr = today.year + months_to_goal // 12
        mo = today.month + months_to_goal % 12
        if mo > 12: yr += 1; mo -= 12
        proj = date(yr, mo, 1)
    return {
        "shortfall": shortfall,
        "months_left": months_left,
        "req_monthly": round(req_monthly, 2),
        "gap": round(monthly_contrib - req_monthly, 2),
        "on_track": proj is not None and proj <= target_date,
        "projected": proj,
        "pct": min(100, saved / target * 100) if target else 0,
    }

def health_score(monthly_exp, ef, net_income, monthly_savings,
                  total_debt, annual_income, total_invest,
                  surplus, net_worth, prev_nw=0):
    s = {}
    ef_mo = ef / monthly_exp if monthly_exp else 0
    s["Emergency Fund"] = 20 if ef_mo>=6 else (15 if ef_mo>=3 else (8 if ef_mo>=1 else 0))
    sr = monthly_savings / net_income * 100 if net_income else 0
    s["Savings Rate"] = 20 if sr>=30 else (17 if sr>=20 else (10 if sr>=10 else (5 if sr>=5 else 0)))
    dti = total_debt / annual_income if annual_income else 1
    s["Debt Load"] = 20 if dti<0.15 else (15 if dti<0.30 else (8 if dti<0.50 else (3 if dti<1 else 0)))
    ir = total_invest / (annual_income*5)*100 if annual_income else 0
    s["Investments"] = 20 if ir>=50 else (15 if ir>=25 else (8 if ir>=10 else (3 if ir>0 else 0)))
    sp = surplus / net_income*100 if net_income else 0
    s["Budget Control"] = 10 if sp>=10 else (7 if sp>=0 else 0)
    ngr = (net_worth - prev_nw) / prev_nw * 100 if prev_nw else (5 if net_worth > 0 else 0)
    s["Net Worth Growth"] = 10 if ngr>=10 else (7 if ngr>=5 else (4 if ngr>=0 else 0))
    total = sum(s.values())
    grade = ("A+ Excellent" if total>=85 else "A  Very Good" if total>=70 else
             "B  Good" if total>=55 else "C  Fair" if total>=40 else
             "D  Needs Work" if total>=25 else "F  Critical")
    return {"scores": s, "total": total, "grade": grade, "maxes": {
        "Emergency Fund":20,"Savings Rate":20,"Debt Load":20,
        "Investments":20,"Budget Control":10,"Net Worth Growth":10}}

def super_projection(current, age, ret_age, salary, vol_contrib=0, ret=0.07):
    yrs = ret_age - age
    sg  = salary * SUPER_SG
    total_c = sg + vol_contrib
    bal = current
    for _ in range(yrs):
        bal = bal * (1+ret) + total_c * 0.85
    return {"balance": round(bal,2),
            "monthly_4pct": round(bal*SWR/12,2),
            "years": yrs, "annual_sg": round(sg,2)}

def fi_calc(nw, annual_savings, annual_expenses, ret=0.07):
    target = annual_expenses / SWR
    bal = nw
    for yr in range(1, 101):
        bal = bal*(1+ret) + annual_savings
        if bal >= target:
            return {"fi_number": round(target,2), "years": yr, "pct": round(nw/target*100,2)}
    return {"fi_number": round(target,2), "years": ">100", "pct": round(nw/target*100,2)}

# Business models
def biz_freelance(rate, hrs_week, util, overhead_monthly, tax_rate, weeks=46):
    gross = rate * hrs_week * weeks * util
    net_bt = gross - overhead_monthly*12
    tax    = max(0, net_bt * tax_rate)
    net_at = net_bt - tax
    billed = hrs_week * weeks * util
    return {"gross": round(gross,2), "net": round(net_at,2),
            "monthly": round(net_at/12,2),
            "eff_hourly": round(net_at/billed,2) if billed else 0,
            "billed_hrs": round(billed)}

def biz_saas(price, customers_y, churn=0.05, cogs_pct=0.20, fixed=36000, cac=200):
    results = []
    for yr, cust in enumerate(customers_y, 1):
        avg = cust * (1 - churn*6)
        arr = avg * price * 12
        cogs = arr * cogs_pct
        acq = cust * cac
        gp  = arr - cogs
        np  = gp - fixed - acq
        results.append({"year":yr,"customers":int(avg),"mrr":round(arr/12,2),
                         "arr":round(arr,2),"gross_profit":round(gp,2),"net_profit":round(np,2)})
    return results

def biz_ecom(aov, orders_y, cogs=0.40, returns=0.08, ads_monthly=1000, platform=0.03, fulfilment=8):
    results = []
    for yr, mo_ord in enumerate(orders_y, 1):
        ann = mo_ord * 12
        gross = ann * aov
        ret_  = gross * returns
        net_r = gross - ret_
        cogs_ = net_r * cogs
        plt_  = net_r * platform
        ful_  = ann * fulfilment
        ads_  = ads_monthly * 12
        gp    = net_r - cogs_
        np    = gp - plt_ - ful_ - ads_
        margin= np/gross*100 if gross else 0
        results.append({"year":yr,"monthly_orders":mo_ord,"gross_revenue":round(gross,2),
                         "gross_profit":round(gp,2),"net_profit":round(np,2),"margin":round(margin,1)})
    return results

def biz_agency(retainer, clients_y, overhead_monthly=1800, staff_monthly=0, churn=0.28):
    results = []
    for yr, cl in enumerate(clients_y, 1):
        avg = cl * (1 - churn/2)
        rev = avg * retainer * 12
        np  = rev - (overhead_monthly+staff_monthly)*12
        results.append({"year":yr,"clients":round(avg,1),"revenue":round(rev,2),
                         "net_profit":round(np,2),"margin":round(np/rev*100 if rev else 0,1)})
    return results

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR — USER INPUTS
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="logo-wrap">
      <div class="logo-name">◆ Finora</div>
      <div class="logo-tag">FINANCIAL INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👤 Your Profile")
    name = st.text_input("Name", "Alex Chen")
    age  = st.slider("Age", 18, 70, 32)

    st.markdown("### 💰 Income")
    gross_income   = st.number_input("Annual Gross Salary ($)", 30000, 500000, 95000, 1000)
    other_income   = st.number_input("Other Monthly Income ($)", 0, 20000, 800, 100,
                                      help="Side hustle, rental, dividends")

    st.markdown("### 🏠 Monthly Expenses")
    rent           = st.number_input("Rent / Mortgage ($)",   0, 10000, 2100, 50)
    groceries      = st.number_input("Groceries ($)",          0,  5000,  550, 25)
    transport      = st.number_input("Transport ($)",          0,  3000,  280, 25)
    utilities      = st.number_input("Utilities ($)",          0,  2000,  160, 10)
    phone_internet = st.number_input("Phone + Internet ($)",   0,   500,  135, 5)
    insurance      = st.number_input("Insurance ($)",          0,  2000,  200, 10)
    dining         = st.number_input("Dining Out ($)",         0,  3000,  380, 25)
    entertainment  = st.number_input("Entertainment ($)",      0,  2000,  120, 10)
    clothing       = st.number_input("Clothing ($)",           0,  2000,  150, 10)
    subscriptions  = st.number_input("Subscriptions ($)",      0,  1000,   95,  5)
    gym            = st.number_input("Gym / Fitness ($)",      0,   500,   60,  5)
    savings_contr  = st.number_input("Manual Savings ($)",     0,  5000,  500, 50)

    st.markdown("### 💳 Debts")
    car_balance    = st.number_input("Car Loan Balance ($)",      0, 100000, 14200, 500)
    car_rate       = st.slider("Car Loan Rate (%)",  1.0, 20.0, 6.9, 0.1) / 100
    car_min        = st.number_input("Car Min Payment ($)",       0, 2000, 380, 10)
    cc_balance     = st.number_input("Credit Card Balance ($)",   0,  50000, 3400, 100)
    cc_rate        = st.slider("Credit Card Rate (%)", 5.0, 30.0, 19.9, 0.1) / 100
    cc_min         = st.number_input("CC Min Payment ($)",        0, 2000, 150, 10)
    extra_debt_pay = st.number_input("Extra Debt Payment ($/mo)", 0, 2000, 200, 50)

    st.markdown("### 📈 Investments")
    invest_etf     = st.number_input("ETF Portfolio Value ($)",   0, 1000000, 27700, 500)
    invest_stocks  = st.number_input("Stocks Value ($)",          0, 1000000,  3800, 500)
    invest_crypto  = st.number_input("Crypto Value ($)",          0,  500000,  4100, 100)
    invest_contrib = st.number_input("Monthly Invest Contribution ($)", 0, 10000, 600, 50)
    super_balance  = st.number_input("Super Balance ($)",         0, 2000000, 42000, 500)
    super_vol      = st.number_input("Voluntary Super Contr ($/yr)", 0, 27500, 5000, 500)
    ef_balance     = st.number_input("Emergency Fund ($)",         0,  200000, 8500, 500)
    savings_acc    = st.number_input("Savings Account ($)",        0,  200000, 12000, 500)

    st.markdown("### 🎯 Goals")
    g1_name   = st.text_input("Goal 1 Name", "House Deposit")
    g1_target = st.number_input("Goal 1 Target ($)", 1000, 2000000, 120000, 1000)
    g1_saved  = st.number_input("Goal 1 Saved ($)", 0, 2000000, 12000, 500)
    g1_monthly= st.number_input("Goal 1 Monthly ($)", 0, 10000, 1200, 100)
    g1_date   = st.date_input("Goal 1 Date", date(2028, 6, 30))

    g2_name   = st.text_input("Goal 2 Name", "Europe Trip")
    g2_target = st.number_input("Goal 2 Target ($)", 500, 200000, 8000, 500)
    g2_saved  = st.number_input("Goal 2 Saved ($)", 0, 200000, 1500, 100)
    g2_monthly= st.number_input("Goal 2 Monthly ($)", 0, 5000, 400, 50)
    g2_date   = st.date_input("Goal 2 Date", date(2025, 12, 31))

    st.markdown("### ⚙️ Settings")
    ret_age   = st.slider("Retirement Age", 50, 70, 67)
    inv_return= st.slider("Expected Investment Return (%)", 3.0, 12.0, 7.0, 0.5) / 100
    dependents= st.slider("Dependents", 0, 6, 0)
    risk_exp  = st.slider("Investment Experience (1–5)", 1, 5, 3)
    risk_tol  = st.slider("Risk Tolerance (1–5)", 1, 5, 3)

# ══════════════════════════════════════════════════════════════════════
# COMPUTE ALL VALUES
# ══════════════════════════════════════════════════════════════════════

# Tax
tax = calc_tax(gross_income)
net_monthly = tax["net_monthly"] + other_income

# Expenses dict
expenses = {
    "rent": rent, "groceries": groceries, "transport": transport,
    "utilities": utilities, "phone": phone_internet, "insurance": insurance,
    "dining": dining, "entertainment": entertainment, "clothing": clothing,
    "subscriptions": subscriptions, "gym": gym, "savings": savings_contr,
}
total_expenses = sum(expenses.values())
debt_payments  = car_min + cc_min
invest_annual  = invest_contrib * 12

# Budget
budget = budget_analyse(net_monthly, expenses, debt_payments, invest_contrib)

# Net worth
total_investments = invest_etf + invest_stocks + invest_crypto
total_assets      = ef_balance + savings_acc + total_investments + super_balance
total_debt        = car_balance + cc_balance
net_worth         = total_assets - total_debt

# Investment projection
total_invest_now  = total_investments
proj_rows         = invest_project(total_invest_now, invest_annual, inv_return, 20)

# Risk
r_score = risk_score(age, gross_income, total_debt, age-18+2,  # rough timeline
                      risk_exp, risk_tol, ef_balance > 0, dependents)

# Goals
g1 = goal_calc(g1_target, g1_saved, g1_monthly, g1_date, inv_return)
g2 = goal_calc(g2_target, g2_saved, g2_monthly, g2_date, inv_return)

# Debt payoff
debts_list = [
    {"balance": car_balance, "rate": car_rate, "min": car_min, "name": "Car Loan"},
    {"balance": cc_balance,  "rate": cc_rate,  "min": cc_min,  "name": "Credit Card"},
]
payoff = debt_payoff(debts_list, extra_debt_pay)

# Super
super_proj = super_projection(super_balance, age, ret_age, gross_income, super_vol, inv_return)

# FI
fi = fi_calc(net_worth, invest_annual + savings_contr*12, total_expenses*12, inv_return)

# Health score
hs = health_score(
    total_expenses, ef_balance, net_monthly, budget["savings"],
    total_debt, gross_income, total_investments,
    budget["surplus"], net_worth, net_worth * 0.88
)

# ══════════════════════════════════════════════════════════════════════
# MAIN CONTENT — TABS
# ══════════════════════════════════════════════════════════════════════

st.markdown(f"""
<h1 style="font-family:'DM Serif Display',serif; font-size:32px;
    background:linear-gradient(135deg,#818cf8,#34d399);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:4px;">
  ◆ Finora
</h1>
<p style="color:#4b4b6a; font-size:13px; margin-bottom:24px; letter-spacing:0.08em;">
  FINANCIAL INTELLIGENCE ENGINE &nbsp;·&nbsp; {name.upper()}
</p>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "📊 Dashboard", "💸 Budget", "📈 Investments",
    "🎯 Goals", "💳 Debt", "🏢 Business", "🔮 Retirement"
])

# ─────────────────────────────────────────
# TAB 1 — DASHBOARD
# ─────────────────────────────────────────
with tabs[0]:

    # Top KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    def kpi(col, label, value, cls=""):
        col.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value {cls}">{value}</div>
        </div>""", unsafe_allow_html=True)

    kpi(c1, "Net Worth",       f"${net_worth:,.0f}",    "positive" if net_worth > 0 else "negative")
    kpi(c2, "Monthly Take-Home", f"${net_monthly:,.0f}", "accent")
    kpi(c3, "Savings Rate",    f"{budget['savings_rate']:.1f}%", "positive" if budget['savings_rate'] >= 20 else "negative")
    kpi(c4, "Health Score",    f"{hs['total']}/100",    "positive" if hs['total'] >= 55 else "negative")
    kpi(c5, "FI Progress",     f"{fi['pct']:.1f}%",     "accent")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<p class="section-title">Net Worth Breakdown</p>', unsafe_allow_html=True)
        fig_nw = go.Figure()
        fig_nw.add_trace(go.Bar(
            x=["Cash & EF", "ETF/Stocks/Crypto", "Superannuation"],
            y=[ef_balance + savings_acc, total_investments, super_balance],
            marker_color=[ACCENT, GREEN, YELLOW],
            name="Assets", text=[f"${v:,.0f}" for v in [ef_balance+savings_acc, total_investments, super_balance]],
            textposition="outside", textfont=dict(color=TEXT_COLOR, size=11),
        ))
        fig_nw.add_trace(go.Bar(
            x=["Car Loan", "Credit Card"],
            y=[-car_balance, -cc_balance],
            marker_color=[RED, "#fb923c"],
            name="Debts", text=[f"-${v:,.0f}" for v in [car_balance, cc_balance]],
            textposition="outside", textfont=dict(color=TEXT_COLOR, size=11),
        ))
        dark_layout(fig_nw, height=280)
        fig_nw.update_layout(barmode="relative", xaxis_tickfont=dict(size=11))
        st.plotly_chart(fig_nw, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        st.markdown('<p class="section-title">Financial Health</p>', unsafe_allow_html=True)
        grade = hs["grade"].split()[0]
        color = "#34d399" if hs["total"] >= 70 else "#fbbf24" if hs["total"] >= 50 else "#f87171"
        st.markdown(f"""
        <div style="text-align:center; padding: 10px 0 20px;">
          <div style="font-family:'DM Serif Display',serif; font-size:56px;
               background:linear-gradient(135deg,{color},{ACCENT});
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            {hs['total']}
          </div>
          <div style="color:#6b6b8a; font-size:12px; letter-spacing:0.1em;">{hs['grade'].upper()}</div>
        </div>""", unsafe_allow_html=True)

        for dim, pts in hs["scores"].items():
            mx  = hs["maxes"][dim]
            pct = int(pts / mx * 100)
            cls = "green" if pct >= 75 else "yellow" if pct >= 40 else "red"
            st.markdown(f"""
            <div style="margin-bottom:8px;">
              <div style="display:flex; justify-content:space-between; font-size:12px; color:#9090b0; margin-bottom:3px;">
                <span>{dim}</span><span style="color:#e8e8f0;">{pts}/{mx}</span>
              </div>
              <div class="prog-wrap"><div class="prog-fill {cls}" style="width:{pct}%"></div></div>
            </div>""", unsafe_allow_html=True)

    # AI Insights
    st.markdown('<p class="section-title">AI Insights</p>', unsafe_allow_html=True)
    insights = []
    if "variances" in budget and budget["variances"]["wants"] > 0:
        pass
    wants_var = budget["wants"] - budget["targets"]["wants"]
    if wants_var > 0:
        insights.append(("warning", f"💡 Wants spending is ${wants_var:,.0f} over budget. Investing this monthly adds ~${wants_var*12*10:,.0f} to your portfolio over 10 years at {inv_return*100:.0f}% return."))
    if budget["savings_rate"] < 20:
        insights.append(("warning", f"⚠️ Savings rate is {budget['savings_rate']:.1f}% — below the 20% target. Each 1% improvement moves your FI date forward ~6 months."))
    if budget["surplus"] > 300:
        insights.append(("success", f"✅ ${budget['surplus']:,.0f}/month surplus detected. Auto-invest this into VGS or IVV for maximum compounding."))
    ef_months = ef_balance / total_expenses if total_expenses else 0
    if ef_months < 3:
        insights.append(("danger", f"🚨 Emergency fund covers only {ef_months:.1f} months. Build to 3–6 months (${total_expenses*3:,.0f}) before investing aggressively."))
    if cc_balance > 0 and cc_rate > 0.12:
        insights.append(("danger", f"💳 Credit card at {cc_rate*100:.1f}% interest. Paying this off = a guaranteed {cc_rate*100:.0f}% return — better than most investments."))
    if not insights:
        insights.append(("success", "✅ Finances are in solid shape. Keep building momentum!"))

    ins_cols = st.columns(min(len(insights), 2))
    for i, (typ, msg) in enumerate(insights):
        ins_cols[i % 2].markdown(f'<div class="insight-card {typ}">{msg}</div>', unsafe_allow_html=True)

    # Tax summary
    st.markdown('<p class="section-title">Tax Summary (ATO 2024–25)</p>', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns(4)
    kpi(t1, "Gross Income",    f"${gross_income:,.0f}")
    kpi(t2, "Total Tax",       f"${tax['total_tax']:,.0f}", "negative")
    kpi(t3, "Net Annual",      f"${tax['net_annual']:,.0f}", "positive")
    kpi(t4, "Effective Rate",  f"{tax['eff_rate']}%")

# ─────────────────────────────────────────
# TAB 2 — BUDGET
# ─────────────────────────────────────────
with tabs[1]:
    st.markdown('<p class="section-title">50/30/20 Budget Analysis</p>', unsafe_allow_html=True)

    bc1, bc2, bc3 = st.columns(3)
    for col, cat, actual, target in [
        (bc1, "Needs (50%)",    budget["needs"],   budget["targets"]["needs"]),
        (bc2, "Wants (30%)",    budget["wants"],   budget["targets"]["wants"]),
        (bc3, "Savings (20%)",  budget["savings"], budget["targets"]["savings"]),
    ]:
        var = actual - target
        cls = "positive" if var <= 0 else "negative"
        col.markdown(f"""
        <div class="fin-card">
          <div class="metric-label">{cat}</div>
          <div class="metric-value">${actual:,.0f}</div>
          <div style="font-size:12px; color:#6b6b8a; margin:6px 0;">Target ${target:,.0f}</div>
          <div style="font-size:13px; color:{'#34d399' if var<=0 else '#f87171'};">
            {'+' if var>=0 else ''}${var:,.0f} {'over' if var > 0 else 'under'}
          </div>
        </div>""", unsafe_allow_html=True)

    # Donut
    fig_budget = go.Figure(go.Pie(
        labels=["Needs", "Wants", "Savings", "Uncategorized"],
        values=[budget["needs"], budget["wants"], budget["savings"], budget["uncategorized"]],
        hole=0.55,
        marker_colors=[ACCENT, YELLOW, GREEN, "#6b6b8a"],
        textfont=dict(color="#e8e8f0", size=12),
    ))
    fig_budget.update_layout(
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        height=300, margin=dict(l=0,r=0,t=0,b=0),
        showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
        annotations=[dict(text=f"${net_monthly:,.0f}<br>net/mo",
                          font=dict(size=14, color="#e8e8f0"), showarrow=False)],
    )

    col_d, col_b = st.columns([1, 2])
    with col_d:
        st.plotly_chart(fig_budget, use_container_width=True, config={"displayModeBar": False})
    with col_b:
        st.markdown('<p class="section-title" style="font-size:16px">Expense Breakdown</p>', unsafe_allow_html=True)
        for cat, amt in sorted(expenses.items(), key=lambda x: -x[1]):
            pct = amt / total_expenses * 100 if total_expenses else 0
            cls = "green" if pct < 10 else "yellow" if pct < 20 else "red"
            st.markdown(f"""
            <div style="margin-bottom:7px;">
              <div style="display:flex;justify-content:space-between;font-size:12px;color:#9090b0;margin-bottom:2px;">
                <span style="text-transform:capitalize;">{cat}</span>
                <span style="color:#e8e8f0;">${amt:,.0f} &nbsp; <span style="color:#6b6b8a">{pct:.1f}%</span></span>
              </div>
              <div class="prog-wrap"><div class="prog-fill {cls}" style="width:{min(pct*3,100):.0f}%"></div></div>
            </div>""", unsafe_allow_html=True)

    sr_color = "#34d399" if budget["savings_rate"] >= 20 else "#f87171"
    st.markdown(f"""
    <div class="fin-card" style="margin-top:16px;">
      <span class="metric-label">Monthly Surplus</span>
      <span style="font-family:'DM Serif Display',serif; font-size:22px; color:{'#34d399' if budget['surplus'] > 0 else '#f87171'};">
        ${budget['surplus']:+,.2f}
      </span>
      &nbsp;&nbsp;
      <span class="metric-label" style="margin-left:30px">Savings Rate</span>
      <span style="font-family:'DM Serif Display',serif; font-size:22px; color:{sr_color}">
        {budget['savings_rate']:.1f}%
      </span>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 3 — INVESTMENTS
# ─────────────────────────────────────────
with tabs[2]:
    st.markdown('<p class="section-title">Portfolio Overview</p>', unsafe_allow_html=True)

    i1, i2, i3, i4 = st.columns(4)
    kpi(i1, "Total Portfolio",   f"${total_investments:,.0f}", "accent")
    kpi(i2, "Annual Contribution", f"${invest_annual:,.0f}")
    kpi(i3, "Expected Return",   f"{inv_return*100:.1f}%/yr", "positive")
    kpi(i4, "10-Year Target",    f"${proj_rows[9]['balance']:,.0f}", "positive")

    # Portfolio allocation donut
    alloc_labels = ["ETFs", "Stocks", "Crypto"]
    alloc_vals   = [invest_etf, invest_stocks, invest_crypto]
    fig_alloc = go.Figure(go.Pie(
        labels=alloc_labels, values=alloc_vals, hole=0.55,
        marker_colors=[ACCENT, GREEN, YELLOW],
    ))
    fig_alloc.update_layout(
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        height=280, margin=dict(l=0,r=0,t=0,b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR)),
        annotations=[dict(text="Allocation", font=dict(size=13, color="#9090b0"), showarrow=False)],
    )

    # 20-year growth chart
    years   = [r["year"] for r in proj_rows]
    balance = [r["balance"] for r in proj_rows]
    contrib = [r["contributed"] + total_invest_now for r in proj_rows]
    growth  = [r["growth"] for r in proj_rows]

    fig_growth = go.Figure()
    fig_growth.add_trace(go.Scatter(x=years, y=balance, name="Portfolio Value",
        line=dict(color=ACCENT, width=2.5),
        fill="tozeroy", fillcolor="rgba(129,140,248,0.08)"))
    fig_growth.add_trace(go.Scatter(x=years, y=contrib, name="Amount Invested",
        line=dict(color=GREEN, width=1.5, dash="dot")))
    dark_layout(fig_growth, "20-Year Portfolio Growth", 300)
    fig_growth.update_layout(xaxis_title="Years", yaxis_title="Value ($)",
                              yaxis_tickformat="$,.0f")

    c_alloc, c_growth = st.columns([1, 2])
    with c_alloc:
        st.plotly_chart(fig_alloc, use_container_width=True, config={"displayModeBar": False})
    with c_growth:
        st.plotly_chart(fig_growth, use_container_width=True, config={"displayModeBar": False})

    # Risk profile
    st.markdown('<p class="section-title">Risk Profile</p>', unsafe_allow_html=True)
    r1, r2 = st.columns([1, 2])
    with r1:
        prof = ("Conservative" if r_score < 20 else "Moderate" if r_score < 40 else
                "Balanced" if r_score < 60 else "Growth" if r_score < 80 else "Aggressive")
        color = GREEN if r_score < 40 else YELLOW if r_score < 65 else RED
        st.markdown(f"""
        <div class="fin-card" style="text-align:center">
          <div class="metric-label">Risk Score</div>
          <div style="font-family:'DM Serif Display',serif;font-size:52px;color:{color};">{r_score}</div>
          <div style="color:{color};font-size:13px;font-weight:500;">{prof}</div>
          <div style="color:#6b6b8a;font-size:11px;margin-top:8px;">Max drawdown ~{int(r_score*0.6)}%</div>
        </div>""", unsafe_allow_html=True)
    with r2:
        alloc_map = {
            "Conservative": {"Cash/Bonds": 70, "Defensive ETFs": 20, "Broad ETFs": 10},
            "Moderate":      {"Bonds": 40, "Broad ETFs": 35, "Growth ETFs": 15, "Cash": 10},
            "Balanced":      {"Broad ETFs": 40, "Growth ETFs": 25, "Bonds": 25, "Intl ETFs": 10},
            "Growth":        {"Growth ETFs": 40, "Broad ETFs": 30, "Intl ETFs": 20, "Crypto": 10},
            "Aggressive":    {"Growth ETFs": 40, "Tech ETFs": 25, "Intl ETFs": 20, "Crypto": 15},
        }
        rec = alloc_map.get(prof, alloc_map["Balanced"])
        fig_rec = go.Figure(go.Pie(
            labels=list(rec.keys()), values=list(rec.values()), hole=0.45,
            marker_colors=[ACCENT, GREEN, YELLOW, "#fb923c", RED],
        ))
        fig_rec.update_layout(
            paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
            height=240, margin=dict(l=0,r=0,t=20,b=0),
            title=dict(text="Recommended Allocation", font=dict(color="#e8e8f0", size=13)),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_COLOR, size=11)),
        )
        st.plotly_chart(fig_rec, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────
# TAB 4 — GOALS
# ─────────────────────────────────────────
with tabs[3]:
    st.markdown('<p class="section-title">Goal Tracker</p>', unsafe_allow_html=True)

    for goal_name, result, target, saved, monthly, target_dt in [
        (g1_name, g1, g1_target, g1_saved, g1_monthly, g1_date),
        (g2_name, g2, g2_target, g2_saved, g2_monthly, g2_date),
    ]:
        status_color = "#34d399" if result["on_track"] else "#f59e0b"
        status_txt   = "✅ On Track" if result["on_track"] else "⚠️ Behind"
        pct = result["pct"]
        bar_cls = "green" if result["on_track"] else "yellow"

        st.markdown(f"""
        <div class="fin-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="font-family:'DM Serif Display',serif; font-size:18px;">{goal_name}</span>
            <span style="color:{status_color}; font-size:13px; font-weight:500;">{status_txt}</span>
          </div>
          <div style="display:flex; gap:32px; margin-bottom:14px;">
            <div><div class="metric-label">Target</div><div style="font-size:18px;color:#e8e8f0;">${target:,.0f}</div></div>
            <div><div class="metric-label">Saved</div><div style="font-size:18px;color:#34d399;">${saved:,.0f}</div></div>
            <div><div class="metric-label">Required/mo</div><div style="font-size:18px;color:#818cf8;">${result['req_monthly']:,.0f}</div></div>
            <div><div class="metric-label">Your Contrib</div><div style="font-size:18px;color:{'#34d399' if result['gap']>=0 else '#f87171'};">${monthly:,.0f}</div></div>
            <div><div class="metric-label">Deadline</div><div style="font-size:18px;color:#e8e8f0;">{target_dt.strftime('%b %Y')}</div></div>
          </div>
          <div class="prog-wrap" style="height:12px;">
            <div class="prog-fill {bar_cls}" style="width:{pct:.1f}%"></div>
          </div>
          <div style="font-size:11px;color:#6b6b8a;margin-top:4px;">{pct:.1f}% complete
          {"  ·  Projected: " + result['projected'].strftime('%b %Y') if result['projected'] else ""}
          </div>
        </div>""", unsafe_allow_html=True)

    # Scenario simulator
    st.markdown('<p class="section-title">Scenario: If I invest more?</p>', unsafe_allow_html=True)
    sim_col1, sim_col2 = st.columns(2)
    sim_extra = sim_col1.slider("Extra monthly contribution ($)", 0, 2000, 200, 50)
    sim_target = sim_col2.number_input("Target amount ($)", 1000, 2000000, g1_target, 1000)

    sim_r = return_rate = inv_return / 12
    bal   = g1_saved
    months_base = months_extra = None
    for m in range(1, 601):
        bal = bal * (1 + sim_r) + g1_monthly
        if bal >= sim_target and months_base is None:
            months_base = m
    bal = g1_saved
    for m in range(1, 601):
        bal = bal * (1 + sim_r) + g1_monthly + sim_extra
        if bal >= sim_target and months_extra is None:
            months_extra = m

    if months_base and months_extra:
        saved_months = months_base - months_extra
        st.markdown(f"""
        <div class="insight-card success">
          💡 Adding <strong>${sim_extra:,.0f}/mo</strong> extra reaches ${sim_target:,.0f} in
          <strong>{months_extra} months</strong> vs {months_base} months normally —
          that's <strong>{saved_months} months faster</strong>
          ({saved_months//12}y {saved_months%12}m earlier).
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 5 — DEBT
# ─────────────────────────────────────────
with tabs[4]:
    st.markdown('<p class="section-title">Debt Payoff Strategy</p>', unsafe_allow_html=True)

    d1, d2, d3 = st.columns(3)
    kpi(d1, "Total Debt",         f"${total_debt:,.0f}", "negative")
    kpi(d2, "Avalanche Months",   str(payoff["avalanche"]["months"]))
    kpi(d3, "Interest Saved",     f"${payoff['snowball']['interest'] - payoff['avalanche']['interest']:,.0f}", "positive")

    col_av, col_sn = st.columns(2)
    for col, strategy, result in [
        (col_av, "🏔 Avalanche", payoff["avalanche"]),
        (col_sn, "⛄ Snowball",  payoff["snowball"]),
    ]:
        yrs = result["months"] // 12
        mos = result["months"] % 12
        col.markdown(f"""
        <div class="fin-card">
          <div style="font-family:'DM Serif Display',serif;font-size:17px;margin-bottom:10px;">{strategy}</div>
          <div style="margin-bottom:8px;">
            <div class="metric-label">Payoff Time</div>
            <div style="font-size:22px;color:#e8e8f0;">{yrs}y {mos}m</div>
          </div>
          <div>
            <div class="metric-label">Total Interest Paid</div>
            <div style="font-size:22px;color:#f87171;">${result['interest']:,.0f}</div>
          </div>
          <div style="font-size:11px;color:#6b6b8a;margin-top:10px;">
            {"Highest interest first — saves most money" if "Avalanche" in strategy else "Smallest balance first — fastest wins"}
          </div>
        </div>""", unsafe_allow_html=True)

    # Debt payoff timeline chart
    debts_copy = [dict(d) for d in debts_list]
    timeline_data = {"month": [], "Car Loan": [], "Credit Card": []}
    balances = {d["name"]: d["balance"] for d in debts_list}
    rates    = {d["name"]: d["rate"] for d in debts_list}
    mins     = {d["name"]: d["min"] for d in debts_list}
    av_order = sorted(debts_list, key=lambda x: -x["rate"])

    for m in range(1, payoff["avalanche"]["months"] + 2):
        timeline_data["month"].append(m)
        timeline_data["Car Loan"].append(max(0, balances.get("Car Loan", 0)))
        timeline_data["Credit Card"].append(max(0, balances.get("Credit Card", 0)))
        rem_extra = extra_debt_pay
        for d in av_order:
            nm = d["name"]
            if balances.get(nm, 0) <= 0: continue
            i   = balances[nm] * rates[nm] / 12
            balances[nm] = max(0, balances[nm] + i - mins[nm])
        for d in av_order:
            nm = d["name"]
            if balances.get(nm, 0) > 0 and rem_extra > 0:
                pay = min(rem_extra, balances[nm])
                balances[nm] -= pay; rem_extra -= pay; break

    fig_debt = go.Figure()
    fig_debt.add_trace(go.Scatter(
        x=timeline_data["month"], y=timeline_data["Car Loan"],
        name="Car Loan", fill="tozeroy",
        line=dict(color=YELLOW), fillcolor="rgba(251,191,36,0.1)"))
    fig_debt.add_trace(go.Scatter(
        x=timeline_data["month"], y=timeline_data["Credit Card"],
        name="Credit Card", fill="tozeroy",
        line=dict(color=RED), fillcolor="rgba(248,113,113,0.1)"))
    dark_layout(fig_debt, "Debt Elimination Timeline (Avalanche Method)", 300)
    fig_debt.update_layout(xaxis_title="Months", yaxis_title="Balance ($)", yaxis_tickformat="$,.0f")
    st.plotly_chart(fig_debt, use_container_width=True, config={"displayModeBar": False})

# ─────────────────────────────────────────
# TAB 6 — BUSINESS EARNINGS
# ─────────────────────────────────────────
with tabs[5]:
    st.markdown('<p class="section-title">Realistic Business Earnings</p>', unsafe_allow_html=True)
    st.markdown('<div class="insight-card">All figures are conservative → realistic. No hype. Based on real market data for 1-person operations in AU/US.</div>', unsafe_allow_html=True)

    biz_type = st.selectbox("Business Model", ["Freelance", "SaaS", "E-Commerce", "Agency"])

    if biz_type == "Freelance":
        b1, b2, b3 = st.columns(3)
        fl_rate = b1.number_input("Hourly Rate ($)", 30, 500, 110, 5)
        fl_hrs  = b2.slider("Target Hrs/Week", 5, 40, 30)
        fl_util = b3.slider("Utilization (%)", 30, 95, 68) / 100
        fl_oh   = b1.number_input("Monthly Overhead ($)", 0, 5000, 600, 50)
        fl_tax  = b2.slider("Tax Rate (%)", 10, 50, 32) / 100

        fl = biz_freelance(fl_rate, fl_hrs, fl_util, fl_oh, fl_tax)
        fc1, fc2, fc3, fc4 = st.columns(4)
        kpi(fc1, "Annual Gross",    f"${fl['gross']:,.0f}")
        kpi(fc2, "Annual Net",      f"${fl['net']:,.0f}", "positive")
        kpi(fc3, "Monthly Net",     f"${fl['monthly']:,.0f}", "positive")
        kpi(fc4, "Effective Hourly",f"${fl['eff_hourly']:,.0f}", "accent")

        # utilization sensitivity chart
        utils = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        nets  = [biz_freelance(fl_rate, fl_hrs, u, fl_oh, fl_tax)["net"] for u in utils]
        fig_fl = go.Figure(go.Bar(
            x=[f"{int(u*100)}%" for u in utils], y=nets,
            marker_color=[ACCENT if u == fl_util else GRID_COLOR for u in utils],
            text=[f"${v:,.0f}" for v in nets], textposition="outside",
            textfont=dict(color=TEXT_COLOR, size=11),
        ))
        dark_layout(fig_fl, "Annual Net Income by Utilization Rate", 280)
        fig_fl.update_layout(yaxis_tickformat="$,.0f")
        st.plotly_chart(fig_fl, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div class="insight-card warning">⚠️ At {int(fl_util*100)}% utilization you bill {fl["billed_hrs"]:,} hours/year. Year 1 freelancers often hit 50–60% utilization while building a client base.</div>', unsafe_allow_html=True)

    elif biz_type == "SaaS":
        s1, s2 = st.columns(2)
        s_price = s1.number_input("Monthly Price/User ($)", 5, 500, 49, 1)
        s_churn = s2.slider("Monthly Churn (%)", 1.0, 15.0, 5.0, 0.5) / 100
        s_cogs  = s1.slider("COGS (% of revenue)", 5, 50, 18) / 100
        s_fixed = s2.number_input("Fixed Annual Costs ($)", 0, 200000, 36000, 1000)
        s_cac   = s1.number_input("CAC per Customer ($)", 0, 2000, 200, 10)
        sc1, sc2, sc3 = st.columns(3)
        s_y1 = sc1.number_input("Customers Y1", 1, 10000, 50, 5)
        s_y2 = sc2.number_input("Customers Y2", 1, 10000, 180, 10)
        s_y3 = sc3.number_input("Customers Y3", 1, 10000, 450, 25)

        saas = biz_saas(s_price, [s_y1, s_y2, s_y3], s_churn, s_cogs, s_fixed, s_cac)
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(x=["Year 1","Year 2","Year 3"],
                               y=[r["arr"] for r in saas], name="ARR",
                               marker_color=ACCENT))
        fig_s.add_trace(go.Bar(x=["Year 1","Year 2","Year 3"],
                               y=[r["net_profit"] for r in saas], name="Net Profit",
                               marker_color=[GREEN if r["net_profit"]>=0 else RED for r in saas]))
        dark_layout(fig_s, "SaaS Revenue & Profitability", 300)
        fig_s.update_layout(barmode="group", yaxis_tickformat="$,.0f")
        st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar": False})
        for r in saas:
            profit_color = "positive" if r["net_profit"] >= 0 else "negative"
            st.markdown(f"""
            <div class="fin-card" style="display:inline-block; width:30%; margin-right:2%;">
              <div class="metric-label">Year {r['year']}</div>
              <div style="font-size:13px; color:#9090b0;">Customers: <strong style="color:#e8e8f0">{r['customers']}</strong></div>
              <div style="font-size:13px; color:#9090b0;">MRR: <strong style="color:{ACCENT}">${r['mrr']:,.0f}</strong></div>
              <div style="font-size:13px; color:#9090b0;">Net: <strong style="color:{'#34d399' if r['net_profit']>=0 else '#f87171'}">${r['net_profit']:+,.0f}</strong></div>
            </div>""", unsafe_allow_html=True)
        ann_churn = 1 - (1 - s_churn) ** 12
        st.markdown(f'<div class="insight-card {"danger" if ann_churn > 0.4 else "warning"}">📉 {s_churn*100:.1f}% monthly churn = <strong>{ann_churn*100:.0f}% annual churn</strong>. {"This is critically high — focus on retention above all." if ann_churn > 0.5 else "Aim below 3% monthly for sustainable growth."}</div>', unsafe_allow_html=True)

    elif biz_type == "E-Commerce":
        e1, e2, e3 = st.columns(3)
        e_aov  = e1.number_input("Avg Order Value ($)", 10, 1000, 75, 5)
        e_cogs = e2.slider("COGS (%)", 10, 80, 38) / 100
        e_ads  = e3.number_input("Monthly Ad Spend ($)", 0, 20000, 1200, 100)
        ea1, ea2, ea3 = st.columns(3)
        e_y1 = ea1.number_input("Monthly Orders Y1", 1, 5000, 80, 5)
        e_y2 = ea2.number_input("Monthly Orders Y2", 1, 5000, 220, 10)
        e_y3 = ea3.number_input("Monthly Orders Y3", 1, 5000, 500, 25)

        ecom = biz_ecom(e_aov, [e_y1, e_y2, e_y3], e_cogs, 0.08, e_ads)
        fig_e = go.Figure()
        fig_e.add_trace(go.Bar(x=["Year 1","Year 2","Year 3"],
                               y=[r["gross_revenue"] for r in ecom], name="Gross Revenue", marker_color=ACCENT))
        fig_e.add_trace(go.Bar(x=["Year 1","Year 2","Year 3"],
                               y=[r["gross_profit"] for r in ecom], name="Gross Profit", marker_color=GREEN))
        fig_e.add_trace(go.Bar(x=["Year 1","Year 2","Year 3"],
                               y=[r["net_profit"] for r in ecom], name="Net Profit",
                               marker_color=[GREEN if r["net_profit"]>=0 else RED for r in ecom]))
        dark_layout(fig_e, "E-Commerce P&L", 300)
        fig_e.update_layout(barmode="group", yaxis_tickformat="$,.0f")
        st.plotly_chart(fig_e, use_container_width=True, config={"displayModeBar": False})

    elif biz_type == "Agency":
        ag1, ag2, ag3 = st.columns(3)
        a_ret = ag1.number_input("Monthly Retainer/Client ($)", 500, 20000, 3500, 250)
        a_oh  = ag2.number_input("Monthly Overhead ($)", 0, 10000, 1800, 100)
        a_st  = ag3.number_input("Staff Cost ($/mo)", 0, 50000, 0, 500)
        ag4, ag5, ag6 = st.columns(3)
        a_y1 = ag4.number_input("Clients Y1", 1, 50, 4, 1)
        a_y2 = ag5.number_input("Clients Y2", 1, 100, 8, 1)
        a_y3 = ag6.number_input("Clients Y3", 1, 200, 14, 1)

        agency = biz_agency(a_ret, [a_y1, a_y2, a_y3], a_oh, a_st)
        fig_ag = go.Figure()
        fig_ag.add_trace(go.Bar(x=["Year 1","Year 2","Year 3"],
                                y=[r["revenue"] for r in agency], name="Revenue", marker_color=ACCENT))
        fig_ag.add_trace(go.Bar(x=["Year 1","Year 2","Year 3"],
                                y=[r["net_profit"] for r in agency], name="Net Profit",
                                marker_color=[GREEN if r["net_profit"]>=0 else RED for r in agency]))
        dark_layout(fig_ag, "Agency Revenue & Profit", 300)
        fig_ag.update_layout(barmode="group", yaxis_tickformat="$,.0f")
        st.plotly_chart(fig_ag, use_container_width=True, config={"displayModeBar": False})
        biggest = agency[-1]["revenue"] / max(a_y3 * (1-0.28/2), 1)
        st.markdown(f'<div class="insight-card warning">⚠️ If your top client ({int(100/max(a_y1,1))}% of revenue) leaves, that could be a ${biggest:,.0f}/year revenue hit. Aim for no single client over 20% of total revenue.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# TAB 7 — RETIREMENT
# ─────────────────────────────────────────
with tabs[6]:
    st.markdown('<p class="section-title">Retirement & Financial Independence</p>', unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    kpi(r1, "Super at Retirement",    f"${super_proj['balance']:,.0f}", "positive")
    kpi(r2, "Monthly from Super",     f"${super_proj['monthly_4pct']:,.0f}/mo", "accent")
    kpi(r3, "FI Number (4% rule)",    f"${fi['fi_number']:,.0f}")
    kpi(r4, "Years to FI",            str(fi["years"]))

    # Super growth chart
    super_rows = []
    sup_bal = super_balance
    yrs_to_ret = super_proj["years"]
    annual_sg_contrib = (gross_income * SUPER_SG + super_vol) * 0.85  # after 15% tax
    for yr in range(1, yrs_to_ret + 1):
        sup_bal = sup_bal * (1 + inv_return) + annual_sg_contrib
        super_rows.append({"year": age + yr, "balance": round(sup_bal, 2)})

    fig_sup = go.Figure()
    fig_sup.add_trace(go.Scatter(
        x=[r["year"] for r in super_rows],
        y=[r["balance"] for r in super_rows],
        fill="tozeroy", name="Super Balance",
        line=dict(color=GREEN, width=2.5),
        fillcolor="rgba(52,211,153,0.08)",
    ))
    dark_layout(fig_sup, f"Superannuation Growth to Age {ret_age}", 280)
    fig_sup.update_layout(xaxis_title="Age", yaxis_title="Balance ($)", yaxis_tickformat="$,.0f")
    st.plotly_chart(fig_sup, use_container_width=True, config={"displayModeBar": False})

    # FI progress
    st.markdown('<p class="section-title">Financial Independence Progress</p>', unsafe_allow_html=True)
    fi_pct = min(100, fi["pct"])
    bar_col = "green" if fi_pct >= 50 else "yellow" if fi_pct >= 25 else "red"
    st.markdown(f"""
    <div class="fin-card">
      <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
        <span style="font-size:14px; color:#9090b0;">FI Progress</span>
        <span style="font-size:14px; color:#e8e8f0;">${net_worth:,.0f} / ${fi['fi_number']:,.0f}</span>
      </div>
      <div class="prog-wrap" style="height:16px;">
        <div class="prog-fill {bar_col}" style="width:{fi_pct:.1f}%"></div>
      </div>
      <div style="font-size:12px; color:#6b6b8a; margin-top:6px;">{fi_pct:.1f}% to Financial Independence
        {" · FI at age " + str(age + fi['years']) if isinstance(fi['years'], int) else ""}
      </div>
    </div>""", unsafe_allow_html=True)

    # Compound table
    st.markdown('<p class="section-title">Compound Growth: Every $1,000/yr Extra Invested</p>', unsafe_allow_html=True)
    rows_c = []
    for extra_k in [1000, 3000, 5000, 10000, 20000]:
        bal = 0
        for _ in range(yrs_to_ret):
            bal = bal * (1 + inv_return) + extra_k
        rows_c.append({"Extra/yr": f"${extra_k:,}", "Value at Retirement": f"${bal:,.0f}",
                        "Total Contributed": f"${extra_k*yrs_to_ret:,}",
                        "Pure Growth": f"${bal - extra_k*yrs_to_ret:,.0f}"})
    import pandas as pd
    st.dataframe(
        pd.DataFrame(rows_c).style.hide(axis="index"),
        use_container_width=True
    )

    st.markdown(f'<div class="insight-card success">💡 Your super is projected at <strong>${super_proj["balance"]:,.0f}</strong> at age {ret_age}. Under the 4% withdrawal rule, that\'s <strong>${super_proj["monthly_4pct"]:,.0f}/month</strong> — adjust the sidebar sliders to model different scenarios.</div>', unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 40px 0 20px; color:#2a2a42; font-size:11px; letter-spacing:0.08em;">
  FINORA FINANCIAL ENGINE · NOT FINANCIAL ADVICE · FOR EDUCATIONAL USE ONLY
</div>""", unsafe_allow_html=True)
