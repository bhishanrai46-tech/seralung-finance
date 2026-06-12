"""
Seralung Finance — goal-based financial wizard (Streamlit).
Run:  streamlit run app.py     Deps: streamlit, numpy, pandas

FINANCIAL HEALTH MODEL (realistic, multi-dimensional):
  HEADLINE = life-stage-weighted blend of two orthogonal sub-scores:
    • FOUNDATION (resilience NOW): emergency runway, debt burden (cost-weighted),
      savings rate, protection & income stability.
    • GOAL-READINESS (trajectory): probability of reaching your Ultimate Goal,
      computed by Monte Carlo in REAL (inflation-adjusted) terms, net of fees/tax,
      counting invested assets + ongoing contributions (incl. employer).
  The 50/30/20 rule is no longer scored — it is shown only as a budget diagnostic.
  Full formulas: calculation_notes()  (also shown in-app on the Action Plan step).
"""
import base64
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Seralung Finance", layout="wide", initial_sidebar_state="collapsed")

# ════════════════════════════ FINANCE ENGINE ════════════════════════════
ASSETS   = ["Cash","Bonds","Equity ETFs","Stocks","Property","Crypto"]
ASSET_CLR= ["#16794D","#7C3AED","#3DA968","#B7791F","#0E7C7B","#C53929"]
R  = np.array([0.035,0.045,0.080,0.095,0.070,0.180])
V  = np.array([0.010,0.050,0.150,0.240,0.140,0.650])
RF, Z, PHI = 0.035, 1.645, 0.103138
CORR = np.array([[1,.15,0,-.05,.05,0],[.15,1,.25,.10,.30,.05],[0,.25,1,.88,.60,.35],
                 [-.05,.10,.88,1,.50,.40],[.05,.30,.60,.50,1,.25],[0,.05,.35,.40,.25,1]])
COV = np.outer(V,V)*CORR
TIER_W = {"Defensive":[40,40,12,0,8,0],"Conservative":[22,33,25,3,15,2],
          "Balanced":[10,22,35,10,18,5],"Growth":[5,12,45,18,15,5],"Aggressive":[2,5,48,25,12,8]}
TIERS  = list(TIER_W)
TIER_CLR={"Defensive":"#0E7C7B","Conservative":"#16794D","Balanced":"#16794D","Growth":"#B7791F","Aggressive":"#C53929"}
TIER_BG ={"Defensive":"#DFF2F1","Conservative":"#E7F5EC","Balanced":"#E7F5EC","Growth":"#FBF3E2","Aggressive":"#FBEAE7"}
TIER_OPT={
 "Defensive":["High-interest savings & term deposits","Government bond ETFs (e.g. VGB, IAF)","Cash management / money-market funds","Capital-guaranteed products"],
 "Conservative":["Diversified bond ETFs (corporate + government)","Blue-chip dividend ETFs","Small allocation to broad index funds","Defensive listed property (A-REIT ETFs)"],
 "Balanced":["Broad-market index ETFs (VAS, VGS, IVV)","Balanced multi-asset funds (~60/40)","Listed property / infrastructure ETFs","Investment-grade bond ETFs for ballast"],
 "Growth":["Global & domestic equity ETFs (growth tilt)","International index funds (developed + emerging)","Sector / thematic ETFs as satellites","Small allocation to quality individual stocks"],
 "Aggressive":["Growth & thematic equity ETFs","Emerging-market & small-cap ETFs","Selective individual growth stocks","Small, capped crypto allocation (under 10%)"]}
CATS  = ["Housing","Utilities","Groceries","Transport","Insurance","Healthcare","Debt Repayment",
         "Dining Out","Entertainment","Shopping","Subscriptions","Travel","Savings/Invest","Other"]
CTYPE = {"Housing":"Need","Utilities":"Need","Groceries":"Need","Transport":"Need","Insurance":"Need",
         "Healthcare":"Need","Debt Repayment":"Need","Dining Out":"Want","Entertainment":"Want",
         "Shopping":"Want","Subscriptions":"Want","Travel":"Want","Savings/Invest":"Savings","Other":"Want"}
DEFAULT_EXP = [["Rent / Mortgage","Housing",1800],["Electricity & Gas","Utilities",200],
   ["Groceries","Groceries",650],["Car & Fuel","Transport",350],["Health Insurance","Insurance",180],
   ["Loan Repayment","Debt Repayment",400],["Streaming & Apps","Subscriptions",55],["Dining Out","Dining Out",300]]
QUESTIONS = [
 ("When do you expect to need this money?",["Under 3 years","3–7 years","7–15 years","15+ years"]),
 ("How stable is your income?",["Retired or fixed income","Variable or self-employed","Stable salary","Very secure"]),
 ("If your portfolio fell 30% in three months, you would:",["Sell everything","Sell some","Hold and wait","Buy more at lower prices"]),
 ("How much investing experience do you have?",["None","Basic — shares & funds","Three or more years active","Ten or more years, multi-asset"]),
 ("Your primary investment goal:",["Protect capital","Modest growth with protection","Balanced growth","Maximum growth"]),
 ("Do you expect significant withdrawals within five years?",["Yes — most of it","Yes — a meaningful portion","Possibly — small amounts","No — long-term"]),
 ("Maximum annual loss you could absorb:",["Under 5%","5–15%","15–25%","25% or more"]),
 ("This investment is what share of your net worth?",["Over 75%","50–75%","25–50%","Under 25%"]),
 ("How do market swings make you feel?",["Very anxious","Uneasy","Mostly calm","Indifferent — it is normal"]),
 ("Your investment knowledge level:",["Beginner","Some understanding","Confident","Advanced"])]
TOL = [("Conservative",10,18,1),("Moderately Conservative",19,25,2),("Balanced",26,31,3),("Growth",32,36,4),("Aggressive",37,40,5)]

def sf(x):
    try:
        v=float(x); return max(0.0,v) if np.isfinite(v) else 0.0
    except (TypeError,ValueError): return 0.0

def metrics(wpct):
    w=np.array(wpct,float)/100.0; rp=float(w@R); sd=float(w@COV@w)**0.5
    return {"rp":rp,"sd":sd,"sharpe":(rp-RF)/sd if sd>0 else 0.0,"var95":max(0,Z*sd-rp),
            "cvar95":max(0,sd*(PHI/0.05)-rp),"maxdd":min(0.95,2.4*sd),"div":float(w@V)/sd if sd>0 else 1.0}
TIER_M={t:metrics(TIER_W[t]) for t in TIERS}

def compute_budget(ss):
    income=sf(ss["income_primary"])+sf(ss["income_secondary"]); cash=sf(ss["savings"])
    total=needs=wants=debt=0.0; cat_sums={}
    if ss["entry_mode"]=="total":
        total=sf(ss["total_expenses"]); needs=total
    else:
        for _,row in ss["expenses_df"].iterrows():
            amt=sf(row.get("Amount",0))
            if amt<=0: continue
            cat=row.get("Category","Other"); cat=cat if cat in CATS else "Other"
            total+=amt; t=CTYPE.get(cat,"Want")
            if t=="Need": needs+=amt
            elif t=="Want": wants+=amt
            if cat=="Debt Repayment": debt+=amt
            cat_sums[cat]=cat_sums.get(cat,0)+amt
    surplus=income-total; sr=surplus/income if income>0 else 0
    essential=needs if needs>0 else total; runway=cash/essential if essential>0 else 0
    dti=debt/income if income>0 else 0
    return dict(income=income,cash=cash,total=total,needs=needs,wants=wants,debt=debt,surplus=surplus,
                sr=sr,essential=essential,runway=runway,dti=dti,cat_sums=cat_sums)

def capacity(b):
    run=min(100,b["runway"]/6*100); sr=min(100,max(0,b["sr"])/0.25*100); dti=max(0,100-b["dti"]/0.50*100)
    return round(.40*run+.40*sr+.20*dti)
def cap_level(c):
    return (5,"Strong") if c>=80 else (4,"Solid") if c>=60 else (3,"Moderate") if c>=40 else (2,"Limited") if c>=20 else (1,"Fragile")
def tol_profile(ss):
    s=sum(int(ss[f"quiz_q{i}"])+1 for i in range(1,11))
    for n,lo,hi,lv in TOL:
        if lo<=s<=hi: return n,lv,s
    return "Balanced",3,s
def rec_tier(cap_l,tol_l): return TIERS[max(1,min(5,min(cap_l,tol_l)))-1]

# ---- time value of money ----
def future_value(S0,C,r,years):
    i=r/12; m=int(round(years*12))
    if abs(i)<1e-12: return S0+C*m
    g=(1+i)**m; return S0*g+C*((g-1)/i)
def required_contribution(T,S0,r,years):
    i=r/12; m=int(round(years*12))
    if abs(i)<1e-12: return max(0,(T-S0)/m)
    g=(1+i)**m; return max(0,(T-S0*g)*i/(g-1))
def years_to_goal(T,S0,C,r):
    i=r/12
    if T<=S0: return 0.0
    if abs(i)<1e-12: return ((T-S0)/C)/12 if C>0 else float("inf")
    num,den=T+C/i,S0+C/i
    if den<=0 or num/den<=0: return float("inf")
    m=np.log(num/den)/np.log(1+i); return m/12 if m>0 else float("inf")

def goal_target(ss):
    return sf(ss["goal_income"])*12/0.04 if ss["goal_mode"]=="income" else sf(ss["goal_lump"])
def real_net(rp,drag,infl):  # net-of-fee/tax, inflation-adjusted return
    return (1+(rp-drag))/(1+infl)-1

@st.cache_data(show_spinner=False)
def prob_success(S0,Cm,rr,sd,years,T,n=4000,seed=42):
    """Monte Carlo probability of reaching T (today's $) in REAL terms. Returns (prob, median)."""
    rng=np.random.default_rng(seed); m=int(round(years*12)); mu=rr/12; s=sd/np.sqrt(12)
    w=np.full(n,max(0.0,S0))
    for _ in range(m):
        w=np.maximum(0.0, w*(1+rng.normal(mu,s,n)))+Cm
    return float(np.mean(w>=T)), float(np.median(w))

def goal_assess(S0,Cm,rp,sd,T,years,infl,drag):
    rr=real_net(rp,drag,infl)
    prob,med=prob_success(round(S0,-2),round(Cm,1),round(rr,4),round(sd,4),int(max(1,years)),round(max(1,T),-2))
    return dict(rr=rr,prob=prob,med=med,req=required_contribution(T,S0,rr,years),
                ytg=years_to_goal(T,S0,Cm,rr),now=S0/T if T>0 else 0,Cm=Cm)

def rating(s):
    return ("Excellent","#16794D","#E7F5EC") if s>=80 else ("Good","#0E7C7B","#DFF2F1") if s>=65 \
      else ("Fair","#B7791F","#FBF3E2") if s>=45 else ("At Risk","#C53929","#FBEAE7") if s>=25 else ("Critical","#C53929","#FBEAE7")

# ════════════════════════════ SVG CHARTS ════════════════════════════
def _img(svg,mw):
    return f'<img src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}" style="display:block;margin:0 auto;width:100%;max-width:{mw}px"/>'
def _polar(cx,cy,r,deg):
    a=(deg-90)*np.pi/180; return cx+r*np.cos(a), cy+r*np.sin(a)
def _arc(cx,cy,r,a0,a1):
    x0,y0=_polar(cx,cy,r,a0); x1,y1=_polar(cx,cy,r,a1); large=0 if (a1-a0)<=180 else 1
    return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}"
def gauge(score,color,sub="out of 100"):
    cx,cy,r,start,sweep=110,110,80,135,270; end=start+sweep*max(0,min(100,score))/100
    svg=(f'<svg viewBox="0 0 220 200" xmlns="http://www.w3.org/2000/svg">'
         f'<path d="{_arc(cx,cy,r,start,start+sweep)}" fill="none" stroke="#E6EEF0" stroke-width="16" stroke-linecap="round"/>'
         f'<path d="{_arc(cx,cy,r,start,end)}" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round"/>'
         f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="Plus Jakarta Sans,sans-serif" font-weight="800" font-size="40" fill="{color}">{round(score)}</text>'
         f'<text x="{cx}" y="{cy+20}" text-anchor="middle" font-family="Plus Jakarta Sans,sans-serif" font-size="12" fill="#64748B">{sub}</text></svg>')
    return _img(svg,230)
def donut(segs,center):
    cx,cy,r,sw=90,90,62,24; C=2*np.pi*r; off=0; circ=""; tot=sum(v for _,v,_ in segs) or 1
    for _,v,clr in segs:
        ln=v/tot*C
        circ+=(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{clr}" stroke-width="{sw}" '
               f'stroke-dasharray="{ln:.2f} {C-ln:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})"/>'); off+=ln
    svg=(f'<svg viewBox="0 0 180 180" xmlns="http://www.w3.org/2000/svg">{circ}'
         f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-family="Plus Jakarta Sans,sans-serif" font-weight="700" font-size="15" fill="#1E2A32">{center}</text></svg>')
    return _img(svg,220)
def legend(segs):
    return '<div class="legend">'+''.join(f'<div class="li"><span class="sw" style="background:{c}"></span>{l}</div>' for l,_,c in segs)+'</div>'

# ════════════════════════════ CSS ════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#EEF1F5!important;font-family:'Plus Jakarta Sans',sans-serif;color:#1E2A32!important}
.stApp p,.stApp label,.stApp li,[data-testid="stMarkdownContainer"]{color:#1E2A32}
.block-container{padding:0 22px 5rem;max-width:1180px}
#MainMenu,footer,header{visibility:hidden}.stDeployButton{display:none!important}[data-testid="stSidebarNav"]{display:none!important}
[data-testid="stVerticalBlock"]{gap:.3rem!important}
h1,h2,h3,h4{font-family:'Plus Jakarta Sans',sans-serif!important;margin:0!important;color:#1E2A32!important}
.topbar{background:linear-gradient(100deg,#0B2545,#14365F);color:#fff;margin:0 -22px;padding:14px 22px;display:flex;justify-content:space-between;align-items:center}
.topbar h1{font-size:1.15rem;font-weight:800;color:#fff!important}.topbar p{font-size:.8rem;color:#B9C6D6;margin-top:1px}
.pillc{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);color:#fff;font-size:.74rem;font-weight:600;padding:5px 12px;border-radius:20px;display:flex;gap:8px;align-items:center}
.dotz{display:flex;gap:4px}.dotz i{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.28);display:inline-block}.dotz i.on{background:#F59E0B}
.stepnav{background:#fff;margin:0 -22px;padding:16px 22px 14px;border-bottom:1px solid #E3E8EF;display:flex;justify-content:space-between}
.snode{display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;position:relative}
.snode .circle{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;background:#fff;border:2px solid #E3E8EF;color:#94A3B8;z-index:2}
.snode .lbl{font-size:.74rem;font-weight:600;color:#94A3B8;text-align:center;line-height:1.15}
.snode .line{position:absolute;top:17px;left:50%;width:100%;height:2px;background:#E3E8EF;z-index:1}.snode:last-child .line{display:none}
.banner{margin:0 -22px 6px;padding:16px 22px;display:flex;gap:14px;align-items:center}
.banner .bi{width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;color:#fff;flex-shrink:0}
.banner .pl{font-size:.66rem;font-weight:800;letter-spacing:.04em;padding:3px 10px;border-radius:20px;color:#fff}.banner .cp{background:#16794D;color:#fff;font-size:.66rem;font-weight:800;padding:3px 10px;border-radius:20px;margin-left:6px}
.banner h2{font-size:1.05rem;font-weight:800;margin-top:5px!important}.banner .sb{font-size:.82rem;color:#64748B}
.sec{display:flex;align-items:center;gap:10px;margin:18px 0 10px}.sec span{font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;font-weight:700;color:#16794D;white-space:nowrap}.sec .ln{flex:1;height:1px;background:#E3E8EF}
.note{border-left:3.5px solid #16794D;background:#E7F5EC;border-radius:0 10px 10px 0;padding:10px 14px;margin:7px 0;font-size:.88rem;line-height:1.55}
.note.warn{border-color:#B7791F;background:#FBF3E2}.note.alert{border-color:#C53929;background:#FBEAE7}
.metric{background:#fff;border:1px solid #E3E8EF;border-top:3px solid #16794D;border-radius:0 0 14px 14px;padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,.04);height:100%}
.metric .ml{font-size:.66rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#64748B;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.metric .mv{font-size:1.5rem;font-weight:800;line-height:1.15;margin-top:6px;word-break:break-word}.metric .ms{font-size:.71rem;color:#64748B;margin-top:4px;line-height:1.4}
.card{background:#fff;border:1px solid #E3E8EF;border-radius:16px;box-shadow:0 1px 6px rgba(15,40,70,.05)}
.legend{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;font-size:.76rem;margin-top:8px}.legend .li{display:flex;align-items:center;gap:5px}.legend .sw{width:9px;height:9px;border-radius:2px}
.brk{margin-bottom:11px}.brk .l{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}.brk .nm{font-size:.88rem;font-weight:500}.brk .sc{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.84rem}
.brk .bar{height:6px;background:rgba(0,0,0,.07);border-radius:3px;overflow:hidden}.brk .bar i{display:block;height:100%;border-radius:3px}
.subscore{background:#fff;border:1px solid #E3E8EF;border-radius:12px;padding:12px 14px;margin-bottom:8px}
.subscore .h{display:flex;justify-content:space-between;align-items:baseline}.subscore .t{font-size:.8rem;font-weight:700}.subscore .v{font-family:'JetBrains Mono',monospace;font-weight:800;font-size:1.05rem}.subscore .d{font-size:.74rem;color:#64748B;margin-top:2px}
.opt-item{background:#fff;border:1px solid #E3E8EF;border-left:3px solid #16794D;border-radius:0 10px 10px 0;padding:9px 14px;margin-bottom:5px;font-size:.88rem}
.tierhead{border:1px solid #E3E8EF;border-left:4px solid #16794D;border-radius:0 14px 14px 0;padding:15px 18px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.04)}.tierhead h3{font-size:1.5rem;font-weight:800}.tierhead .er{font-size:.82rem;color:#64748B;margin-top:3px}
.cmp{width:100%;border-collapse:collapse;border:1px solid #E3E8EF;border-radius:12px;overflow:hidden}
.cmp th{background:#16794D;color:#fff;text-align:left;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;font-weight:600;padding:8px 11px;white-space:nowrap}
.cmp td{padding:9px 11px;border-bottom:1px solid #E3E8EF;font-family:'JetBrains Mono',monospace;font-size:.82rem}.cmp td.tn{font-family:'Plus Jakarta Sans',sans-serif;font-weight:700}
.cmpnote{font-size:.7rem;color:#64748B;margin-top:6px;line-height:1.5}.diag{font-size:.7rem;color:#94A3B8;font-style:italic;margin:2px 0 6px}
.rrow{background:#fff;border:1px solid #E3E8EF;border-radius:10px;padding:9px 13px;margin-bottom:7px}.rrow .top{display:flex;justify-content:space-between;align-items:center}.rrow .name{font-weight:700;font-size:.88rem}.rrow .val{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.88rem}.rrow .val .id{color:#94A3B8;font-weight:400;font-size:.78rem}.rrow .hint{font-size:.7rem;color:#64748B;margin-top:2px}
.scen{border:1px solid #E3E8EF;border-top:3px solid #16794D;border-radius:0 0 12px 12px;padding:13px 15px;background:#fff}.scen .sl{font-size:.66rem;font-weight:700;text-transform:uppercase;color:#64748B}.scen .sv{font-family:'JetBrains Mono',monospace;font-size:1.25rem;font-weight:700;margin-top:5px}.scen .sd{font-family:'JetBrains Mono',monospace;font-size:.78rem;margin-top:3px}
.goalwrap{background:linear-gradient(120deg,#0E5C39,#16794D);border-radius:18px;padding:18px 20px;color:#fff;box-shadow:0 6px 22px rgba(14,92,57,.22)}
.goalwrap .gt{font-size:.7rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#BFE6CF}.goalwrap h3{font-size:1.2rem;font-weight:800;margin-top:3px;color:#fff!important}.goalwrap .gsub{font-size:.82rem;color:#CDEAD9;margin-top:3px}
.ptrack{height:14px;border-radius:8px;background:rgba(255,255,255,.18);overflow:hidden;position:relative;margin-top:6px}.ptrack .pp{height:100%;background:rgba(255,255,255,.45);position:absolute;left:0;top:0;border-radius:8px}.ptrack .pn{height:100%;background:#9BE7BC;position:absolute;left:0;top:0;border-radius:8px}
.plab{display:flex;justify-content:space-between;font-size:.74rem;color:#CDEAD9;margin-top:6px;font-family:'JetBrains Mono',monospace}
.gstat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);border-radius:12px;padding:11px 13px}.gstat .l{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#BFE6CF}.gstat .v{font-family:'JetBrains Mono',monospace;font-size:1.05rem;font-weight:700;margin-top:3px}.gstat .s{font-size:.66rem;color:#CDEAD9;margin-top:2px}
.readwrap{border:1px solid #E3E8EF;border-left:4px solid #16794D;border-radius:0 14px 14px 0;padding:16px 20px}.readwrap .ov{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748B}.readwrap .rt{font-size:1.65rem;font-weight:800}.readwrap .rd{font-size:.85rem;color:#64748B;margin-top:5px;line-height:1.5}
.action{background:#fff;border:1px solid #E3E8EF;border-radius:0 14px 14px 0;padding:13px 16px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.03)}.action .ah{display:flex;align-items:center;gap:10px;margin-bottom:5px;flex-wrap:wrap}.action .num{color:#fff;font-size:.78rem;font-weight:800;width:24px;height:24px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center}.action .tag{font-size:.6rem;font-weight:700;padding:2px 9px;border-radius:20px;text-transform:uppercase;letter-spacing:.05em}.action .at{font-size:.97rem;font-weight:700}.action .ad{font-size:.87rem;color:#64748B;line-height:1.6;padding-left:34px}
.stNumberInput input,.stTextInput input,.stTextArea textarea{background:#fff!important;border:1.5px solid #E3E8EF!important;border-radius:10px!important;color:#1E2A32!important;font-family:'JetBrains Mono',monospace!important}
.stNumberInput label,.stTextInput label,.stSelectbox label,.stSlider label,.stRadio label{font-size:.7rem!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.03em!important;color:#64748B!important}
.stSelectbox div[data-baseweb="select"]>div{background:#fff!important;border:1.5px solid #E3E8EF!important;border-radius:10px!important}
.stButton>button{background:#16794D;color:#fff;border:none;border-radius:50px;font-weight:600;padding:9px 18px;box-shadow:0 2px 8px rgba(22,121,77,.2);width:100%}
.stButton>button:hover{background:#0E5C39;color:#fff}
.stButton>button[kind="secondary"],button[data-testid="stBaseButton-secondary"]{background:#fff!important;color:#1E2A32!important;border:1.5px solid #E3E8EF!important;box-shadow:none!important}
.stButton>button[kind="secondary"]:hover,button[data-testid="stBaseButton-secondary"]:hover{border-color:#16794D!important;color:#16794D!important}
.stDownloadButton>button{background:#13243B;color:#fff;border:none;border-radius:11px;font-weight:700;padding:12px;width:100%}
div[data-testid="stRadio"] [role="radiogroup"]>label{padding:7px 11px;border-radius:9px;margin-bottom:2px}
div[data-testid="stRadio"] [role="radiogroup"]>label:hover{background:#E7F5EC}
[data-testid="stExpander"]{border:1px solid #E3E8EF!important;border-radius:12px!important;background:#fff}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border-radius:12px;overflow:hidden;border:1px solid #D8E6DD}
</style>
"""
STEP_META=[("budget","Budget","📁","#F59E0B","#FBEFD8","Budget","Know your financial health & risk before investing"),
           ("health","Fin. Health","💎","#06B6D4","#D6F1F7","Financial Health","Set your goal, then score your fitness to reach it"),
           ("portfolio","Portfolio","◔","#7C3AED","#ECE6FB","Portfolio Diversification","Explore investment tiers"),
           ("markets","Markets","📈","#F97316","#FCE7D6","Market Research","Live prices & fundamentals — US & Australian markets"),
           ("actions","Actions","✅","#10B981","#D7F5E6","Action Plan","Get your personalised plan")]
fmt=lambda n:"$"+format(int(round(n)),",")

# ════════════════════════════ STATE ════════════════════════════
def init_state():
    d={"step":1,"max_step":1,"income_primary":6000,"income_secondary":0,"savings":15000,
       "total_assets":60000,"total_liabilities":20000,"employer_contrib":0,
       "age":35,"dependents":0,"has_insurance":True,"tax_adv_pct":50,"inflation":2.5,"tax_drag_max":1.5,
       "entry_mode":"individual","total_expenses":0,"selected_tier":"Defensive",
       "country":"United States","goal_mode":"income","goal_income":5000,"goal_lump":1000000,"goal_years":25,
       "fb_rating":0,"fb_name":"","fb_text":"","fb_sent":False,
       **{f"quiz_q{i}":2 for i in range(1,11)}}
    for k,v in d.items(): st.session_state.setdefault(k,v)
    if "expenses_df" not in st.session_state:
        st.session_state["expenses_df"]=pd.DataFrame(DEFAULT_EXP,columns=["Expense","Category","Amount"])
init_state(); ss=st.session_state
def goto(s): ss["step"]=s; ss["max_step"]=max(ss["max_step"],s)

# ════════════════════════════ SHELL ════════════════════════════
st.markdown(CSS,unsafe_allow_html=True)
step=ss["step"]; meta=STEP_META[step-1]; accent,abg=meta[3],meta[4]
dots="".join(f'<i class="{"on" if i<step else ""}"></i>' for i in range(5))
st.markdown(f'<div class="topbar"><div><h1>Seralung Finance</h1><p>Understand Risk. Invest with Confidence.</p></div>'
            f'<div class="pillc"><span>{step}/5 steps complete</span><span class="dotz">{dots}</span></div></div>',unsafe_allow_html=True)
nav=""
for i,m in enumerate(STEP_META):
    n=i+1; a=m[3]
    if n<step: cls,inner="done",f'<div class="circle" style="background:{a};border-color:{a};color:#fff">✓</div>'
    elif n==step: cls,inner="active",f'<div class="circle" style="border-color:{a};color:{a};box-shadow:0 0 0 4px {a}33">{n}</div>'
    elif n<=ss["max_step"]: cls,inner="",f'<div class="circle">{n}</div>'
    else: cls,inner="",'<div class="circle">🔒</div>'
    lncol=a if n<step else "#E3E8EF"
    lbl=m[1].replace(" ","<br>",1) if m[1]=="Fin. Health" else m[1]
    nav+=f'<div class="snode {cls}"><div class="line" style="background:{lncol}"></div>{inner}<div class="lbl" style="{"color:"+a if n==step else ""}">{lbl}</div></div>'
st.markdown(f'<div class="stepnav">{nav}</div>',unsafe_allow_html=True)
cp='<span class="cp">✓ COMPLETE</span>' if step<ss["max_step"] else ""
st.markdown(f'<div class="banner" style="background:{abg}"><div class="bi" style="background:{accent}">{meta[2]}</div>'
            f'<div><span class="pl" style="background:{accent}">STEP {step} OF 5</span>{cp}<h2>{meta[5]}</h2><div class="sb">{meta[6]}</div></div></div>',unsafe_allow_html=True)

def sec(l): st.markdown(f'<div class="sec"><span>{l}</span><div class="ln"></div></div>',unsafe_allow_html=True)
def note(t,k="info"): st.markdown(f'<div class="note {k}">{t}</div>',unsafe_allow_html=True)
def mcard(l,v,s,clr="#16794D",bg="#fff"):
    return f'<div class="metric" style="border-top-color:{clr};background:{bg}"><div class="ml">{l}</div><div class="mv" style="color:{clr}">{v}</div><div class="ms">{s}</div></div>'

# ════════════════════════════ STEP 1 — BUDGET ════════════════════════════
def assess_health(b):
    """Assemble inputs and run the institutional engine + a complementary MC probability."""
    capL=cap_level(capacity(b))[0]; tolL=tol_profile(ss)[1]; rec=rec_tier(capL,tolL)
    rp,sd=TIER_M[rec]["rp"],TIER_M[rec]["sd"]
    surplus=max(0,b["surplus"])+sf(ss["employer_contrib"])
    T=goal_target(ss); years=int(sf(ss["goal_years"]) or 1)
    res=calculate_institutional_financial_health(
        age=int(sf(ss["age"]) or 18),dependents=int(sf(ss["dependents"])),
        monthly_income=b["income"],monthly_essentials=b["essential"],monthly_surplus=surplus,
        current_savings=b["cash"],total_assets=sf(ss["total_assets"]),total_liabilities=sf(ss["total_liabilities"]),
        debt_repayment=b["debt"],has_basic_insurance=bool(ss["has_insurance"]),
        tax_advantaged_ratio=sf(ss["tax_adv_pct"])/100,target_goal_lump=T,years_to_goal=years,
        portfolio_return_nominal=rp,inflation_rate=sf(ss["inflation"])/100,tax_drag_max=sf(ss["tax_drag_max"])/100)
    actual_drag=sf(ss["tax_drag_max"])/100*(1-sf(ss["tax_adv_pct"])/100)
    ga=goal_assess(b["cash"],surplus,rp,sd,T,years,sf(ss["inflation"])/100,actual_drag)
    return res,ga,rec,capL,tolL,surplus,T,years

def page_budget():
    note("Enter your income, balance sheet and expenses below — every metric recalculates live as you type.")
    sec("Income, Savings &amp; Balance Sheet")
    a=st.columns(3)
    a[0].number_input("Monthly after-tax income ($)",min_value=0,step=250,key="income_primary")
    a[1].number_input("Secondary income (optional)",min_value=0,step=100,key="income_secondary")
    a[2].number_input("Emergency cash savings ($)",min_value=0,step=1000,key="savings")
    c=st.columns(3)
    c[0].number_input("Total assets — investments, super, property ($)",min_value=0,step=5000,key="total_assets",help="Everything except your liquid emergency cash. Drives your net-worth / solvency pillar.")
    c[1].number_input("Total liabilities — all debt principal ($)",min_value=0,step=5000,key="total_liabilities",help="Mortgage + student loans + card balances. Net worth = cash + assets − liabilities.")
    c[2].number_input("Employer / retirement contribution ($/mo)",min_value=0,step=50,key="employer_contrib",help="Super / 401k match — added to your monthly contribution toward the goal.")
    sec("Your bills &amp; expenses")
    t1,_=st.columns([1,3])
    mode=t1.radio("Entry mode",["Enter Individually","Enter Total at Once"],index=0 if ss["entry_mode"]=="individual" else 1,label_visibility="collapsed")
    ss["entry_mode"]="individual" if mode=="Enter Individually" else "total"
    if ss["entry_mode"]=="total":
        st.number_input("Total monthly expenses ($)",min_value=0,step=100,key="total_expenses")
    else:
        st.caption("Edit any cell · use + below the table to add a row · select a row and press ⌫ to delete")
        ss["expenses_df"]=st.data_editor(ss["expenses_df"],num_rows="dynamic",use_container_width=True,key="exp_editor",
            column_config={"Expense":st.column_config.TextColumn("Expense",width="large"),
                "Category":st.column_config.SelectboxColumn("Category",options=CATS,width="medium"),
                "Amount":st.column_config.NumberColumn("Amount ($/mo)",min_value=0,step=10,format="%d")})
    b=compute_budget(ss); ss["budget"]=b
    if b["income"]<=0: note("Enter your monthly income above to see your budget analysis.","warn"); return
    sec("Budget Summary")
    sc="#16794D" if b["surplus"]>0 else "#C53929"; sbg="#E7F5EC" if b["surplus"]>0 else "#FBEAE7"
    srC="#16794D" if b["sr"]>=.2 else("#B7791F" if b["sr"]>=.1 else "#C53929"); srBg="#E7F5EC" if b["sr"]>=.2 else("#FBF3E2" if b["sr"]>=.1 else "#FBEAE7")
    g=st.columns(4)
    g[0].markdown(mcard("Total Income",fmt(b["income"]),"Per month","#1E2A32"),unsafe_allow_html=True)
    g[1].markdown(mcard("Total Expenses",fmt(b["total"]),f"{b['total']/b['income']*100:.0f}% of income","#B7791F","#FBF3E2"),unsafe_allow_html=True)
    g[2].markdown(mcard("Monthly Surplus",(fmt(b["surplus"]) if b["surplus"]>=0 else "-"+fmt(-b["surplus"])),"Income − expenses",sc,sbg),unsafe_allow_html=True)
    g[3].markdown(mcard("Savings Rate",f"{b['sr']*100:.1f}%","Surplus / income",srC,srBg),unsafe_allow_html=True)
    nw=b["cash"]+sf(ss["total_assets"])-sf(ss["total_liabilities"]); nwc="#16794D" if nw>=0 else "#C53929"
    g2=st.columns(4)
    g2[0].markdown(mcard("Net Worth",(fmt(nw) if nw>=0 else "-"+fmt(-nw)),"Cash + assets − debt",nwc,"#fff"),unsafe_allow_html=True)
    g2[1].markdown(mcard("Liquid Cash",fmt(b["cash"]),"Emergency reserve","#0E7C7B","#DFF2F1"),unsafe_allow_html=True)
    g2[2].markdown(mcard("Invested Assets",fmt(sf(ss["total_assets"])),"Super / ETFs / property","#16794D","#E7F5EC"),unsafe_allow_html=True)
    g2[3].markdown(mcard("Total Debt",fmt(sf(ss["total_liabilities"])),"Outstanding principal","#C53929","#FBEAE7"),unsafe_allow_html=True)
    if ss["entry_mode"]=="individual" and b["cat_sums"]:
        sec("Where Your Money Goes")
        d1,d2=st.columns(2)
        pal=ASSET_CLR+["#0E7C7B","#B7791F","#7C3AED","#3DA968","#C53929","#6B7280","#16794D","#0E7C7B"]
        segs=[(k,v,pal[i]) for i,(k,v) in enumerate(sorted(b["cat_sums"].items(),key=lambda x:-x[1]))]
        d1.markdown(f'<div class="card" style="padding:16px">{donut(segs,fmt(b["total"]))}{legend(segs)}</div>',unsafe_allow_html=True)
        rc="#16794D" if b["runway"]>=6 else("#B7791F" if b["runway"]>=3 else "#C53929"); rcb="#E7F5EC" if b["runway"]>=6 else("#FBF3E2" if b["runway"]>=3 else "#FBEAE7")
        d2.markdown(mcard("Emergency Fund Runway",f"{b['runway']:.1f} months",f"{fmt(b['cash'])} cash ÷ {fmt(b['essential'])}/mo essentials",rc,rcb),unsafe_allow_html=True)
        if b["runway"]<3: d2.markdown('<div class="note alert">Your emergency fund is below 3 months. This is the most important fix before investing.</div>',unsafe_allow_html=True)
        elif b["runway"]<6: d2.markdown('<div class="note warn">Aim for 6 months of essentials before investing.</div>',unsafe_allow_html=True)
        else: d2.markdown('<div class="note">Healthy buffer — solid foundation to invest from.</div>',unsafe_allow_html=True)
        sec("Budget Mix Diagnostic (50 / 30 / 20)")
        st.markdown('<div class="diag">A budgeting reference only — this does <b>not</b> affect your financial health score.</div>',unsafe_allow_html=True)
        nr=b["needs"]/b["income"]*100; wr=b["wants"]/b["income"]*100; sv=max(0,b["surplus"])/b["income"]*100
        for name,val,ideal,hint in [("Needs",nr,50,"housing, food, transport, insurance, debt"),("Wants",wr,30,"dining, entertainment, shopping, travel"),("Savings",sv,20,"everything left over")]:
            ok=(val<=ideal+2) if name!="Savings" else (val>=ideal-2); clr="#16794D" if ok else "#B7791F"
            st.markdown(f'<div class="rrow"><div class="top"><span class="name">{name}</span><span class="val" style="color:{clr}">{val:.0f}%<span class="id"> / {ideal}%</span></span></div><div class="hint">{hint}</div></div>',unsafe_allow_html=True)

# ════════════════════════════ STEP 2 — FINANCIAL HEALTH ════════════════════════════
def _bars(items):
    out=""
    for label,gv,mx in items:
        p=gv/mx*100 if mx else 0; cc="#16794D" if p>=70 else("#B7791F" if p>=40 else "#C53929")
        out+=f'<div class="brk"><div class="l"><span class="nm">{label}</span><span class="sc" style="color:{cc}">{gv:g}/{mx}</span></div><div class="bar"><i style="width:{p:.0f}%;background:{cc}"></i></div></div>'
    return out

def page_health():
    b=ss.get("budget") or compute_budget(ss)
    st.markdown('<div class="goalwrap"><div class="gt">Ultimate Goal</div>'
                '<h3>Set your destination — health is measured against it</h3>'
                '<div class="gsub">Health blends your resilience now (50) with your readiness to reach this goal (50).</div></div>',unsafe_allow_html=True)
    gm=st.radio("Goal type",["Target passive income","Target lump sum"],index=0 if ss["goal_mode"]=="income" else 1,horizontal=True,label_visibility="collapsed")
    ss["goal_mode"]="income" if gm=="Target passive income" else "lumpsum"
    gc=st.columns(2)
    if ss["goal_mode"]=="income": gc[0].number_input("Desired passive income ($/month, today's $)",min_value=0,step=250,key="goal_income")
    else: gc[0].number_input("Target lump sum ($, today's $)",min_value=0,step=10000,key="goal_lump")
    gc[1].number_input("Years until you want it",min_value=1,max_value=60,step=1,key="goal_years")
    sec("About You")
    ac=st.columns(4)
    ac[0].number_input("Age",min_value=18,max_value=90,step=1,key="age")
    ac[1].number_input("Financial dependents",min_value=0,max_value=10,step=1,key="dependents",help="More dependents = a deeper emergency buffer is required (target rises from 6 to 9 months).")
    ac[2].slider("Tax-advantaged share of investments (%)",0,100,key="tax_adv_pct",help="Super / 401k etc. A higher share cuts the tax drag on your returns.")
    ac[3].checkbox("I have adequate insurance",key="has_insurance",help="Life / health / income protection — worth 15 resilience points.")
    with st.expander("⚙ Assumptions (inflation & tax drag)"):
        e=st.columns(2)
        e[0].number_input("Inflation (% per year)",min_value=0.0,max_value=10.0,step=0.1,key="inflation",help="Goal & projections are in today's purchasing power.")
        e[1].number_input("Max tax drag in retail accounts (% per year)",min_value=0.0,max_value=3.0,step=0.1,key="tax_drag_max",help="Reduced by your tax-advantaged share.")

    if b["income"]<=0:
        note("Complete the Budget step first — your score is built from your income, balance sheet, this goal and your assumptions.","warn"); return

    res,ga,rec,capL,tolL,surplus,T,years=assess_health(b)
    total=res["total_score"]; rt,clr,bg=rating(total); bd=res["breakdown"]; dg=res["diagnostics"]; pj=res["projections"]
    res_pts=bd["liquidity_elasticity"]+bd["savings_efficiency"]+bd["insurance_security"]
    rdy_pts=bd["goal_trajectory"]+bd["solvency_leverage"]+bd["debt_risk"]
    readiness=round(ga["prob"]*100)

    sec("Financial Health Score")
    h1,h2=st.columns([1,1.15])
    h1.markdown(f'<div class="card" style="padding:16px;text-align:center">{gauge(total,clr)}'
                f'<div style="margin-top:2px"><span style="background:{bg};color:{clr};font-weight:700;font-size:.95rem;padding:5px 20px;border-radius:20px;display:inline-block">{res["rating_category"]}</span></div>'
                f'<div style="font-size:.72rem;color:#64748B;margin-top:8px">Resilience {res_pts:g}/50 · Readiness {rdy_pts:g}/50</div></div>',unsafe_allow_html=True)
    resilience_bars=_bars([("Liquidity &amp; elasticity",bd["liquidity_elasticity"],20),("Savings efficiency",bd["savings_efficiency"],15),("Insurance &amp; security",bd["insurance_security"],15)])
    readiness_bars=_bars([("Goal trajectory",bd["goal_trajectory"],30),("Solvency &amp; leverage",bd["solvency_leverage"],10),("Cash-flow debt risk",bd["debt_risk"],10)])
    h2.markdown(f'<div class="subscore"><div class="h"><span class="t">🛡 Current Resilience</span><span class="v" style="color:#16794D">{res_pts:g}/50</span></div></div>{resilience_bars}'
                f'<div class="subscore" style="margin-top:8px"><div class="h"><span class="t">🎯 Future Readiness</span><span class="v" style="color:#16794D">{rdy_pts:g}/50</span></div></div>{readiness_bars}',unsafe_allow_html=True)
    note(f"Your financial health is <b>{rt}</b> — {res_pts:g}/50 resilience now and {rdy_pts:g}/50 readiness for your goal. Monte-Carlo cross-check: about a <b>{readiness}% chance</b> of reaching {fmt(T)} with the {rec} portfolio.",
         "good" if total>=65 else("warn" if total>=45 else "alert"))

    sec("Where You Stand")
    nowp=min(100,b["cash"]/T*100) if T>0 else 0; projp=min(100,pj["inflation_adjusted_fv"]/T*100) if T>0 else 0
    nw=dg["net_worth"]
    st.markdown(f'<div class="goalwrap"><div class="gt">Progress to {fmt(T)} (today\'s $)</div>'
                f'<div class="ptrack"><div class="pp" style="width:{projp}%"></div><div class="pn" style="width:{nowp}%"></div></div>'
                f'<div class="plab"><span>Cash now: {nowp:.1f}%</span><span>Projected in {years}y: {fmt(pj["inflation_adjusted_fv"])} ({projp:.0f}%)</span></div>'
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px">'
                f'<div class="gstat"><div class="l">Goal target</div><div class="v">{fmt(T)}</div><div class="s">{("$%s/mo via 4%% rule"%format(int(sf(ss["goal_income"])),",")) if ss["goal_mode"]=="income" else "lump sum, today\'s $"}</div></div>'
                f'<div class="gstat"><div class="l">Chance of success</div><div class="v">{readiness}%</div><div class="s">Monte Carlo, real terms</div></div>'
                f'<div class="gstat"><div class="l">Projected value</div><div class="v">{fmt(pj["inflation_adjusted_fv"])}</div><div class="s">@ {dg["real_compounding_rate"]*100:.1f}% real, after tax</div></div>'
                f'<div class="gstat"><div class="l">To stay on track</div><div class="v">{fmt(pj["required_monthly_surplus"])}/mo</div><div class="s">vs your {fmt(surplus)}/mo now</div></div>'
                f'</div></div>',unsafe_allow_html=True)
    sec("Solvency &amp; Assumptions")
    dcol=st.columns(4)
    nwc="#16794D" if nw>=dg["target_net_worth"] else("#B7791F" if nw>=0 else "#C53929")
    dcol[0].markdown(mcard("Net Worth",(fmt(nw) if nw>=0 else "-"+fmt(-nw)),f"Age-target: {fmt(dg['target_net_worth'])}",nwc,"#fff"),unsafe_allow_html=True)
    dcol[1].markdown(mcard("Real Return Used",f"{dg['real_compounding_rate']*100:.2f}%",f"{rec} tier, after inflation & tax","#0E7C7B","#DFF2F1"),unsafe_allow_html=True)
    dcol[2].markdown(mcard("Actual Tax Drag",f"{dg['actual_tax_drag']*100:.2f}%",f"{int(sf(ss['tax_adv_pct']))}% tax-advantaged","#B7791F","#FBF3E2"),unsafe_allow_html=True)
    dcol[3].markdown(mcard("Target Runway",f"{dg['target_runway_months']} months",f"{int(sf(ss['dependents']))} dependents","#16794D","#E7F5EC"),unsafe_allow_html=True)
    if total>=80: note("Strong across both halves — resilient now and on track for your goal.","good")
    elif rdy_pts<25: note(f"Your readiness is the weak half ({rdy_pts:g}/50). Lift contributions toward {fmt(pj['required_monthly_surplus'])}/mo, extend the horizon, or explore a higher-growth tier on the Portfolio step.","warn")
    elif res_pts<30: note(f"Your resilience is the weak half ({res_pts:g}/50). Build your buffer, insurance and savings rate before adding market risk.","warn")

    sec("Risk Profile — 10 Questions")
    note("These set your comfort with volatility, which picks your suggested portfolio (and the return used above).")
    for i,(q,opts) in enumerate(QUESTIONS):
        st.markdown(f'<div style="background:#fff;border:1px solid #E3E8EF;border-radius:14px;padding:12px 16px 4px;margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,.03)">'
                    f'<span style="background:#D6F1F7;color:#0E7490;font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:5px;font-family:JetBrains Mono">{i+1:02d}/10</span> '
                    f'<b style="font-size:.95rem">{q}</b></div>',unsafe_allow_html=True)
        st.radio(q,list(range(4)),format_func=lambda x,o=opts:o[x],key=f"quiz_q{i+1}",label_visibility="collapsed",horizontal=True)
    sec("Risk Analysis")
    tname,tolL2,tscore=tol_profile(ss); capL2,capW=cap_level(capacity(b))
    r1,r2,r3=st.columns(3)
    r1.markdown(mcard("Risk Tolerance",tname,f"Level {tolL2}/5 · score {tscore}/40",TIER_CLR.get(rec,'#16794D'),"#E7F5EC"),unsafe_allow_html=True)
    capclr=["#C53929","#C53929","#B7791F","#0E7C7B","#16794D"][capL2-1]; capbg=["#FBEAE7","#FBEAE7","#FBF3E2","#DFF2F1","#E7F5EC"][capL2-1]
    r2.markdown(mcard("Risk Capacity",capW,f"Level {capL2}/5 · from your budget",capclr,capbg),unsafe_allow_html=True)
    r3.markdown(mcard("Suggested Tier",rec,"Prudent match (lower of the two)",TIER_CLR[rec],TIER_BG[rec]),unsafe_allow_html=True)

# ════════════════════════════ STEP 3 — PORTFOLIO ════════════════════════════
def page_portfolio():
    b=ss.get("budget") or compute_budget(ss)
    capL=cap_level(capacity(b))[0]; tolL=tol_profile(ss)[1]; rec=rec_tier(capL,tolL); recClr=TIER_CLR.get(rec,"#16794D")
    note("Five model portfolios from lowest to highest risk, with key risk and return figures for each.")
    note(f'Based on your risk capacity and tolerance, your suggested starting tier is <b style="color:{recClr}">{rec}</b>.')
    sec("Choose a tier to explore")
    cols=st.columns(5)
    for i,t in enumerate(TIERS):
        if cols[i].button(("★ "+t) if t==rec else t,key=f"tier_{t}",type="primary" if t==ss["selected_tier"] else "secondary"):
            ss["selected_tier"]=t; st.rerun()
    t=ss["selected_tier"] if ss["selected_tier"] in TIERS else rec; m=TIER_M[t]; clr,bg=TIER_CLR[t],TIER_BG[t]
    d1,d2=st.columns(2)
    segs=[(f"{ASSETS[i]} {TIER_W[t][i]}%",TIER_W[t][i],ASSET_CLR[i]) for i in range(6) if TIER_W[t][i]>0]
    d1.markdown(f'<div class="card" style="padding:16px">{donut(segs,t)}{legend(segs)}</div>',unsafe_allow_html=True)
    title=f"{t} · suggested for you" if t==rec else t
    d2.markdown(f'<div class="tierhead" style="border-left-color:{clr};background:{bg}"><h3 style="color:{clr}">{title}</h3>'
                f'<div class="er">Expected return <b style="color:#1E2A32">{m["rp"]*100:.1f}%</b> p.a. · Volatility <b style="color:#1E2A32">{m["sd"]*100:.1f}%</b></div></div>',unsafe_allow_html=True)
    mm=d2.columns(2)
    mm[0].markdown(mcard("Sharpe Ratio",f"{m['sharpe']:.2f}","Return per unit of risk","#16794D","#E7F5EC"),unsafe_allow_html=True)
    mm[0].markdown(mcard("Value at Risk (95%)",f"{m['var95']*100:.1f}%","Worst year in 20 (1-yr)","#C53929","#FBEAE7"),unsafe_allow_html=True)
    mm[1].markdown(mcard("Diversification",f"{m['div']:.2f}×","Higher = better spread","#0E7C7B","#DFF2F1"),unsafe_allow_html=True)
    mm[1].markdown(mcard("Est. Max Drawdown",f"{m['maxdd']*100:.0f}%","Peak-to-trough estimate","#B7791F","#FBF3E2"),unsafe_allow_html=True)
    sec(f"Investment options for {t}")
    st.markdown("".join(f'<div class="opt-item" style="border-left-color:{clr}">{o}</div>' for o in TIER_OPT[t]),unsafe_allow_html=True)
    sec("All Tiers Compared")
    rows=""
    for tt in TIERS:
        mt=TIER_M[tt]; star=" ★" if tt==rec else ""
        rows+=(f'<tr style="background:{TIER_BG[tt] if tt==rec else "#fff"}"><td class="tn" style="color:{TIER_CLR[tt]}">{tt}{star}</td>'
               f'<td>{mt["rp"]*100:.1f}%</td><td>{mt["sd"]*100:.1f}%</td><td>{mt["sharpe"]:.2f}</td>'
               f'<td style="color:#C53929">{mt["var95"]*100:.1f}%</td><td style="color:#C53929">{mt["cvar95"]*100:.1f}%</td><td style="color:#B7791F">{mt["maxdd"]*100:.0f}%</td></tr>')
    st.markdown(f'<table class="cmp"><thead><tr><th>Tier</th><th>Exp. Return</th><th>Volatility</th><th>Sharpe</th><th>VaR 95%</th><th>CVaR 95%</th><th>Max DD</th></tr></thead><tbody>{rows}</tbody></table>'
                '<div class="cmpnote"><b>VaR 95%</b>: in the worst 1-in-20 year, losses are expected to exceed this. <b>CVaR 95%</b>: average loss in those worst years. <b>Max DD</b>: estimated peak-to-trough fall. Long-run assumptions, not forecasts.</div>',unsafe_allow_html=True)

# ════════════════════════════ HEALTH ENGINE (inlined) ════════════════════════════
"""
health_engine.py
================
Institutional Financial Health Score (out of 100), using a Weighted Hybrid Model
split evenly between Current Resilience (50) and Future Readiness (50).

The single public entry point is ``calculate_institutional_financial_health``.
It is pure (no I/O, no Streamlit) so it can be unit-tested and reused anywhere.
"""

from typing import Any, Dict


def _clamp(value: float, low: float, high: float) -> float:
    """Constrain *value* to the inclusive range [low, high]."""
    return max(low, min(high, value))


def calculate_institutional_financial_health(
    age: int,
    dependents: int,
    monthly_income: float,
    monthly_essentials: float,
    monthly_surplus: float,
    current_savings: float,
    total_assets: float,
    total_liabilities: float,
    debt_repayment: float,
    has_basic_insurance: bool,
    tax_advantaged_ratio: float,
    target_goal_lump: float,
    years_to_goal: int,
    portfolio_return_nominal: float,
    inflation_rate: float = 0.025,
    tax_drag_max: float = 0.015,
) -> Dict[str, Any]:
    """Compute a comprehensive Financial Health Score (0-100).

    The score is the sum of six sub-pillars across two equal halves:
      Current Resilience (50)  = Liquidity(20) + Savings Efficiency(15) + Insurance(15)
      Future Readiness  (50)  = Goal Trajectory(30) + Solvency(10) + Debt Risk(10)

    All monetary inputs are monthly unless their name says otherwise. Returns a
    dictionary with the total score, rating, per-pillar breakdown, diagnostics
    and forward projections. Every division is guarded against zero.
    """
    # ── Sanitise inputs (defensive: never trust the caller) ──────────────
    age = max(0, int(age))
    dependents = max(0, int(dependents))
    monthly_income = max(0.0, float(monthly_income))
    monthly_essentials = max(0.0, float(monthly_essentials))
    monthly_surplus = max(0.0, float(monthly_surplus))
    current_savings = max(0.0, float(current_savings))
    total_assets = max(0.0, float(total_assets))
    total_liabilities = max(0.0, float(total_liabilities))
    debt_repayment = max(0.0, float(debt_repayment))
    tax_advantaged_ratio = _clamp(float(tax_advantaged_ratio), 0.0, 1.0)
    target_goal_lump = max(0.0, float(target_goal_lump))
    years_to_goal = max(0, int(years_to_goal))
    inflation_rate = float(inflation_rate)
    tax_drag_max = max(0.0, float(tax_drag_max))

    # ════════════════════════════════════════════════════════════════════
    # PILLAR 1 — CURRENT RESILIENCE (50 pts)
    # ════════════════════════════════════════════════════════════════════

    # 1a. Liquidity & Elasticity (20) — emergency runway vs a dependents-aware target.
    #     More dependents => less budget elasticity => a deeper buffer is required.
    target_runway_months: int = 9 if dependents > 0 else 6
    if monthly_essentials > 0:
        runway_months: float = current_savings / monthly_essentials
    else:
        # No essential outgoings: any cash is effectively infinite runway.
        runway_months = float("inf") if current_savings > 0 else 0.0
    liquidity_pts: float = _clamp(runway_months / target_runway_months, 0.0, 1.0) * 20.0

    # 1b. Savings Efficiency (15) — surplus as a share of income, benchmarked to 25%.
    if monthly_income > 0:
        savings_rate: float = monthly_surplus / monthly_income
    else:
        savings_rate = 0.0
    savings_pts: float = _clamp(savings_rate / 0.25, 0.0, 1.0) * 15.0

    # 1c. Structural Security & Insurance (15) — binary risk-mitigation gate.
    insurance_pts: float = 15.0 if has_basic_insurance else 0.0

    resilience_total: float = liquidity_pts + savings_pts + insurance_pts

    # ════════════════════════════════════════════════════════════════════
    # PILLAR 2 — FUTURE READINESS (50 pts)
    # ════════════════════════════════════════════════════════════════════

    # 2a. Goal Trajectory with tax friction (30) — real, after-tax future value.
    #     Tax drag shrinks with the share held in tax-advantaged accounts.
    actual_tax_drag: float = tax_drag_max * (1.0 - tax_advantaged_ratio)
    net_return: float = portfolio_return_nominal - actual_tax_drag
    # Convert nominal-after-tax to a REAL rate so the goal stays in today's dollars.
    r_real: float = ((1.0 + net_return) / (1.0 + inflation_rate)) - 1.0

    i: float = r_real / 12.0           # monthly real rate
    m: int = years_to_goal * 12        # total months

    if abs(i) < 1e-12:
        # Zero real growth: simple accumulation of contributions on top of savings.
        future_value: float = current_savings + monthly_surplus * m
    else:
        growth: float = (1.0 + i) ** m
        future_value = current_savings * growth + monthly_surplus * ((growth - 1.0) / i)

    if target_goal_lump > 0:
        trajectory_pts: float = _clamp(future_value / target_goal_lump, 0.0, 1.0) * 30.0
    else:
        trajectory_pts = 0.0  # No goal defined => nothing to score against.

    # 2b. Total Solvency & Leverage (10) — net worth vs an age-based target.
    net_worth: float = current_savings + total_assets - total_liabilities
    annual_income: float = monthly_income * 12.0
    # Age-adjusted target multiple of income: age 30 -> 2x, age 50 -> 4x.
    target_nw_ratio: float = (age / 10.0) - 1.0
    target_nw_ratio = max(0.1, target_nw_ratio)  # guard tiny/negative early-age targets
    target_net_worth: float = target_nw_ratio * annual_income

    if net_worth < 0 or annual_income <= 0:
        solvency_pts: float = 0.0
        nw_ratio: float = net_worth / annual_income if annual_income > 0 else 0.0
    else:
        nw_ratio = net_worth / annual_income
        solvency_pts = _clamp(nw_ratio / target_nw_ratio, 0.0, 1.0) * 10.0

    # 2c. Cash-Flow Debt Risk (10) — debt-service ratio, full marks at/under 20%.
    if monthly_income > 0:
        dti: float = debt_repayment / monthly_income
    else:
        dti = 1.0  # no income but debt to service => maximum risk
    if dti <= 0.20:
        debt_pts: float = 10.0
    elif dti >= 0.40:
        debt_pts = 0.0
    else:
        # Linear taper from 10 pts at 20% DTI to 0 pts at 40% DTI.
        debt_pts = 10.0 * (1.0 - (dti - 0.20) / 0.20)

    readiness_total: float = trajectory_pts + solvency_pts + debt_pts

    # ════════════════════════════════════════════════════════════════════
    # AGGREGATE + CLASSIFY
    # ════════════════════════════════════════════════════════════════════
    raw_total: float = resilience_total + readiness_total
    total_score: int = int(round(_clamp(raw_total, 0.0, 100.0)))

    if total_score < 25:
        rating = "Critical"
    elif total_score < 45:
        rating = "At Risk"
    elif total_score < 65:
        rating = "Fair"
    elif total_score < 80:
        rating = "Good"
    else:
        rating = "Excellent"

    # Required monthly surplus to exactly hit the target on the expected real path.
    if target_goal_lump > 0 and m > 0:
        if abs(i) < 1e-12:
            required_surplus: float = max(0.0, (target_goal_lump - current_savings) / m)
        else:
            growth = (1.0 + i) ** m
            required_surplus = max(
                0.0, (target_goal_lump - current_savings * growth) * i / (growth - 1.0)
            )
    else:
        required_surplus = 0.0

    return {
        "total_score": total_score,
        "rating_category": rating,
        "breakdown": {
            "liquidity_elasticity": round(liquidity_pts, 1),
            "savings_efficiency": round(savings_pts, 1),
            "insurance_security": round(insurance_pts, 1),
            "goal_trajectory": round(trajectory_pts, 1),
            "solvency_leverage": round(solvency_pts, 1),
            "debt_risk": round(debt_pts, 1),
        },
        "diagnostics": {
            "net_worth": round(net_worth, 2),
            "real_compounding_rate": round(r_real, 4),
            "actual_tax_drag": round(actual_tax_drag, 4),
            "target_runway_months": target_runway_months,
            "target_net_worth": round(target_net_worth, 2),
        },
        "projections": {
            "inflation_adjusted_fv": round(future_value, 2),
            "target_gap": round(target_goal_lump - future_value, 2),
            "required_monthly_surplus": round(required_surplus, 2),
        },
    }


# ════════════════════════════ STEP 4 — MARKET RESEARCH (inlined) ════════════════════════════
"""
markets.py — Market Research for Seralung Finance.

Live US & Australian market data via the free ``yfinance`` library (Yahoo
Finance, no API key). Quotes are typically delayed up to ~20 minutes.
Segments: Stocks, ETFs, Real Estate (REITs), Bonds (bond ETFs — individual
bonds don't trade with public tickers the way shares do).

Top-5 lists are curated by market capitalisation / fund size, verified against
public rankings in June 2026 — EXAMPLES TO EXPLORE, never buy recommendations.

Set environment variable SERALUNG_DEMO=1 to run on deterministic synthetic
data (no internet needed) — used for testing and offline demos.
"""
import base64
import os
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st

try:
    import yfinance as yf
    YF_OK = True
except Exception:                                    # pragma: no cover
    YF_OK = False

SEGMENTS = ["Stocks", "ETFs", "Real Estate", "Bonds"]

COUNTRIES = {
    "United States": {
        "cur": "US$",
        "Stocks": [("NVDA", "NVIDIA"), ("AAPL", "Apple"), ("GOOGL", "Alphabet"),
                   ("MSFT", "Microsoft"), ("AMZN", "Amazon")],
        "ETFs": [("VOO", "Vanguard S&P 500"), ("VTI", "Vanguard Total Market"),
                 ("QQQ", "Invesco Nasdaq-100"), ("SCHD", "Schwab US Dividend"),
                 ("IWM", "iShares Russell 2000")],
        "Real Estate": [("WELL", "Welltower"), ("PLD", "Prologis"),
                        ("AMT", "American Tower"), ("EQIX", "Equinix"),
                        ("DLR", "Digital Realty")],
        "Bonds": [("BND", "Vanguard Total Bond"), ("AGG", "iShares Core US Aggregate"),
                  ("TLT", "iShares 20+ Yr Treasury"), ("LQD", "iShares IG Corporate"),
                  ("SGOV", "iShares 0-3 Mo Treasury")],
        "note": {"ETFs": "VOO, IVV and SPY all track the S&P 500 — we show VOO, the largest.",
                 "Bonds": "Individual bonds don't have public tickers — these are the largest bond ETFs."},
    },
    "Australia": {
        "cur": "A$",
        "Stocks": [("CBA.AX", "Commonwealth Bank"), ("BHP.AX", "BHP Group"),
                   ("WBC.AX", "Westpac Banking"), ("NAB.AX", "National Australia Bank"),
                   ("ANZ.AX", "ANZ Group")],
        "ETFs": [("VAS.AX", "Vanguard Australian Shares"), ("VGS.AX", "Vanguard MSCI Intl"),
                 ("IVV.AX", "iShares S&P 500"), ("A200.AX", "Betashares Australia 200"),
                 ("NDQ.AX", "Betashares Nasdaq 100")],
        "Real Estate": [("GMG.AX", "Goodman Group"), ("SCG.AX", "Scentre Group"),
                        ("SGP.AX", "Stockland"), ("DXS.AX", "Dexus"),
                        ("MGR.AX", "Mirvac Group")],
        "Bonds": [("VAF.AX", "Vanguard Aust. Fixed Interest"), ("VGB.AX", "Vanguard Aust. Govt Bond"),
                  ("IAF.AX", "iShares Core Composite Bond"), ("VBND.AX", "Vanguard Global Aggregate"),
                  ("BOND.AX", "SPDR S&P/ASX Bond")],
        "note": {"Bonds": "Individual bonds don't have public tickers — these are the largest ASX bond ETFs."},
    },
}
CODE2SYM = {"USD": "US$", "AUD": "A$", "GBP": "£", "GBp": "GBp ", "INR": "₹",
            "CAD": "C$", "EUR": "€", "JPY": "¥", "HKD": "HK$", "SGD": "S$",
            "NZD": "NZ$", "CHF": "CHF "}


# ════════════════════════════ DATA ════════════════════════════
def _demo_on() -> bool:
    return os.environ.get("SERALUNG_DEMO") == "1"


def _demo_series(symbol: str) -> pd.Series:
    idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=252, freq="B")
    rng = np.random.default_rng(abs(hash(symbol)) % (2 ** 31))
    p = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.011, 252)))
    return pd.Series(p, index=idx)


_DEMO_INFO = {"trailingPE": 21.4, "forwardPE": 18.9, "trailingPegRatio": 1.4,
              "priceToBook": 4.1, "enterpriseToEbitda": 13.2, "returnOnEquity": 0.24,
              "profitMargins": 0.21, "operatingMargins": 0.27, "revenueGrowth": 0.09,
              "earningsGrowth": 0.11, "freeCashflow": 8.4e9, "currentRatio": 1.8,
              "debtToEquity": 92.0, "dividendYield": 0.021, "payoutRatio": 0.34,
              "currency": "USD"}


@st.cache_data(ttl=300, show_spinner=False)
def load_history(symbol: str, period: str = "1y") -> Optional[pd.Series]:
    """Daily adjusted close history; None on any failure."""
    if _demo_on():
        return _demo_series(symbol)
    if not YF_OK:
        return None
    try:
        df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
        if df is None or df.empty or "Close" not in df:
            return None
        s = df["Close"].dropna()
        return s if len(s) >= 2 else None
    except Exception:
        return None


@st.cache_data(ttl=900, show_spinner=False)
def load_fundamentals(symbol: str) -> dict:
    """yfinance .info dict; {} on any failure (fields are often patchy)."""
    if _demo_on():
        return dict(_DEMO_INFO)
    if not YF_OK:
        return {}
    try:
        info = yf.Ticker(symbol).info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def stats_from_history(s: pd.Series) -> dict:
    v = np.asarray(s.values, dtype=float)
    last, prev = float(v[-1]), float(v[-2])
    day = last / prev - 1.0 if prev > 0 else 0.0
    yr = last / float(v[0]) - 1.0 if v[0] > 0 else 0.0
    lr = np.diff(np.log(np.clip(v, 1e-9, None)))
    vol = float(lr.std() * np.sqrt(252)) if lr.size > 1 else 0.0
    mu = float(lr.mean() * 252) if lr.size > 1 else 0.0
    # Illustrative 1-yr range: ±1σ (lognormal) around a CLAMPED drift (|mu_c| ≤ σ/2)
    # so uncertainty strictly dominates and the range brackets the current price.
    mu_c = float(np.clip(mu, -vol / 2.0, vol / 2.0))
    return {"last": last, "day": day, "yr": yr,
            "hi52": float(v.max()), "lo52": float(v.min()),
            "vol": vol, "mu": mu,
            "rng_lo": last * float(np.exp(mu_c - vol)),
            "rng_hi": last * float(np.exp(mu_c + vol))}


# ════════════════════ FUNDAMENTALS CHECKLIST ════════════════════
def _f(info: dict, key: str) -> Optional[float]:
    v = info.get(key)
    try:
        v = float(v)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _abbr(x: float) -> str:
    a = abs(x)
    for d, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if a >= d:
            return f"{x / d:,.2f}{suf}"
    return f"{x:,.0f}"


def fundamentals_rows(info: dict) -> dict:
    """Pure: turn a yfinance .info dict into an evaluated checklist.

    Returns {"rows":[{label,val,status,guide}], "passed":int, "rated":int}.
    status in good/warn/bad/na/info. Handles known yfinance quirks:
    debtToEquity is reported in PERCENT; dividendYield may arrive as a
    fraction (0.021) or a percent (2.1) depending on version.
    """
    rows = []

    def add(label, val, status, guide):
        rows.append({"label": label, "val": val, "status": status, "guide": guide})

    def low(v, good, warn):     # lower is better
        return "na" if v is None else ("good" if v <= good else "warn" if v <= warn else "bad")

    def high(v, good, warn):    # higher is better
        return "na" if v is None else ("good" if v >= good else "warn" if v >= warn else "bad")

    pe = _f(info, "trailingPE")
    add("P/E (trailing)", f"{pe:.1f}" if pe is not None else "N/A",
        low(pe, 25, 40), "≤25 guide — always compare to industry")
    fpe = _f(info, "forwardPE")
    add("P/E (forward)", f"{fpe:.1f}" if fpe is not None else "N/A",
        low(fpe, 22, 35), "what the market expects next year")
    peg = _f(info, "trailingPegRatio")
    if peg is None:
        peg = _f(info, "pegRatio")
    add("PEG ratio", f"{peg:.2f}" if peg is not None else "N/A",
        low(peg, 1.0, 2.0), "<1 cheap for its growth — estimate-driven")
    pb = _f(info, "priceToBook")
    add("Price / Book", f"{pb:.2f}" if pb is not None else "N/A",
        low(pb, 3, 6), "asset-based lens; key for banks & REITs")
    ee = _f(info, "enterpriseToEbitda")
    add("EV / EBITDA", f"{ee:.1f}" if ee is not None else "N/A",
        low(ee, 12, 18), "valuation including debt — robust across firms")

    roe = _f(info, "returnOnEquity")
    roe = roe * 100 if roe is not None else None
    add("Return on equity", f"{roe:.1f}%" if roe is not None else "N/A",
        high(roe, 15, 8), ">15% — check it isn't leverage-inflated")
    pm = _f(info, "profitMargins")
    pm = pm * 100 if pm is not None else None
    add("Profit margin", f"{pm:.1f}%" if pm is not None else "N/A",
        high(pm, 10, 5), "pricing power; watch the trend")
    rg = _f(info, "revenueGrowth")
    rg = rg * 100 if rg is not None else None
    add("Revenue growth (yoy)", f"{rg:+.1f}%" if rg is not None else "N/A",
        high(rg, 5, 0), "is the business actually growing?")
    fcf = _f(info, "freeCashflow")
    add("Free cash flow", _abbr(fcf) if fcf is not None else "N/A",
        "na" if fcf is None else ("good" if fcf > 0 else "bad"),
        "cash is harder to fake than earnings")

    cr = _f(info, "currentRatio")
    add("Current ratio", f"{cr:.2f}" if cr is not None else "N/A",
        high(cr, 1.5, 1.0), ">1.5 guide — not meaningful for banks")
    de = _f(info, "debtToEquity")
    de = de / 100.0 if de is not None else None     # yfinance reports PERCENT
    add("Debt / equity", f"{de:.2f}" if de is not None else "N/A",
        low(de, 1.5, 2.5), "<1.5 guide — banks run higher by design")

    dy = _f(info, "dividendYield")
    if dy is not None and dy <= 0.25:               # fraction -> percent
        dy *= 100
    add("Dividend yield", f"{dy:.2f}%" if dy is not None else "N/A",
        "info", "income — judge with the payout ratio below")
    pr = _f(info, "payoutRatio")
    pr = pr * 100 if pr is not None else None
    add("Payout ratio", f"{pr:.0f}%" if pr is not None else "N/A",
        "na" if pr is None else low(pr, 80, 100),
        "<80% sustainable; ≥100% often precedes a cut")

    rated = [r for r in rows if r["status"] in ("good", "warn", "bad")]
    passed = sum(1 for r in rated if r["status"] == "good")
    return {"rows": rows, "passed": passed, "rated": len(rated)}


# ════════════════════════════ SVG ════════════════════════════
def _b64img(svg: str, mw: int) -> str:
    b64 = base64.b64encode(svg.encode()).decode()
    return (f'<img src="data:image/svg+xml;base64,{b64}" '
            f'style="display:block;width:100%;max-width:{mw}px"/>')


def sparkline(vals, w: int = 130, h: int = 36) -> str:
    v = np.asarray([x for x in vals if np.isfinite(x)], dtype=float)
    if v.size < 2:
        return ""
    rng = (v.max() - v.min()) or 1.0
    xs = np.linspace(2, w - 2, v.size)
    ys = h - 4 - (v - v.min()) / rng * (h - 8)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    clr = "#16794D" if v[-1] >= v[0] else "#C53929"
    return _b64img(f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
                   f'<polyline points="{pts}" fill="none" stroke="{clr}" stroke-width="2" '
                   f'stroke-linejoin="round" stroke-linecap="round"/></svg>', w)


def big_chart(s: pd.Series, w: int = 640, h: int = 220) -> str:
    v = np.asarray(s.values, dtype=float)
    rng = (v.max() - v.min()) or 1.0
    xs = np.linspace(46, w - 10, v.size)
    ys = h - 26 - (v - v.min()) / rng * (h - 50)
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    clr = "#16794D" if v[-1] >= v[0] else "#C53929"
    area = f"46,{h-26} {pts} {w-10:.1f},{h-26}"
    grid = labels = ""
    for frac in (0.0, 0.5, 1.0):
        val = v.min() + frac * rng
        y = h - 26 - frac * (h - 50)
        grid += f'<line x1="46" y1="{y:.0f}" x2="{w-10}" y2="{y:.0f}" stroke="#EEF1F5"/>'
        labels += (f'<text x="42" y="{y+3:.0f}" text-anchor="end" font-size="10" '
                   f'fill="#94A3B8" font-family="JetBrains Mono">{val:,.0f}</text>')
    try:
        t0, t1 = s.index[0].strftime("%b %y"), s.index[-1].strftime("%b %y")
    except Exception:
        t0 = t1 = ""
    return _b64img(f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">{grid}'
                   f'<polygon points="{area}" fill="{clr}" opacity="0.08"/>'
                   f'<polyline points="{pts}" fill="none" stroke="{clr}" stroke-width="2.2" '
                   f'stroke-linejoin="round" stroke-linecap="round"/>{labels}'
                   f'<text x="46" y="{h-8}" font-size="10" fill="#94A3B8" '
                   f'font-family="Plus Jakarta Sans">{t0}</text>'
                   f'<text x="{w-10}" y="{h-8}" text-anchor="end" font-size="10" fill="#94A3B8" '
                   f'font-family="Plus Jakarta Sans">{t1}</text></svg>', w)


# ════════════════════════════ UI ════════════════════════════
def _sec(label):
    st.markdown(f'<div class="sec"><span>{label}</span><div class="ln"></div></div>',
                unsafe_allow_html=True)


def _note(t, k="info"):
    st.markdown(f'<div class="note {k}">{t}</div>', unsafe_allow_html=True)


def _mcard(l, v, s, clr="#16794D", bg="#fff"):
    return (f'<div class="metric" style="border-top-color:{clr};background:{bg}">'
            f'<div class="ml">{l}</div><div class="mv" style="color:{clr}">{v}</div>'
            f'<div class="ms">{s}</div></div>')


def _row(sym: str, name: str, s: Optional[pd.Series], cur: str) -> str:
    if s is None:
        return (f'<div class="mktrow"><div class="mi"><b>{name}</b>'
                f'<span class="msym">{sym}</span></div>'
                f'<div style="color:#94A3B8;font-size:.8rem">data unavailable</div></div>')
    q = stats_from_history(s)
    dc = "#16794D" if q["day"] >= 0 else "#C53929"
    yc = "#16794D" if q["yr"] >= 0 else "#C53929"
    return (f'<div class="mktrow"><div class="mi"><b>{name}</b>'
            f'<span class="msym">{sym}</span></div>'
            f'<div class="mq"><span class="mp">{cur}{q["last"]:,.2f}</span>'
            f'<span style="color:{dc}">{q["day"]*100:+.2f}% day</span>'
            f'<span style="color:{yc}">{q["yr"]*100:+.1f}% 1y</span></div>'
            f'<div class="mspark">{sparkline(s.values[-90:])}</div></div>')


_FCLR = {"good": "#16794D", "warn": "#B7791F", "bad": "#C53929",
         "na": "#94A3B8", "info": "#0E7C7B"}
_FTXT = {"good": "healthy", "warn": "borderline", "bad": "weak",
         "na": "no data", "info": "context"}


def page_markets():
    st.markdown("""<style>
.mktrow{background:#fff;border:1px solid #E3E8EF;border-radius:12px;padding:11px 16px;margin-bottom:7px;
  display:flex;align-items:center;gap:14px;box-shadow:0 1px 3px rgba(0,0,0,.03)}
.mktrow .mi{flex:1.4;display:flex;flex-direction:column}.mktrow .mi b{font-size:.92rem}
.mktrow .msym{font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#94A3B8}
.mktrow .mq{flex:1.6;display:flex;gap:16px;align-items:baseline;font-family:'JetBrains Mono',monospace;font-size:.8rem;flex-wrap:wrap}
.mktrow .mp{font-size:1.05rem;font-weight:700}
.mktrow .mspark{flex:0 0 130px}
.frow{background:#fff;border:1px solid #E3E8EF;border-radius:10px;padding:8px 13px;margin-bottom:6px;
  display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.frow .fl{flex:1.3;font-weight:600;font-size:.85rem;min-width:150px}
.frow .fv{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.88rem;min-width:80px}
.frow .fs{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;min-width:84px}
.frow .fg{flex:2;font-size:.72rem;color:#64748B}
@media(max-width:700px){.mktrow{flex-wrap:wrap}.mktrow .mspark{flex:1 1 100%}}
</style>""", unsafe_allow_html=True)

    _note("Live market data from Yahoo Finance (free — quotes are typically delayed up to "
          "~20 minutes depending on the exchange). Educational reference only, <b>not</b> a "
          "recommendation to buy or sell anything.")
    if not YF_OK and not _demo_on():
        _note("The <b>yfinance</b> package is not installed — add <code>yfinance</code> to "
              "requirements.txt and reboot the app.", "alert")
        return

    _sec("Choose a country &amp; market")
    c1, c2 = st.columns([1.4, 3])
    country = c1.selectbox("Country", list(COUNTRIES), key="country")
    seg = c2.radio("Segment", SEGMENTS, horizontal=True, key="mkt_seg",
                   label_visibility="collapsed")
    cdef = COUNTRIES[country]
    cur = cdef["cur"]

    _sec(f"Top 5 — {country} · {seg}")
    extra = cdef.get("note", {}).get(seg, "")
    st.markdown(f'<div class="diag">Curated by market size &amp; fund assets (verified June '
                f'2026) — examples to explore, <b>not</b> buy recommendations.'
                f'{" " + extra if extra else ""}</div>', unsafe_allow_html=True)
    data = {}
    with st.spinner("Fetching live prices…"):
        for sym, name in cdef[seg]:
            data[sym] = load_history(sym)
    st.markdown("".join(_row(sym, name, data[sym], cur) for sym, name in cdef[seg]),
                unsafe_allow_html=True)
    if all(v is None for v in data.values()):
        _note("Couldn't reach Yahoo Finance just now (it sometimes rate-limits shared "
              "servers). Wait a minute and press <b>Refresh data</b> below — or run the app "
              "locally.", "warn")

    _sec("Research a ticker")
    r1, r2, r3 = st.columns([2, 2, 1])
    pick = r1.selectbox("From the list", [f"{n} ({s})" for s, n in cdef[seg]],
                        key=f"mkt_pick_{country}_{seg}")
    custom = r2.text_input("…or any Yahoo symbol", key="mkt_custom",
                           placeholder="e.g. TSLA, WES.AX, VAP.AX")
    if r3.button("⟳ Refresh data", key="mkt_refresh", type="secondary"):
        for fn in (load_history, load_fundamentals):
            if hasattr(fn, "clear"):
                fn.clear()
        st.rerun()
    sym = custom.strip().upper() if custom.strip() else pick.split("(")[-1].rstrip(")")
    s = load_history(sym)
    if s is None:
        _note(f"No data for <b>{sym}</b> — check the symbol (ASX tickers end in <b>.AX</b>) "
              f"or try again shortly.", "warn")
        return

    info = load_fundamentals(sym)
    dcur = CODE2SYM.get(str(info.get("currency", "")), cur if not custom.strip() else "$")
    q = stats_from_history(s)
    dc = "#16794D" if q["day"] >= 0 else "#C53929"
    st.markdown(f'<div class="card" style="padding:16px 18px">'
                f'<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">'
                f'<div><b style="font-size:1.05rem">{sym}</b> '
                f'<span style="font-family:JetBrains Mono;font-size:1.3rem;font-weight:800;margin-left:10px">{dcur}{q["last"]:,.2f}</span> '
                f'<span style="font-family:JetBrains Mono;color:{dc};margin-left:6px">{q["day"]*100:+.2f}% today</span></div>'
                f'<span style="font-size:.72rem;color:#94A3B8">1-year daily closes · Yahoo Finance</span></div>'
                f'{big_chart(s)}</div>', unsafe_allow_html=True)
    g = st.columns(4)
    yc = "#16794D" if q["yr"] >= 0 else "#C53929"
    g[0].markdown(_mcard("1-Year Return", f"{q['yr']*100:+.1f}%", "Price change over the period",
                         yc, "#E7F5EC" if q["yr"] >= 0 else "#FBEAE7"), unsafe_allow_html=True)
    g[1].markdown(_mcard("52-Week Range", f"{q['lo52']:,.2f}–{q['hi52']:,.2f}", "Low – high",
                         "#0E7C7B", "#DFF2F1"), unsafe_allow_html=True)
    g[2].markdown(_mcard("Volatility", f"{q['vol']*100:.1f}%", "Annualised, from daily moves",
                         "#B7791F", "#FBF3E2"), unsafe_allow_html=True)
    g[3].markdown(_mcard("Illustrative 1-Yr Range", f"{q['rng_lo']:,.0f}–{q['rng_hi']:,.0f}",
                         "±1σ, drift clamped — NOT a forecast", "#7C3AED", "#ECE6FB"),
                  unsafe_allow_html=True)

    _sec(f"Fundamentals check — {sym}")
    if not info or len(info) < 3:
        _note("Fundamentals are unavailable for this symbol right now (Yahoo's data is "
              "patchy for some listings, and ETFs/bond funds have no company fundamentals). "
              "The price history above still works.", "warn")
    else:
        res = fundamentals_rows(info)
        rows_html = ""
        for r in res["rows"]:
            c = _FCLR[r["status"]]
            rows_html += (f'<div class="frow"><span class="fl">{r["label"]}</span>'
                          f'<span class="fv">{r["val"]}</span>'
                          f'<span class="fs" style="color:{c}">● {_FTXT[r["status"]]}</span>'
                          f'<span class="fg">{r["guide"]}</span></div>')
        st.markdown(rows_html, unsafe_allow_html=True)
        sc = "#16794D" if res["passed"] >= res["rated"] * 0.7 else \
             ("#B7791F" if res["passed"] >= res["rated"] * 0.4 else "#C53929")
        st.markdown(f'<div class="note" style="border-color:{sc}">'
                    f'<b>{res["passed"]} of {res["rated"]}</b> rated checks look healthy. '
                    f'This is a screening aid: thresholds are general guides and several '
                    f'(P/E, current ratio, debt/equity) are industry-relative — banks and '
                    f'REITs legitimately break them. A passing screen is where research '
                    f'<i>starts</i>: moat, management, industry trend and your own position '
                    f'sizing are not in any ratio.</div>', unsafe_allow_html=True)

    _note("The illustrative range projects this asset's past volatility one year forward "
          "(±1σ), with the historical drift clamped so momentum never dominates. Markets do "
          "not follow the past — treat it as a width-of-uncertainty illustration, never a "
          "prediction. Past performance does not guarantee future results.", "warn")


# ════════════════════════════ STEP 5 — ACTIONS ════════════════════════════
def build_recs(b,res,ga,rec,capW,tname,tolL,capL,T,years):
    bd=res["breakdown"]; dg=res["diagnostics"]; pj=res["projections"]; recs=[]
    if bd["liquidity_elasticity"]<bd_max(20)*0.5:
        recs.append(("alert","Build your emergency fund first",f"You are below half of your {dg['target_runway_months']}-month target. Aim for {fmt(b['essential']*dg['target_runway_months'])} in cash before taking market risk."))
    elif bd["liquidity_elasticity"]<20:
        recs.append(("warn","Top up your emergency fund",f"Build toward {dg['target_runway_months']} months ({fmt(b['essential']*dg['target_runway_months'])}) for a full buffer."))
    if bd["insurance_security"]==0:
        recs.append(("warn","Add basic protection",f"Without adequate life/health/income insurance you forfeit 15 resilience points — one shock can undo years of progress."))
    if b["sr"]<0: recs.append(("alert","You are spending more than you earn",f"Expenses exceed income by {fmt(-b['surplus'])}/mo. No investment can outrun a monthly deficit."))
    elif bd["savings_efficiency"]<7.5: recs.append(("warn","Lift your savings rate",f"You are saving {b['sr']*100:.0f}% of income. Reaching 25% sharply raises both halves of your score."))
    if bd["debt_risk"]<5: recs.append(("alert","Reduce your debt service",f"Debt repayments are {b['dti']*100:.0f}% of income (lending norms cap near 36%). Bringing this under 20% restores full marks here."))
    elif bd["debt_risk"]<10: recs.append(("warn","Watch your debt load",f"Debt service is {b['dti']*100:.0f}% of income — keep it under 20%."))
    if dg["net_worth"]<0: recs.append(("alert","Your net worth is negative",f"Liabilities exceed assets by {fmt(-dg['net_worth'])}. Paying down principal is a guaranteed return and lifts your solvency score."))
    elif bd["solvency_leverage"]<5: recs.append(("info","Build toward your net-worth target",f"Your age-based target is {fmt(dg['target_net_worth'])}. You're at {fmt(dg['net_worth'])} — grow assets and trim debt to close it."))
    if bd["goal_trajectory"]<15: recs.append(("alert","Your goal needs more fuel",f"Only a {round(ga['prob']*100)}% chance of reaching {fmt(T)} in {years}y. Lift contributions toward {fmt(pj['required_monthly_surplus'])}/mo, extend the horizon, or consider a higher-growth tier."))
    elif bd["goal_trajectory"]<25: recs.append(("warn","Goal is slightly behind",f"Projected to cover {min(999,pj['inflation_adjusted_fv']/T*100):.0f}% of {fmt(T)}. A small contribution increase closes the gap."))
    gd=tolL-capL
    if gd>=2: recs.append(("alert","Do not invest beyond your capacity",f"Your comfort with risk ({tname}) exceeds what your finances support ({capW}). Start at {rec}."))
    elif gd<=-2: recs.append(("info","You can afford more growth when ready",f"Your finances ({capW}) could support more risk than your current comfort ({tname}). Increase exposure gradually."))
    if res["total_score"]>=80 and bd["goal_trajectory"]>=25: recs.append(("good","You are positioned to invest toward your goal",f"Strong on both halves. Consider {fmt(max(0,b['surplus']))}/mo automated into {rec}."))
    if not any(k in("alert","warn") for k,_,_ in recs): recs.append(("good","You are on a healthy path to your goal","No critical issues. Keep contributing consistently and review quarterly."))
    recs.sort(key=lambda r:{"alert":0,"warn":1,"info":2,"good":3}[r[0]]); return recs

def bd_max(x): return x  # readability helper

def calculation_notes():
    return """**Institutional Financial Health Score (out of 100)** — a Weighted Hybrid Model split evenly between **Current Resilience (50)** and **Future Readiness (50)**.

**① Current Resilience (50)**
• *Liquidity & elasticity (20)* = min(1, runway ÷ target) · 20, where runway = cash ÷ monthly essentials. The target is **6 months, rising to 9 if you have any dependents** (lower budget elasticity needs a deeper buffer).
• *Savings efficiency (15)* = min(1, savings-rate ÷ 25%) · 15.
• *Insurance & security (15)* = 15 if you hold adequate life/health/income cover, else 0.

**② Future Readiness (50)**
• *Goal trajectory with tax friction (30)* = min(1, FV ÷ target) · 30.
  – Actual tax drag = max tax drag · (1 − tax-advantaged share) — holding more in super/401k cuts the drag.
  – Net return = nominal − actual tax drag; Real rate = (1+net)/(1+inflation) − 1.
  – FV = cash·(1+i)ᵐ + surplus·(((1+i)ᵐ−1)/i), i = real/12, m = years·12 (today's dollars).
• *Solvency & leverage (10)* = min(1, NW-ratio ÷ target) · 10, NW = cash + assets − liabilities, NW-ratio = NW ÷ annual income. **Age-based target = age/10 − 1** (age 30 → 2×, age 50 → 4× income). Negative net worth scores 0.
• *Cash-flow debt risk (10)* = 10 if DTI ≤ 20%, tapering linearly to 0 at DTI = 40%.

**Rating:** Critical <25 · At Risk 25–44 · Fair 45–64 · Good 65–79 · Excellent ≥80.

**Complementary realism check.** Alongside the deterministic trajectory above, a Monte-Carlo
simulation (4,000 real-terms paths) reports your **probability of actually reaching the goal** —
shown as "chance of success" — because a single projected line hides volatility risk.

**The 50/30/20 rule is not scored** — it appears on the Budget step purely as a spending-mix diagnostic."""

def report_text(b,res,ga,rec,capW,tname,T,years):
    bd=res["breakdown"]; dg=res["diagnostics"]; pj=res["projections"]
    L=["SERALUNG FINANCE — PERSONAL FINANCIAL REPORT","="*52,"","Educational only. Not personal financial advice.","",
       "FINANCIAL HEALTH (institutional hybrid)","-"*52,f"  Total score:      {res['total_score']}/100 ({res['rating_category']})",
       f"  Resilience:       {bd['liquidity_elasticity']+bd['savings_efficiency']+bd['insurance_security']:g}/50",
       f"  Readiness:        {bd['goal_trajectory']+bd['solvency_leverage']+bd['debt_risk']:g}/50",
       f"  Chance of goal:   {round(ga['prob']*100)}% (Monte Carlo, real terms)","",
       "BREAKDOWN","-"*52,f"  Liquidity (20):   {bd['liquidity_elasticity']:g}",f"  Savings (15):     {bd['savings_efficiency']:g}",
       f"  Insurance (15):   {bd['insurance_security']:g}",f"  Trajectory (30):  {bd['goal_trajectory']:g}",
       f"  Solvency (10):    {bd['solvency_leverage']:g}",f"  Debt risk (10):   {bd['debt_risk']:g}","",
       "ULTIMATE GOAL","-"*52,f"  Target:           {fmt(T)} (today's $)",f"  Projected FV:     {fmt(pj['inflation_adjusted_fv'])} @ {dg['real_compounding_rate']*100:.1f}% real",
       f"  Gap:              {fmt(pj['target_gap'])}",f"  Required:         {fmt(pj['required_monthly_surplus'])}/mo","",
       "BALANCE SHEET","-"*52,f"  Net worth:        {fmt(dg['net_worth'])}",f"  Age-based target: {fmt(dg['target_net_worth'])}",
       f"  Liquid cash:      {fmt(b['cash'])}",f"  Monthly surplus:  {fmt(b['surplus'])}","",
       "RISK PROFILE","-"*52,f"  Tolerance:        {tname}",f"  Capacity:         {capW}",f"  Suggested tier:   {rec}","","PRIORITISED ACTIONS","-"*52]
    recs=ss.get("_recs",[])
    tg={"alert":"[DO FIRST] ","warn":"[IMPORTANT] ","info":"[CONSIDER] ","good":"[ON TRACK] "}
    for idx,(k,t,d) in enumerate(recs,1):
        L.append(f"  {idx}. {tg[k]}{t}"); cur=""
        for wd in d.split():
            if len(cur)+len(wd)+1>66: L.append("     "+cur); cur=wd
            else: cur=(cur+" "+wd).strip()
        if cur: L.append("     "+cur)
        L.append("")
    L+=["","Generated by Seralung Finance."]; return "\n".join(L)

def page_actions():
    b=ss.get("budget") or compute_budget(ss)
    if b["income"]<=0: note("Complete the Budget and Financial Health steps to generate your plan.","warn"); return
    res,ga,rec,capL,tolL,surplus,T,years=assess_health(b)
    tname=tol_profile(ss)[0]; capW=cap_level(capacity(b))[1]; total=res["total_score"]
    rt,rclr,rbg=rating(total)
    recs=build_recs(b,res,ga,rec,capW,tname,tolL,capL,T,years); ss["_recs"]=recs
    nA=sum(1 for r in recs if r[0]=="alert"); nW=sum(1 for r in recs if r[0]=="warn"); recClr=TIER_CLR.get(rec,"#16794D")
    res_pts=res["breakdown"]["liquidity_elasticity"]+res["breakdown"]["savings_efficiency"]+res["breakdown"]["insurance_security"]
    rdy_pts=res["breakdown"]["goal_trajectory"]+res["breakdown"]["solvency_leverage"]+res["breakdown"]["debt_risk"]
    sec("Investment Readiness")
    a1,a2=st.columns(2)
    a1.markdown(f'<div class="card" style="padding:16px">{gauge(total,rclr)}</div>',unsafe_allow_html=True)
    a2.markdown(f'<div class="readwrap" style="border-left-color:{rclr};background:{rbg}"><div class="ov">Overall</div>'
                f'<div class="rt" style="color:{rclr}">{res["rating_category"]}</div><div class="rd">{nA} critical item{"s" if nA!=1 else ""} and {nW} to watch. '
                f'Resilience {res_pts:g}/50, readiness {rdy_pts:g}/50 ({round(ga["prob"]*100)}% chance). Suggested portfolio: <b style="color:{recClr}">{rec}</b>.</div></div>',unsafe_allow_html=True)
    sec("Your Prioritised Action Plan")
    cmap={"alert":("#FBEAE7","#C53929"),"warn":("#FBF3E2","#B7791F"),"info":("#E7F5EC","#16794D"),"good":("#E7F5EC","#16794D")}
    tmap={"alert":"Do first","warn":"Important","info":"Consider","good":"On track"}
    for idx,(k,t,d) in enumerate(recs,1):
        bg2,ac=cmap[k]
        st.markdown(f'<div class="action" style="border-left:3.5px solid {ac}"><div class="ah"><span class="num" style="background:{ac}">{idx}</span>'
                    f'<span class="tag" style="background:{bg2};color:{ac}">{tmap[k]}</span><span class="at">{t}</span></div><div class="ad">{d}</div></div>',unsafe_allow_html=True)
    st.download_button("⤓ Download My Financial Report (.txt)",data=report_text(b,res,ga,rec,capW,tname,T,years),
        file_name="seralung_finance_report.txt",mime="text/plain",use_container_width=True)
    with st.expander("📐 See the calculation details (every formula)"):
        st.markdown(calculation_notes())
    sec("Share Your Feedback")
    if ss["fb_sent"]:
        st.markdown('<div class="card" style="padding:18px"><b>Thanks for your feedback ✓</b><br><span style="color:#64748B">It helps us improve Seralung Finance.</span></div>',unsafe_allow_html=True)
    else:
        st.caption("Help us improve Seralung Finance — your feedback is saved for this session.")
        fc=st.columns(5)
        for n in range(1,6):
            if fc[n-1].button("★" if n<=ss["fb_rating"] else "☆",key=f"star_{n}",type="secondary"):
                ss["fb_rating"]=n; st.rerun()
        st.text_input("Your name",key="fb_name",placeholder="e.g. Sarah")
        st.text_area("Your feedback",key="fb_text",placeholder="What did you think? What could be better?")
        if st.button("✓ Submit Feedback",disabled=ss["fb_rating"]==0): ss["fb_sent"]=True; st.rerun()

# ════════════════════════════ DISPATCH + NAV ════════════════════════════
{1:page_budget,2:page_health,3:page_portfolio,4:page_markets,5:page_actions}[step]()
st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)
segs="".join(f'<span style="width:42px;height:5px;border-radius:4px;background:{STEP_META[i][3] if i<step else "#E2E8F0"};display:inline-block;margin-right:7px"></span>' for i in range(5))
nb1,nb2,nb3=st.columns([1,2,1])
with nb1:
    if st.button("‹ Back",key="backbtn",disabled=step==1,type="secondary"): goto(step-1); st.rerun()
with nb2: st.markdown(f'<div style="text-align:center;padding-top:8px">{segs}</div>',unsafe_allow_html=True)
with nb3:
    if step<5:
        if st.button("Next Step ›",key="nextbtn"): goto(step+1); st.rerun()
    else:
        if st.button("Complete!",key="donebtn"): st.balloons()
st.markdown('<div style="border-top:1px solid #E3E8EF;margin-top:24px;padding:14px 0;text-align:center;font-size:.72rem;color:#94A3B8">'
            '<b style="color:#16794D">Seralung Finance</b> · Educational only — not personal financial advice.</div>',unsafe_allow_html=True)
