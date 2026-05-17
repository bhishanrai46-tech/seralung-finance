"""
db.py — Supabase auth + data persistence
Place in same folder as seralung_premium.py

Streamlit Cloud secrets:
    SUPABASE_URL = "https://your-project.supabase.co"
    SUPABASE_KEY = "eyJ..."
"""
import streamlit as st
from supabase import create_client, Client

DATA_KEYS = ["expenses","subscriptions","bills","assets","liabilities","goals","transactions"]

# ── income is now saved here so it persists across logins ────────────────────
SETTING_DEFAULTS = {
    "primary_income": 6000.0,   # NEW — income persists
    "other_income":   500.0,    # NEW — income persists
    "needs_pct": 50, "wants_pct": 30, "invest_pct": 20,
    "risk_profile": "Moderate", "age": 32, "retirement_age": 65,
    "em_pct": 30, "idx_pct": 40, "stk_pct": 20, "cry_pct": 10,
    "streak_days": 0,
}

def _clean_url(raw: str) -> str:
    url = raw.strip().rstrip("/")
    if not url.startswith("http"): url = "https://" + url
    return url

def init_supabase() -> Client:
    if "sb_client" in st.session_state:
        return st.session_state["sb_client"]
    missing = [k for k in ["SUPABASE_URL","SUPABASE_KEY"] if k not in st.secrets]
    if missing:
        st.error(f"Missing secrets: {', '.join(missing)}\n\nAdd them in Streamlit Cloud → App Settings → Secrets.")
        st.stop()
    url = _clean_url(st.secrets["SUPABASE_URL"])
    key = st.secrets["SUPABASE_KEY"].strip()
    if "supabase.co" not in url:
        st.error(f"SUPABASE_URL looks wrong: `{url}`\nShould be: `https://abcdef.supabase.co`")
        st.stop()
    if not key.startswith("eyJ"):
        st.error("SUPABASE_KEY should start with `eyJ`. Use the **anon/public** key from Supabase → Project Settings → API.")
        st.stop()
    try:
        client = create_client(url, key)
        st.session_state["sb_client"] = client
        return client
    except Exception as e:
        st.error(f"Cannot connect to Supabase. URL: `{url}`\nError: {e}")
        st.stop()

def get_user():
    return st.session_state.get("sb_user", None)

def _store_session(session):
    st.session_state["sb_user"]          = session.user
    st.session_state["sb_access_token"]  = session.access_token
    st.session_state["sb_refresh_token"] = session.refresh_token

def _clear_session():
    for k in ["sb_user","sb_access_token","sb_refresh_token","sb_client","data_loaded","chat_history"]:
        st.session_state.pop(k, None)

def restore_session(sb: Client) -> bool:
    tok = st.session_state.get("sb_access_token")
    ref = st.session_state.get("sb_refresh_token")
    if not tok or not ref: return False
    try:
        res = sb.auth.set_session(tok, ref)
        if res and res.user:
            _store_session(res.session); return True
    except Exception:
        _clear_session()
    return False

def logout(sb: Client):
    try: sb.auth.sign_out()
    except Exception: pass
    _clear_session(); st.rerun()

def load_user_data(sb: Client) -> bool:
    user = get_user()
    if not user: return False
    try:
        res = sb.table("user_data").select("*").eq("user_id", user.id).execute()
        if res.data:
            row = res.data[0]
            for k in DATA_KEYS:
                if row.get(k) is not None: st.session_state[k] = row[k]
            settings = row.get("settings") or {}
            for k, default in SETTING_DEFAULTS.items():
                st.session_state[k] = settings.get(k, default)
            # Migrate old goal format
            for i, g in enumerate(st.session_state.get("goals", [])):
                if "amount" in g and "target" not in g:
                    st.session_state.goals[i]["target"] = g["amount"]
                    del st.session_state.goals[i]["amount"]
                if "saved" not in g: st.session_state.goals[i]["saved"] = 0.0
            return True
        return False
    except Exception as e:
        st.warning(f"Could not load saved data: {e}")
        return False

def save_user_data(sb: Client) -> bool:
    user = get_user()
    if not user: return False
    try:
        payload = {"user_id": user.id}
        for k in DATA_KEYS:
            payload[k] = st.session_state.get(k, [])
        payload["settings"] = {k: st.session_state.get(k, d) for k, d in SETTING_DEFAULTS.items()}
        sb.table("user_data").upsert(payload, on_conflict="user_id").execute()
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

def _friendly_error(raw: str) -> str:
    r = raw.lower()
    if "invalid path" in r or "invalid url" in r:
        return "Config error: SUPABASE_URL is wrong.\nMust be: https://abcdef.supabase.co (no trailing slash)"
    if "email not confirmed" in r:
        return "Please confirm your email first — check your inbox."
    if "invalid login" in r or "invalid_credentials" in r:
        return "Wrong email or password."
    if "already registered" in r:
        return "Email already registered. Switch to Sign in."
    if "rate limit" in r:
        return "Too many attempts. Wait a minute and try again."
    return raw[:200]

def login_page(sb: Client, T: dict):
    A   = T.get("accent","#059669")
    SU  = T.get("surface","#FFFFFF")
    S2  = T.get("surface2","#F3F4F6")
    BO  = T.get("border","#E5E7EB")
    TX  = T.get("text","#111827")
    MU  = T.get("muted","#6B7280")
    BG  = T.get("bg","#F9FAFB")

    st.markdown(f"""
<style>
html,body,.stApp{{background:{BG}!important;}}
.lw{{max-width:420px;margin:3.5rem auto 0;background:{SU};border:1px solid {BO};
  border-radius:18px;padding:2.2rem 2rem 1.8rem;box-shadow:0 4px 24px rgba(0,0,0,0.08);}}
.lt{{font-size:1.6rem;font-weight:800;color:{TX};text-align:center;letter-spacing:-.02em;margin-bottom:.2rem;}}
.ls{{color:{MU};font-size:.78rem;text-align:center;margin-bottom:1.4rem;}}
.le{{background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:.6rem .9rem;
  color:#991B1B;font-size:.78rem;margin:.4rem 0;line-height:1.5;white-space:pre-wrap;}}
.lo{{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:.6rem .9rem;
  color:#166534;font-size:.78rem;margin:.4rem 0;}}
[data-testid="stTextInput"] input{{
  background:{S2}!important;border:1.5px solid {BO}!important;
  border-radius:9px!important;color:{TX}!important;font-size:.88rem!important;}}
[data-testid="stTextInput"] input:focus{{border-color:{A}!important;}}
label,[data-testid="stWidgetLabel"] *{{color:{TX}!important;font-size:.8rem!important;}}
.stButton>button{{
  background:{A}!important;border:none!important;border-radius:9px!important;
  color:#fff!important;font-weight:700!important;font-size:.88rem!important;
  width:100%;padding:.55rem 1rem!important;}}
.stButton>button:hover{{filter:brightness(1.06);}}
.stRadio [role="radiogroup"]{{justify-content:center;gap:1.5rem;}}
.stRadio label span{{color:{TX}!important;font-size:.85rem!important;}}
</style>""", unsafe_allow_html=True)

    _,col,_=st.columns([1,2,1])
    with col:
        st.markdown("<div class='lw'>",unsafe_allow_html=True)
        st.markdown("<div class='lt'>Seralung Finance</div>",unsafe_allow_html=True)
        st.markdown("<div class='ls'>Track. Spend. Build.</div>",unsafe_allow_html=True)
        mode=st.radio("",["Sign in","Create account"],horizontal=True,label_visibility="collapsed")
        email=st.text_input("Email",placeholder="you@example.com",key="login_email")
        password=st.text_input("Password",placeholder="At least 6 characters",type="password",key="login_pass")
        confirm=None
        if mode=="Create account":
            confirm=st.text_input("Confirm password",placeholder="Repeat password",type="password",key="login_confirm")
        if st.button("Create account" if mode=="Create account" else "Sign in",use_container_width=True):
            err=None
            if not email or "@" not in email: err="Enter a valid email address."
            elif not password:               err="Enter your password."
            elif mode=="Create account" and len(password)<6: err="Password must be 6+ characters."
            elif mode=="Create account" and confirm!=password: err="Passwords do not match."
            if err:
                st.markdown(f"<div class='le'>{err}</div>",unsafe_allow_html=True)
            else:
                with st.spinner("Please wait..."):
                    try:
                        if mode=="Create account":
                            res=sb.auth.sign_up({"email":email.strip(),"password":password})
                            if res.user and res.session:
                                _store_session(res.session); st.rerun()
                            elif res.user:
                                st.markdown("<div class='lo'>Account created! Check your email to confirm, then sign in.</div>",unsafe_allow_html=True)
                            else:
                                st.markdown("<div class='le'>Sign-up failed. Try a different email.</div>",unsafe_allow_html=True)
                        else:
                            res=sb.auth.sign_in_with_password({"email":email.strip(),"password":password})
                            if res.session: _store_session(res.session); st.rerun()
                            else: st.markdown("<div class='le'>Sign-in failed.</div>",unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"<div class='le'>{_friendly_error(str(e))}</div>",unsafe_allow_html=True)
        st.markdown(f"<div style='text-align:center;margin-top:1rem;font-size:.66rem;color:{MU};'>"
                    "Your data is encrypted and stored securely.</div>",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)
