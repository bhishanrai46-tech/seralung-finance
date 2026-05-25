"""
Meridian — Smart Investment Guide  v3  (Website Edition)
=========================================================
Run:  streamlit run meridian_app.py
Needs: streamlit plotly
"""

import math, random
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Meridian · Smart Investing",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ───────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ───────────────────────────────────────────────────────────────
BG       = "#F0F4FF"
CARD     = "#FFFFFF"
BORDER   = "#E5E7EB"
TEXT     = "#111827"
MUTED    = "#6B7280"
PRIMARY  = "#4361EE"
P_SOFT   = "#EEF2FF"
P_DARK   = "#2C47C9"
SUCCESS  = "#10B981"
S_SOFT   = "#ECFDF5"
WARNING  = "#F59E0B"
W_SOFT   = "#FFFBEB"
DANGER   = "#EF4444"
D_SOFT   = "#FEF2F2"
PURPLE   = "#8B5CF6"
PU_SOFT  = "#F5F3FF"
ORANGE   = "#F97316"
O_SOFT   = "#FFF7ED"

FH = "'Outfit', sans-serif"
FB = "'Nunito', sans-serif"
FM = "'JetBrains Mono', monospace"

PROFILE_COLORS = {
    "Conservative":           ("#10B981", "#ECFDF5"),
    "Moderately Conservative":("#0EA5E9", "#F0F9FF"),
    "Balanced":               ("#4361EE", "#EEF2FF"),
    "Growth":                 ("#8B5CF6", "#F5F3FF"),
    "Aggressive":             ("#EF4444", "#FEF2F2"),
}
PROFILE_ICONS = {
    "Conservative": "🛡️",
    "Moderately Conservative": "⚖️",
    "Balanced": "📊",
    "Growth": "🚀",
    "Aggressive": "⚡",
}

ASSET_NAMES  = ["Australian Shares","International Shares","Property & REITs",
                "Fixed Income & Bonds","Cash & Term Deposits"]
ASSET_KEYS   = ["aus_shares","intl_shares","property_reits","fixed_income","cash_td"]
ASSET_COLORS = [PRIMARY,"#10B981","#F59E0B","#8B5CF6","#06B6D4"]
ASSET_ICONS  = ["🇦🇺","🌐","🏠","📈","💰"]
CUR_SYM      = {"AUD":"A$","USD":"$","EUR":"€","GBP":"£","SGD":"S$"}

# ───────────────────────────────────────────────────────────────
# SESSION STATE
# ───────────────────────────────────────────────────────────────
_d = {
    **{f"q{i}": 0 for i in range(1, 11)},
    "risk_score":0,"risk_profile":"","profile_done":False,
    "aus_shares":0,"intl_shares":0,"property_reits":0,
    "fixed_income":0,"cash_td":0,"currency":"AUD",
    "goal_amount":1_000_000,"goal_years":20,
    "monthly_contrib":2_000,"cgt_rate":32,"cost_base_pct":60,
}
for k,v in _d.items():
    if k not in st.session_state: st.session_state[k]=v

# ───────────────────────────────────────────────────────────────
# QUESTIONS
# ───────────────────────────────────────────────────────────────
QUESTIONS = [
    ("⏱️  How long can you leave this money invested?",
     ["Less than 3 years — I might need it soon",
      "3–7 years — medium-term plan",
      "7–15 years — building long-term wealth",
      "15+ years — retirement or passing it on"],
     "The longer you can leave money invested, the more risk you can afford to take. Markets always go up and down — but history shows they recover given enough time."),
    ("💼  How stable is your income?",
     ["I'm retired or on a fixed income",
      "Variable — I'm self-employed or on contracts",
      "Stable salary — regular paycheques",
      "Very secure — government or tenured job"],
     "If your income is reliable, you don't need to sell investments when markets drop. Unstable income means you might need to cash out at a bad time."),
    ("🏦  How many months of expenses do you have saved in cash?",
     ["Less than 1 month",
      "1–3 months",
      "3–6 months",
      "6+ months — well covered"],
     "A cash safety net means you won't have to sell investments in an emergency. Without one, a surprise expense could force you to sell at exactly the wrong moment."),
    ("📚  How much investing experience do you have?",
     ["None — I mostly use savings accounts",
      "Some — I understand shares and funds",
      "3+ years of active investing in shares or ETFs",
      "10+ years across different asset types"],
     "Experience matters because you know how you actually behave when markets fall — not just how you think you'd behave."),
    ("📉  If your portfolio dropped 30% in 3 months, what would you do?",
     ["Sell everything immediately",
      "Sell some to reduce risk",
      "Hold on and wait for recovery",
      "Buy more while prices are low"],
     "A 30% drop isn't rare — it happened in 2008 and again in 2020. Be honest here. What you'd actually do matters more than what sounds good."),
    ("🎯  What's your main goal for this money?",
     ["Protect what I have — safety is everything",
      "Grow slowly with capital protection as backup",
      "Balanced growth over the medium to long term",
      "Maximum growth — I can handle big swings"],
     "Your goal shapes everything. A retiree taking income and a 30-year-old building wealth need very different portfolios, even with the same risk score."),
    ("💸  Will you need to withdraw money in the next 5 years?",
     ["Yes — most of it within 5 years",
      "Yes — a meaningful portion",
      "Maybe — only small amounts",
      "No — this money stays invested"],
     "If you'll need money soon, it shouldn't be in risky investments. A market crash right before you need to withdraw can be devastating."),
    ("💳  How's your current debt situation?",
     ["High debt relative to my income",
      "Moderate — I have a mortgage",
      "Low — I'm paying it down steadily",
      "Debt free"],
     "Paying off a 20% credit card is a guaranteed 20% return. High-interest debt usually beats any investment return in the short term."),
    ("💎  What share of your total wealth is this portfolio?",
     ["Over 75% — this is most of what I have",
      "50–75% of my total wealth",
      "25–50% of my total wealth",
      "Less than 25% — I have lots of other assets"],
     "If this is most of your wealth, caution is wise — regardless of your other answers. You can't afford to lose what you can't replace."),
    ("📊  How much loss could you handle in a year without stressing out?",
     ["Less than 5% — any big loss is unacceptable",
      "5–15% — some drops are okay",
      "15–25% — I understand markets go in cycles",
      "25%+ — I'm focused on the long term"],
     "Tip: turn your answer into a dollar number. Percentages feel abstract — dollars don't. If you're unsure, go with the safer option."),
]

# ───────────────────────────────────────────────────────────────
# PROFILES
# ───────────────────────────────────────────────────────────────
PROFILES = {
    "Conservative": {
        "range":(10,18),"ret":"3–5% p.a.","ret_mid":0.04,"draw":"5–10%",
        "draw_mid":0.075,"horizon":"1–5 years","vol":0.05,
        "headline":"Keeping what you have comes first.",
        "desc":"You prefer safety over growth. Your money stays mostly in bonds and cash, with a small slice in shares for a little extra return.",
        "targets":{"Australian Shares":8,"International Shares":12,"Property & REITs":5,"Fixed Income & Bonds":45,"Cash & Term Deposits":30},
    },
    "Moderately Conservative": {
        "range":(19,25),"ret":"4–6% p.a.","ret_mid":0.05,"draw":"10–15%",
        "draw_mid":0.125,"horizon":"3–7 years","vol":0.08,
        "headline":"Slow and steady growth, with a safety cushion.",
        "desc":"You want a bit more growth than cash gives, but keeping capital safe still matters a lot. Good for investors approaching retirement.",
        "targets":{"Australian Shares":15,"International Shares":20,"Property & REITs":10,"Fixed Income & Bonds":40,"Cash & Term Deposits":15},
    },
    "Balanced": {
        "range":(26,31),"ret":"5–8% p.a.","ret_mid":0.065,"draw":"15–25%",
        "draw_mid":0.20,"horizon":"5–10 years","vol":0.11,
        "headline":"A genuine mix of growth and protection.",
        "desc":"Half your money works hard for growth, half provides a safety net. You accept that markets go up and down and you're comfortable riding that out.",
        "targets":{"Australian Shares":25,"International Shares":30,"Property & REITs":15,"Fixed Income & Bonds":22,"Cash & Term Deposits":8},
    },
    "Growth": {
        "range":(32,36),"ret":"7–10% p.a.","ret_mid":0.08,"draw":"25–35%",
        "draw_mid":0.30,"horizon":"7–15 years","vol":0.15,
        "headline":"Building wealth for the long haul.",
        "desc":"Most of your money is in shares and property for maximum long-term growth. You know big drops happen and you're okay waiting for recovery.",
        "targets":{"Australian Shares":30,"International Shares":40,"Property & REITs":15,"Fixed Income & Bonds":12,"Cash & Term Deposits":3},
    },
    "Aggressive": {
        "range":(37,40),"ret":"8–12% p.a.","ret_mid":0.09,"draw":"35–50%",
        "draw_mid":0.425,"horizon":"15+ years","vol":0.19,
        "headline":"Maximum growth. Big swings are fine by you.",
        "desc":"Almost everything goes into shares and property. You have a long timeline, stable income, and genuine comfort watching your portfolio swing 40% without panicking.",
        "targets":{"Australian Shares":35,"International Shares":45,"Property & REITs":15,"Fixed Income & Bonds":5,"Cash & Term Deposits":0},
    },
}

STRESS_SCENARIOS = {
    "📉  Small Dip  −15%": {
        "headline":"Small Market Dip  −15%",
        "desc":"Happens every few years. Markets typically bounce back within 6–18 months. A normal part of investing.",
        "recovery_years":1.0,
        "shocks":{"Australian Shares":-0.18,"International Shares":-0.16,"Property & REITs":-0.11,"Fixed Income & Bonds":+0.03,"Cash & Term Deposits":0.0},
    },
    "🐻  Bear Market  −30%": {
        "headline":"Bear Market  −30%",
        "desc":"Similar to the COVID crash of March 2020 or the 2022 rate-hike selloff. Recovery usually takes 1–3 years.",
        "recovery_years":2.5,
        "shocks":{"Australian Shares":-0.33,"International Shares":-0.30,"Property & REITs":-0.22,"Fixed Income & Bonds":+0.06,"Cash & Term Deposits":0.0},
    },
    "💥  Major Crash  −50%": {
        "headline":"Major Crash  −50%",
        "desc":"GFC-level event (2008). The ASX fell 54% peak to trough and took 5 years to fully recover. Rare, but it happens.",
        "recovery_years":5.0,
        "shocks":{"Australian Shares":-0.54,"International Shares":-0.50,"Property & REITs":-0.42,"Fixed Income & Bonds":+0.09,"Cash & Term Deposits":0.0},
    },
}

# ───────────────────────────────────────────────────────────────
# HELPERS — ANALYTICS
# ───────────────────────────────────────────────────────────────
def sym(): return CUR_SYM.get(st.session_state["currency"],"$")

def fmt(n):
    if n is None: return f"{sym()}0"
    s=sym(); sign="−" if n<0 else ""; n=abs(n)
    if n>=1_000_000: return f"{sign}{s}{n/1e6:.2f}M"
    if n>=1_000:     return f"{sign}{s}{n:,.0f}"
    return f"{sign}{s}{n:.0f}"

def pv():   return {n:st.session_state[k] for n,k in zip(ASSET_NAMES,ASSET_KEYS)}
def total_pv(): return sum(st.session_state[k] for k in ASSET_KEYS)
def get_profile(score):
    for name,data in PROFILES.items():
        lo,hi=data["range"]
        if lo<=score<=hi: return name
    return "Balanced"

def health_score(holdings, tgts, total):
    if total==0: return 0,0,0,0
    gaps=[abs(holdings.get(a,0)/total*100-tgts.get(a,0)) for a in ASSET_NAMES]
    align=max(0.0,40.0-sum(gaps)/len(gaps)*2.2)
    pcts=[holdings.get(a,0)/total*100 for a in ASSET_NAMES]
    n_m=sum(1 for p in pcts if p>=2)
    divers=max(0.0,min(30.0,n_m*6.0)-max(0.0,(max(pcts)-50)*0.55))
    cur_d=(holdings.get("Cash & Term Deposits",0)+holdings.get("Fixed Income & Bonds",0))/total*100
    tgt_d=tgts.get("Cash & Term Deposits",0)+tgts.get("Fixed Income & Bonds",0)
    liq=max(0.0,30.0-abs(cur_d-tgt_d)*1.4)
    tot=align+divers+liq
    return round(tot),round(align),round(divers),round(liq)

def stress_test(holdings,total,scenario):
    shocks=scenario["shocks"]; new_total=0.0; breakdown={}
    for asset in ASSET_NAMES:
        val=holdings.get(asset,0)
        shocked=val*(1+shocks.get(asset,0))
        new_total+=shocked; breakdown[asset]=shocked-val
    return new_total,new_total-total,breakdown

def monte_carlo(cur,monthly,years,pname,n=1000):
    params={"Conservative":(0.040,0.050),"Moderately Conservative":(0.050,0.080),
            "Balanced":(0.065,0.110),"Growth":(0.080,0.150),"Aggressive":(0.090,0.190)}
    mu_a,sig_a=params.get(pname,(0.065,0.110))
    m_mu=mu_a/12; m_sig=sig_a/math.sqrt(12)
    random.seed(42)
    yearly=[[ ] for _ in range(years+1)]
    for _ in range(n):
        yearly[0].append(float(cur))
    all_paths=[]
    for sim in range(n):
        val=float(cur)
        for yr in range(1,years+1):
            for _ in range(12):
                val=max(0.0,val*(1+random.gauss(m_mu,m_sig))+monthly)
            yearly[yr].append(val)
        all_paths.append(val)
    all_paths.sort()
    p=lambda x:all_paths[max(0,int(x*n)-1)]
    yr_med={y:sorted(yearly[y])[n//2] for y in range(years+1)}
    yr_p10={y:sorted(yearly[y])[max(0,int(0.1*n)-1)] for y in range(years+1)}
    yr_p90={y:sorted(yearly[y])[min(n-1,int(0.9*n))] for y in range(years+1)}
    return p(0.10),p(0.25),p(0.50),p(0.75),p(0.90),yr_med,yr_p10,yr_p90

def smart_allocate(new_money,holdings,tgts,total):
    proj=total+new_money; needs={}
    for a in ASSET_NAMES:
        gap=proj*tgts.get(a,0)/100-holdings.get(a,0)
        if gap>0: needs[a]=gap
    if not needs: return {a:0 for a in ASSET_NAMES}
    tot_need=sum(needs.values()); result={}; running=0
    items=list(needs.items())
    for i,(a,g) in enumerate(items):
        if i==len(items)-1: result[a]=new_money-running
        else:
            alloc=round(new_money*g/tot_need/100)*100
            result[a]=alloc; running+=alloc
    return result

def cgt_cost(sell,cost_base_pct,rate):
    cost=sell*cost_base_pct/100; gain=max(0.0,sell-cost)
    return gain*0.50*rate/100

# ───────────────────────────────────────────────────────────────
# SVG DECORATIONS
# ───────────────────────────────────────────────────────────────
HERO_SVG = """
<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" style="position:absolute;right:0;top:0;height:200px;opacity:0.18;">
  <circle cx="500" cy="40" r="90" fill="#fff"/>
  <circle cx="420" cy="130" r="50" fill="#fff"/>
  <circle cx="560" cy="160" r="35" fill="#fff"/>
  <rect x="320" y="80" width="12" height="80" rx="4" fill="#fff" opacity="0.7"/>
  <rect x="342" y="50" width="12" height="110" rx="4" fill="#fff" opacity="0.7"/>
  <rect x="364" y="100" width="12" height="60" rx="4" fill="#fff" opacity="0.7"/>
  <rect x="386" y="70" width="12" height="90" rx="4" fill="#fff" opacity="0.7"/>
  <polyline points="320,100 342,65 364,110 386,80 408,55" stroke="#fff" stroke-width="2.5" fill="none" opacity="0.9"/>
</svg>"""

def icon_svg(name):
    svgs = {
        "shield": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7z"/></svg>',
        "chart":  '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="13" width="4" height="8"/><rect x="10" y="8" width="4" height="13"/><rect x="17" y="3" width="4" height="18"/></svg>',
        "target": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        "bolt":   '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="13,2 3,14 12,14 11,22 21,10 12,10 13,2"/></svg>',
        "wallet": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="14" rx="2"/><path d="M16 14a2 2 0 0 0 0-4h-4v4h4z"/><path d="M6 6V4a2 2 0 0 1 2-2h8"/></svg>',
        "scale":  '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M3 9l9-6 9 6M5 21h14"/><path d="M3 9h4l2 6H3z M17 9h4l-2 6h-4z" stroke="none" fill="currentColor" opacity="0.3"/></svg>',
        "info":   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "check":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20,6 9,17 4,12"/></svg>',
        "warn":   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "fire":   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 11-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 3z"/></svg>',
    }
    return svgs.get(name,"")

# ───────────────────────────────────────────────────────────────
# UI COMPONENTS
# ───────────────────────────────────────────────────────────────
def tip(text, kind="info"):
    cfg = {
        "info":  (P_SOFT, PRIMARY,  icon_svg("info")),
        "good":  (S_SOFT, SUCCESS,  icon_svg("check")),
        "warn":  (W_SOFT, WARNING,  icon_svg("warn")),
        "alert": (D_SOFT, DANGER,   icon_svg("fire")),
    }
    bg,ac,ico=cfg.get(kind,cfg["info"])
    st.markdown(
        f"<div style='background:{bg};border-radius:12px;padding:1rem 1.2rem;"
        f"margin:0.75rem 0;display:flex;gap:0.75rem;align-items:flex-start;'>"
        f"<div style='color:{ac};flex-shrink:0;margin-top:1px;'>{ico}</div>"
        f"<div style='font-family:{FB};font-size:0.9rem;color:{TEXT};"
        f"line-height:1.65;'>{text}</div></div>",
        unsafe_allow_html=True,
    )

def section_label(text, icon=""):
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:0.5rem;"
        f"margin:2rem 0 1rem;'>"
        f"<div style='font-family:{FH};font-size:1.05rem;color:{TEXT};"
        f"font-weight:700;'>{icon} {text}</div>"
        f"<div style='flex:1;height:1px;background:{BORDER};margin-left:0.5rem;'></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

def metric_cards(cards):
    cols=st.columns(len(cards),gap="small")
    for col,(icon,lbl,val,note,accent) in zip(cols,cards):
        with col:
            st.markdown(
                f"<div style='background:{CARD};border-radius:14px;"
                f"border:1.5px solid {BORDER};padding:18px 20px;"
                f"box-shadow:0 2px 12px rgba(0,0,0,0.05);'>"
                f"<div style='font-size:1.5rem;margin-bottom:6px;'>{icon}</div>"
                f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.12em;"
                f"text-transform:uppercase;color:{MUTED};margin-bottom:4px;'>{lbl}</div>"
                f"<div style='font-family:{FH};font-size:1.85rem;color:{accent};"
                f"font-weight:700;line-height:1;'>{val}</div>"
                f"<div style='font-family:{FB};font-size:0.72rem;color:{MUTED};"
                f"margin-top:5px;'>{note}</div></div>",
                unsafe_allow_html=True,
            )

def info_table(headers, rows):
    hdr="".join(
        f"<th style='text-align:left;padding:10px 14px;background:{BG};"
        f"font-family:{FM};font-size:0.57rem;text-transform:uppercase;"
        f"letter-spacing:0.1em;color:{MUTED};font-weight:600;white-space:nowrap;'>{h}</th>"
        for h in headers)
    body=""
    for i,row in enumerate(rows):
        bg=CARD if i%2==0 else BG
        cells="".join(
            f"<td style='padding:10px 14px;font-family:{FB};font-size:0.85rem;"
            f"color:{TEXT};background:{bg};border-bottom:1px solid {BORDER};'>{c}</td>"
            for c in row)
        body+=f"<tr>{cells}</tr>"
    st.markdown(
        f"<div style='border-radius:12px;overflow:hidden;border:1.5px solid {BORDER};"
        f"box-shadow:0 2px 12px rgba(0,0,0,0.04);margin:0.5rem 0 1.2rem;'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True,
    )

def donut(labels, values, colors, center=""):
    fig=go.Figure(go.Pie(
        labels=labels,values=values,hole=0.64,
        marker=dict(colors=colors,line=dict(color="#fff",width=3)),
        textinfo="label+percent",
        textfont=dict(family="Nunito, sans-serif",size=11,color=TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10,b=10,l=10,r=10),height=260,showlegend=False,
        font=dict(family="Nunito, sans-serif",color=TEXT),
        annotations=[dict(text=center,x=0.5,y=0.5,
            font=dict(size=13,family="Outfit, sans-serif",color=TEXT),
            showarrow=False)] if center else [])
    return fig

def action_card(title, amount, current_pct, target_pct, kind="sell", priority="", extra=""):
    ac=DANGER if kind=="sell" else SUCCESS
    bg=D_SOFT  if kind=="sell" else S_SOFT
    label="Sell" if kind=="sell" else "Buy"
    st.markdown(
        f"<div style='background:{CARD};border-radius:14px;border:1.5px solid {BORDER};"
        f"box-shadow:0 2px 12px rgba(0,0,0,0.05);padding:1.1rem 1.4rem;"
        f"margin-bottom:0.75rem;border-left:4px solid {ac};'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<div style='font-family:{FH};font-size:1rem;font-weight:700;color:{TEXT};'>{title}</div>"
        f"<div style='background:{bg};color:{ac};font-family:{FM};font-size:0.9rem;"
        f"font-weight:700;padding:4px 12px;border-radius:20px;'>{label} {amount}</div></div>"
        f"<div style='font-family:{FB};font-size:0.82rem;color:{MUTED};margin:6px 0 0;'>"
        f"Currently {current_pct:.1f}% → Target {target_pct:.0f}%"
        f"{'  ·  ' + extra if extra else ''}</div>"
        f"{'<div style=\"margin-top:6px;\"><span style=\"font-family:'+FM+';font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;background:'+ac+';color:#fff;padding:2px 8px;border-radius:10px;\">'+priority+'</span></div>' if priority else ''}"
        f"</div>",
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────────────────────
# GLOBAL CSS
# ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Nunito:ital,wght@0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

html,body,.stApp,[data-testid="stAppViewContainer"]{{
    background:{BG} !important;
    font-family:{FB};color:{TEXT};
}}
.block-container{{padding:0 2rem 4rem;max-width:1120px;}}
#MainMenu,footer,header{{visibility:hidden;}}
.stDeployButton{{display:none!important;}}

h1,h2,h3,h4{{font-family:{FH}!important;font-weight:700!important;color:{TEXT}!important;}}
p,span,li{{color:{TEXT}!important;}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{{
    gap:4px;border-bottom:2px solid {BORDER};background:transparent;padding:0 0 0 2px;
}}
.stTabs [data-baseweb="tab"]{{
    font-family:{FM};font-size:0.62rem;letter-spacing:0.12em;
    text-transform:uppercase;color:{MUTED};background:{CARD};
    border:1.5px solid {BORDER};border-bottom:none;border-radius:10px 10px 0 0;
    padding:10px 20px;margin-right:2px;
}}
.stTabs [aria-selected="true"]{{
    color:{PRIMARY}!important;border-color:{PRIMARY}!important;
    border-bottom:2px solid {CARD}!important;background:{CARD}!important;
    font-weight:600!important;
}}
.stTabs [data-baseweb="tab-highlight"]{{background:{PRIMARY}!important;height:0!important;}}
.stTabs [data-baseweb="tab-panel"]{{padding-top:1.5rem;background:transparent;}}

/* ── INPUTS ── */
div[data-testid="stNumberInput"] label,div[data-testid="stSelectbox"] label{{
    font-family:{FM}!important;font-size:0.62rem!important;
    letter-spacing:0.12em!important;text-transform:uppercase!important;color:{MUTED}!important;
}}
.stNumberInput input{{
    background:{CARD}!important;border:1.5px solid {BORDER}!important;
    border-radius:10px!important;color:{TEXT}!important;
    font-family:{FM}!important;font-size:0.9rem!important;
    box-shadow:0 1px 4px rgba(0,0,0,0.04)!important;
}}
.stNumberInput input:focus{{border-color:{PRIMARY}!important;box-shadow:0 0 0 3px rgba(67,97,238,0.12)!important;}}
.stNumberInput button{{
    background:{BG}!important;color:{MUTED}!important;
    border-color:{BORDER}!important;border-radius:8px!important;
}}
.stSelectbox>div>div{{
    background:{CARD}!important;border:1.5px solid {BORDER}!important;
    border-radius:10px!important;color:{TEXT}!important;
    box-shadow:0 1px 4px rgba(0,0,0,0.04)!important;
}}
[role="listbox"]*,[role="option"]{{background:{CARD}!important;color:{TEXT}!important;font-family:{FB}!important;}}

/* ── RADIO ── */
.stRadio>div>label{{font-family:{FB}!important;font-size:0.9rem!important;color:{TEXT}!important;font-weight:400!important;}}
div[data-testid="stRadio"]>label{{
    font-family:{FM}!important;font-size:0.6rem!important;
    letter-spacing:0.12em!important;text-transform:uppercase!important;color:{MUTED}!important;
}}

/* ── BUTTON ── */
.stButton>button{{
    background:linear-gradient(135deg,{PRIMARY},{P_DARK})!important;
    color:#fff!important;border:none!important;border-radius:12px!important;
    font-family:{FH}!important;font-size:0.85rem!important;font-weight:700!important;
    letter-spacing:0.04em!important;padding:0.75rem 2.5rem!important;
    box-shadow:0 4px 14px rgba(67,97,238,0.35)!important;
    transition:all 0.2s!important;
}}
.stButton>button:hover{{opacity:0.88!important;transform:translateY(-1px)!important;}}

/* ── SLIDER ── */
.stSlider label{{font-family:{FM}!important;font-size:0.6rem!important;letter-spacing:0.12em!important;text-transform:uppercase!important;color:{MUTED}!important;}}
.stSlider [data-testid="stThumb"]{{background:{PRIMARY}!important;}}

/* ── EXPANDER ── */
div[data-testid="stExpander"]{{
    background:{CARD}!important;border:1.5px solid {BORDER}!important;
    border-radius:12px!important;box-shadow:0 2px 8px rgba(0,0,0,0.04)!important;
}}
div[data-testid="stExpander"] summary,div[data-testid="stExpander"] summary span{{
    font-family:{FB}!important;font-size:0.85rem!important;font-weight:600!important;color:{TEXT}!important;
}}
hr{{border:none;border-top:1.5px solid {BORDER};margin:1.5rem 0;}}
</style>
""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────
# HERO HEADER
# ───────────────────────────────────────────────────────────────
cur_list=list(CUR_SYM.keys())
p_done=st.session_state["profile_done"]
h_done=total_pv()>0

st.markdown(f"""
<div style='background:linear-gradient(135deg,{PRIMARY} 0%,{P_DARK} 60%,#1a1f6e 100%);
     border-radius:20px;padding:2.2rem 2.5rem;margin-bottom:1.5rem;
     position:relative;overflow:hidden;'>
  {HERO_SVG}
  <div style='position:relative;z-index:1;'>
    <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem;'>
      <span style='font-size:1.8rem;'>💎</span>
      <span style='font-family:{FH};font-size:2rem;color:#fff;font-weight:800;'>Meridian</span>
    </div>
    <p style='font-family:{FB};font-size:1rem;color:rgba(255,255,255,0.85);
       margin:0 0 1.5rem;'>Your smart guide to investing — know your risk, build the right portfolio.</p>
    <div style='display:flex;flex-wrap:wrap;gap:0.6rem;'>
""" + "".join([
    f"<span style='background:{'rgba(255,255,255,0.25)' if done else 'rgba(255,255,255,0.08)'};"
    f"color:#fff;font-family:{FM};font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;"
    f"padding:5px 14px;border-radius:20px;border:1px solid rgba(255,255,255,{'0.5' if done else '0.2'});'>"
    f"{'✓  ' if done else f'{i+1}.  '}{label}</span>"
    for i,(label,done) in enumerate([
        ("Risk Profile",p_done),("Portfolio",h_done),("Analysis",p_done and h_done),
        ("Rebalancing",p_done and h_done),("Stress Test",p_done and h_done),("Goals",p_done and h_done),
    ])
]) + f"""
    </div>
  </div>
</div>
<div style='background:{W_SOFT};border:1.5px solid #FDE68A;border-radius:10px;
     padding:8px 16px;margin-bottom:1rem;font-family:{FB};font-size:0.8rem;color:#92400E;'>
  ⚠️ &nbsp;<strong>Heads up:</strong> This is for education only — not personal financial advice.
  Always talk to a licensed financial adviser before making investment decisions.
</div>
""", unsafe_allow_html=True)

# Currency selector (top-right inline)
c1,_,c3=st.columns([7,1,1])
with c3:
    st.selectbox("",cur_list,index=cur_list.index(st.session_state["currency"]),
                 key="currency",label_visibility="collapsed")

# ───────────────────────────────────────────────────────────────
# TABS
# ───────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
    "🧪 Risk Quiz","💼 My Portfolio","📊 Analysis",
    "⚖️ Rebalancing","🧨 Stress Test","🎯 Goals",
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — RISK QUIZ
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        f"<div style='background:{CARD};border-radius:16px;border:1.5px solid {BORDER};"
        f"box-shadow:0 2px 12px rgba(0,0,0,0.05);padding:1.5rem 1.8rem;margin-bottom:1.5rem;'>"
        f"<div style='font-family:{FH};font-size:1.3rem;font-weight:700;color:{TEXT};margin-bottom:0.4rem;'>"
        f"What kind of investor are you?</div>"
        f"<div style='font-family:{FB};font-size:0.9rem;color:{MUTED};line-height:1.65;'>"
        f"Answer 10 quick questions and we'll work out your investor type — and build the right "
        f"portfolio for you. Be honest — the more accurate your answers, the better your results.</div></div>",
        unsafe_allow_html=True,
    )

    total_score=0
    for i,(question,options,insight) in enumerate(QUESTIONS):
        qkey=f"q{i+1}"
        st.markdown(
            f"<div style='background:{CARD};border-radius:14px;border:1.5px solid {BORDER};"
            f"box-shadow:0 2px 10px rgba(0,0,0,0.04);padding:1.2rem 1.5rem;margin-bottom:1rem;'>"
            f"<div style='display:flex;align-items:flex-start;gap:0.75rem;margin-bottom:0.9rem;'>"
            f"<div style='background:{P_SOFT};color:{PRIMARY};font-family:{FM};font-size:0.7rem;"
            f"font-weight:700;padding:3px 9px;border-radius:20px;flex-shrink:0;margin-top:1px;'>{i+1}/{len(QUESTIONS)}</div>"
            f"<div style='font-family:{FH};font-size:1rem;font-weight:700;color:{TEXT};'>{question}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        selected_idx=st.radio(
            label=question,options=list(range(len(options))),
            format_func=lambda x,opts=options:opts[x],
            index=st.session_state[qkey],
            key=f"radio_{qkey}",label_visibility="collapsed")
        st.session_state[qkey]=selected_idx
        total_score+=selected_idx+1
        with st.expander("💡 Why does this matter?"):
            st.markdown(
                f"<div style='font-family:{FB};font-size:0.875rem;color:{MUTED};"
                f"line-height:1.65;padding:0.2rem 0;'>{insight}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    col_btn,_=st.columns([2,5])
    with col_btn:
        if st.button("✨  Get My Investor Profile"):
            pn=get_profile(total_score)
            st.session_state["risk_score"]=total_score
            st.session_state["risk_profile"]=pn
            st.session_state["profile_done"]=True
            try: st.rerun()
            except: st.experimental_rerun()

    if st.session_state["profile_done"]:
        pname=st.session_state["risk_profile"]
        prof=PROFILES[pname]
        pct_score=((st.session_state["risk_score"]-10)/30)*100
        pac,pbg=PROFILE_COLORS[pname]
        icon=PROFILE_ICONS[pname]
        tgts=prof["targets"]
        total_val=total_pv()

        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:linear-gradient(135deg,{pac},{pbg});border-radius:18px;"
            f"padding:2rem 2.2rem;margin-bottom:1.2rem;border:1.5px solid {BORDER};"
            f"box-shadow:0 4px 20px rgba(0,0,0,0.08);'>"
            f"<div style='font-size:3rem;margin-bottom:0.5rem;'>{icon}</div>"
            f"<div style='font-family:{FH};font-size:0.65rem;letter-spacing:0.15em;"
            f"text-transform:uppercase;color:rgba(0,0,0,0.5);margin-bottom:0.3rem;'>Your Investor Profile</div>"
            f"<div style='font-family:{FH};font-size:2.2rem;font-weight:800;color:{TEXT};'>{pname}</div>"
            f"<div style='font-family:{FB};font-size:0.95rem;color:{TEXT};opacity:0.8;"
            f"margin:0.5rem 0 1rem;line-height:1.6;'>{prof['headline']}</div>"
            f"<div style='font-family:{FB};font-size:0.85rem;color:{TEXT};opacity:0.7;"
            f"line-height:1.65;'>{prof['desc']}</div>"
            f"<div style='margin-top:1.2rem;'>"
            f"<div style='font-family:{FM};font-size:0.6rem;letter-spacing:0.1em;"
            f"text-transform:uppercase;color:rgba(0,0,0,0.4);margin-bottom:6px;'>"
            f"Risk Score  {st.session_state['risk_score']}/40</div>"
            f"<div style='height:8px;background:rgba(0,0,0,0.1);border-radius:6px;overflow:hidden;'>"
            f"<div style='width:{pct_score:.0f}%;height:100%;background:{pac};"
            f"border-radius:6px;'></div></div></div></div>",
            unsafe_allow_html=True,
        )

        if total_val>0:
            draw_est=total_val*prof["draw_mid"]
            metric_cards([
                ("📈","Expected Return",prof["ret"],"Historical estimate p.a.",pac),
                ("📉","Typical Max Drop",prof["draw"],f"In a bad market",DANGER),
                ("💸","Drop in Dollars",fmt(draw_est),"Based on your portfolio",DANGER),
                ("⏳","Ideal Time Frame",prof["horizon"],"Minimum recommended",SUCCESS),
            ])
        else:
            metric_cards([
                ("📈","Expected Return",prof["ret"],"Historical estimate p.a.",pac),
                ("📉","Typical Max Drop",prof["draw"],"In a bad market",DANGER),
                ("⏳","Ideal Time Frame",prof["horizon"],"Minimum recommended",SUCCESS),
            ])

        section_label("Your Target Mix","🎯")
        active_t={k:v for k,v in tgts.items() if v>0}
        col_ch,col_lg=st.columns([1,1])
        with col_ch:
            st.plotly_chart(donut(list(active_t.keys()),list(active_t.values()),
                [ASSET_COLORS[ASSET_NAMES.index(k)] for k in active_t],f"<b>{pname[:4]}.</b>"),
                use_container_width=True)
        with col_lg:
            st.markdown("<br>",unsafe_allow_html=True)
            for aname,pctv in tgts.items():
                clr=ASSET_COLORS[ASSET_NAMES.index(aname)]
                ico=ASSET_ICONS[ASSET_NAMES.index(aname)]
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:0.75rem;"
                    f"padding:0.5rem 0;border-bottom:1px solid {BORDER};'>"
                    f"<span style='font-size:1.1rem;'>{ico}</span>"
                    f"<div style='flex:1;font-family:{FB};font-size:0.85rem;color:{TEXT};'>{aname}</div>"
                    f"<div style='background:{clr}22;color:{clr};font-family:{FM};font-size:0.8rem;"
                    f"font-weight:700;padding:2px 10px;border-radius:20px;'>{pctv}%</div></div>",
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════════
# TAB 2 — MY PORTFOLIO
# ══════════════════════════════════════════════════════════════
with tab2:
    if not p_done:
        tip("Complete the Risk Quiz first to unlock this section.","info")
    else:
        st.markdown(
            f"<div style='background:{CARD};border-radius:14px;border:1.5px solid {BORDER};"
            f"padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>"
            f"<div style='font-family:{FH};font-size:1.2rem;font-weight:700;'>What do you currently own?</div>"
            f"<div style='font-family:{FB};font-size:0.875rem;color:{MUTED};margin-top:4px;'>"
            f"Enter the value of each investment type. Include super, shares, ETFs, property equity, "
            f"bonds, and savings. The full picture gives you the best result.</div></div>",
            unsafe_allow_html=True,
        )

        descs=[
            "ASX shares, Australian ETFs & managed funds",
            "Global ETFs (S&P 500, MSCI World), international funds",
            "Investment property equity, A-REITs, global REITs",
            "Government & corporate bonds, bond ETFs, term deposits 1yr+",
            "Savings accounts, term deposits under 1 year, offset accounts",
        ]
        ca,cb=st.columns(2,gap="large")
        for idx,(aname,key,desc,ico) in enumerate(zip(ASSET_NAMES,ASSET_KEYS,descs,ASSET_ICONS)):
            col=ca if idx<3 else cb
            with col:
                clr=ASSET_COLORS[idx]
                st.markdown(
                    f"<div style='background:{CARD};border-radius:12px;border:1.5px solid {BORDER};"
                    f"padding:1rem 1.2rem;margin-bottom:0.5rem;border-left:4px solid {clr};'>"
                    f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:4px;'>"
                    f"<span style='font-size:1.2rem;'>{ico}</span>"
                    f"<div style='font-family:{FH};font-size:0.9rem;font-weight:700;color:{TEXT};'>{aname}</div></div>"
                    f"<div style='font-family:{FB};font-size:0.73rem;color:{MUTED};margin-bottom:8px;'>{desc}</div>",
                    unsafe_allow_html=True,
                )
                st.number_input(aname,min_value=0,step=1000,key=key,label_visibility="collapsed")
                st.markdown("</div>",unsafe_allow_html=True)

        total=total_pv()
        if total==0:
            st.markdown("<br>",unsafe_allow_html=True)
            tip("Enter your holdings above to see your portfolio breakdown.","info")
        else:
            holdings=pv()
            active={k:v for k,v in holdings.items() if v>0}
            pname=st.session_state["risk_profile"]
            tgts=PROFILES[pname]["targets"]
            hs,ha,hd,hl=health_score(holdings,tgts,total)

            # Health score
            section_label("Portfolio Health","❤️")
            if hs>=75: hclr,hlabel=SUCCESS,"Healthy"
            elif hs>=50: hclr,hlabel=WARNING,"Needs attention"
            else: hclr,hlabel=DANGER,"Action needed"

            hcol1,hcol2=st.columns([1,2],gap="large")
            with hcol1:
                st.markdown(
                    f"<div style='background:{CARD};border-radius:16px;border:1.5px solid {BORDER};"
                    f"padding:1.5rem;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.05);'>"
                    f"<div style='font-family:{FM};font-size:0.6rem;letter-spacing:0.12em;"
                    f"text-transform:uppercase;color:{MUTED};margin-bottom:8px;'>Overall Score</div>"
                    f"<div style='font-family:{FH};font-size:4rem;font-weight:800;color:{hclr};line-height:1;'>{hs}</div>"
                    f"<div style='font-family:{FM};font-size:0.65rem;color:{MUTED};'>/100</div>"
                    f"<div style='background:{hclr}22;color:{hclr};font-family:{FB};font-size:0.8rem;"
                    f"font-weight:700;padding:4px 14px;border-radius:20px;margin-top:10px;display:inline-block;'>{hlabel}</div>"
                    f"<div style='height:8px;background:{BORDER};border-radius:6px;margin-top:14px;overflow:hidden;'>"
                    f"<div style='width:{hs}%;height:100%;background:{hclr};border-radius:6px;'></div></div></div>",
                    unsafe_allow_html=True,
                )
            with hcol2:
                for lbl,score,tot_pts,tip_txt,desc in [
                    ("🎯  Alignment",ha,40,"How close you are to your target mix",f"{ha}/{tot_pts} — How closely your holdings match your {pname} profile"),
                    ("🌐  Diversification",hd,30,"Spread across investment types",f"{hd}/{tot_pts} — Spread across different asset classes"),
                    ("🛡️  Safety Buffer",hl,30,"Defensive assets vs target",f"{hl}/{tot_pts} — Your cash & bonds weighting vs target"),
                ]:
                    bar=score/tot_pts*100
                    clr2=SUCCESS if bar>=70 else (WARNING if bar>=40 else DANGER)
                    st.markdown(
                        f"<div style='background:{CARD};border-radius:12px;border:1.5px solid {BORDER};"
                        f"padding:1rem 1.2rem;margin-bottom:0.6rem;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;'>"
                        f"<div style='font-family:{FB};font-size:0.85rem;font-weight:700;color:{TEXT};'>{lbl}</div>"
                        f"<div style='background:{clr2}22;color:{clr2};font-family:{FM};"
                        f"font-size:0.75rem;font-weight:700;padding:2px 10px;border-radius:20px;'>{score}/{tot_pts}</div></div>"
                        f"<div style='height:6px;background:{BORDER};border-radius:4px;overflow:hidden;margin-bottom:6px;'>"
                        f"<div style='width:{bar:.0f}%;height:100%;background:{clr2};border-radius:4px;'></div></div>"
                        f"<div style='font-family:{FB};font-size:0.75rem;color:{MUTED};'>{desc}</div></div>",
                        unsafe_allow_html=True,
                    )

            if hs>=75: tip("Great work — your portfolio is well-structured. Check in quarterly to keep it on track.","good")
            elif ha<20: tip(f"Your allocation is quite different from your {pname} target. Head to the Rebalancing tab to see what to change.","alert")
            elif hd<15: tip("Too much in one investment type. A market crash there could really hurt your overall wealth.","warn")
            else: tip("Some gaps to close, but nothing drastic. The Rebalancing tab shows the most tax-friendly way to fix it.","warn")

            section_label("Your Holdings","💼")
            metric_cards([
                ("💰","Total Portfolio",fmt(total),"Across all asset types",PRIMARY),
                ("📦","Investment Types",str(len(active)),"out of 5 categories",SUCCESS),
                ("🏆","Biggest Position",max(active,key=active.get),f"{max(active.values())/total*100:.0f}% of total",WARNING),
                ("❤️","Health Score",f"{hs}/100","Alignment · Spread · Safety",hclr),
            ])
            st.markdown("<br>",unsafe_allow_html=True)
            col_c,col_d=st.columns([1,1])
            with col_c:
                st.plotly_chart(donut(list(active.keys()),list(active.values()),
                    [ASSET_COLORS[ASSET_NAMES.index(k)] for k in active],f"<b>{fmt(total)}</b>"),
                    use_container_width=True)
            with col_d:
                st.markdown("<br>",unsafe_allow_html=True)
                for aname in sorted(holdings,key=lambda x:holdings[x],reverse=True):
                    val=holdings[aname]
                    if val==0: continue
                    pctv=val/total*100
                    clr=ASSET_COLORS[ASSET_NAMES.index(aname)]
                    ico=ASSET_ICONS[ASSET_NAMES.index(aname)]
                    st.markdown(
                        f"<div style='display:flex;align-items:center;gap:0.6rem;"
                        f"padding:0.5rem 0;border-bottom:1px solid {BORDER};'>"
                        f"<span style='font-size:1rem;'>{ico}</span>"
                        f"<div style='flex:1;font-family:{FB};font-size:0.85rem;color:{TEXT};'>{aname}</div>"
                        f"<div style='font-family:{FM};font-size:0.75rem;color:{MUTED};margin-right:6px;'>{pctv:.1f}%</div>"
                        f"<div style='font-family:{FM};font-size:0.85rem;font-weight:700;color:{TEXT};'>{fmt(val)}</div></div>",
                        unsafe_allow_html=True,
                    )
            for aname,val in holdings.items():
                if val and val/total*100>60:
                    tip(f"⚠️ {aname} is {val/total*100:.0f}% of your portfolio. That's a lot of eggs in one basket. "
                        f"See the Stress Test tab to understand what happens if this asset drops sharply.","warn")
                    break

# ══════════════════════════════════════════════════════════════
# TAB 3 — ANALYSIS
# ══════════════════════════════════════════════════════════════
with tab3:
    if not p_done: tip("Complete the Risk Quiz first.","info")
    elif total_pv()==0: tip("Enter your holdings in the My Portfolio tab.","info")
    else:
        pname=st.session_state["risk_profile"]
        tgts=PROFILES[pname]["targets"]
        holdings=pv(); total=total_pv()
        pac,_=PROFILE_COLORS[pname]

        st.markdown(
            f"<div style='background:{CARD};border-radius:14px;border:1.5px solid {BORDER};"
            f"padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>"
            f"<div style='font-family:{FH};font-size:1.1rem;font-weight:700;'>Your profile: <span style='color:{pac};'>{pname}</span></div>"
            f"<div style='font-family:{FB};font-size:0.875rem;color:{MUTED};margin-top:4px;'>"
            f"Here's how your current investments compare to the ideal mix for a {pname} investor. "
            f"The gaps show where action is needed.</div></div>",
            unsafe_allow_html=True,
        )

        section_label("Current vs Target","📊")
        cur_pcts=[holdings.get(a,0)/total*100 for a in ASSET_NAMES]
        tgt_pcts=[tgts.get(a,0) for a in ASSET_NAMES]
        short_names=[a.split("&")[0].strip()[:14] for a in ASSET_NAMES]

        fig3=go.Figure()
        fig3.add_trace(go.Bar(name="What you have",x=short_names,y=cur_pcts,
            marker_color=WARNING,marker_line_width=0,
            hovertemplate="%{x}<br>You have: %{y:.1f}%<extra></extra>"))
        fig3.add_trace(go.Bar(name="Target",x=short_names,y=tgt_pcts,
            marker_color=PRIMARY,marker_line_width=0,
            hovertemplate="%{x}<br>Target: %{y:.1f}%<extra></extra>"))
        fig3.update_layout(
            barmode="group",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10,b=10,l=10,r=10),height=280,
            legend=dict(bgcolor="rgba(0,0,0,0)",borderwidth=0,
                font=dict(family="JetBrains Mono",size=10,color=MUTED),orientation="h",y=1.08),
            xaxis=dict(showgrid=False,tickfont=dict(family="JetBrains Mono",size=9,color=MUTED)),
            yaxis=dict(showgrid=True,gridcolor=BORDER,
                tickfont=dict(family="JetBrains Mono",size=9,color=MUTED),ticksuffix="%"),
            font=dict(family="Nunito, sans-serif",color=TEXT),
            bargap=0.25,bargroupgap=0.08)
        st.plotly_chart(fig3,use_container_width=True)

        section_label("Gap Breakdown","🔍")
        rows=[]; overs=[]; unders=[]
        for aname in ASSET_NAMES:
            cp=holdings.get(aname,0)/total*100; tp=tgts.get(aname,0)
            gap=cp-tp; cv=holdings.get(aname,0); tv=total*tp/100; dv=cv-tv
            ico=ASSET_ICONS[ASSET_NAMES.index(aname)]
            if gap>5:
                status=f"<span style='background:{D_SOFT};color:{DANGER};font-family:{FM};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:12px;'>▲ Over by {gap:.1f}%</span>"
                overs.append((aname,gap))
            elif gap<-5:
                status=f"<span style='background:{W_SOFT};color:{WARNING};font-family:{FM};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:12px;'>▼ Under by {abs(gap):.1f}%</span>"
                unders.append((aname,gap))
            else:
                status=f"<span style='background:{S_SOFT};color:{SUCCESS};font-family:{FM};font-size:0.72rem;font-weight:700;padding:2px 8px;border-radius:12px;'>✓ On target</span>"
            rows.append([f"{ico} {aname}",f"{cp:.1f}%",f"{tp:.0f}%",status,fmt(cv),fmt(tv),fmt(dv)])
        info_table(["Asset","You Have","Target","Status","Your Value","Target Value","Gap"],rows)

        if overs:
            b=max(overs,key=lambda x:x[1])
            tip(f"<strong>Too much in {b[0]}</strong> — you're {b[1]:.1f}% over your target. "
                f"This often happens when a strong-performing asset grows faster than the rest. "
                f"See Rebalancing to fix it.","warn")
        if unders:
            b=min(unders,key=lambda x:x[1])
            tip(f"<strong>Not enough in {b[0]}</strong> — you're {abs(b[1]):.1f}% below target. "
                f"Underweighting defensive assets leaves you more exposed to crashes than your "
                f"profile suggests. Direct your next contribution here first.","warn")
        if not overs and not unders:
            tip("Your portfolio is well-matched to your investor profile. Keep it up — just review every 3 months.","good")

        section_label("Side-by-Side","📍")
        col_l,col_r=st.columns(2,gap="large")
        with col_l:
            st.markdown(f"<div style='text-align:center;font-family:{FM};font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:{MUTED};margin-bottom:6px;'>What You Own</div>",unsafe_allow_html=True)
            a_act={k:v for k,v in holdings.items() if v>0}
            st.plotly_chart(donut(list(a_act.keys()),list(a_act.values()),[ASSET_COLORS[ASSET_NAMES.index(k)] for k in a_act],"Current"),use_container_width=True)
        with col_r:
            st.markdown(f"<div style='text-align:center;font-family:{FM};font-size:0.6rem;letter-spacing:0.1em;text-transform:uppercase;color:{MUTED};margin-bottom:6px;'>Target for {pname}</div>",unsafe_allow_html=True)
            t_act={k:v for k,v in tgts.items() if v>0}
            st.plotly_chart(donut(list(t_act.keys()),list(t_act.values()),[ASSET_COLORS[ASSET_NAMES.index(k)] for k in t_act],pname[:4]+"."),use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 4 — REBALANCING
# ══════════════════════════════════════════════════════════════
with tab4:
    if not p_done: tip("Complete the Risk Quiz first.","info")
    elif total_pv()==0: tip("Enter your holdings in My Portfolio first.","info")
    else:
        pname=st.session_state["risk_profile"]
        tgts=PROFILES[pname]["targets"]
        holdings=pv(); total=total_pv()

        st.markdown(
            f"<div style='background:{CARD};border-radius:14px;border:1.5px solid {BORDER};"
            f"padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>"
            f"<div style='font-family:{FH};font-size:1.1rem;font-weight:700;'>What should I buy and sell?</div>"
            f"<div style='font-family:{FB};font-size:0.875rem;color:{MUTED};margin-top:4px;'>"
            f"Rebalancing means trimming what's grown too big and adding to what's fallen behind. "
            f"The goal is keeping your portfolio in line with your risk profile — without guessing about markets.</div></div>",
            unsafe_allow_html=True,
        )

        section_label("Tax Settings","🧾")
        tip("These numbers are used to estimate how much tax you'd pay if you sell. Adjust them to match your situation.","info")
        cgt1,cgt2=st.columns(2,gap="large")
        with cgt1:
            st.session_state["cgt_rate"]=st.slider("Your tax rate (%)",0,47,int(st.session_state["cgt_rate"]),1)
        with cgt2:
            st.session_state["cost_base_pct"]=st.slider("Original cost as % of current value",20,100,int(st.session_state["cost_base_pct"]),5,
                help="If you paid $50k for something now worth $100k, set this to 50%")

        sells,buys,holds_l=[],[],[]
        for aname in ASSET_NAMES:
            cv=holdings.get(aname,0); cp=cv/total*100
            tp=tgts.get(aname,0); tv=total*tp/100; diff=cv-tv; gap=cp-tp
            if gap>2: sells.append((aname,diff,cp,tp))
            elif gap<-2: buys.append((aname,abs(diff),cp,tp))
            else: holds_l.append((aname,cp,tp))
        sells.sort(key=lambda x:x[1],reverse=True)
        buys.sort(key=lambda x:x[1],reverse=True)

        if sells:
            section_label("Trim These (Overweight)","🔴")
            for i,(aname,amount,cp,tp) in enumerate(sells):
                cgt_e=cgt_cost(amount,st.session_state["cost_base_pct"],st.session_state["cgt_rate"])
                net=amount-cgt_e
                action_card(aname,fmt(amount),cp,tp,"sell",
                    "Highest priority" if i==0 else "Secondary",
                    f"Est. tax: {fmt(cgt_e)}  ·  You keep: {fmt(net)}")

        if buys:
            section_label("Add to These (Underweight)","🟢")
            for i,(aname,amount,cp,tp) in enumerate(buys):
                action_card(aname,fmt(amount),cp,tp,"buy","Highest priority" if i==0 else "Secondary")

        if holds_l:
            section_label("Leave These Alone","⚪")
            hold_text=" &nbsp;·&nbsp; ".join(
                f"<span style='color:{SUCCESS};font-weight:700;'>✓</span> {a} ({c:.1f}%)"
                for a,c,_ in holds_l)
            st.markdown(f"<div style='font-family:{FB};font-size:0.875rem;color:{MUTED};padding:0.5rem 0;'>{hold_text}</div>",unsafe_allow_html=True)

        # Smart allocation
        st.markdown("---")
        section_label("Where Should My Next Investment Go?","💡")
        tip("The smartest way to rebalance is to put new money into underweight assets — no selling means no tax.","good")
        new_money=st.number_input("How much do you want to invest?",min_value=0,step=500,value=10000)
        if new_money>0:
            allocs=smart_allocate(new_money,holdings,tgts,total)
            alloc_rows=[]
            for aname,amount in allocs.items():
                if amount>0:
                    ico=ASSET_ICONS[ASSET_NAMES.index(aname)]
                    pct=amount/new_money*100
                    alloc_rows.append([f"{ico} {aname}",fmt(amount),f"{pct:.0f}%","Closes your gap"])
            if alloc_rows:
                info_table(["Where to Put It","Amount","% of Investment","Why"],alloc_rows)
                tip(f"Investing {fmt(new_money)} this way moves you closer to your target — with no selling and no tax.","good")
            else:
                tip("Your portfolio is already on target — spread your new money in line with your target weights.","good")

        # Summary table
        section_label("Full Action Plan","📋")
        total_cgt=0
        srows=[]
        for aname in ASSET_NAMES:
            cv=holdings.get(aname,0); cp=cv/total*100
            tp=tgts.get(aname,0); tv=total*tp/100; diff=tv-cv
            ico=ASSET_ICONS[ASSET_NAMES.index(aname)]
            if diff>500:
                act=f"<span style='color:{SUCCESS};font-weight:700;'>Buy {fmt(diff)}</span>"
                cgt_cell="—"
            elif diff<-500:
                cgt_e=cgt_cost(abs(diff),st.session_state["cost_base_pct"],st.session_state["cgt_rate"])
                total_cgt+=cgt_e
                act=f"<span style='color:{DANGER};font-weight:700;'>Sell {fmt(abs(diff))}</span>"
                cgt_cell=f"<span style='color:{WARNING};'>{fmt(cgt_e)}</span>"
            else:
                act=f"<span style='color:{MUTED};'>Hold</span>"
                cgt_cell="—"
            srows.append([f"{ico} {aname}",f"{cp:.1f}%",fmt(cv),f"{tp:.0f}%",fmt(tv),act,cgt_cell])
        info_table(["Asset","Have %","Value","Target %","Target Value","Action","Est. Tax"],srows)
        if total_cgt>0:
            tip(f"Total estimated tax on these sales: <strong>{fmt(total_cgt)}</strong>. "
                f"(Assumes 50% CGT discount for assets held 12+ months.) Confirm with your accountant.","warn")

        section_label("Important Tips","📌")
        for title,txt,kind in [
            ("Start with super 🏦","Selling inside super has no capital gains tax. Always rebalance in super first.","good"),
            ("Use new money first 💸","Adding to underweight assets with fresh contributions = no tax, less effort.","good"),
            ("Tax on selling outside super 🧾","If you sell shares held 12+ months, only half the profit is taxed. Shares held less than 12 months — all profit is taxed.","warn"),
            ("Don't over-trade 📅","Checking and tweaking monthly costs more than it helps. Review once a year, or if any asset drifts 10%+ off target.","info"),
        ]:
            with st.expander(title):
                tip(txt,kind)

# ══════════════════════════════════════════════════════════════
# TAB 5 — STRESS TEST
# ══════════════════════════════════════════════════════════════
with tab5:
    if not p_done: tip("Complete the Risk Quiz first.","info")
    elif total_pv()==0: tip("Enter your holdings in My Portfolio first.","info")
    else:
        holdings=pv(); total=total_pv()
        pname=st.session_state["risk_profile"]
        prof=PROFILES[pname]

        st.markdown(
            f"<div style='background:linear-gradient(135deg,{D_SOFT},{W_SOFT});border-radius:14px;"
            f"border:1.5px solid #FECACA;padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>"
            f"<div style='font-family:{FH};font-size:1.1rem;font-weight:700;color:{TEXT};'>What if markets crash?</div>"
            f"<div style='font-family:{FB};font-size:0.875rem;color:{MUTED};margin-top:4px;'>"
            f"Markets drop — it's inevitable. This tool shows you the actual dollar impact on your "
            f"portfolio in three real-world scenarios, and how long it would take to recover. "
            f"No panic, just facts.</div></div>",
            unsafe_allow_html=True,
        )

        section_label("Choose a Scenario","🎭")
        scen_name=st.radio("",list(STRESS_SCENARIOS.keys()),horizontal=True,label_visibility="collapsed")
        scenario=STRESS_SCENARIOS[scen_name]
        new_total,net_loss,breakdown=stress_test(holdings,total,scenario)
        pct_loss=abs(net_loss)/total*100 if total>0 else 0

        st.markdown(
            f"<div style='background:{D_SOFT};border-radius:14px;border:1.5px solid #FECACA;"
            f"padding:1.5rem 1.8rem;margin:1rem 0;'>"
            f"<div style='font-family:{FH};font-size:1.4rem;font-weight:800;color:{DANGER};margin-bottom:0.4rem;'>"
            f"{scenario['headline']}</div>"
            f"<div style='font-family:{FB};font-size:0.9rem;color:{TEXT};line-height:1.65;'>{scenario['desc']}</div></div>",
            unsafe_allow_html=True,
        )

        metric_cards([
            ("💼","Your Portfolio Now",fmt(total),"Before the crash",PRIMARY),
            ("📉","Estimated Loss",fmt(net_loss),f"−{pct_loss:.1f}% of your total",DANGER),
            ("🏁","Portfolio After",fmt(new_total),"Approximate value post-crash",WARNING),
            ("⏰","Est. Recovery Time",f"~{scenario['recovery_years']:.0f} yrs",f"At {prof['ret_mid']*100:.0f}% p.a. growth",SUCCESS),
        ])

        section_label("Impact by Asset","💥")
        impact_rows=[]
        bar_a,bar_v,bar_c=[],[],[]
        for aname in ASSET_NAMES:
            val=holdings.get(aname,0)
            if val==0: continue
            delta=breakdown.get(aname,0)
            shock=scenario["shocks"].get(aname,0)
            ico=ASSET_ICONS[ASSET_NAMES.index(aname)]
            clr2=DANGER if delta<0 else SUCCESS
            delta_str=(
                f"<span style='color:{DANGER};font-weight:700;'>{fmt(delta)}</span>"
                if delta<0 else
                f"<span style='color:{SUCCESS};font-weight:700;'>+{fmt(delta)}</span>"
            )
            impact_rows.append([f"{ico} {aname}",fmt(val),f"{shock*100:+.0f}%",fmt(val+delta),delta_str])
            bar_a.append(aname.split(" ")[0]); bar_v.append(delta); bar_c.append(clr2)
        info_table(["Asset","Before","Shock","After","Change"],impact_rows)

        fig_bar=go.Figure()
        fig_bar.add_trace(go.Bar(x=bar_a,y=bar_v,marker_color=bar_c,marker_line_width=0,
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10,b=10,l=10,r=10),height=220,showlegend=False,
            xaxis=dict(showgrid=False,tickfont=dict(family="JetBrains Mono",size=9,color=MUTED)),
            yaxis=dict(showgrid=True,gridcolor=BORDER,tickfont=dict(family="JetBrains Mono",size=9,color=MUTED),tickprefix=sym()),
            font=dict(family="Nunito, sans-serif",color=TEXT))
        st.plotly_chart(fig_bar,use_container_width=True)

        section_label("Recovery Timeline","📈")
        tip("This shows how long each crash type would take to recover from — assuming your portfolio grows at your profile's expected rate with no new contributions.","info")
        years_x=list(range(16))
        fig_rec=go.Figure()
        fig_rec.add_hline(y=total,line_dash="dash",line_color=PRIMARY,line_width=2,
            annotation_text="Your current value",annotation_font=dict(family="JetBrains Mono",size=9,color=PRIMARY))
        rec_clrs=[SUCCESS,WARNING,DANGER]
        for (sn,sc),rc in zip(STRESS_SCENARIOS.items(),rec_clrs):
            shock_loss=sum(holdings.get(a,0)*sc["shocks"].get(a,0) for a in ASSET_NAMES)
            crashed=total+shock_loss
            vals=[crashed*(1+prof["ret_mid"])**y for y in years_x]
            fig_rec.add_trace(go.Scatter(x=years_x,y=vals,mode="lines",name=sn.split("  ")[0],
                line=dict(color=rc,width=2),hovertemplate="Year %{x}<br>%{y:,.0f}<extra></extra>"))
        fig_rec.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10,b=10,l=10,r=10),height=280,
            legend=dict(bgcolor="rgba(0,0,0,0)",borderwidth=0,font=dict(family="JetBrains Mono",size=9,color=MUTED),orientation="h",y=1.08),
            xaxis=dict(title="Years after crash",showgrid=False,tickfont=dict(family="JetBrains Mono",size=9,color=MUTED)),
            yaxis=dict(showgrid=True,gridcolor=BORDER,tickfont=dict(family="JetBrains Mono",size=9,color=MUTED),tickprefix=sym()),
            font=dict(family="Nunito, sans-serif",color=TEXT))
        st.plotly_chart(fig_rec,use_container_width=True)

        if pct_loss>prof["draw_mid"]*100*1.3:
            tip(f"Your portfolio would drop <strong>{pct_loss:.0f}%</strong> in this scenario — more than expected for a {pname} investor ({prof['draw']}). Your allocation might be carrying more risk than you realise. Check the Rebalancing tab.","alert")
        elif pct_loss<prof["draw_mid"]*100*0.7:
            tip(f"Your defensive holdings do a great job in this scenario. Your drop of <strong>{pct_loss:.1f}%</strong> is less than the typical {pname} investor — that's your bonds and cash doing their job.","good")
        else:
            tip(f"Your estimated drop of <strong>{fmt(abs(net_loss))}</strong> ({pct_loss:.1f}%) fits what you'd expect from a {pname} portfolio. Recovery is projected in about {scenario['recovery_years']:.0f} year(s).","info")

# ══════════════════════════════════════════════════════════════
# TAB 6 — GOAL PROJECTIONS
# ══════════════════════════════════════════════════════════════
with tab6:
    if not p_done: tip("Complete the Risk Quiz first.","info")
    else:
        pname=st.session_state["risk_profile"]
        prof=PROFILES[pname]; total=total_pv()
        pac,pbg=PROFILE_COLORS[pname]

        st.markdown(
            f"<div style='background:linear-gradient(135deg,{PU_SOFT},{P_SOFT});border-radius:14px;"
            f"border:1.5px solid #DDD6FE;padding:1.2rem 1.5rem;margin-bottom:1.5rem;'>"
            f"<div style='font-family:{FH};font-size:1.1rem;font-weight:700;color:{TEXT};'>Will I reach my goal?</div>"
            f"<div style='font-family:{FB};font-size:0.875rem;color:{MUTED};margin-top:4px;'>"
            f"We run 1,000 different 'what-if' scenarios using your investor profile's expected returns "
            f"and show you the range of likely outcomes. Not a crystal ball — but the closest thing to it.</div></div>",
            unsafe_allow_html=True,
        )

        section_label("Your Numbers","🔢")
        gc1,gc2,gc3=st.columns(3,gap="large")
        with gc1:
            goal_amount=st.number_input("I want to reach",min_value=0,step=50_000,value=int(st.session_state["goal_amount"]))
            st.session_state["goal_amount"]=goal_amount
        with gc2:
            goal_years=st.slider("In how many years?",1,40,int(st.session_state["goal_years"]),1)
            st.session_state["goal_years"]=goal_years
        with gc3:
            monthly_contrib=st.number_input("I'll add each month",min_value=0,step=250,value=int(st.session_state["monthly_contrib"]))
            st.session_state["monthly_contrib"]=monthly_contrib

        start=total if total>0 else 0
        if start==0 and monthly_contrib==0:
            tip("Enter your current portfolio value (My Portfolio tab) or a monthly contribution amount to run projections.","info")
        else:
            with st.spinner("Running 1,000 simulations…"):
                p10,p25,p50,p75,p90,yr_med,yr_p10,yr_p90=monte_carlo(start,monthly_contrib,goal_years,pname,1000)

            # Probability
            if p90<goal_amount:     prob,pclr="Under 10%",DANGER
            elif p75<goal_amount:   prob,pclr="10–25%",DANGER
            elif p50<goal_amount:   prob,pclr="25–50%",WARNING
            elif p25<goal_amount:   prob,pclr="50–75%",SUCCESS
            elif p10<goal_amount:   prob,pclr="75–90%",SUCCESS
            else:                   prob,pclr="Over 90%",SUCCESS

            total_in=start+monthly_contrib*goal_years*12
            section_label("Projection Results","🎯")
            metric_cards([
                ("🏁","Starting Value",fmt(start),"Your portfolio today",PRIMARY),
                ("💸","Total You'll Put In",fmt(total_in),f"{fmt(monthly_contrib)}/mo × {goal_years}yrs",MUTED),
                ("📊","Most Likely Outcome",fmt(p50),"Median of 1,000 simulations",pac),
                ("🎯","Chance of Reaching Goal",prob,f"Target: {fmt(goal_amount)}",pclr),
            ])

            # Fan chart
            section_label("Projection Chart","📈")
            yrs=list(range(goal_years+1))
            fig_mc=go.Figure()
            fig_mc.add_trace(go.Scatter(
                x=yrs+yrs[::-1],y=[yr_p90[y] for y in yrs]+[yr_p10[y] for y in yrs][::-1],
                fill="toself",fillcolor=f"rgba(67,97,238,0.10)",
                line=dict(color="rgba(0,0,0,0)"),name="10th–90th range",hoverinfo="skip"))
            fig_mc.add_trace(go.Scatter(x=yrs,y=[yr_med[y] for y in yrs],
                mode="lines",name="Most likely",line=dict(color=PRIMARY,width=3),
                hovertemplate="Year %{x}<br>Median: %{y:,.0f}<extra></extra>"))
            fig_mc.add_trace(go.Scatter(x=yrs,y=[yr_p10[y] for y in yrs],
                mode="lines",name="Pessimistic (10th)",line=dict(color=DANGER,width=1.5,dash="dot"),
                hovertemplate="Year %{x}<br>10th: %{y:,.0f}<extra></extra>"))
            fig_mc.add_trace(go.Scatter(x=yrs,y=[yr_p90[y] for y in yrs],
                mode="lines",name="Optimistic (90th)",line=dict(color=SUCCESS,width=1.5,dash="dot"),
                hovertemplate="Year %{x}<br>90th: %{y:,.0f}<extra></extra>"))
            if goal_amount>0:
                fig_mc.add_hline(y=goal_amount,line_dash="dash",line_color=PURPLE,line_width=2,
                    annotation_text=f"Your goal: {fmt(goal_amount)}",
                    annotation_font=dict(family="JetBrains Mono",size=10,color=PURPLE))
            fig_mc.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10,b=10,l=10,r=10),height=360,
                legend=dict(bgcolor="rgba(0,0,0,0)",borderwidth=0,
                    font=dict(family="JetBrains Mono",size=9,color=MUTED),orientation="h",y=1.08),
                xaxis=dict(title="Years from now",showgrid=False,tickfont=dict(family="JetBrains Mono",size=9,color=MUTED)),
                yaxis=dict(showgrid=True,gridcolor=BORDER,tickfont=dict(family="JetBrains Mono",size=9,color=MUTED),tickprefix=sym()),
                font=dict(family="Nunito, sans-serif",color=TEXT))
            st.plotly_chart(fig_mc,use_container_width=True)

            section_label("Outcomes at Year " + str(goal_years),"📋")
            info_table(["Scenario","Portfolio Value","What It Means"],[
                ["🟢 Best case (top 10%)",  fmt(p90),"Only 1 in 10 scenarios beat this"],
                ["📈 Good (top 25%)",       fmt(p75),"Better than 3 in 4 scenarios"],
                ["📊 Most likely (median)", fmt(p50),"The middle outcome of all simulations"],
                ["📉 Tough (bottom 25%)",   fmt(p25),"Worse than 3 in 4 scenarios"],
                ["🔴 Worst case (bottom 10%)",fmt(p10),"Only 1 in 10 scenarios fall below this"],
            ])

            section_label("What If I Contributed More?","💸")
            tip("Increasing monthly contributions often has more impact than chasing higher returns.","info")
            sens_rows=[]
            for extra in [0,500,1000,2000,3000]:
                _,_,sp50,_,_,_,_,_=monte_carlo(start,monthly_contrib+extra,goal_years,pname,500)
                hit=sp50>=goal_amount
                clr2=SUCCESS if hit else DANGER
                sens_rows.append([
                    f"+{fmt(extra)}/mo" if extra>0 else "Current plan",
                    fmt(monthly_contrib+extra)+"/mo",
                    fmt(sp50),
                    f"<span style='color:{clr2};font-weight:700;'>{'✓ Reaches' if hit else '✗ Misses'} goal</span>"
                ])
            info_table(["Scenario","Monthly Contribution","Median Outcome","Goal Status"],sens_rows)

            if pclr==SUCCESS:
                tip(f"You're on track! Your plan has a strong chance of reaching <strong>{fmt(goal_amount)}</strong>. "
                    f"Stay consistent — don't try to time the market. Every month in counts.","good")
            elif pclr==WARNING:
                gap=goal_amount-p50
                extra=gap/(goal_years*12) if goal_years>0 else 0
                tip(f"You're close but not quite there. Your median outcome is <strong>{fmt(p50)}</strong> — "
                    f"about <strong>{fmt(gap)}</strong> short of your goal. "
                    f"Adding <strong>{fmt(extra)}/month</strong> could close that gap.","warn")
            else:
                tip(f"Under your current plan, reaching <strong>{fmt(goal_amount)}</strong> in {goal_years} years is unlikely. "
                    f"Try: increasing contributions, extending your timeline, or (carefully) considering a higher-risk profile.","alert")

# ───────────────────────────────────────────────────────────────
# FOOTER
# ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='background:{CARD};border-radius:14px;border:1.5px solid {BORDER};"
    f"padding:1.5rem 2rem;text-align:center;margin-top:1rem;'>"
    f"<div style='font-size:1.5rem;margin-bottom:0.5rem;'>💎</div>"
    f"<div style='font-family:{FH};font-size:1rem;font-weight:700;color:{TEXT};margin-bottom:0.3rem;'>Meridian</div>"
    f"<div style='font-family:{FB};font-size:0.8rem;color:{MUTED};line-height:1.8;'>"
    f"For education only — not personal financial advice.<br>"
    f"Always check with a licensed financial adviser (AFSL) before investing.</div></div>",
    unsafe_allow_html=True,
)
