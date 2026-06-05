"""
Seralung Finance — goal-based financial wizard (Streamlit).
Run:  streamlit run app.py
Deps: streamlit, numpy, pandas

WHAT CHANGED (per request):
  • Financial Health is now GOAL-BASED. You set your Ultimate Goal first, then the
    score measures how well-positioned you are to reach it (trajectory toward the
    goal is 50% of the score). The old budget-ratio rule has been removed.
  • "Where you stand": current progress, projected coverage, gap, required monthly
    contribution and years-to-goal are all shown on the Financial Health step.

CALCULATION DETAILS are documented in calculation_notes() (shown in-app under an
expander on the Action Plan step) and in README.md.
"""
import base64
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Seralung Finance", layout="wide", initial_sidebar_state="collapsed")

# ════════════════════════════════════════════════════════════════
# FINANCE ENGINE  (verified exact against the reference figures)
# ════════════════════════════════════════════════════════════════
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
    w=np.array(wpct,float)/100.0
    rp=float(w@R); sd=float(w@COV@w)**0.5
    return {"rp":rp,"sd":sd,"sharpe":(rp-RF)/sd if sd>0 else 0.0,
            "var95":max(0,Z*sd-rp),"cvar95":max(0,sd*(PHI/0.05)-rp),
            "maxdd":min(0.95,2.4*sd),"div":float(w@V)/sd if sd>0 else 1.0}
TIER_M={t:metrics(TIER_W[t]) for t in TIERS}

def compute_budget(ss):
    income=sf(ss["income_primary"])+sf(ss["income_secondary"]); savings=sf(ss["savings"])
    total=needs=wants=debt=0.0; cat_sums={}
    if ss["entry_mode"]=="total":
        total=sf(ss["total_expenses"]); needs=total
    else:
        for _,row in ss["expenses_df"].iterrows():
            amt=sf(row.get("Amount",0));
            if amt<=0: continue
            cat=row.get("Category","Other"); cat=cat if cat in CATS else "Other"
            total+=amt; t=CTYPE.get(cat,"Want")
            if t=="Need": needs+=amt
            elif t=="Want": wants+=amt
            if cat=="Debt Repayment": debt+=amt
            cat_sums[cat]=cat_sums.get(cat,0)+amt
    surplus=income-total; sr=surplus/income if income>0 else 0
    essential=needs if needs>0 else total; runway=savings/essential if essential>0 else 0
    dti=debt/income if income>0 else 0
    return dict(income=income,savings=savings,total=total,needs=needs,wants=wants,debt=debt,
                surplus=surplus,sr=sr,essential=essential,runway=runway,dti=dti,cat_sums=cat_sums)

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

# ---- Ultimate Goal time-value math (monthly compounding) ----
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

def goal_health(b, T, r, years):
    """GOAL-BASED financial health (0-100). Trajectory toward the goal is the
    dominant factor (50 pts); supported by buffer, savings discipline and debt."""
    if b["income"]<=0 or T<=0: return 0,{}
    Cm=max(0,b["surplus"]); FV=future_value(b["savings"],Cm,r,years); cov=FV/T
    p_traj=min(1,max(0,cov))*50
    p_run =min(1,b["runway"]/6)*20
    p_sr  =min(1,max(0,b["sr"])/0.20)*15
    p_debt=15 if b["dti"]<=0.20 else max(0,15-(b["dti"]-0.20)*60)
    score=round(min(100,p_traj+p_run+p_sr+p_debt))
    parts={"Goal trajectory":(round(p_traj),50),"Emergency runway":(round(p_run),20),
           "Savings rate":(round(p_sr),15),"Debt load":(round(p_debt),15)}
    extra=dict(fv=FV,cov=cov,req=required_contribution(T,b["savings"],r,years),
               ytg=years_to_goal(T,b["savings"],Cm,r),now=b["savings"]/T if T>0 else 0,Cm=Cm)
    return score,(parts,extra)

def rating(s):
    return ("Excellent","#16794D","#E7F5EC") if s>=80 else ("Good","#0E7C7B","#DFF2F1") if s>=65 \
      else ("Fair","#B7791F","#FBF3E2") if s>=45 else ("At Risk","#C53929","#FBEAE7") if s>=25 else ("Critical","#C53929","#FBEAE7")

# ════════════════════════════════════════════════════════════════
# SVG CHARTS  (rendered as base64 <img> so Streamlit never strips them)
# ════════════════════════════════════════════════════════════════
def _img(svg, mw):
    b64=base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" style="display:block;margin:0 auto;width:100%;max-width:{mw}px"/>'
def _polar(cx,cy,r,deg):
    a=(deg-90)*np.pi/180; return cx+r*np.cos(a), cy+r*np.sin(a)
def _arc(cx,cy,r,a0,a1):
    x0,y0=_polar(cx,cy,r,a0); x1,y1=_polar(cx,cy,r,a1); large=0 if (a1-a0)<=180 else 1
    return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}"
def gauge(score,color):
    cx,cy,r,start,sweep=110,110,80,135,270
    end=start+sweep*max(0,min(100,score))/100
    svg=(f'<svg viewBox="0 0 220 200" xmlns="http://www.w3.org/2000/svg">'
         f'<path d="{_arc(cx,cy,r,start,start+sweep)}" fill="none" stroke="#E6EEF0" stroke-width="16" stroke-linecap="round"/>'
         f'<path d="{_arc(cx,cy,r,start,end)}" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round"/>'
         f'<text x="{cx}" y="{cy-2}" text-anchor="middle" font-family="Plus Jakarta Sans,sans-serif" font-weight="800" font-size="40" fill="{color}">{round(score)}</text>'
         f'<text x="{cx}" y="{cy+20}" text-anchor="middle" font-family="Plus Jakarta Sans,sans-serif" font-size="13" fill="#64748B">out of 100</text></svg>')
    return _img(svg,240)
def donut(segs,center):
    cx,cy,r,sw=90,90,62,24; C=2*np.pi*r; off=0; circ=""
    tot=sum(v for _,v,_ in segs) or 1
    for _,v,clr in segs:
        ln=v/tot*C
        circ+=(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{clr}" stroke-width="{sw}" '
               f'stroke-dasharray="{ln:.2f} {C-ln:.2f}" stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        off+=ln
    svg=(f'<svg viewBox="0 0 180 180" xmlns="http://www.w3.org/2000/svg">{circ}'
         f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-family="Plus Jakarta Sans,sans-serif" font-weight="700" font-size="15" fill="#1E2A32">{center}</text></svg>')
    return _img(svg,220)
def legend(segs):
    return '<div class="legend">'+''.join(f'<div class="li"><span class="sw" style="background:{c}"></span>{l}</div>' for l,_,c in segs)+'</div>'

# ════════════════════════════════════════════════════════════════
# CSS
# ════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#EEF1F5!important;font-family:'Plus Jakarta Sans',sans-serif;color:#1E2A32!important}
.stApp p,.stApp label,.stApp li,[data-testid="stMarkdownContainer"]{color:#1E2A32}
.block-container{padding:0 22px 5rem;max-width:1180px}
#MainMenu,footer,header{visibility:hidden}.stDeployButton{display:none!important}
[data-testid="stSidebarNav"]{display:none!important}
[data-testid="stVerticalBlock"]{gap:.3rem!important}
h1,h2,h3,h4{font-family:'Plus Jakarta Sans',sans-serif!important;margin:0!important;color:#1E2A32!important}
.topbar{background:linear-gradient(100deg,#0B2545,#14365F);color:#fff;border-radius:0 0 0 0;margin:0 -22px;padding:14px 22px;display:flex;justify-content:space-between;align-items:center}
.topbar h1{font-size:1.15rem;font-weight:800;color:#fff!important}.topbar p{font-size:.8rem;color:#B9C6D6;margin-top:1px}
.pillc{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);color:#fff;font-size:.74rem;font-weight:600;padding:5px 12px;border-radius:20px;display:flex;gap:8px;align-items:center}
.dotz{display:flex;gap:4px}.dotz i{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.28);display:inline-block}.dotz i.on{background:#F59E0B}
.stepnav{background:#fff;margin:0 -22px;padding:16px 22px 14px;border-bottom:1px solid #E3E8EF;display:flex;justify-content:space-between}
.snode{display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;position:relative}
.snode .circle{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;background:#fff;border:2px solid #E3E8EF;color:#94A3B8;z-index:2}
.snode .lbl{font-size:.74rem;font-weight:600;color:#94A3B8;text-align:center;line-height:1.15}
.snode .line{position:absolute;top:17px;left:50%;width:100%;height:2px;background:#E3E8EF;z-index:1}.snode:last-child .line{display:none}
.snode.done .circle{color:#fff}.snode.active .circle{background:#fff}
.banner{margin:0 -22px 6px;padding:16px 22px;display:flex;gap:14px;align-items:center}
.banner .bi{width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;color:#fff;flex-shrink:0}
.banner .pl{font-size:.66rem;font-weight:800;letter-spacing:.04em;padding:3px 10px;border-radius:20px;color:#fff;display:inline-block}
.banner .cp{background:#16794D;color:#fff;font-size:.66rem;font-weight:800;padding:3px 10px;border-radius:20px;margin-left:6px}
.banner h2{font-size:1.05rem;font-weight:800;margin-top:5px!important}.banner .sb{font-size:.82rem;color:#64748B}
.sec{display:flex;align-items:center;gap:10px;margin:18px 0 10px}.sec span{font-size:.72rem;letter-spacing:.07em;text-transform:uppercase;font-weight:700;color:#16794D;white-space:nowrap}.sec .ln{flex:1;height:1px;background:#E3E8EF}
.note{border-left:3.5px solid #16794D;background:#E7F5EC;border-radius:0 10px 10px 0;padding:10px 14px;margin:7px 0;font-size:.88rem;line-height:1.55}
.note.warn{border-color:#B7791F;background:#FBF3E2}.note.alert{border-color:#C53929;background:#FBEAE7}
.metric{background:#fff;border:1px solid #E3E8EF;border-top:3px solid #16794D;border-radius:0 0 14px 14px;padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,.04);height:100%}
.metric .ml{font-size:.66rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#64748B;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.metric .mv{font-size:1.5rem;font-weight:800;line-height:1.15;margin-top:6px;word-break:break-word}.metric .ms{font-size:.71rem;color:#64748B;margin-top:4px;line-height:1.4}
.card{background:#fff;border:1px solid #E3E8EF;border-radius:16px;box-shadow:0 1px 6px rgba(15,40,70,.05)}
.legend{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;font-size:.76rem;margin-top:8px}.legend .li{display:flex;align-items:center;gap:5px}.legend .sw{width:9px;height:9px;border-radius:2px}
.brk{margin-bottom:13px}.brk .l{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}.brk .nm{font-size:.9rem;font-weight:500}.brk .sc{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.86rem}
.brk .bar{height:6px;background:rgba(0,0,0,.07);border-radius:3px;overflow:hidden}.brk .bar i{display:block;height:100%;border-radius:3px}
.opt-item{background:#fff;border:1px solid #E3E8EF;border-left:3px solid #16794D;border-radius:0 10px 10px 0;padding:9px 14px;margin-bottom:5px;font-size:.88rem}
.tierhead{border:1px solid #E3E8EF;border-left:4px solid #16794D;border-radius:0 14px 14px 0;padding:15px 18px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.04)}.tierhead h3{font-size:1.5rem;font-weight:800}.tierhead .er{font-size:.82rem;color:#64748B;margin-top:3px}
.cmp{width:100%;border-collapse:collapse;border:1px solid #E3E8EF;border-radius:12px;overflow:hidden}
.cmp th{background:#16794D;color:#fff;text-align:left;font-size:.68rem;text-transform:uppercase;letter-spacing:.05em;font-weight:600;padding:8px 11px;white-space:nowrap}
.cmp td{padding:9px 11px;border-bottom:1px solid #E3E8EF;font-family:'JetBrains Mono',monospace;font-size:.82rem}.cmp td.tn{font-family:'Plus Jakarta Sans',sans-serif;font-weight:700}
.cmpnote{font-size:.7rem;color:#64748B;margin-top:6px;line-height:1.5}
.scen{border:1px solid #E3E8EF;border-top:3px solid #16794D;border-radius:0 0 12px 12px;padding:13px 15px;background:#fff}.scen .sl{font-size:.66rem;font-weight:700;text-transform:uppercase;color:#64748B}.scen .sv{font-family:'JetBrains Mono',monospace;font-size:1.25rem;font-weight:700;margin-top:5px}.scen .sd{font-family:'JetBrains Mono',monospace;font-size:.78rem;margin-top:3px}
.goalwrap{background:linear-gradient(120deg,#0E5C39,#16794D);border-radius:18px;padding:18px 20px;color:#fff;box-shadow:0 6px 22px rgba(14,92,57,.22)}
.goalwrap .gt{font-size:.7rem;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#BFE6CF}.goalwrap h3{font-size:1.25rem;font-weight:800;margin-top:3px;color:#fff!important}.goalwrap .gsub{font-size:.82rem;color:#CDEAD9;margin-top:3px}
.ptrack{height:14px;border-radius:8px;background:rgba(255,255,255,.18);overflow:hidden;position:relative;margin-top:6px}.ptrack .pp{height:100%;background:rgba(255,255,255,.45);position:absolute;left:0;top:0;border-radius:8px}.ptrack .pn{height:100%;background:#9BE7BC;position:absolute;left:0;top:0;border-radius:8px}
.plab{display:flex;justify-content:space-between;font-size:.74rem;color:#CDEAD9;margin-top:6px;font-family:'JetBrains Mono',monospace}
.gstat{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);border-radius:12px;padding:11px 13px}.gstat .l{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#BFE6CF}.gstat .v{font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;margin-top:3px}.gstat .s{font-size:.66rem;color:#CDEAD9;margin-top:2px}
.readwrap{border:1px solid #E3E8EF;border-left:4px solid #16794D;border-radius:0 14px 14px 0;padding:16px 20px}.readwrap .ov{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#64748B}.readwrap .rt{font-size:1.65rem;font-weight:800}.readwrap .rd{font-size:.85rem;color:#64748B;margin-top:5px;line-height:1.5}
.action{background:#fff;border:1px solid #E3E8EF;border-radius:0 14px 14px 0;padding:13px 16px;margin-bottom:8px;box-shadow:0 1px 4px rgba(0,0,0,.03)}.action .ah{display:flex;align-items:center;gap:10px;margin-bottom:5px;flex-wrap:wrap}.action .num{color:#fff;font-size:.78rem;font-weight:800;width:24px;height:24px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center}.action .tag{font-size:.6rem;font-weight:700;padding:2px 9px;border-radius:20px;text-transform:uppercase;letter-spacing:.05em}.action .at{font-size:.97rem;font-weight:700}.action .ad{font-size:.87rem;color:#64748B;line-height:1.6;padding-left:34px}
/* Streamlit widget theming */
.stNumberInput input,.stTextInput input,.stTextArea textarea{background:#fff!important;border:1.5px solid #E3E8EF!important;border-radius:10px!important;color:#1E2A32!important;font-family:'JetBrains Mono',monospace!important}
.stNumberInput label,.stTextInput label,.stSelectbox label,.stSlider label,.stRadio label{font-size:.7rem!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.03em!important;color:#64748B!important}
.stSelectbox div[data-baseweb="select"]>div{background:#fff!important;border:1.5px solid #E3E8EF!important;border-radius:10px!important}
.stButton>button{background:#16794D;color:#fff;border:none;border-radius:50px;font-weight:600;padding:9px 18px;box-shadow:0 2px 8px rgba(22,121,77,.2);width:100%}
.stButton>button:hover{background:#0E5C39;color:#fff}
.stButton>button[kind="secondary"],button[data-testid="stBaseButton-secondary"]{background:#fff!important;color:#1E2A32!important;border:1.5px solid #E3E8EF!important;box-shadow:none!important}
.stButton>button[kind="secondary"]:hover,button[data-testid="stBaseButton-secondary"]:hover{border-color:#16794D!important;color:#16794D!important}
.stDownloadButton>button{background:#13243B;color:#fff;border:none;border-radius:11px;font-weight:700;padding:12px;width:100%}
.stRadio [role="radiogroup"]{gap:2px}
div[data-testid="stRadio"] [role="radiogroup"]>label{padding:7px 11px;border-radius:9px;margin-bottom:2px}
div[data-testid="stRadio"] [role="radiogroup"]>label:hover{background:#E7F5EC}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border-radius:12px;overflow:hidden;border:1px solid #D8E6DD}
</style>
"""

STEP_META=[("budget","Budget","📁","#F59E0B","#FBEFD8","Budget","Know your financial health & risk before investing"),
           ("health","Fin. Health","💎","#06B6D4","#D6F1F7","Financial Health","Set your goal, then score your fitness to reach it"),
           ("portfolio","Portfolio","◔","#7C3AED","#ECE6FB","Portfolio Diversification","Explore investment tiers"),
           ("forecast","Forecast","📈","#F97316","#FCE7D6","Forecast","Forecast your portfolio growth"),
           ("actions","Actions","✅","#10B981","#D7F5E6","Action Plan","Get your personalised plan")]

fmt=lambda n:"$"+format(int(round(n)),",")

# ════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════
def init_state():
    d={"step":1,"max_step":1,"income_primary":6000,"income_secondary":0,"savings":15000,
       "entry_mode":"individual","total_expenses":0,"selected_tier":"Defensive",
       "goal_mode":"income","goal_income":5000,"goal_lump":1000000,"goal_years":25,
       "fb_rating":0,"fb_name":"","fb_text":"","fb_sent":False,
       **{f"quiz_q{i}":0 for i in range(1,11)},
       **{f"w{i}":TIER_W["Balanced"][i] for i in range(6)}}
    for k,v in d.items(): st.session_state.setdefault(k,v)
    if "expenses_df" not in st.session_state:
        st.session_state["expenses_df"]=pd.DataFrame(DEFAULT_EXP,columns=["Expense","Category","Amount"])
init_state()
ss=st.session_state

def goto(step):
    ss["step"]=step; ss["max_step"]=max(ss["max_step"],step)

# ════════════════════════════════════════════════════════════════
# SHELL (header / step nav / banner)
# ════════════════════════════════════════════════════════════════
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
            f'<div><span class="pl" style="background:{accent}">STEP {step} OF 5</span>{cp}<h2>{meta[5]}</h2><div class="sb">{meta[6]}</div></div></div>',
            unsafe_allow_html=True)

# helpers
def sec(label): st.markdown(f'<div class="sec"><span>{label}</span><div class="ln"></div></div>',unsafe_allow_html=True)
def note(t,k="info"): st.markdown(f'<div class="note {k}">{t}</div>',unsafe_allow_html=True)
def mcard(l,v,s,clr="#16794D",bg="#fff"):
    return f'<div class="metric" style="border-top-color:{clr};background:{bg}"><div class="ml">{l}</div><div class="mv" style="color:{clr}">{v}</div><div class="ms">{s}</div></div>'

# ════════════════════════════════════════════════════════════════
# STEP 1 — BUDGET  (budget-ratio rule removed)
# ════════════════════════════════════════════════════════════════
def page_budget():
    note("Enter your income and expenses below — every metric recalculates live as you type.")
    sec("Income &amp; Savings")
    c1,c2,c3=st.columns(3)
    c1.number_input("Monthly after-tax income ($)",min_value=0,step=250,key="income_primary")
    c2.number_input("Secondary income (optional)",min_value=0,step=100,key="income_secondary")
    c3.number_input("Current cash savings ($)",min_value=0,step=1000,key="savings")
    sec("Your bills &amp; expenses")
    t1,t2=st.columns([1,4])
    mode=t1.radio("Entry mode",["Enter Individually","Enter Total at Once"],
                  index=0 if ss["entry_mode"]=="individual" else 1,label_visibility="collapsed")
    ss["entry_mode"]="individual" if mode=="Enter Individually" else "total"
    if ss["entry_mode"]=="total":
        st.number_input("Total monthly expenses ($)",min_value=0,step=100,key="total_expenses")
    else:
        st.caption("Edit any cell · use the + below the table to add a row · select a row and press ⌫ to delete")
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
    if ss["entry_mode"]=="individual" and b["cat_sums"]:
        sec("Where Your Money Goes")
        d1,d2=st.columns(2)
        pal=ASSET_CLR+["#0E7C7B","#B7791F","#7C3AED","#3DA968","#C53929","#6B7280","#16794D","#0E7C7B"]
        segs=[(k,v,pal[i]) for i,(k,v) in enumerate(sorted(b["cat_sums"].items(),key=lambda x:-x[1]))]
        d1.markdown(f'<div class="card" style="padding:16px">{donut(segs,fmt(b["total"]))}{legend(segs)}</div>',unsafe_allow_html=True)
        rc="#16794D" if b["runway"]>=6 else("#B7791F" if b["runway"]>=3 else "#C53929"); rcb="#E7F5EC" if b["runway"]>=6 else("#FBF3E2" if b["runway"]>=3 else "#FBEAE7")
        d2.markdown(mcard("Emergency Fund Runway",f"{b['runway']:.1f} months",f"{fmt(b['savings'])} savings ÷ {fmt(b['essential'])}/mo essentials",rc,rcb),unsafe_allow_html=True)
        if b["runway"]<3: d2.markdown('<div class="note alert">Your emergency fund is below 3 months. This is the most important fix before investing.</div>',unsafe_allow_html=True)
        elif b["runway"]<6: d2.markdown('<div class="note warn">Aim for 6 months of essentials before investing.</div>',unsafe_allow_html=True)
        else: d2.markdown('<div class="note">Healthy buffer — solid foundation to invest from.</div>',unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# STEP 2 — FINANCIAL HEALTH  (goal-based)
# ════════════════════════════════════════════════════════════════
def page_health():
    b=ss.get("budget") or compute_budget(ss)
    # ---- ULTIMATE GOAL (set FIRST) ----
    st.markdown('<div class="goalwrap"><div class="gt">Ultimate Goal</div>'
                '<h3>Set your destination — health is measured against it</h3>'
                '<div class="gsub">Your financial health below scores how well-positioned you are to reach this goal.</div></div>',unsafe_allow_html=True)
    gm=st.radio("Goal type",["Target passive income","Target lump sum"],
                index=0 if ss["goal_mode"]=="income" else 1,horizontal=True,label_visibility="collapsed")
    ss["goal_mode"]="income" if gm=="Target passive income" else "lumpsum"
    gc1,gc2=st.columns(2)
    if ss["goal_mode"]=="income":
        gc1.number_input("Desired passive income ($/month)",min_value=0,step=250,key="goal_income")
    else:
        gc1.number_input("Target lump sum ($)",min_value=0,step=10000,key="goal_lump")
    gc2.number_input("Years until you want it",min_value=1,max_value=60,step=1,key="goal_years")

    if b["income"]<=0:
        note("Complete the Budget step first — your score is built from your income, savings and this goal.","warn"); return

    T=goal_target(ss); cap=capacity(b); capL,capW=cap_level(cap); tname,tolL,tscore=tol_profile(ss)
    rec=rec_tier(capL,tolL); r_goal=TIER_M[rec]["rp"]
    score,(parts,ex)=goal_health(b,T,r_goal,sf(ss["goal_years"]) or 1)
    rt,clr,bg=rating(score)

    sec("Financial Health Score — toward your goal")
    h1,h2=st.columns(2)
    h1.markdown(f'<div class="card" style="padding:16px;text-align:center">{gauge(score,clr)}'
                f'<div style="margin-top:2px"><span style="background:{bg};color:{clr};font-weight:700;font-size:.95rem;padding:5px 20px;border-radius:20px;display:inline-block">{rt}</span></div></div>',unsafe_allow_html=True)
    bars=""
    for k,(g,mx) in parts.items():
        p=g/mx*100; c="#16794D" if p>=70 else("#B7791F" if p>=40 else "#C53929")
        bars+=f'<div class="brk"><div class="l"><span class="nm">{k}</span><span class="sc" style="color:{c}">{g}/{mx}</span></div><div class="bar"><i style="width:{p:.0f}%;background:{c}"></i></div></div>'
    h2.markdown(f'<div style="padding-top:8px">{bars}</div>',unsafe_allow_html=True)
    note(f"Your financial health toward this goal is <b>{rt}</b>. On your current trajectory you are projected to reach "
         f"<b>{min(ex['cov'],9.99)*100:.0f}%</b> of your {fmt(T)} goal "
         f"({'on track' if ex['cov']>=1 else 'short of target'}).", "good" if score>=65 else("warn" if score>=45 else "alert"))

    # ---- WHERE YOU STAND ----
    sec("Where You Stand")
    nowp=min(100,ex["now"]*100); projp=min(100,ex["cov"]*100)
    st.markdown(f'<div class="goalwrap"><div class="gt">Progress to {fmt(T)}</div>'
                f'<div class="ptrack"><div class="pp" style="width:{projp}%"></div><div class="pn" style="width:{nowp}%"></div></div>'
                f'<div class="plab"><span>Now: {ex["now"]*100:.1f}% ({fmt(b["savings"])})</span><span>Projected in {int(sf(ss["goal_years"]))}y: {fmt(ex["fv"])}</span></div>'
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px">'
                f'<div class="gstat"><div class="l">Goal target</div><div class="v">{fmt(T)}</div><div class="s">{("$%s/mo via 4%% rule"%format(int(sf(ss["goal_income"])),",")) if ss["goal_mode"]=="income" else "lump sum"}</div></div>'
                f'<div class="gstat"><div class="l">Projected value</div><div class="v">{fmt(ex["fv"])}</div><div class="s">@ {r_goal*100:.1f}% ({rec})</div></div>'
                f'<div class="gstat"><div class="l">{"Surplus vs goal" if ex["fv"]>=T else "Shortfall"}</div><div class="v">{("+" if ex["fv"]>=T else "−")+fmt(abs(T-ex["fv"]))}</div><div class="s">{"ahead" if ex["fv"]>=T else "still needed"}</div></div>'
                f'<div class="gstat"><div class="l">To stay on track</div><div class="v">{fmt(ex["req"])}/mo</div><div class="s">vs your {fmt(ex["Cm"])}/mo now</div></div>'
                f'</div></div>',unsafe_allow_html=True)
    ytg=ex["ytg"]
    if ex["fv"]>=T: note(f"On track — at {fmt(ex['Cm'])}/mo you reach this goal in about {ytg:.1f} years.","good")
    elif np.isfinite(ytg): note(f"At {fmt(ex['Cm'])}/mo you'd get there in about {ytg:.1f} years. Contributing {fmt(ex['req'])}/mo hits it in {int(sf(ss['goal_years']))}.","warn")
    else: note(f"Current contributions won't reach this goal — raise savings toward {fmt(ex['req'])}/mo to hit it in {int(sf(ss['goal_years']))} years.","alert")

    # ---- RISK PROFILE ----
    sec("Risk Profile — 10 Questions")
    note("These measure your personal comfort with volatility. Your profile updates live as you answer.")
    for i,(q,opts) in enumerate(QUESTIONS):
        st.markdown(f'<div style="background:#fff;border:1px solid #E3E8EF;border-radius:14px;padding:12px 16px 4px;margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,.03)">'
                    f'<span style="background:#D6F1F7;color:#0E7490;font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:5px;font-family:JetBrains Mono">{i+1:02d}/10</span> '
                    f'<b style="font-size:.95rem">{q}</b></div>',unsafe_allow_html=True)
        st.radio(q,list(range(4)),format_func=lambda x,o=opts:o[x],index=int(ss[f"quiz_q{i+1}"]),
                 key=f"quiz_q{i+1}",label_visibility="collapsed",horizontal=True)
    sec("Risk Analysis")
    r1,r2,r3=st.columns(3)
    r1.markdown(mcard("Risk Tolerance",tname,f"Level {tolL}/5 · score {tscore}/40",TIER_CLR.get(rec,'#16794D'),"#E7F5EC"),unsafe_allow_html=True)
    capclr=["#C53929","#C53929","#B7791F","#0E7C7B","#16794D"][capL-1]; capbg=["#FBEAE7","#FBEAE7","#FBF3E2","#DFF2F1","#E7F5EC"][capL-1]
    r2.markdown(mcard("Risk Capacity",capW,f"Level {capL}/5 · from your budget",capclr,capbg),unsafe_allow_html=True)
    r3.markdown(mcard("Suggested Tier",rec,"Prudent match (lower of the two)",TIER_CLR[rec],TIER_BG[rec]),unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# STEP 3 — PORTFOLIO
# ════════════════════════════════════════════════════════════════
def page_portfolio():
    b=ss.get("budget") or compute_budget(ss)
    capL=cap_level(capacity(b))[0]; tolL=tol_profile(ss)[1]; rec=rec_tier(capL,tolL); recClr=TIER_CLR.get(rec,"#16794D")
    note("Five model portfolios from lowest to highest risk, with key risk and return figures for each.")
    note(f'Based on your risk capacity and tolerance, your suggested starting tier is <b style="color:{recClr}">{rec}</b>.')
    sec("Choose a tier to explore")
    cols=st.columns(5)
    for i,t in enumerate(TIERS):
        lbl=("★ "+t) if t==rec else t
        if cols[i].button(lbl,key=f"tier_{t}",type="primary" if t==ss["selected_tier"] else "secondary"):
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

# ════════════════════════════════════════════════════════════════
# STEP 4 — FORECAST
# ════════════════════════════════════════════════════════════════
def page_forecast():
    note("Drag the sliders to build a custom portfolio. Metrics update using Modern Portfolio Theory.")
    sec("Load a Preset")
    pc=st.columns(5)
    for i,t in enumerate(TIERS):
        if pc[i].button(t,key=f"preset_{t}",type="secondary"):
            for j in range(6): ss[f"w{j}"]=TIER_W[t][j]
            st.rerun()
    left,right=st.columns(2)
    with left:
        st.markdown('<div style="font-size:.68rem;font-weight:700;text-transform:uppercase;color:#64748B;margin-bottom:4px">Asset Allocation</div>',unsafe_allow_html=True)
        for i,nm in enumerate(ASSETS):
            st.slider(f"{nm}  ·  ret {R[i]*100:.1f}% / vol {V[i]*100:.0f}%",0,100,key=f"w{i}")
        wsum=sum(int(ss[f"w{i}"]) for i in range(6))
        st.markdown(f'<div style="display:flex;justify-content:space-between;font-weight:700;border-top:1px solid #E3E8EF;padding-top:10px;font-family:JetBrains Mono">'
                    f'<span>Total</span><span style="color:{"#16794D" if wsum==100 else "#C53929"}">{wsum}%</span></div>',unsafe_allow_html=True)
    w=[int(ss[f"w{i}"]) for i in range(6)]; wn=[x/sum(w)*100 for x in w] if sum(w)>0 else w
    m=metrics(wn)
    with right:
        lvl="Defensive" if m["sd"]<.05 else "Conservative" if m["sd"]<.085 else "Moderate" if m["sd"]<.125 else "Growth" if m["sd"]<.155 else "Aggressive"
        st.markdown(f'<div class="metric" style="border-top-color:#F97316"><div class="ml">Portfolio Risk Level</div>'
                    f'<div class="mv" style="color:#F97316">{lvl}</div><div class="ms">Volatility: {m["sd"]*100:.1f}% p.a.</div></div>',unsafe_allow_html=True)
        q=st.columns(2)
        q[0].markdown(mcard("Exp. Return",f"{m['rp']*100:.1f}%","Per year","#16794D","#E7F5EC"),unsafe_allow_html=True)
        q[0].markdown(mcard("VaR 95%",f"{m['var95']*100:.1f}%","Worst 1-in-20 year","#C53929","#FBEAE7"),unsafe_allow_html=True)
        q[1].markdown(mcard("Sharpe Ratio",f"{m['sharpe']:.2f}","Risk-adjusted return","#0E7C7B","#DFF2F1"),unsafe_allow_html=True)
        q[1].markdown(mcard("Max Drawdown",f"{m['maxdd']*100:.0f}%","Est. peak-to-trough","#B7791F","#FBF3E2"),unsafe_allow_html=True)
        segs=[(ASSETS[i],w[i],ASSET_CLR[i]) for i in range(6) if w[i]>0]
        st.markdown(f'<div class="card" style="padding:14px;margin-top:10px">{donut(segs,str(sum(w))+"%")}{legend(segs)}</div>',unsafe_allow_html=True)
    P=10000
    sec("1-Year Outcome Scenarios (on $10,000 invested)")
    s1=st.columns(3)
    for col,(lab,val,clr) in zip(s1,[("BEAR (−2σ)",P*(1+m["rp"]-2*m["sd"]),"#C53929"),("BASE",P*(1+m["rp"]),"#16794D"),("BULL (+1σ)",P*(1+m["rp"]+m["sd"]),"#16794D")]):
        d=val-P; dc="#16794D" if d>=0 else "#C53929"
        col.markdown(f'<div class="scen" style="border-top-color:{clr}"><div class="sl">{lab}</div><div class="sv" style="color:{clr}">{fmt(val)}</div>'
                     f'<div class="sd" style="color:{dc}">{"+" if d>=0 else "−"}{fmt(abs(d))} ({d/P*100:+.1f}%)</div></div>',unsafe_allow_html=True)
    sec("5-Year Projection (on $10,000 invested)")
    s5=st.columns(3)
    for col,(lab,val,clr) in zip(s5,[("WORST",P*(1+m["rp"]-Z*m["sd"])**5,"#C53929"),("EXPECTED",P*(1+m["rp"])**5,"#0E7C7B"),("BEST",P*(1+m["rp"]+m["sd"])**5,"#16794D")]):
        col.markdown(f'<div class="scen" style="border-top-color:{clr}"><div class="sl">{lab}</div><div class="sv" style="color:{"#16794D" if val>=P else "#C53929"}">{fmt(val)}</div>'
                     f'<div class="sd">{ (val/P-1)*100:+.0f}% total</div></div>',unsafe_allow_html=True)
    note("Projections use long-run capital-market assumptions and are <b>estimates, not guarantees</b>. Figures are before taxes and fees.","warn")
    # goal progress with the custom portfolio
    b=ss.get("budget") or compute_budget(ss); T=goal_target(ss); yrs=sf(ss["goal_years"]) or 1
    fv=future_value(b["savings"],max(0,b["surplus"]),m["rp"],yrs); projp=min(100,fv/T*100) if T>0 else 0
    sec("Reaching Your Ultimate Goal With This Portfolio")
    st.markdown(f'<div class="goalwrap"><div class="gt">Progress to {fmt(T)}</div>'
                f'<div class="ptrack"><div class="pp" style="width:{projp}%"></div></div>'
                f'<div class="plab"><span>This portfolio @ {m["rp"]*100:.1f}%</span><span>Projected in {int(yrs)}y: {fmt(fv)} ({projp:.0f}%)</span></div></div>',unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# STEP 5 — ACTIONS
# ════════════════════════════════════════════════════════════════
def build_recs(b,score,capL,capW,tolL,tname,rec):
    recs=[]
    if b["runway"]<3:
        tgt=b["essential"]*6; gap=max(0,tgt-b["savings"])
        recs.append(("alert","Build your emergency fund first",
            f"You have {b['runway']:.1f} months of essential expenses saved. Aim for 6 months (~{fmt(tgt)}). At your current surplus of {fmt(b['surplus'])}/mo, that is about {round(gap/b['surplus']) if b['surplus']>0 else '—'} months away." if b["surplus"]>0
            else f"You have {b['runway']:.1f} months saved and no surplus — free up cash flow first."))
    elif b["runway"]<6:
        recs.append(("warn","Top up your emergency fund",f"You have {b['runway']:.1f} months. Building to 6 gives a full buffer before taking investment risk."))
    if b["sr"]<0: recs.append(("alert","You are spending more than you earn",f"Expenses exceed income by {fmt(-b['surplus'])}/mo. No investment can outrun a monthly deficit."))
    elif b["sr"]<0.10: recs.append(("warn","Lift your savings rate",f"You are saving {b['sr']*100:.0f}% of income. Reaching 20% ({fmt(b['income']*0.20)}/mo) accelerates your goal."))
    if b["income"]>0 and b["needs"]/b["income"]>0.55: recs.append(("warn","Fixed costs are high",f"Needs are {b['needs']/b['income']*100:.0f}% of income (ideal ≤50%). Housing, transport, and insurance are the usual culprits — structural changes here free up the most room."))
    if b["dti"]>0.20: recs.append(("warn","Debt load is elevated",f"Debt repayments are {b['dti']*100:.0f}% of income. Clearing high-interest debt is effectively a guaranteed return."))
    gd=tolL-capL
    if gd>=2: recs.append(("alert","Do not invest beyond your capacity",f"Your comfort with risk ({tname}) exceeds what your finances support ({capW}). Start at {rec}."))
    elif gd<=-2: recs.append(("info","You can afford more growth when ready",f"Your finances ({capW}) could support more risk than your current comfort ({tname}). Increase exposure gradually as confidence builds."))
    if score>=65 and b["runway"]>=6: recs.append(("good","You are positioned to invest toward your goal",f"Strong foundation. Consider {fmt(max(0,b['surplus']))}/mo automated into the {rec} tier."))
    if not any(k in("alert","warn") for k,_,_ in recs): recs.append(("good","You are on a healthy path to your goal","No critical issues. Keep contributing consistently and review quarterly."))
    recs.sort(key=lambda r:{"alert":0,"warn":1,"info":2,"good":3}[r[0]]); return recs

def report_text(b,score,rt,capW,tname,rec,recs,T,fv,yrs,r):
    L=["SERALUNG FINANCE — PERSONAL FINANCIAL REPORT","="*52,"","Educational only. Not personal financial advice.","",
       "ULTIMATE GOAL","-"*52,f"  Target:           {fmt(T)}",f"  Projected in {yrs:g}y:  {fmt(fv)} @ {r*100:.1f}% p.a.",f"  Progress:         {fv/T*100:.0f}% of target" if T>0 else "  Progress:         —","",
       "GOAL-BASED FINANCIAL HEALTH","-"*52,f"  Score:            {score}/100",f"  Rating:           {rt}","",
       "MONTHLY CASH FLOW","-"*52,f"  Income:           {fmt(b['income'])}",f"  Expenses:         {fmt(b['total'])}",f"  Surplus:          {fmt(b['surplus'])}",f"  Savings rate:     {b['sr']*100:.1f}%","",
       "EMERGENCY FUND","-"*52,f"  Cash savings:     {fmt(b['savings'])}",f"  Essentials/mo:    {fmt(b['essential'])}",f"  Runway:           {b['runway']:.1f} months","",
       "RISK PROFILE","-"*52,f"  Tolerance:        {tname}",f"  Capacity:         {capW}",f"  Suggested tier:   {rec}","","PRIORITISED ACTIONS","-"*52]
    tg={"alert":"[DO FIRST] ","warn":"[IMPORTANT] ","info":"[CONSIDER] ","good":"[ON TRACK] "}
    for i,(k,t,d) in enumerate(recs,1):
        L.append(f"  {i}. {tg[k]}{t}"); cur=""
        for wd in d.split():
            if len(cur)+len(wd)+1>66: L.append("     "+cur); cur=wd
            else: cur=(cur+" "+wd).strip()
        if cur: L.append("     "+cur)
        L.append("")
    L+=["","Generated by Seralung Finance."]
    return "\n".join(L)

def calculation_notes():
    return """**How every number is calculated**

**Budget.** Income = primary + secondary. Each expense is classed Need / Want / Savings.
Surplus = income − total expenses. Savings rate = surplus ÷ income.
Essentials = sum of Needs. Emergency runway = cash savings ÷ monthly essentials.
Debt-to-income (DTI) = debt repayments ÷ income.

**Portfolio metrics (Modern Portfolio Theory).** For weights w (summing to 100%):
• Expected return Rp = Σ wᵢ·rᵢ  • Variance σ² = wᵀΣw, where Σᵢⱼ = σᵢ·σⱼ·ρᵢⱼ  • Volatility σ = √σ²
• Sharpe = (Rp − Rf) ÷ σ, with Rf = 3.5%
• VaR 95% (1-yr, parametric-normal) = max(0, 1.645·σ − Rp)
• CVaR 95% (expected shortfall) = max(0, σ·φ(1.645)/0.05 − Rp), φ(1.645)=0.1031
• Diversification ratio = (Σ wᵢ·σᵢ) ÷ σ   • Est. max drawdown ≈ min(95%, 2.4·σ)

**Scenarios (on $10,000).** 1-yr: Bear = P·(1+Rp−2σ), Base = P·(1+Rp), Bull = P·(1+Rp+σ).
5-yr: Worst = P·(1+Rp−1.645σ)⁵, Expected = P·(1+Rp)⁵, Best = P·(1+Rp+σ)⁵.

**Ultimate Goal (time value of money, monthly compounding).** i = r/12, m = years·12:
• Projected value FV = S₀·(1+i)ᵐ + C·[((1+i)ᵐ−1)/i]  (S₀ = savings, C = monthly contribution)
• Target from passive income = (annual income) ÷ 4% safe-withdrawal rate
• Required monthly C* = (T − S₀·(1+i)ᵐ)·i ÷ ((1+i)ᵐ−1)
• Years to reach T = ln((T + C/i)/(S₀ + C/i)) ÷ ln(1+i) ÷ 12

**GOAL-BASED financial health (0–100)** — the headline change:
• Goal trajectory (50 pts) = min(1, FV ÷ T) · 50  ← how far your projection reaches the goal
• Emergency runway (20 pts) = min(1, runway ÷ 6) · 20
• Savings rate (15 pts) = min(1, savings rate ÷ 20%) · 15
• Debt load (15 pts) = 15 if DTI ≤ 20% else max(0, 15 − (DTI−20%)·60)
The return r used for the trajectory is the expected return of your *suggested* tier
(from risk capacity + tolerance), so the score reflects a prudent path to the goal."""

def page_actions():
    b=ss.get("budget") or compute_budget(ss)
    T=goal_target(ss); capL,capW=cap_level(capacity(b)); tname,tolL,_=tol_profile(ss); rec=rec_tier(capL,tolL)
    r_goal=TIER_M[rec]["rp"]; yrs=sf(ss["goal_years"]) or 1
    score,(parts,ex)=goal_health(b,T,r_goal,yrs); rt,_,_=rating(score)
    recs=build_recs(b,score,capL,capW,tolL,tname,rec)
    nA=sum(1 for r in recs if r[0]=="alert"); nW=sum(1 for r in recs if r[0]=="warn")
    readiness=max(0,min(100,score-nA*12-nW*5)); rdg,rclr,rbg=rating(readiness); recClr=TIER_CLR.get(rec,"#16794D")
    projp=min(100,ex["cov"]*100) if T>0 else 0
    sec("Investment Readiness")
    a1,a2=st.columns(2)
    a1.markdown(f'<div class="card" style="padding:16px">{gauge(readiness,rclr)}</div>',unsafe_allow_html=True)
    a2.markdown(f'<div class="readwrap" style="border-left-color:{rclr};background:{rbg}"><div class="ov">Overall</div>'
                f'<div class="rt" style="color:{rclr}">{rdg}</div><div class="rd">{nA} critical item{"s" if nA!=1 else ""} and {nW} to watch. '
                f'Suggested portfolio: <b style="color:{recClr}">{rec}</b>.<br>You are projected to reach <b style="color:#16794D">{projp:.0f}%</b> of your {fmt(T)} goal in {int(yrs)} years.</div></div>',unsafe_allow_html=True)
    sec("Your Prioritised Action Plan")
    cmap={"alert":("#FBEAE7","#C53929"),"warn":("#FBF3E2","#B7791F"),"info":("#E7F5EC","#16794D"),"good":("#E7F5EC","#16794D")}
    tmap={"alert":"Do first","warn":"Important","info":"Consider","good":"On track"}
    for i,(k,t,d) in enumerate(recs,1):
        bg2,ac=cmap[k]
        st.markdown(f'<div class="action" style="border-left:3.5px solid {ac}"><div class="ah">'
                    f'<span class="num" style="background:{ac}">{i}</span><span class="tag" style="background:{bg2};color:{ac}">{tmap[k]}</span>'
                    f'<span class="at">{t}</span></div><div class="ad">{d}</div></div>',unsafe_allow_html=True)
    fv=ex["fv"]
    st.download_button("⤓ Download My Financial Report (.txt)",
        data=report_text(b,score,rt,capW,tname,rec,recs,T,fv,yrs,r_goal),
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
        if st.button("✓ Submit Feedback",disabled=ss["fb_rating"]==0):
            ss["fb_sent"]=True; st.rerun()

# ════════════════════════════════════════════════════════════════
# DISPATCH + BOTTOM NAV
# ════════════════════════════════════════════════════════════════
{1:page_budget,2:page_health,3:page_portfolio,4:page_forecast,5:page_actions}[step]()

st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)
segs="".join(f'<span style="width:42px;height:5px;border-radius:4px;background:{STEP_META[i][3] if i<step else "#E2E8F0"};display:inline-block;margin-right:7px"></span>' for i in range(5))
nb1,nb2,nb3=st.columns([1,2,1])
with nb1:
    if st.button("‹ Back",key="backbtn",disabled=step==1,type="secondary"):
        goto(step-1); st.rerun()
with nb2:
    st.markdown(f'<div style="text-align:center;padding-top:8px">{segs}</div>',unsafe_allow_html=True)
with nb3:
    if step<5:
        if st.button("Next Step ›",key="nextbtn"):
            goto(step+1); st.rerun()
    else:
        if st.button("Complete!",key="donebtn"):
            st.balloons()

st.markdown('<div style="border-top:1px solid #E3E8EF;margin-top:24px;padding:14px 0;text-align:center;font-size:.72rem;color:#94A3B8">'
            '<b style="color:#16794D">Seralung Finance</b> · Educational only — not personal financial advice.</div>',unsafe_allow_html=True)
