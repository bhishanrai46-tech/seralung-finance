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
PROT_PTS = {"Well protected & stable":15,"Partly protected":8,"Minimal or unstable":0}

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

def foundation_score(b,debt_rate,prot):
    p_run=min(1,b["runway"]/6)*35
    base=25*(1-min(1,b["dti"]/0.36))            # debt-service vs 36% lending norm
    if b["dti"]>0:
        cost=1+max(0,debt_rate-0.08)*3           # interest above 8% amplifies the penalty
        p_debt=max(0,25-(25-base)*min(2.5,cost))
    else:
        p_debt=25
    p_sr=min(1,max(0,b["sr"])/0.20)*25
    p_prot=PROT_PTS.get(prot,8)
    score=round(min(100,p_run+p_debt+p_sr+p_prot))
    return score,{"Emergency runway":(round(p_run),35),"Debt burden":(round(p_debt),25),
                  "Savings rate":(round(p_sr),25),"Protection & stability":(round(p_prot),15)}

def blend_weights(years):
    wg=min(0.60,max(0.40,0.65-0.01*years)); return 1-wg,wg

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
           ("forecast","Forecast","📈","#F97316","#FCE7D6","Forecast","Forecast your portfolio growth"),
           ("actions","Actions","✅","#10B981","#D7F5E6","Action Plan","Get your personalised plan")]
fmt=lambda n:"$"+format(int(round(n)),",")

# ════════════════════════════ STATE ════════════════════════════
def init_state():
    d={"step":1,"max_step":1,"income_primary":6000,"income_secondary":0,"savings":15000,
       "invested_assets":25000,"employer_contrib":0,"debt_rate":8.0,"inflation":2.5,"drag":0.7,
       "protection":"Partly protected","entry_mode":"individual","total_expenses":0,"selected_tier":"Defensive",
       "goal_mode":"income","goal_income":5000,"goal_lump":1000000,"goal_years":25,
       "fb_rating":0,"fb_name":"","fb_text":"","fb_sent":False,
       **{f"quiz_q{i}":2 for i in range(1,11)},**{f"w{i}":TIER_W["Balanced"][i] for i in range(6)}}
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
def page_budget():
    note("Enter your income, savings and expenses below — every metric recalculates live as you type.")
    sec("Income, Savings &amp; Investments")
    a=st.columns(3)
    a[0].number_input("Monthly after-tax income ($)",min_value=0,step=250,key="income_primary")
    a[1].number_input("Secondary income (optional)",min_value=0,step=100,key="income_secondary")
    a[2].number_input("Emergency cash savings ($)",min_value=0,step=1000,key="savings")
    c=st.columns(3)
    c[0].number_input("Current invested assets ($)",min_value=0,step=1000,key="invested_assets",help="Money already invested toward your goal (super/401k, ETFs, shares). Separate from your emergency cash.")
    c[1].number_input("Employer / retirement contribution ($/mo)",min_value=0,step=50,key="employer_contrib",help="Employer super / 401k match — counted as a monthly contribution toward your goal.")
    c[2].number_input("Avg. interest rate on your debt (%)",min_value=0.0,max_value=40.0,step=0.5,key="debt_rate",help="High-interest debt (cards) hurts your Foundation score more than a low-rate mortgage.")
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
        # ---- 50/30/20 as a DIAGNOSTIC only (not scored) ----
        sec("Budget Mix Diagnostic (50 / 30 / 20)")
        st.markdown('<div class="diag">A budgeting reference only — this does <b>not</b> affect your financial health score.</div>',unsafe_allow_html=True)
        nr=b["needs"]/b["income"]*100; wr=b["wants"]/b["income"]*100; sv=max(0,b["surplus"])/b["income"]*100
        for name,val,ideal,hint in [("Needs",nr,50,"housing, food, transport, insurance, debt"),
                                     ("Wants",wr,30,"dining, entertainment, shopping, travel"),
                                     ("Savings",sv,20,"everything left over")]:
            ok=(val<=ideal+2) if name!="Savings" else (val>=ideal-2); clr="#16794D" if ok else "#B7791F"
            st.markdown(f'<div class="rrow"><div class="top"><span class="name">{name}</span>'
                        f'<span class="val" style="color:{clr}">{val:.0f}%<span class="id"> / {ideal}%</span></span></div>'
                        f'<div class="hint">{hint}</div></div>',unsafe_allow_html=True)

# ════════════════════════════ STEP 2 — FINANCIAL HEALTH ════════════════════════════
def page_health():
    b=ss.get("budget") or compute_budget(ss)
    st.markdown('<div class="goalwrap"><div class="gt">Ultimate Goal</div>'
                '<h3>Set your destination — health is measured against it</h3>'
                '<div class="gsub">Your health blends how resilient you are now with the probability of reaching this goal.</div></div>',unsafe_allow_html=True)
    gm=st.radio("Goal type",["Target passive income","Target lump sum"],index=0 if ss["goal_mode"]=="income" else 1,horizontal=True,label_visibility="collapsed")
    ss["goal_mode"]="income" if gm=="Target passive income" else "lumpsum"
    gc=st.columns(3)
    if ss["goal_mode"]=="income": gc[0].number_input("Desired passive income ($/month, today's $)",min_value=0,step=250,key="goal_income")
    else: gc[0].number_input("Target lump sum ($, today's $)",min_value=0,step=10000,key="goal_lump")
    gc[1].number_input("Years until you want it",min_value=1,max_value=60,step=1,key="goal_years")
    gc[2].selectbox("Protection & income stability",list(PROT_PTS),key="protection",
                    help="Insurance cover and how secure/diversified your income is — part of your Foundation score.")
    with st.expander("⚙ Assumptions (inflation, fees & tax)"):
        e=st.columns(2)
        e[0].number_input("Inflation (% per year)",min_value=0.0,max_value=10.0,step=0.1,key="inflation",help="Goal & projections are shown in today's purchasing power.")
        e[1].number_input("Fees + tax drag (% per year)",min_value=0.0,max_value=3.0,step=0.1,key="drag",help="Subtracted from returns. ~0.2% index fund to ~1%+ active, plus tax.")

    if b["income"]<=0:
        note("Complete the Budget step first — your score is built from your income, savings, this goal and your assumptions.","warn"); return

    T=goal_target(ss); cap=capacity(b); capL,capW=cap_level(cap); tname,tolL,tscore=tol_profile(ss)
    rec=rec_tier(capL,tolL); rp,sd=TIER_M[rec]["rp"],TIER_M[rec]["sd"]
    Cm=max(0,b["surplus"])+sf(ss["employer_contrib"]); yrs=sf(ss["goal_years"]) or 1
    ga=goal_assess(sf(ss["invested_assets"]),Cm,rp,sd,T,yrs,sf(ss["inflation"])/100,sf(ss["drag"])/100)
    readiness=round(ga["prob"]*100)
    F,fparts=foundation_score(b,sf(ss["debt_rate"])/100,ss["protection"])
    wf,wg=blend_weights(yrs); head=round(wf*F+wg*readiness); rt,clr,bg=rating(head)

    sec("Financial Health Score")
    h1,h2=st.columns([1,1.05])
    h1.markdown(f'<div class="card" style="padding:16px;text-align:center">{gauge(head,clr)}'
                f'<div style="margin-top:2px"><span style="background:{bg};color:{clr};font-weight:700;font-size:.95rem;padding:5px 20px;border-radius:20px;display:inline-block">{rt}</span></div>'
                f'<div style="font-size:.72rem;color:#64748B;margin-top:8px">Blend: {wf*100:.0f}% Foundation · {wg*100:.0f}% Goal-readiness</div></div>',unsafe_allow_html=True)
    fclr="#16794D" if F>=70 else("#B7791F" if F>=45 else "#C53929"); gclr="#16794D" if readiness>=70 else("#B7791F" if readiness>=45 else "#C53929")
    bars=""
    for k,(gv,mx) in fparts.items():
        p=gv/mx*100; cc="#16794D" if p>=70 else("#B7791F" if p>=40 else "#C53929")
        bars+=f'<div class="brk"><div class="l"><span class="nm">{k}</span><span class="sc" style="color:{cc}">{gv}/{mx}</span></div><div class="bar"><i style="width:{p:.0f}%;background:{cc}"></i></div></div>'
    h2.markdown(f'<div class="subscore"><div class="h"><span class="t">🛡 Foundation (resilience now)</span><span class="v" style="color:{fclr}">{F}/100</span></div>'
                f'<div class="d">Emergency buffer, debt burden, savings rate & protection.</div></div>'
                f'<div style="padding:2px 4px 0">{bars}</div>'
                f'<div class="subscore" style="margin-top:6px"><div class="h"><span class="t">🎯 Goal-readiness (probability)</span><span class="v" style="color:{gclr}">{readiness}/100</span></div>'
                f'<div class="d">A <b>{readiness}% chance</b> of reaching {fmt(T)} in {int(yrs)}y, in today\'s dollars, with the {rec} portfolio (net of fees, after inflation).</div></div>',unsafe_allow_html=True)
    note(f"Your financial health is <b>{rt}</b> — a {wf*100:.0f}/{wg*100:.0f} blend of a <b>{F}</b> Foundation and a <b>{readiness}%</b> probability of reaching your goal.",
         "good" if head>=65 else("warn" if head>=45 else "alert"))

    sec("Where You Stand")
    nowp=min(100,ga["now"]*100); projp=min(100,ga["med"]/T*100) if T>0 else 0
    st.markdown(f'<div class="goalwrap"><div class="gt">Progress to {fmt(T)} (today\'s $)</div>'
                f'<div class="ptrack"><div class="pp" style="width:{projp}%"></div><div class="pn" style="width:{nowp}%"></div></div>'
                f'<div class="plab"><span>Invested now: {ga["now"]*100:.1f}% ({fmt(sf(ss["invested_assets"]))})</span><span>Median projection in {int(yrs)}y: {fmt(ga["med"])}</span></div>'
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px">'
                f'<div class="gstat"><div class="l">Goal target</div><div class="v">{fmt(T)}</div><div class="s">{("$%s/mo via 4%% rule"%format(int(sf(ss["goal_income"])),",")) if ss["goal_mode"]=="income" else "lump sum, today\'s $"}</div></div>'
                f'<div class="gstat"><div class="l">Chance of success</div><div class="v">{readiness}%</div><div class="s">Monte Carlo, real terms</div></div>'
                f'<div class="gstat"><div class="l">Median projection</div><div class="v">{fmt(ga["med"])}</div><div class="s">in {int(yrs)}y @ {ga["rr"]*100:.1f}% real</div></div>'
                f'<div class="gstat"><div class="l">To stay on track</div><div class="v">{fmt(ga["req"])}/mo</div><div class="s">vs your {fmt(Cm)}/mo now</div></div>'
                f'</div></div>',unsafe_allow_html=True)
    ytg=ga["ytg"]
    if readiness>=70: note(f"On track — about a {readiness}% chance of reaching {fmt(T)}. At {fmt(Cm)}/mo your median path gets there in ~{ytg:.0f} years.","good")
    elif np.isfinite(ytg): note(f"At {fmt(Cm)}/mo your median path reaches the goal in ~{ytg:.0f} years. To hit it in {int(yrs)}y with confidence, lift contributions toward {fmt(ga['req'])}/mo or choose a higher-return tier.","warn")
    else: note(f"On the conservative {rec} portfolio this goal isn't reachable at your current saving. Raise contributions toward {fmt(ga['req'])}/mo, extend the horizon, or step up risk on the Forecast step.","alert")

    sec("Risk Profile — 10 Questions")
    note("These set your comfort with volatility, which picks your suggested portfolio (and the return used above).")
    for i,(q,opts) in enumerate(QUESTIONS):
        st.markdown(f'<div style="background:#fff;border:1px solid #E3E8EF;border-radius:14px;padding:12px 16px 4px;margin-bottom:6px;box-shadow:0 1px 3px rgba(0,0,0,.03)">'
                    f'<span style="background:#D6F1F7;color:#0E7490;font-size:.68rem;font-weight:700;padding:2px 8px;border-radius:5px;font-family:JetBrains Mono">{i+1:02d}/10</span> '
                    f'<b style="font-size:.95rem">{q}</b></div>',unsafe_allow_html=True)
        st.radio(q,list(range(4)),format_func=lambda x,o=opts:o[x],key=f"quiz_q{i+1}",label_visibility="collapsed",horizontal=True)
    sec("Risk Analysis")
    r1,r2,r3=st.columns(3)
    r1.markdown(mcard("Risk Tolerance",tname,f"Level {tolL}/5 · score {tscore}/40",TIER_CLR.get(rec,'#16794D'),"#E7F5EC"),unsafe_allow_html=True)
    capclr=["#C53929","#C53929","#B7791F","#0E7C7B","#16794D"][capL-1]; capbg=["#FBEAE7","#FBEAE7","#FBF3E2","#DFF2F1","#E7F5EC"][capL-1]
    r2.markdown(mcard("Risk Capacity",capW,f"Level {capL}/5 · from your budget",capclr,capbg),unsafe_allow_html=True)
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

# ════════════════════════════ STEP 4 — FORECAST ════════════════════════════
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
        st.markdown(f'<div style="display:flex;justify-content:space-between;font-weight:700;border-top:1px solid #E3E8EF;padding-top:10px;font-family:JetBrains Mono"><span>Total</span><span style="color:{"#16794D" if wsum==100 else "#C53929"}">{wsum}%</span></div>',unsafe_allow_html=True)
    w=[int(ss[f"w{i}"]) for i in range(6)]; wn=[x/sum(w)*100 for x in w] if sum(w)>0 else w; m=metrics(wn)
    with right:
        lvl="Defensive" if m["sd"]<.05 else "Conservative" if m["sd"]<.085 else "Moderate" if m["sd"]<.125 else "Growth" if m["sd"]<.155 else "Aggressive"
        st.markdown(f'<div class="metric" style="border-top-color:#F97316"><div class="ml">Portfolio Risk Level</div><div class="mv" style="color:#F97316">{lvl}</div><div class="ms">Volatility: {m["sd"]*100:.1f}% p.a.</div></div>',unsafe_allow_html=True)
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
        col.markdown(f'<div class="scen" style="border-top-color:{clr}"><div class="sl">{lab}</div><div class="sv" style="color:{clr}">{fmt(val)}</div><div class="sd" style="color:{dc}">{"+" if d>=0 else "−"}{fmt(abs(d))} ({d/P*100:+.1f}%)</div></div>',unsafe_allow_html=True)
    sec("5-Year Projection (on $10,000 invested)")
    s5=st.columns(3)
    for col,(lab,val,clr) in zip(s5,[("WORST",P*(1+m["rp"]-Z*m["sd"])**5,"#C53929"),("EXPECTED",P*(1+m["rp"])**5,"#0E7C7B"),("BEST",P*(1+m["rp"]+m["sd"])**5,"#16794D")]):
        col.markdown(f'<div class="scen" style="border-top-color:{clr}"><div class="sl">{lab}</div><div class="sv" style="color:{"#16794D" if val>=P else "#C53929"}">{fmt(val)}</div><div class="sd">{(val/P-1)*100:+.0f}% total</div></div>',unsafe_allow_html=True)
    note("Projections use long-run capital-market assumptions and are <b>estimates, not guarantees</b>. Figures are before taxes and fees.","warn")
    b=ss.get("budget") or compute_budget(ss); T=goal_target(ss); yrs=sf(ss["goal_years"]) or 1
    Cm=max(0,b["surplus"])+sf(ss["employer_contrib"])
    ga=goal_assess(sf(ss["invested_assets"]),Cm,m["rp"],m["sd"],T,yrs,sf(ss["inflation"])/100,sf(ss["drag"])/100)
    projp=min(100,ga["med"]/T*100) if T>0 else 0
    sec("Reaching Your Ultimate Goal With This Portfolio")
    st.markdown(f'<div class="goalwrap"><div class="gt">Progress to {fmt(T)} (real, net of fees)</div>'
                f'<div class="ptrack"><div class="pp" style="width:{projp}%"></div></div>'
                f'<div class="plab"><span>This portfolio · {round(ga["prob"]*100)}% chance of success</span><span>Median in {int(yrs)}y: {fmt(ga["med"])} ({projp:.0f}%)</span></div></div>',unsafe_allow_html=True)

# ════════════════════════════ STEP 5 — ACTIONS ════════════════════════════
def build_recs(b,head,readiness,F,capL,capW,tolL,tname,rec,ga,T,yrs):
    recs=[]
    if b["runway"]<3:
        tgt=b["essential"]*6
        recs.append(("alert","Build your emergency fund first",
            f"You have {b['runway']:.1f} months of essentials saved. Aim for 6 (~{fmt(tgt)}) before taking market risk." ))
    elif b["runway"]<6:
        recs.append(("warn","Top up your emergency fund",f"You have {b['runway']:.1f} months. Building to 6 gives a full buffer before investing."))
    if b["sr"]<0: recs.append(("alert","You are spending more than you earn",f"Expenses exceed income by {fmt(-b['surplus'])}/mo. No investment can outrun a monthly deficit."))
    elif b["sr"]<0.10: recs.append(("warn","Lift your savings rate",f"You are saving {b['sr']*100:.0f}% of income. Reaching 20% ({fmt(b['income']*0.20)}/mo) sharply raises your goal-readiness."))
    if b["dti"]>0.20 and sf(ss["debt_rate"])>=10: recs.append(("alert","Clear high-interest debt first",f"Your debt averages {sf(ss['debt_rate']):.0f}% — paying it down is a guaranteed return that beats most portfolios."))
    elif b["dti"]>0.30: recs.append(("warn","Debt load is elevated",f"Debt repayments are {b['dti']*100:.0f}% of income (lending norms cap near 36%)."))
    if ss["protection"]=="Minimal or unstable": recs.append(("warn","Shore up your safety net",f"Without adequate insurance or stable income, one shock can undo years of progress — this caps your Foundation score."))
    if readiness<40 and b["income"]>0:
        recs.append(("alert" if readiness<20 else "warn","Your goal needs more fuel",
            f"Only a {readiness}% chance of reaching {fmt(T)} in {int(yrs)}y. Lift contributions toward {fmt(ga['req'])}/mo, extend the horizon, or raise risk to close the gap."))
    gd=tolL-capL
    if gd>=2: recs.append(("alert","Do not invest beyond your capacity",f"Your comfort with risk ({tname}) exceeds what your finances support ({capW}). Start at {rec}."))
    elif gd<=-2: recs.append(("info","You can afford more growth when ready",f"Your finances ({capW}) could support more risk than your current comfort ({tname}). Increase exposure gradually."))
    if F>=70 and readiness>=70: recs.append(("good","You are positioned to invest toward your goal",f"Strong foundation and a {readiness}% chance of success. Consider {fmt(max(0,b['surplus']))}/mo automated into {rec}."))
    if not any(k in("alert","warn") for k,_,_ in recs): recs.append(("good","You are on a healthy path to your goal","No critical issues. Keep contributing consistently and review quarterly."))
    recs.sort(key=lambda r:{"alert":0,"warn":1,"info":2,"good":3}[r[0]]); return recs

def calculation_notes():
    return """**How financial health is calculated (the realistic model)**

The headline score is a **life-stage-weighted blend** of two independent sub-scores:

`Headline = w_F · Foundation + w_G · Goal-readiness`, where the goal weight
`w_G = clamp(0.65 − 0.01·years, 0.40, 0.60)` — nearer goals lean on readiness, distant goals on foundation.

**① Foundation — resilience right now (0–100)**
• Emergency runway (35) = min(1, runway ÷ 6) · 35
• Debt burden (25) = starts from 25·(1 − min(1, DTI ÷ 36%)); the shortfall is then *amplified* when your average debt rate exceeds 8% (×up to 2.5) — so a 20% card hurts far more than a 3% mortgage.
• Savings rate (25) = min(1, savings-rate ÷ 20%) · 25
• Protection & stability (15) = 15 well-protected / 8 partly / 0 minimal.

**② Goal-readiness — probability of reaching your goal (0–100)**
A Monte Carlo simulation (4,000 paths, monthly steps) projects your invested assets plus
monthly contributions (including employer/super) and returns the **probability of reaching
the target**. Everything is in **real, today's-dollar terms**:
• Net return = tier expected return − fees/tax drag; Real return = (1+net)/(1+inflation) − 1
• Target from passive income = annual income ÷ 4% safe-withdrawal rate (already in today's $)
• The portfolio used is your *suggested* tier (capacity + tolerance). Readiness = % of paths ≥ target.

**Supporting figures**
• Required monthly C* = (T − S₀·(1+i)ᵐ)·i ÷ ((1+i)ᵐ−1), i = real-rate/12, m = years·12
• Years to goal = ln((T + C/i)/(S₀ + C/i)) ÷ ln(1+i) ÷ 12
• Portfolio metrics (MPT): Rp = Σwᵢrᵢ; σ = √(wᵀΣw); Sharpe = (Rp−Rf)/σ;
  VaR₉₅ = max(0, 1.645σ − Rp); CVaR₉₅ = max(0, σ·φ(1.645)/0.05 − Rp); MaxDD ≈ min(95%, 2.4σ).

**The 50/30/20 rule is not scored** — it is shown on the Budget step purely as a spending-mix
diagnostic, because a balanced budget doesn't tell you whether you can withstand a shock or
reach your goal. Resilience and trajectory do."""

def report_text(b,head,F,readiness,rt,capW,tname,rec,recs,T,ga,yrs):
    L=["SERALUNG FINANCE — PERSONAL FINANCIAL REPORT","="*52,"","Educational only. Not personal financial advice.","",
       "FINANCIAL HEALTH (goal-based blend)","-"*52,f"  Headline:         {head}/100 ({rt})",f"  Foundation:       {F}/100",f"  Goal-readiness:   {readiness}/100  ({readiness}% chance of success)","",
       "ULTIMATE GOAL","-"*52,f"  Target:           {fmt(T)} (today's $)",f"  Median projection:{fmt(ga['med'])} in {yrs:g}y @ {ga['rr']*100:.1f}% real",f"  Required:         {fmt(ga['req'])}/mo on the expected path","",
       "MONTHLY CASH FLOW","-"*52,f"  Income:           {fmt(b['income'])}",f"  Expenses:         {fmt(b['total'])}",f"  Surplus:          {fmt(b['surplus'])}",f"  Savings rate:     {b['sr']*100:.1f}%","",
       "RESILIENCE","-"*52,f"  Emergency runway: {b['runway']:.1f} months",f"  Invested assets:  {fmt(sf(ss['invested_assets']))}",f"  Debt service:     {b['dti']*100:.0f}% of income","",
       "RISK PROFILE","-"*52,f"  Tolerance:        {tname}",f"  Capacity:         {capW}",f"  Suggested tier:   {rec}","","PRIORITISED ACTIONS","-"*52]
    tg={"alert":"[DO FIRST] ","warn":"[IMPORTANT] ","info":"[CONSIDER] ","good":"[ON TRACK] "}
    for i,(k,t,d) in enumerate(recs,1):
        L.append(f"  {i}. {tg[k]}{t}"); cur=""
        for wd in d.split():
            if len(cur)+len(wd)+1>66: L.append("     "+cur); cur=wd
            else: cur=(cur+" "+wd).strip()
        if cur: L.append("     "+cur)
        L.append("")
    L+=["","Generated by Seralung Finance."]; return "\n".join(L)

def page_actions():
    b=ss.get("budget") or compute_budget(ss)
    T=goal_target(ss); capL,capW=cap_level(capacity(b)); tname,tolL,_=tol_profile(ss); rec=rec_tier(capL,tolL)
    rp,sd=TIER_M[rec]["rp"],TIER_M[rec]["sd"]; yrs=sf(ss["goal_years"]) or 1
    Cm=max(0,b["surplus"])+sf(ss["employer_contrib"])
    ga=goal_assess(sf(ss["invested_assets"]),Cm,rp,sd,T,yrs,sf(ss["inflation"])/100,sf(ss["drag"])/100)
    readiness=round(ga["prob"]*100); F,_=foundation_score(b,sf(ss["debt_rate"])/100,ss["protection"])
    wf,wg=blend_weights(yrs); head=round(wf*F+wg*readiness); rt,_,_=rating(head)
    recs=build_recs(b,head,readiness,F,capL,capW,tolL,tname,rec,ga,T,yrs)
    nA=sum(1 for r in recs if r[0]=="alert"); nW=sum(1 for r in recs if r[0]=="warn")
    rdg,rclr,rbg=rating(head); recClr=TIER_CLR.get(rec,"#16794D")
    sec("Investment Readiness")
    a1,a2=st.columns(2)
    a1.markdown(f'<div class="card" style="padding:16px">{gauge(head,rclr)}</div>',unsafe_allow_html=True)
    a2.markdown(f'<div class="readwrap" style="border-left-color:{rclr};background:{rbg}"><div class="ov">Overall</div>'
                f'<div class="rt" style="color:{rclr}">{rdg}</div><div class="rd">{nA} critical item{"s" if nA!=1 else ""} and {nW} to watch. '
                f'Foundation <b>{F}</b>, goal-readiness <b>{readiness}%</b>. Suggested portfolio: <b style="color:{recClr}">{rec}</b>.</div></div>',unsafe_allow_html=True)
    sec("Your Prioritised Action Plan")
    cmap={"alert":("#FBEAE7","#C53929"),"warn":("#FBF3E2","#B7791F"),"info":("#E7F5EC","#16794D"),"good":("#E7F5EC","#16794D")}
    tmap={"alert":"Do first","warn":"Important","info":"Consider","good":"On track"}
    for i,(k,t,d) in enumerate(recs,1):
        bg2,ac=cmap[k]
        st.markdown(f'<div class="action" style="border-left:3.5px solid {ac}"><div class="ah"><span class="num" style="background:{ac}">{i}</span>'
                    f'<span class="tag" style="background:{bg2};color:{ac}">{tmap[k]}</span><span class="at">{t}</span></div><div class="ad">{d}</div></div>',unsafe_allow_html=True)
    st.download_button("⤓ Download My Financial Report (.txt)",
        data=report_text(b,head,F,readiness,rt,capW,tname,rec,recs,T,ga,yrs),
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
{1:page_budget,2:page_health,3:page_portfolio,4:page_forecast,5:page_actions}[step]()
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
