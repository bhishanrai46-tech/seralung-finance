"""
Meridian — Investment Risk & Portfolio Guide  v4
Run:  streamlit run meridian_app.py
Deps: streamlit plotly
"""
import math, random
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Meridian", layout="wide",
                   initial_sidebar_state="collapsed")

# ── TOKENS ────────────────────────────────────────────────────
BG      = "#F5F5F5"
CARD    = "#FFFFFF"
BD      = "#E4E4E7"   # border
TEXT    = "#18181B"
MUTED   = "#71717A"
DIM     = "#A1A1AA"

BLUE    = "#2563EB";  BLUE_S  = "#EFF6FF"
GREEN   = "#16A34A";  GREEN_S = "#F0FDF4"
AMBER   = "#B45309";  AMBER_S = "#FFFBEB"
RED     = "#DC2626";  RED_S   = "#FEF2F2"
PURPLE  = "#7C3AED";  PURPLE_S= "#F5F3FF"

FH = "'Plus Jakarta Sans', system-ui, sans-serif"
FM = "'JetBrains Mono', 'Fira Code', monospace"

ASSET_NAMES  = ["Australian Shares","International Shares","Property & REITs",
                "Fixed Income & Bonds","Cash & Term Deposits"]
ASSET_KEYS   = ["aus_shares","intl_shares","property_reits","fixed_income","cash_td"]
ASSET_CLR    = [BLUE,"#059669",AMBER,PURPLE,"#0891B2"]
CUR_SYM      = {"AUD":"A$","USD":"$","EUR":"€","GBP":"£","SGD":"S$"}

PROFILE_CLR = {
    "Conservative":           GREEN,
    "Moderately Conservative":"#0284C7",
    "Balanced":               BLUE,
    "Growth":                 PURPLE,
    "Aggressive":             RED,
}

# ── SESSION ───────────────────────────────────────────────────
_d = {**{f"q{i}":0 for i in range(1,11)},
      "risk_score":0,"risk_profile":"","profile_done":False,
      "aus_shares":0,"intl_shares":0,"property_reits":0,
      "fixed_income":0,"cash_td":0,"currency":"AUD",
      "goal_amount":1_000_000,"goal_years":20,"monthly_contrib":2_000,
      "cgt_rate":32,"cost_base_pct":60}
for k,v in _d.items():
    if k not in st.session_state: st.session_state[k]=v

# ── QUESTIONS ─────────────────────────────────────────────────
QUESTIONS = [
    ("When do you expect to need this money?",
     ["Under 3 years","3–7 years","7–15 years","15+ years"],
     "Longer timelines let you ride out downturns. Shorter timelines demand more caution — markets don't always cooperate with your schedule."),
    ("How stable is your income?",
     ["Retired / fixed income","Variable / self-employed","Stable salary","Very secure (government / tenured)"],
     "Stable income means you can hold through a crash without selling. Unstable income might force you to liquidate at the worst moment."),
    ("Months of living expenses in accessible cash?",
     ["Less than 1 month","1–3 months","3–6 months","6+ months"],
     "Without a cash buffer you risk selling investments in emergencies. This single gap has derailed more portfolios than bad stock picks."),
    ("How would you describe your investment experience?",
     ["None — mostly savings accounts","Basic — shares and funds","3+ years active investing","10+ years, multiple asset classes"],
     "Experience shapes discipline. Knowing how you actually behaved in 2008 or March 2020 is more reliable than how you think you'd behave."),
    ("If your portfolio fell 30% in 3 months, you would:",
     ["Sell everything","Sell part of it","Hold and wait","Buy more at lower prices"],
     "Be honest. A 30% drop happened in 2008 and 2020. It will happen again. What you actually do in that moment determines your long-term outcome."),
    ("Primary goal for this investment?",
     ["Protect capital — safety first","Modest growth, capital protection priority","Balanced growth over the long term","Maximum growth — volatility is fine"],
     "Your goal sets the entire strategy. A retiree drawing income and a 30-year-old accumulating wealth need fundamentally different portfolios."),
    ("Will you need significant withdrawals within 5 years?",
     ["Yes — most of it","Yes — a meaningful portion","Maybe — small amounts only","No — fully committed long-term"],
     "Money you'll need within 5 years shouldn't be in equities. A crash right before withdrawal is the scenario that hurts most."),
    ("Current debt situation?",
     ["High — relative to income","Moderate — standard mortgage","Low — actively reducing","Debt free"],
     "Paying off 20% credit card debt is a guaranteed 20% return. High-interest debt usually beats any investment return short-term."),
    ("This portfolio is what share of your total net worth?",
     ["Over 75%","50–75%","25–50%","Under 25%"],
     "If this is most of what you own, caution is warranted regardless of other answers. Concentration risk applies across your whole balance sheet."),
    ("Maximum annual loss you could absorb without lifestyle impact?",
     ["Under 5%","5–15%","15–25%","25%+"],
     "Translate this to dollars before answering. Percentages are abstract; a dollar figure on your statement is not. When in doubt, take the safer option."),
]

# ── PROFILES ──────────────────────────────────────────────────
PROFILES = {
    "Conservative":{
        "range":(10,18),"ret":"3–5% p.a.","ret_mid":0.04,
        "draw":"5–10%","draw_mid":0.075,"horizon":"1–5 years","vol":0.05,
        "headline":"Capital preservation. Safety over returns.",
        "desc":"Predominantly bonds and cash with a small equity allocation. Minimal drawdown risk, lower return ceiling. Right for short horizons or low risk tolerance.",
        "targets":{"Australian Shares":8,"International Shares":12,"Property & REITs":5,"Fixed Income & Bonds":45,"Cash & Term Deposits":30}},
    "Moderately Conservative":{
        "range":(19,25),"ret":"4–6% p.a.","ret_mid":0.05,
        "draw":"10–15%","draw_mid":0.125,"horizon":"3–7 years","vol":0.08,
        "headline":"Steady growth with a strong defensive base.",
        "desc":"Fixed income dominates. A measured equity allocation adds inflation-beating returns without significant downside risk.",
        "targets":{"Australian Shares":15,"International Shares":20,"Property & REITs":10,"Fixed Income & Bonds":40,"Cash & Term Deposits":15}},
    "Balanced":{
        "range":(26,31),"ret":"5–8% p.a.","ret_mid":0.065,
        "draw":"15–25%","draw_mid":0.20,"horizon":"5–10 years","vol":0.11,
        "headline":"Equal weight on growth and protection.",
        "desc":"The 60/40 model — proven over decades. Equities drive returns; bonds cushion corrections. Accepts short-term volatility for long-term gains.",
        "targets":{"Australian Shares":25,"International Shares":30,"Property & REITs":15,"Fixed Income & Bonds":22,"Cash & Term Deposits":8}},
    "Growth":{
        "range":(32,36),"ret":"7–10% p.a.","ret_mid":0.08,
        "draw":"25–35%","draw_mid":0.30,"horizon":"7–15 years","vol":0.15,
        "headline":"Long-term wealth accumulation. Volatility accepted.",
        "desc":"Equity-heavy with a small defensive buffer. Drawdowns of 25–35% are expected and temporary. Requires patience and a long runway.",
        "targets":{"Australian Shares":30,"International Shares":40,"Property & REITs":15,"Fixed Income & Bonds":12,"Cash & Term Deposits":3}},
    "Aggressive":{
        "range":(37,40),"ret":"8–12% p.a.","ret_mid":0.09,
        "draw":"35–50%","draw_mid":0.425,"horizon":"15+ years","vol":0.19,
        "headline":"Maximum long-term growth. High tolerance required.",
        "desc":"Near-full equity exposure. Suitable for very long horizons, stable income, and investors with demonstrated ability to hold through severe corrections.",
        "targets":{"Australian Shares":35,"International Shares":45,"Property & REITs":15,"Fixed Income & Bonds":5,"Cash & Term Deposits":0}},
}

STRESS = {
    "Correction  -15%":{
        "label":"-15%  Correction",
        "desc":"Typical pullback. Occurs every 3–5 years on average. Recovery within 6–18 months historically.",
        "rec":1.0,
        "shocks":{"Australian Shares":-0.18,"International Shares":-0.16,"Property & REITs":-0.11,"Fixed Income & Bonds":+0.03,"Cash & Term Deposits":0.0}},
    "Bear Market  -30%":{
        "label":"-30%  Bear Market",
        "desc":"COVID March 2020 / 2022 rate shock level. Recovery typically 1–3 years. Defensive assets absorb meaningful impact.",
        "rec":2.5,
        "shocks":{"Australian Shares":-0.33,"International Shares":-0.30,"Property & REITs":-0.22,"Fixed Income & Bonds":+0.06,"Cash & Term Deposits":0.0}},
    "GFC Crash  -50%":{
        "label":"-50%  GFC-Level Crash",
        "desc":"2008–09 scenario. ASX fell 54% peak-to-trough; full recovery took ~5 years. Rare but within historical range.",
        "rec":5.0,
        "shocks":{"Australian Shares":-0.54,"International Shares":-0.50,"Property & REITs":-0.42,"Fixed Income & Bonds":+0.09,"Cash & Term Deposits":0.0}},
}

# ── HELPERS ───────────────────────────────────────────────────
def sym():   return CUR_SYM.get(st.session_state["currency"],"$")
def pv():    return {n:st.session_state[k] for n,k in zip(ASSET_NAMES,ASSET_KEYS)}
def tpv():   return sum(st.session_state[k] for k in ASSET_KEYS)
def gprof(s):
    for n,d in PROFILES.items():
        if d["range"][0]<=s<=d["range"][1]: return n
    return "Balanced"

def fmt(n):
    if n is None: return f"{sym()}0"
    s=sym(); sg="−" if n<0 else ""; n=abs(n)
    if n>=1_000_000: return f"{sg}{s}{n/1e6:.2f}M"
    if n>=1_000:     return f"{sg}{s}{n:,.0f}"
    return f"{sg}{s}{n:.0f}"

def health(h,t,total):
    if not total: return 0,0,0,0
    gaps=[abs(h.get(a,0)/total*100-t.get(a,0)) for a in ASSET_NAMES]
    align=max(0.0,40.0-sum(gaps)/len(gaps)*2.2)
    pcts=[h.get(a,0)/total*100 for a in ASSET_NAMES]
    nm=sum(1 for p in pcts if p>=2)
    divers=max(0.0,min(30.0,nm*6.0)-max(0.0,(max(pcts)-50)*0.55))
    cd=(h.get("Cash & Term Deposits",0)+h.get("Fixed Income & Bonds",0))/total*100
    td=t.get("Cash & Term Deposits",0)+t.get("Fixed Income & Bonds",0)
    liq=max(0.0,30.0-abs(cd-td)*1.4)
    tot=align+divers+liq
    return round(tot),round(align),round(divers),round(liq)

def stress_run(h,total,sc):
    sh=sc["shocks"]; nt=0.0; bd={}
    for a in ASSET_NAMES:
        v=h.get(a,0); sv=v*(1+sh.get(a,0)); nt+=sv; bd[a]=sv-v
    return nt,nt-total,bd

def monte_carlo(cur,mo,yrs,pname,n=1000):
    P={"Conservative":(0.040,0.050),"Moderately Conservative":(0.050,0.080),
       "Balanced":(0.065,0.110),"Growth":(0.080,0.150),"Aggressive":(0.090,0.190)}
    mu,sig=P.get(pname,(0.065,0.110))
    mm=mu/12; ms=sig/math.sqrt(12)
    random.seed(42)
    ydata=[[float(cur)]*n for _ in range(yrs+1)]
    for s in range(n):
        v=float(cur)
        for yr in range(1,yrs+1):
            for _ in range(12): v=max(0.0,v*(1+random.gauss(mm,ms))+mo)
            ydata[yr][s]=v
    finals=sorted(ydata[yrs])
    p=lambda x:finals[max(0,int(x*n)-1)]
    ym={y:sorted(ydata[y])[n//2] for y in range(yrs+1)}
    yp10={y:sorted(ydata[y])[max(0,int(0.1*n)-1)] for y in range(yrs+1)}
    yp90={y:sorted(ydata[y])[min(n-1,int(0.9*n))] for y in range(yrs+1)}
    return p(.10),p(.25),p(.50),p(.75),p(.90),ym,yp10,yp90

def smart_alloc(money,h,t,total):
    pt=total+money; needs={}
    for a in ASSET_NAMES:
        g=pt*t.get(a,0)/100-h.get(a,0)
        if g>0: needs[a]=g
    if not needs: return {a:0 for a in ASSET_NAMES}
    tn=sum(needs.values()); res={}; run=0
    items=list(needs.items())
    for i,(a,g) in enumerate(items):
        if i==len(items)-1: res[a]=money-run
        else:
            al=round(money*g/tn/100)*100; res[a]=al; run+=al
    return res

def cgt(sell,cb,rate): return max(0.0,sell-sell*cb/100)*0.5*rate/100

# ── CSS ───────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html,body,.stApp,[data-testid="stAppViewContainer"]{{
  background:{BG}!important; font-family:{FH}; color:{TEXT};
}}
.block-container{{ padding:1.2rem 1.8rem 3rem; max-width:1080px; }}
#MainMenu,footer,header{{visibility:hidden;}}
.stDeployButton{{display:none!important;}}
*{{box-sizing:border-box;}}

/* typography */
h1,h2,h3,h4{{ font-family:{FH}!important; font-weight:600!important; color:{TEXT}!important; margin:0!important;}}
p,span,li,div{{ color:{TEXT}; }}

/* tabs */
.stTabs [data-baseweb="tab-list"]{{
  gap:0; border-bottom:1px solid {BD}; background:transparent; padding:0;
}}
.stTabs [data-baseweb="tab"]{{
  font-family:{FM}; font-size:0.68rem; letter-spacing:0.06em; text-transform:uppercase;
  color:{MUTED}; background:transparent; border:none;
  border-bottom:2px solid transparent; padding:8px 16px; margin:0;
}}
.stTabs [aria-selected="true"]{{
  color:{TEXT}!important; border-bottom:2px solid {TEXT}!important;
  background:transparent!important; font-weight:500!important;
}}
.stTabs [data-baseweb="tab-highlight"]{{ display:none!important; }}
.stTabs [data-baseweb="tab-panel"]{{ padding-top:1.2rem; background:transparent; }}

/* inputs */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label{{
  font-family:{FM}!important; font-size:0.62rem!important;
  letter-spacing:0.08em!important; text-transform:uppercase!important; color:{MUTED}!important;
}}
.stNumberInput input{{
  background:{CARD}!important; border:1px solid {BD}!important;
  border-radius:6px!important; color:{TEXT}!important;
  font-family:{FM}!important; font-size:0.88rem!important; padding:6px 10px!important;
}}
.stNumberInput input:focus{{ border-color:{BLUE}!important; outline:none!important;
  box-shadow:0 0 0 3px {BLUE_S}!important; }}
.stNumberInput button{{ background:{CARD}!important; border-color:{BD}!important; border-radius:4px!important; }}
.stSelectbox>div>div{{
  background:{CARD}!important; border:1px solid {BD}!important;
  border-radius:6px!important; font-family:{FM}!important; font-size:0.85rem!important;
}}
[role="listbox"]*,[role="option"]{{
  background:{CARD}!important; color:{TEXT}!important; font-family:{FH}!important;
}}

/* radio */
.stRadio>div>label{{
  font-family:{FH}!important; font-size:0.875rem!important;
  color:{TEXT}!important; font-weight:400!important; line-height:1.5!important;
}}
div[data-testid="stRadio"]>label{{
  font-family:{FM}!important; font-size:0.6rem!important;
  letter-spacing:0.1em!important; text-transform:uppercase!important; color:{MUTED}!important;
}}

/* button */
.stButton>button{{
  background:{TEXT}!important; color:#fff!important;
  border:none!important; border-radius:6px!important;
  font-family:{FH}!important; font-size:0.85rem!important; font-weight:600!important;
  padding:8px 20px!important; letter-spacing:0!important;
  box-shadow:none!important; transition:opacity .15s!important;
}}
.stButton>button:hover{{ opacity:0.8!important; }}

/* slider */
.stSlider label{{
  font-family:{FM}!important; font-size:0.62rem!important;
  letter-spacing:0.08em!important; text-transform:uppercase!important; color:{MUTED}!important;
}}

/* expander */
div[data-testid="stExpander"]{{
  background:{CARD}!important; border:1px solid {BD}!important;
  border-radius:8px!important; box-shadow:none!important;
}}
div[data-testid="stExpander"] summary span{{
  font-family:{FH}!important; font-size:0.85rem!important;
  font-weight:500!important; color:{TEXT}!important;
}}

hr{{ border:none; border-top:1px solid {BD}; margin:1rem 0; }}
</style>
""", unsafe_allow_html=True)

# ── COMPONENTS ────────────────────────────────────────────────
def note(text, kind="info"):
    cfg = {"info":(BLUE_S,BLUE),"good":(GREEN_S,GREEN),
           "warn":(AMBER_S,AMBER),"alert":(RED_S,RED)}
    bg,ac=cfg.get(kind,cfg["info"])
    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {ac};border-radius:0 6px 6px 0;"
        f"padding:8px 12px;margin:6px 0;font-family:{FH};font-size:0.85rem;"
        f"color:{TEXT};line-height:1.55;'>{text}</div>",
        unsafe_allow_html=True)

def sec(label):
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:8px;margin:18px 0 10px;'>"
        f"<span style='font-family:{FM};font-size:0.6rem;letter-spacing:0.12em;"
        f"text-transform:uppercase;color:{MUTED};white-space:nowrap;'>{label}</span>"
        f"<div style='flex:1;height:1px;background:{BD};'></div></div>",
        unsafe_allow_html=True)

def kpis(cards):
    cols=st.columns(len(cards),gap="small")
    for col,(lbl,val,sub,ac) in zip(cols,cards):
        with col:
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BD};border-radius:8px;"
                f"padding:12px 14px;min-width:0;'>"
                f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;"
                f"text-transform:uppercase;color:{MUTED};margin-bottom:4px;"
                f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{lbl}</div>"
                f"<div style='font-family:{FM};font-size:1.15rem;color:{ac};"
                f"font-weight:500;line-height:1.2;word-break:break-word;"
                f"overflow-wrap:break-word;max-width:100%;'>{val}</div>"
                f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};"
                f"margin-top:3px;line-height:1.4;overflow-wrap:break-word;'>{sub}</div>"
                f"</div>",
                unsafe_allow_html=True)

def tbl(headers, rows):
    hdr="".join(
        f"<th style='text-align:left;padding:6px 10px;background:{BG};"
        f"font-family:{FM};font-size:0.58rem;text-transform:uppercase;"
        f"letter-spacing:0.08em;color:{MUTED};font-weight:500;"
        f"white-space:nowrap;border-bottom:1px solid {BD};'>{h}</th>"
        for h in headers)
    body=""
    for i,row in enumerate(rows):
        bg=CARD if i%2==0 else BG
        cells="".join(
            f"<td style='padding:7px 10px;font-family:{FH};font-size:0.82rem;"
            f"color:{TEXT};background:{bg};border-bottom:1px solid {BD};"
            f"word-break:break-word;overflow-wrap:break-word;max-width:200px;'>{c}</td>"
            for c in row)
        body+=f"<tr>{cells}</tr>"
    st.markdown(
        f"<div style='border:1px solid {BD};border-radius:8px;overflow:hidden;"
        f"overflow-x:auto;margin:6px 0 14px;'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr>{hdr}</tr></thead><tbody>{body}</tbody></table></div>",
        unsafe_allow_html=True)

def donut(labels,values,colors,center=""):
    fig=go.Figure(go.Pie(
        labels=labels,values=values,hole=0.64,
        marker=dict(colors=colors,line=dict(color="#fff",width=2)),
        textinfo="label+percent",
        textfont=dict(family="Plus Jakarta Sans, sans-serif",size=10,color=TEXT),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=8,b=8,l=8,r=8),height=240,showlegend=False,
        annotations=[dict(text=center,x=0.5,y=0.5,
            font=dict(size=12,family="JetBrains Mono",color=TEXT),
            showarrow=False)] if center else [])
    return fig

def bar_chart(x,y_cur,y_tgt):
    fig=go.Figure()
    fig.add_trace(go.Bar(name="Current",x=x,y=y_cur,marker_color=AMBER,
        marker_line_width=0,hovertemplate="%{x}<br>Current: %{y:.1f}%<extra></extra>"))
    fig.add_trace(go.Bar(name="Target",x=x,y=y_tgt,marker_color=BLUE,
        marker_line_width=0,hovertemplate="%{x}<br>Target: %{y:.1f}%<extra></extra>"))
    fig.update_layout(
        barmode="group",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=8,b=8,l=8,r=8),height=240,
        legend=dict(bgcolor="rgba(0,0,0,0)",borderwidth=0,orientation="h",y=1.1,
            font=dict(family="JetBrains Mono",size=9,color=MUTED)),
        xaxis=dict(showgrid=False,tickfont=dict(family="JetBrains Mono",size=8,color=MUTED)),
        yaxis=dict(showgrid=True,gridcolor=BD,
            tickfont=dict(family="JetBrains Mono",size=8,color=MUTED),ticksuffix="%"),
        bargap=0.22,bargroupgap=0.06)
    return fig

def action_card(title,amount,cur_pct,tgt_pct,kind,priority,extra=""):
    ac=RED if kind=="sell" else GREEN
    bg=RED_S if kind=="sell" else GREEN_S
    verb="Sell" if kind=="sell" else "Buy"
    st.markdown(
        f"<div style='background:{CARD};border:1px solid {BD};border-radius:8px;"
        f"border-left:3px solid {ac};padding:10px 14px;margin-bottom:6px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"gap:8px;flex-wrap:wrap;'>"
        f"<span style='font-family:{FH};font-size:0.9rem;font-weight:600;"
        f"color:{TEXT};min-width:0;overflow-wrap:break-word;'>{title}</span>"
        f"<span style='background:{bg};color:{ac};font-family:{FM};font-size:0.82rem;"
        f"font-weight:500;padding:2px 10px;border-radius:4px;white-space:nowrap;'>"
        f"{verb} {amount}</span></div>"
        f"<div style='font-family:{FM};font-size:0.72rem;color:{MUTED};margin-top:4px;'>"
        f"{cur_pct:.1f}% → {tgt_pct:.0f}%"
        f"{'   |   '+extra if extra else ''}</div>"
        f"{'<span style=\"font-family:'+FM+';font-size:0.58rem;letter-spacing:0.08em;text-transform:uppercase;color:'+ac+';margin-top:3px;display:block;\">'+priority+'</span>' if priority else ''}"
        f"</div>",
        unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────
p_done=st.session_state["profile_done"]
h_done=tpv()>0

top_l,top_r=st.columns([6,1],gap="small")
with top_l:
    st.markdown(
        f"<div style='padding:16px 0 8px;border-bottom:1px solid {BD};margin-bottom:12px;'>"
        f"<div style='display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;'>"
        f"<span style='font-family:{FM};font-size:1.1rem;font-weight:500;"
        f"color:{TEXT};letter-spacing:-0.02em;'>Meridian</span>"
        f"<span style='font-family:{FM};font-size:0.65rem;color:{MUTED};"
        f"letter-spacing:0.06em;'>Investment Risk & Allocation</span>"
        f"</div>"
        f"<div style='display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;'>"
        + "".join([
            f"<span style='font-family:{FM};font-size:0.6rem;letter-spacing:0.06em;"
            f"text-transform:uppercase;padding:2px 8px;border-radius:3px;"
            f"background:{TEXT if done else BD};color:{'#fff' if done else MUTED};'>"
            f"{'✓ ' if done else ''}{lbl}</span>"
            for lbl,done in [
                ("Profile",p_done),("Portfolio",h_done),
                ("Analysis",p_done and h_done),("Rebalancing",p_done and h_done),
                ("Stress Test",p_done and h_done),("Goals",p_done and h_done)]
        ])
        + f"</div></div>",
        unsafe_allow_html=True)
with top_r:
    cur_list=list(CUR_SYM.keys())
    st.markdown("<div style='padding-top:14px;'>",unsafe_allow_html=True)
    st.selectbox("",cur_list,index=cur_list.index(st.session_state["currency"]),
                 key="currency",label_visibility="collapsed")
    st.markdown("</div>",unsafe_allow_html=True)

st.markdown(
    f"<div style='font-family:{FM};font-size:0.6rem;letter-spacing:0.06em;"
    f"color:{MUTED};padding:4px 0 10px;border-bottom:1px solid {BD};margin-bottom:4px;'>"
    f"Educational purposes only — not personal financial advice — consult a licensed adviser (AFSL)</div>",
    unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6=st.tabs([
    "Risk Assessment","Portfolio","Analysis",
    "Rebalancing","Stress Test","Goal Projections"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — RISK ASSESSMENT
# ══════════════════════════════════════════════════════════════
with tab1:
    note("Answer all 10 questions honestly. Your results depend entirely on the accuracy of your inputs.","info")
    total_score=0
    for i,(q,opts,insight) in enumerate(QUESTIONS):
        qk=f"q{i+1}"
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BD};border-radius:8px;"
            f"padding:12px 14px;margin-bottom:6px;'>"
            f"<div style='display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;'>"
            f"<span style='font-family:{FM};font-size:0.6rem;color:{MUTED};"
            f"padding-top:2px;white-space:nowrap;'>{i+1:02d}/{len(QUESTIONS)}</span>"
            f"<span style='font-family:{FH};font-size:0.92rem;font-weight:600;"
            f"color:{TEXT};line-height:1.4;'>{q}</span></div>",
            unsafe_allow_html=True)
        idx=st.radio(q,list(range(len(opts))),
            format_func=lambda x,o=opts:o[x],
            index=st.session_state[qk],key=f"r_{qk}",
            label_visibility="collapsed")
        st.session_state[qk]=idx
        total_score+=idx+1
        with st.expander("Why this matters"):
            st.markdown(f"<div style='font-family:{FH};font-size:0.83rem;color:{MUTED};"
                f"line-height:1.6;padding:2px 0;'>{insight}</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>",unsafe_allow_html=True)
    col_b,_=st.columns([2,5])
    with col_b:
        if st.button("Calculate profile"):
            pn=gprof(total_score)
            st.session_state.update({"risk_score":total_score,"risk_profile":pn,"profile_done":True})
            try: st.rerun()
            except: st.experimental_rerun()

    if p_done:
        pname=st.session_state["risk_profile"]
        prof=PROFILES[pname]
        pac=PROFILE_CLR[pname]
        score=st.session_state["risk_score"]
        pct=((score-10)/30)*100
        tgts=prof["targets"]
        tv=tpv()

        sec("RESULT")
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {BD};border-radius:8px;"
            f"border-left:4px solid {pac};padding:14px 16px;margin-bottom:10px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;"
            f"gap:8px;flex-wrap:wrap;margin-bottom:6px;'>"
            f"<div>"
            f"<div style='font-family:{FM};font-size:0.6rem;letter-spacing:0.1em;"
            f"text-transform:uppercase;color:{MUTED};margin-bottom:3px;'>Risk Profile</div>"
            f"<div style='font-family:{FH};font-size:1.4rem;font-weight:700;"
            f"color:{pac};line-height:1.2;'>{pname}</div>"
            f"<div style='font-family:{FH};font-size:0.82rem;color:{MUTED};"
            f"margin-top:3px;'>{prof['headline']}</div>"
            f"</div>"
            f"<div style='font-family:{FM};font-size:0.75rem;color:{MUTED};"
            f"white-space:nowrap;'>Score: {score}/40</div></div>"
            f"<div style='height:4px;background:{BD};border-radius:2px;overflow:hidden;'>"
            f"<div style='width:{pct:.0f}%;height:100%;background:{pac};'></div></div>"
            f"<div style='font-family:{FH};font-size:0.83rem;color:{MUTED};"
            f"line-height:1.55;margin-top:8px;'>{prof['desc']}</div></div>",
            unsafe_allow_html=True)

        if tv>0:
            kpis([("Expected return",prof["ret"],"Historical p.a.",pac),
                  ("Typical max drawdown",prof["draw"],"In a correction",RED),
                  ("Dollar drawdown est.",fmt(tv*prof["draw_mid"]),"At current portfolio",RED),
                  ("Minimum horizon",prof["horizon"],"Recommended",MUTED)])
        else:
            kpis([("Expected return",prof["ret"],"Historical p.a.",pac),
                  ("Typical max drawdown",prof["draw"],"In a correction",RED),
                  ("Minimum horizon",prof["horizon"],"Recommended",MUTED)])

        sec("TARGET ALLOCATION")
        at={k:v for k,v in tgts.items() if v>0}
        c1,c2=st.columns([1,1],gap="small")
        with c1:
            st.plotly_chart(donut(list(at.keys()),list(at.values()),
                [ASSET_CLR[ASSET_NAMES.index(k)] for k in at]),
                use_container_width=True)
        with c2:
            st.markdown("<div style='padding-top:8px;'>",unsafe_allow_html=True)
            for an,pv2 in tgts.items():
                clr=ASSET_CLR[ASSET_NAMES.index(an)]
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px;"
                    f"padding:5px 0;border-bottom:1px solid {BD};min-width:0;'>"
                    f"<div style='width:8px;height:8px;border-radius:50%;"
                    f"background:{clr};flex-shrink:0;'></div>"
                    f"<div style='font-family:{FH};font-size:0.82rem;color:{TEXT};"
                    f"flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;"
                    f"white-space:nowrap;'>{an}</div>"
                    f"<div style='font-family:{FM};font-size:0.8rem;color:{pac};"
                    f"font-weight:500;flex-shrink:0;'>{pv2}%</div></div>",
                    unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TAB 2 — PORTFOLIO
# ══════════════════════════════════════════════════════════════
with tab2:
    if not p_done:
        note("Complete the Risk Assessment first.","info"); st.stop()

    note("Enter current market value for each asset class. Include super, direct holdings, ETFs, and cash. Partial inputs will skew the analysis.","info")
    sec("HOLDINGS")
    descs=["ASX shares, AU equity ETFs, managed funds",
           "Global ETFs (S&P 500, MSCI World), intl funds",
           "Investment property equity, A-REITs, global REITs",
           "Govt & corp bonds, bond ETFs, term deposits 1yr+",
           "Savings, term deposits under 1yr, offset accounts"]
    ca,cb=st.columns(2,gap="large")
    for i,(an,key,desc) in enumerate(zip(ASSET_NAMES,ASSET_KEYS,descs)):
        col=ca if i<3 else cb
        with col:
            clr=ASSET_CLR[i]
            st.markdown(
                f"<div style='border-left:3px solid {clr};padding-left:8px;margin-bottom:2px;'>"
                f"<div style='font-family:{FH};font-size:0.85rem;font-weight:600;"
                f"color:{TEXT};'>{an}</div>"
                f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True)
            st.number_input(an,min_value=0,step=1000,key=key,label_visibility="collapsed")

    total=tpv()
    if not total:
        note("Enter holdings above to see your allocation.","info")
    else:
        holdings=pv(); active={k:v for k,v in holdings.items() if v>0}
        pname=st.session_state["risk_profile"]
        tgts=PROFILES[pname]["targets"]
        hs,ha,hd,hl=health(holdings,tgts,total)

        sec("PORTFOLIO HEALTH")
        hclr=GREEN if hs>=75 else (AMBER if hs>=50 else RED)
        hlbl="On track" if hs>=75 else ("Needs attention" if hs>=50 else "Action required")

        h1,h2=st.columns([1,2],gap="small")
        with h1:
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BD};border-radius:8px;"
                f"padding:14px;text-align:center;'>"
                f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;"
                f"text-transform:uppercase;color:{MUTED};margin-bottom:6px;'>Health Score</div>"
                f"<div style='font-family:{FM};font-size:3rem;font-weight:500;"
                f"color:{hclr};line-height:1;'>{hs}</div>"
                f"<div style='font-family:{FM};font-size:0.62rem;color:{MUTED};'>/100</div>"
                f"<div style='font-family:{FH};font-size:0.75rem;color:{hclr};"
                f"font-weight:600;margin-top:6px;'>{hlbl}</div>"
                f"<div style='height:4px;background:{BD};border-radius:2px;"
                f"margin-top:8px;overflow:hidden;'>"
                f"<div style='width:{hs}%;height:100%;background:{hclr};'></div>"
                f"</div></div>",
                unsafe_allow_html=True)
        with h2:
            for lbl,sc,tot,tip_txt in [
                ("Alignment",ha,40,f"{ha}/40 — gap vs target allocation"),
                ("Diversification",hd,30,f"{hd}/30 — spread across asset classes"),
                ("Defensive buffer",hl,30,f"{hl}/30 — cash & bonds vs target"),
            ]:
                bar=sc/tot*100
                clr2=GREEN if bar>=70 else (AMBER if bar>=40 else RED)
                st.markdown(
                    f"<div style='background:{CARD};border:1px solid {BD};border-radius:6px;"
                    f"padding:8px 12px;margin-bottom:5px;'>"
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"margin-bottom:4px;gap:8px;'>"
                    f"<span style='font-family:{FH};font-size:0.82rem;font-weight:500;"
                    f"color:{TEXT};'>{lbl}</span>"
                    f"<span style='font-family:{FM};font-size:0.72rem;color:{clr2};"
                    f"white-space:nowrap;'>{sc}/{tot}</span></div>"
                    f"<div style='height:3px;background:{BD};border-radius:2px;overflow:hidden;"
                    f"margin-bottom:4px;'>"
                    f"<div style='width:{bar:.0f}%;height:100%;background:{clr2};'></div></div>"
                    f"<div style='font-family:{FH};font-size:0.72rem;color:{MUTED};'>{tip_txt}</div>"
                    f"</div>",
                    unsafe_allow_html=True)

        if hs>=75: note("Portfolio is well-aligned. Review quarterly to maintain balance.","good")
        elif ha<20: note(f"Significant deviation from your {pname} target. See the Rebalancing tab for specific actions.","alert")
        elif hd<15: note("High concentration in a single asset class. A sharp correction there has outsized impact on total wealth.","warn")
        else: note("Some gaps to close. The Rebalancing tab shows the most tax-efficient path.","warn")

        sec("CURRENT ALLOCATION")
        kpis([("Total portfolio",fmt(total),"All asset classes",TEXT),
              ("Asset classes",str(len(active)),"of 5",MUTED),
              ("Largest position",max(active,key=active.get)[:16],f"{max(active.values())/total*100:.0f}%",AMBER),
              ("Health score",f"{hs}/100","Alignment · Spread · Buffer",hclr)])
        st.markdown("<div style='height:6px;'></div>",unsafe_allow_html=True)
        c1,c2=st.columns([1,1],gap="small")
        with c1:
            st.plotly_chart(donut(list(active.keys()),list(active.values()),
                [ASSET_CLR[ASSET_NAMES.index(k)] for k in active],fmt(total)),
                use_container_width=True)
        with c2:
            st.markdown("<div style='padding-top:8px;'>",unsafe_allow_html=True)
            for an in sorted(holdings,key=lambda x:holdings[x],reverse=True):
                v=holdings[an]
                if not v: continue
                pct2=v/total*100; clr=ASSET_CLR[ASSET_NAMES.index(an)]
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px;"
                    f"padding:5px 0;border-bottom:1px solid {BD};min-width:0;'>"
                    f"<div style='width:8px;height:8px;border-radius:50%;"
                    f"background:{clr};flex-shrink:0;'></div>"
                    f"<div style='font-family:{FH};font-size:0.82rem;color:{TEXT};"
                    f"flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;"
                    f"white-space:nowrap;'>{an}</div>"
                    f"<div style='font-family:{FM};font-size:0.72rem;color:{MUTED};"
                    f"flex-shrink:0;margin-right:4px;'>{pct2:.1f}%</div>"
                    f"<div style='font-family:{FM};font-size:0.8rem;font-weight:500;"
                    f"color:{TEXT};flex-shrink:0;'>{fmt(v)}</div></div>",
                    unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

        for an,v in holdings.items():
            if v and v/total*100>60:
                note(f"{an} is {v/total*100:.0f}% of your portfolio. See the Stress Test tab for dollar-impact analysis of a sharp correction.","warn")
                break

# ══════════════════════════════════════════════════════════════
# TAB 3 — ANALYSIS
# ══════════════════════════════════════════════════════════════
with tab3:
    if not p_done: note("Complete the Risk Assessment first.","info")
    elif not tpv(): note("Enter holdings in the Portfolio tab.","info")
    else:
        pname=st.session_state["risk_profile"]
        tgts=PROFILES[pname]["targets"]
        holdings=pv(); total=tpv()
        pac=PROFILE_CLR[pname]

        st.markdown(
            f"<div style='font-family:{FH};font-size:0.85rem;color:{MUTED};"
            f"padding-bottom:10px;border-bottom:1px solid {BD};margin-bottom:2px;'>"
            f"Profile: <strong style='color:{pac};'>{pname}</strong> — "
            f"comparing current allocation to target.</div>",
            unsafe_allow_html=True)

        sec("CURRENT VS TARGET")
        short=[a.split("&")[0].strip()[:12] for a in ASSET_NAMES]
        st.plotly_chart(bar_chart(short,
            [holdings.get(a,0)/total*100 for a in ASSET_NAMES],
            [tgts.get(a,0) for a in ASSET_NAMES]),use_container_width=True)

        sec("GAP ANALYSIS")
        rows=[]; overs=[]; unders=[]
        for an in ASSET_NAMES:
            cp=holdings.get(an,0)/total*100; tp=tgts.get(an,0)
            gap=cp-tp; cv=holdings.get(an,0); tv=total*tp/100; dv=cv-tv
            if gap>5:
                st2=f"<span style='color:{RED};font-family:{FM};font-size:0.75rem;'>+{gap:.1f}% over</span>"
                overs.append((an,gap))
            elif gap<-5:
                st2=f"<span style='color:{AMBER};font-family:{FM};font-size:0.75rem;'>{gap:.1f}% under</span>"
                unders.append((an,gap))
            else:
                st2=f"<span style='color:{GREEN};font-family:{FM};font-size:0.75rem;'>on target</span>"
            rows.append([an,f"{cp:.1f}%",f"{tp:.0f}%",st2,fmt(cv),fmt(tv),fmt(dv)])
        tbl(["Asset","Current","Target","Status","Value","Target Value","Gap"],rows)

        if overs:
            b=max(overs,key=lambda x:x[1])
            note(f"Largest overweight: {b[0]} at +{b[1]:.1f}%. Common when a high-performing asset drifts up without rebalancing. See the Rebalancing tab.","warn")
        if unders:
            b=min(unders,key=lambda x:x[1])
            note(f"Largest underweight: {b[0]} at {abs(b[1]):.1f}% below target. Defensive underweights increase drawdown risk. Prioritise new contributions here.","warn")
        if not overs and not unders:
            note("Portfolio is well-aligned to your risk profile. Review quarterly.","good")

        sec("VISUAL COMPARISON")
        cl,cr=st.columns(2,gap="small")
        with cl:
            st.markdown(f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;text-transform:uppercase;color:{MUTED};text-align:center;margin-bottom:4px;'>Current</div>",unsafe_allow_html=True)
            a_a={k:v for k,v in holdings.items() if v>0}
            st.plotly_chart(donut(list(a_a.keys()),list(a_a.values()),
                [ASSET_CLR[ASSET_NAMES.index(k)] for k in a_a],"Current"),
                use_container_width=True)
        with cr:
            st.markdown(f"<div style='font-family:{FM};font-size:0.58rem;letter-spacing:0.1em;text-transform:uppercase;color:{MUTED};text-align:center;margin-bottom:4px;'>Target — {pname}</div>",unsafe_allow_html=True)
            t_a={k:v for k,v in tgts.items() if v>0}
            st.plotly_chart(donut(list(t_a.keys()),list(t_a.values()),
                [ASSET_CLR[ASSET_NAMES.index(k)] for k in t_a],pname[:4]+"."),
                use_container_width=True)

# ══════════════════════════════════════════════════════════════
# TAB 4 — REBALANCING
# ══════════════════════════════════════════════════════════════
with tab4:
    if not p_done: note("Complete the Risk Assessment first.","info")
    elif not tpv(): note("Enter holdings in the Portfolio tab.","info")
    else:
        pname=st.session_state["risk_profile"]
        tgts=PROFILES[pname]["targets"]
        holdings=pv(); total=tpv()

        note("Rebalancing: sell what has drifted overweight, buy what is underweight. Prioritise super first (no CGT). Use new contributions where possible to avoid taxable events.","info")

        sec("TAX SETTINGS")
        c1,c2=st.columns(2,gap="large")
        with c1:
            st.session_state["cgt_rate"]=st.slider("Marginal tax rate (%)",0,47,int(st.session_state["cgt_rate"]),1)
        with c2:
            st.session_state["cost_base_pct"]=st.slider("Cost base as % of current value",20,100,int(st.session_state["cost_base_pct"]),5,
                help="e.g. bought at $50k, now $100k → set 50%")

        sells,buys,holds=[],[],[]
        for an in ASSET_NAMES:
            cv=holdings.get(an,0); cp=cv/total*100
            tp=tgts.get(an,0); tv=total*tp/100; diff=cv-tv; gap=cp-tp
            if gap>2:   sells.append((an,diff,cp,tp))
            elif gap<-2: buys.append((an,abs(diff),cp,tp))
            else:        holds.append((an,cp,tp))
        sells.sort(key=lambda x:x[1],reverse=True)
        buys.sort(key=lambda x:x[1],reverse=True)

        if sells:
            sec("REDUCE — OVERWEIGHT")
            for i,(an,amt,cp,tp) in enumerate(sells):
                cgt_e=cgt(amt,st.session_state["cost_base_pct"],st.session_state["cgt_rate"])
                action_card(an,fmt(amt),cp,tp,"sell",
                    "High priority" if i==0 else "",
                    f"Est. CGT: {fmt(cgt_e)} | Net: {fmt(amt-cgt_e)}")

        if buys:
            sec("INCREASE — UNDERWEIGHT")
            for i,(an,amt,cp,tp) in enumerate(buys):
                action_card(an,fmt(amt),cp,tp,"buy","High priority" if i==0 else "")

        if holds:
            sec("HOLD — ON TARGET")
            st.markdown(
                "<div style='font-family:"+FM+";font-size:0.78rem;color:"+MUTED+";padding:4px 0;'>"
                + "  ·  ".join(f"<span style='color:{GREEN};'>✓</span> {a} ({c:.1f}%)" for a,c,_ in holds)
                +"</div>",unsafe_allow_html=True)

        sec("SMART CONTRIBUTION ALLOCATOR")
        note("Direct new contributions into underweight assets — zero CGT, maximum rebalancing efficiency.","good")
        new_money=st.number_input("New investment to allocate",min_value=0,step=500,value=10000)
        if new_money>0:
            allocs=smart_alloc(new_money,holdings,tgts,total)
            rows2=[]
            for an,amt in allocs.items():
                if amt>0:
                    rows2.append([an,fmt(amt),f"{amt/new_money*100:.0f}%","Closes underweight gap"])
            if rows2:
                tbl(["Asset","Allocate","% of New Money","Rationale"],rows2)
                note(f"Investing {fmt(new_money)} this way reduces gap to target with no capital gains event.","good")
            else:
                note("Portfolio is already on target — contribute proportionally to maintain weights.","good")

        sec("FULL SUMMARY")
        total_cgt=0; srows=[]
        for an in ASSET_NAMES:
            cv=holdings.get(an,0); cp=cv/total*100; tp=tgts.get(an,0)
            tv=total*tp/100; diff=tv-cv
            if diff>500:
                act=f"<span style='color:{GREEN};font-family:{FM};font-size:0.8rem;'>Buy {fmt(diff)}</span>"
                cgt_cell="—"
            elif diff<-500:
                cgt_e=cgt(abs(diff),st.session_state["cost_base_pct"],st.session_state["cgt_rate"])
                total_cgt+=cgt_e
                act=f"<span style='color:{RED};font-family:{FM};font-size:0.8rem;'>Sell {fmt(abs(diff))}</span>"
                cgt_cell=f"<span style='color:{AMBER};font-family:{FM};'>{fmt(cgt_e)}</span>"
            else:
                act=f"<span style='color:{MUTED};font-family:{FM};font-size:0.8rem;'>Hold</span>"
                cgt_cell="—"
            srows.append([an,f"{cp:.1f}%",fmt(cv),f"{tp:.0f}%",fmt(tv),act,cgt_cell])
        tbl(["Asset","Current %","Value","Target %","Target Value","Action","Est. CGT"],srows)
        if total_cgt>0:
            note(f"Total estimated CGT on sells: {fmt(total_cgt)} (50% discount applied for assets held 12+ months). Confirm with your accountant.","warn")

        sec("EXECUTION NOTES")
        for title,txt,kind in [
            ("Super first","No CGT on sales inside an accumulation-phase super fund. Always rebalance within super before acting on non-super assets.","good"),
            ("Use contributions","Directing new money into underweights avoids selling and CGT entirely. Most efficient method over a 12–24 month horizon.","good"),
            ("CGT timing","Assets held under 12 months: full gain taxed. Over 12 months: 50% discount applies. Consider timing sales around the 12-month mark.","warn"),
            ("Review frequency","Annual review is sufficient for most investors. More frequent rebalancing generates friction without proportional benefit.","info"),
        ]:
            with st.expander(title): note(txt,kind)

# ══════════════════════════════════════════════════════════════
# TAB 5 — STRESS TEST
# ══════════════════════════════════════════════════════════════
with tab5:
    if not p_done: note("Complete the Risk Assessment first.","info")
    elif not tpv(): note("Enter holdings in the Portfolio tab.","info")
    else:
        holdings=pv(); total=tpv()
        pname=st.session_state["risk_profile"]
        prof=PROFILES[pname]

        note("Stress testing converts abstract percentage declines into dollar impacts on your specific portfolio. These are calibrated historical scenarios, not predictions.","info")

        sec("SCENARIO")
        scen_name=st.radio("",list(STRESS.keys()),horizontal=True,label_visibility="collapsed")
        sc=STRESS[scen_name]
        nt,net_loss,bd=stress_run(holdings,total,sc)
        pct_loss=abs(net_loss)/total*100

        st.markdown(
            f"<div style='background:{RED_S};border:1px solid #FECACA;"
            f"border-radius:8px;padding:10px 14px;margin:6px 0;'>"
            f"<div style='font-family:{FM};font-size:0.78rem;font-weight:500;"
            f"color:{RED};margin-bottom:3px;'>{sc['label']}</div>"
            f"<div style='font-family:{FH};font-size:0.82rem;color:{TEXT};line-height:1.5;'>{sc['desc']}</div></div>",
            unsafe_allow_html=True)

        kpis([("Before",fmt(total),"Current value",TEXT),
              ("Estimated loss",fmt(net_loss),f"-{pct_loss:.1f}% of portfolio",RED),
              ("Portfolio after",fmt(nt),"Post-crash estimate",AMBER),
              ("Recovery est.",f"~{sc['rec']:.0f}yr",f"At {prof['ret_mid']*100:.0f}% p.a.",GREEN)])

        sec("ASSET-LEVEL IMPACT")
        imp_rows=[]
        bx,bv,bc=[],[],[]
        for an in ASSET_NAMES:
            v=holdings.get(an,0)
            if not v: continue
            delta=bd.get(an,0); shock=sc["shocks"].get(an,0)
            clr2=RED if delta<0 else GREEN
            ds=(f"<span style='color:{RED};font-family:{FM};'>{fmt(delta)}</span>"
                if delta<0 else
                f"<span style='color:{GREEN};font-family:{FM};'>+{fmt(delta)}</span>")
            imp_rows.append([an,fmt(v),f"{shock*100:+.0f}%",fmt(v+delta),ds])
            bx.append(an.split("&")[0].strip()[:10]); bv.append(delta); bc.append(clr2)
        tbl(["Asset","Before","Shock","After","Change"],imp_rows)

        fig_b=go.Figure()
        fig_b.add_trace(go.Bar(x=bx,y=bv,marker_color=bc,marker_line_width=0,
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
        fig_b.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=4,b=4,l=4,r=4),height=200,showlegend=False,
            xaxis=dict(showgrid=False,tickfont=dict(family="JetBrains Mono",size=8,color=MUTED)),
            yaxis=dict(showgrid=True,gridcolor=BD,
                tickfont=dict(family="JetBrains Mono",size=8,color=MUTED),tickprefix=sym()))
        st.plotly_chart(fig_b,use_container_width=True)

        sec("RECOVERY TIMELINE")
        yrs=list(range(16))
        fig_r=go.Figure()
        fig_r.add_hline(y=total,line_dash="dash",line_color=BLUE,line_width=1.5,
            annotation_text="Current value",
            annotation_font=dict(family="JetBrains Mono",size=9,color=BLUE))
        clrs=[GREEN,AMBER,RED]
        for (sn,s_),rc in zip(STRESS.items(),clrs):
            sl=sum(holdings.get(a,0)*s_["shocks"].get(a,0) for a in ASSET_NAMES)
            vals=[(total+sl)*(1+prof["ret_mid"])**y for y in yrs]
            fig_r.add_trace(go.Scatter(x=yrs,y=vals,mode="lines",
                name=s_["label"].split("  ")[0],
                line=dict(color=rc,width=1.8),
                hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
        fig_r.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=4,b=4,l=4,r=4),height=240,
            legend=dict(bgcolor="rgba(0,0,0,0)",borderwidth=0,orientation="h",y=1.12,
                font=dict(family="JetBrains Mono",size=8,color=MUTED)),
            xaxis=dict(title="Years post-crash",showgrid=False,
                tickfont=dict(family="JetBrains Mono",size=8,color=MUTED)),
            yaxis=dict(showgrid=True,gridcolor=BD,
                tickfont=dict(family="JetBrains Mono",size=8,color=MUTED),tickprefix=sym()))
        st.plotly_chart(fig_r,use_container_width=True)

        if pct_loss>prof["draw_mid"]*100*1.3:
            note(f"Your {pct_loss:.1f}% drawdown in this scenario exceeds the typical {prof['draw']} range for a {pname} portfolio. Your current allocation carries more risk than your profile implies.","alert")
        elif pct_loss<prof["draw_mid"]*100*0.7:
            note(f"Defensive holdings absorb the shock well. Your estimated {pct_loss:.1f}% drawdown is below the typical {prof['draw']} for a {pname} investor — bonds and cash doing their job.","good")
        else:
            note(f"Estimated loss of {fmt(abs(net_loss))} ({pct_loss:.1f}%) is consistent with the expected drawdown for a {pname} portfolio. Recovery at {prof['ret_mid']*100:.0f}% p.a.: ~{sc['rec']:.0f} year(s).","info")

# ══════════════════════════════════════════════════════════════
# TAB 6 — GOAL PROJECTIONS
# ══════════════════════════════════════════════════════════════
with tab6:
    if not p_done: note("Complete the Risk Assessment first.","info")
    else:
        pname=st.session_state["risk_profile"]
        prof=PROFILES[pname]; total=tpv()
        pac=PROFILE_CLR[pname]

        note("Monte Carlo simulation — 1,000 independent paths using your profile's historical return and volatility parameters. Outcome probabilities, not point predictions.","info")

        sec("INPUTS")
        g1,g2,g3=st.columns(3,gap="large")
        with g1:
            ga=st.number_input("Target portfolio value",min_value=0,step=50_000,value=int(st.session_state["goal_amount"]))
            st.session_state["goal_amount"]=ga
        with g2:
            gy=st.slider("Time horizon (years)",1,40,int(st.session_state["goal_years"]),1)
            st.session_state["goal_years"]=gy
        with g3:
            mc=st.number_input("Monthly contributions",min_value=0,step=250,value=int(st.session_state["monthly_contrib"]))
            st.session_state["monthly_contrib"]=mc

        start=float(total) if total>0 else 0.0
        if not start and not mc:
            note("Enter your portfolio value (Portfolio tab) or a monthly contribution to run projections.","info")
        else:
            with st.spinner("Running 1,000 simulations…"):
                p10,p25,p50,p75,p90,ym,yp10,yp90=monte_carlo(start,mc,gy,pname,1000)

            if p90<ga:       prob,pc="< 10%",RED
            elif p75<ga:     prob,pc="10–25%",RED
            elif p50<ga:     prob,pc="25–50%",AMBER
            elif p25<ga:     prob,pc="50–75%",GREEN
            elif p10<ga:     prob,pc="75–90%",GREEN
            else:            prob,pc="> 90%",GREEN

            ti=start+mc*gy*12
            sec("RESULTS")
            kpis([("Starting value",fmt(start),"Current portfolio",TEXT),
                  ("Total contributed",fmt(ti),f"{fmt(mc)}/mo × {gy}yr",MUTED),
                  ("Median outcome",fmt(p50),"50th percentile",pac),
                  ("Probability of goal",prob,f"Reaching {fmt(ga)}",pc)])

            sec("PROJECTION CHART")
            yrs=list(range(gy+1))
            fig_mc=go.Figure()
            fig_mc.add_trace(go.Scatter(
                x=yrs+yrs[::-1],
                y=[yp90[y] for y in yrs]+[yp10[y] for y in yrs][::-1],
                fill="toself",fillcolor="rgba(37,99,235,0.08)",
                line=dict(color="rgba(0,0,0,0)"),
                name="10th–90th band",hoverinfo="skip"))
            fig_mc.add_trace(go.Scatter(x=yrs,y=[ym[y] for y in yrs],
                mode="lines",name="Median",
                line=dict(color=BLUE,width=2),
                hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
            fig_mc.add_trace(go.Scatter(x=yrs,y=[yp10[y] for y in yrs],
                mode="lines",name="10th pct",
                line=dict(color=RED,width=1,dash="dot"),
                hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
            fig_mc.add_trace(go.Scatter(x=yrs,y=[yp90[y] for y in yrs],
                mode="lines",name="90th pct",
                line=dict(color=GREEN,width=1,dash="dot"),
                hovertemplate="Yr %{x}  %{y:,.0f}<extra></extra>"))
            if ga>0:
                fig_mc.add_hline(y=ga,line_dash="dash",line_color=PURPLE,line_width=1.5,
                    annotation_text=f"Goal {fmt(ga)}",
                    annotation_font=dict(family="JetBrains Mono",size=9,color=PURPLE))
            fig_mc.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=8,b=8,l=8,r=8),height=320,
                legend=dict(bgcolor="rgba(0,0,0,0)",borderwidth=0,orientation="h",y=1.1,
                    font=dict(family="JetBrains Mono",size=9,color=MUTED)),
                xaxis=dict(title="Years",showgrid=False,
                    tickfont=dict(family="JetBrains Mono",size=8,color=MUTED)),
                yaxis=dict(showgrid=True,gridcolor=BD,
                    tickfont=dict(family="JetBrains Mono",size=8,color=MUTED),tickprefix=sym()))
            st.plotly_chart(fig_mc,use_container_width=True)

            sec(f"OUTCOME DISTRIBUTION — YEAR {gy}")
            tbl(["Percentile","Value","Interpretation"],[
                ["90th (optimistic)", fmt(p90),"Only 10% of simulations exceed this"],
                ["75th",             fmt(p75),"Better than 3 in 4 paths"],
                ["50th (median)",    fmt(p50),"Central estimate"],
                ["25th",             fmt(p25),"Worse than 3 in 4 paths"],
                ["10th (pessimistic)",fmt(p10),"Only 10% of paths fall below this"],
            ])

            sec("CONTRIBUTION SENSITIVITY")
            note("Increasing monthly contributions typically has more impact than chasing higher returns.","info")
            sr=[]
            for ex in [0,500,1000,2000,3000]:
                _,_,sp50,_,_,_,_,_=monte_carlo(start,mc+ex,gy,pname,500)
                hit=sp50>=ga; clr2=GREEN if hit else RED
                sr.append([
                    f"+{fmt(ex)}/mo" if ex else "Current",
                    fmt(mc+ex)+"/mo",fmt(sp50),
                    f"<span style='color:{clr2};font-family:{FM};font-size:0.8rem;'>{'Reaches' if hit else 'Misses'} goal</span>"])
            tbl(["Scenario","Monthly","Median Outcome","Goal"],sr)

            if pc==GREEN:
                note(f"On track. Consistency matters more than return optimisation at this stage. Stay invested through downturns.","good")
            elif pc==AMBER:
                gap2=ga-p50; extra=gap2/(gy*12) if gy else 0
                note(f"Median outcome is {fmt(p50)} — {fmt(gap2)} short of goal. An additional {fmt(extra)}/month closes most of that gap.","warn")
            else:
                note(f"Low probability of reaching {fmt(ga)} in {gy} years at current settings. Consider: higher contributions, longer timeline, or revisiting your risk profile.","alert")

            note("Simulations use historical parameters. They do not account for inflation, fees, taxes, or sequence-of-returns risk. Use as a planning range, not a guarantee.","warn")

# ── FOOTER ────────────────────────────────────────────────────
st.markdown(
    f"<div style='border-top:1px solid {BD};margin-top:2rem;padding:14px 0 8px;"
    f"font-family:{FM};font-size:0.6rem;letter-spacing:0.06em;"
    f"text-transform:uppercase;color:{DIM};text-align:center;'>"
    f"Meridian — Educational purposes only — Not personal financial advice — "
    f"Consult a licensed financial adviser (AFSL)</div>",
    unsafe_allow_html=True)
