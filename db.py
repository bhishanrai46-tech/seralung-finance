"""
db.py — Supabase auth + data persistence for Seralung Finance
Place this file in the same folder as seralung_premium.py

Requires .streamlit/secrets.toml:
    SUPABASE_URL = "https://xxx.supabase.co"
    SUPABASE_KEY = "eyJhbGc..."   # anon/public key

Or set them in Streamlit Cloud → App Settings → Secrets.
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# DATA KEYS — everything that gets saved to / loaded from Supabase
# ─────────────────────────────────────────────────────────────────────────────
DATA_KEYS  = ["expenses","subscriptions","bills","assets","liabilities","goals","transactions"]
SETTING_KEYS = ["needs_pct","wants_pct","invest_pct","risk_profile","age","retirement_age",
                "em_pct","idx_pct","stk_pct","cry_pct","streak_days","total_saved_this_year"]
SETTING_DEFAULTS = {
    "needs_pct":50,"wants_pct":30,"invest_pct":20,"risk_profile":"Moderate",
    "age":32,"retirement_age":65,"em_pct":30,"idx_pct":40,"stk_pct":20,
    "cry_pct":10,"streak_days":0,"total_saved_this_year":0.0,
}

# ─────────────────────────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────────────────────────
def init_supabase() -> Client:
    """Create and cache the Supabase client."""
    if "sb_client" not in st.session_state:
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
            st.session_state["sb_client"] = create_client(url, key)
        except KeyError:
            st.error("Missing SUPABASE_URL or SUPABASE_KEY in secrets. "
                     "Add them in .streamlit/secrets.toml or Streamlit Cloud → Secrets.")
            st.stop()
    return st.session_state["sb_client"]

# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_user():
    """Return the logged-in user object, or None."""
    return st.session_state.get("sb_user", None)

def restore_session(sb: Client) -> bool:
    """Try to restore auth session from stored tokens (survives page reload)."""
    tok = st.session_state.get("sb_access_token")
    ref = st.session_state.get("sb_refresh_token")
    if tok and ref:
        try:
            res = sb.auth.set_session(tok, ref)
            if res and res.user:
                st.session_state["sb_user"] = res.user
                st.session_state["sb_access_token"]  = res.session.access_token
                st.session_state["sb_refresh_token"] = res.session.refresh_token
                return True
        except Exception:
            _clear_session()
    return False

def _store_session(session):
    st.session_state["sb_user"]          = session.user
    st.session_state["sb_access_token"]  = session.access_token
    st.session_state["sb_refresh_token"] = session.refresh_token

def _clear_session():
    for k in ["sb_user","sb_access_token","sb_refresh_token","data_loaded","chat_history"]:
        st.session_state.pop(k, None)

def logout(sb: Client):
    try:
        sb.auth.sign_out()
    except Exception:
        pass
    _clear_session()
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# DATA SYNC
# ─────────────────────────────────────────────────────────────────────────────
def load_user_data(sb: Client) -> bool:
    """Fetch the user's row from Supabase and populate session state."""
    user = get_user()
    if not user:
        return False
    try:
        res = sb.table("user_data").select("*").eq("user_id", user.id).execute()
        if res.data:
            row = res.data[0]
            for k in DATA_KEYS:
                if row.get(k) is not None:
                    st.session_state[k] = row[k]
            settings = row.get("settings") or {}
            for k, default in SETTING_DEFAULTS.items():
                st.session_state[k] = settings.get(k, default)
            return True
        # No row yet — first login, keep demo defaults
        return False
    except Exception as e:
        st.warning(f"Could not load saved data: {e}")
        return False

def save_user_data(sb: Client) -> bool:
    """Upsert the current session state back to Supabase."""
    user = get_user()
    if not user:
        return False
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

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN / SIGNUP UI
# ─────────────────────────────────────────────────────────────────────────────
def login_page(sb: Client, T: dict):
    """
    Renders a full-page login/signup form.
    Call this before the main app and st.stop() if user is not authenticated.
    """
    accent  = T.get("accent","#10B981")
    surface = T.get("surface","#111827")
    surface2= T.get("surface2","#1C2639")
    border  = T.get("border","#1F2D45")
    text    = T.get("text","#F0F6FF")
    muted   = T.get("muted","#6B7A99")
    grad    = T.get("grad","linear-gradient(135deg,#10B981,#3B82F6)")
    bg      = T.get("bg","#090E1A")

    st.markdown(f"""
    <style>
    html,body,.stApp{{background:{bg} !important;}}
    .login-wrap{{
      max-width:440px;margin:4rem auto 0;
      background:{surface};border:1px solid {border};
      border-radius:20px;padding:2.5rem 2rem 2rem;
      box-shadow:0 8px 48px rgba(0,0,0,0.4);
    }}
    .login-title{{
      background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;
      background-clip:text;font-size:1.7rem;font-weight:800;text-align:center;
      letter-spacing:-0.03em;margin-bottom:0.3rem;
    }}
    .login-sub{{color:{muted};font-size:0.8rem;text-align:center;margin-bottom:1.5rem;}}
    .login-err{{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
      border-radius:8px;padding:0.6rem 0.9rem;color:#F87171;font-size:0.78rem;margin-bottom:0.7rem;}}
    .login-ok {{background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);
      border-radius:8px;padding:0.6rem 0.9rem;color:{accent};font-size:0.78rem;margin-bottom:0.7rem;}}
    [data-testid="stTextInput"] input{{
      background:{surface2} !important;border:1px solid {border} !important;
      border-radius:10px !important;color:{text} !important;font-size:0.88rem !important;
    }}
    label,[data-testid="stWidgetLabel"] *{{color:{text} !important;font-size:0.8rem !important;}}
    .stButton>button{{
      background:{grad} !important;border:none !important;border-radius:10px !important;
      color:#fff !important;font-weight:700 !important;font-size:0.88rem !important;
      padding:0.55rem 1rem !important;width:100%;
    }}
    .stButton>button:hover{{opacity:0.88 !important;transform:translateY(-1px);}}
    </style>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>Seralung Finance</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-sub'>Your premium financial companion</div>", unsafe_allow_html=True)

        mode = st.radio("", ["Sign in","Create account"], horizontal=True, label_visibility="collapsed")
        email    = st.text_input("Email",    placeholder="you@example.com")
        password = st.text_input("Password", placeholder="••••••••", type="password")

        if mode == "Create account":
            confirm = st.text_input("Confirm password", placeholder="••••••••", type="password")
            st.markdown(f"<div style='font-size:0.7rem;color:{muted};margin:-0.4rem 0 0.4rem;'>"
                        "Minimum 6 characters. A verification email will be sent.</div>", unsafe_allow_html=True)

        if st.button("Create account" if mode == "Create account" else "Sign in", use_container_width=True):
            if not email or not password:
                st.markdown("<div class='login-err'>Please enter your email and password.</div>", unsafe_allow_html=True)
            elif mode == "Create account" and password != confirm:
                st.markdown("<div class='login-err'>Passwords do not match.</div>", unsafe_allow_html=True)
            elif mode == "Create account" and len(password) < 6:
                st.markdown("<div class='login-err'>Password must be at least 6 characters.</div>", unsafe_allow_html=True)
            else:
                with st.spinner("Please wait..."):
                    try:
                        if mode == "Create account":
                            res = sb.auth.sign_up({"email": email, "password": password})
                            if res.user:
                                if res.session:
                                    _store_session(res.session)
                                    st.session_state["just_registered"] = True
                                    st.rerun()
                                else:
                                    st.markdown("<div class='login-ok'>Account created! Check your email to confirm, then sign in.</div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div class='login-err'>Sign-up failed. Try a different email.</div>", unsafe_allow_html=True)
                        else:
                            res = sb.auth.sign_in_with_password({"email": email, "password": password})
                            if res.session:
                                _store_session(res.session)
                                st.rerun()
                            else:
                                st.markdown("<div class='login-err'>Invalid email or password.</div>", unsafe_allow_html=True)
                    except Exception as e:
                        msg = str(e)
                        if "Email not confirmed" in msg:
                            st.markdown("<div class='login-err'>Please confirm your email first. Check your inbox.</div>", unsafe_allow_html=True)
                        elif "Invalid login" in msg or "invalid_credentials" in msg:
                            st.markdown("<div class='login-err'>Invalid email or password.</div>", unsafe_allow_html=True)
                        elif "already registered" in msg:
                            st.markdown("<div class='login-err'>Email already registered. Sign in instead.</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='login-err'>Error: {msg[:120]}</div>", unsafe_allow_html=True)

        st.markdown(f"<div style='text-align:center;margin-top:1.2rem;font-size:0.68rem;color:{muted};'>"
                    "Your data is encrypted and stored securely in Supabase.<br>"
                    "We never sell your financial data.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
