"""
db.py — Supabase auth + data persistence for Seralung Finance
Place in same folder as seralung_premium.py

Streamlit Cloud secrets (App Settings → Secrets):
    SUPABASE_URL = "https://your-project.supabase.co"
    SUPABASE_KEY = "eyJ..."
"""
import streamlit as st
from supabase import create_client, Client

DATA_KEYS = [
    "expenses","subscriptions","bills","assets",
    "liabilities","goals","transactions",
]
SETTING_DEFAULTS = {
    "primary_income": 6000.0,
    "other_income":   500.0,
    "needs_pct": 50, "wants_pct": 30, "invest_pct": 20,
    "risk_profile": "Moderate", "age": 32, "retirement_age": 65,
    "em_pct": 30, "idx_pct": 40, "stk_pct": 20, "cry_pct": 10,
}

# ─────────────────────────────────────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────────────────────────────────────
def _clean_url(raw):
    url = raw.strip().rstrip("/")
    if not url.startswith("http"): url = "https://" + url
    return url

def init_supabase() -> Client:
    if "sb_client" in st.session_state:
        return st.session_state["sb_client"]
    missing = [k for k in ["SUPABASE_URL","SUPABASE_KEY"] if k not in st.secrets]
    if missing:
        st.error(f"Missing Streamlit secrets: {', '.join(missing)}\n\n"
                 "Go to Streamlit Cloud → your app → ⋮ → Settings → Secrets and add:\n\n"
                 "SUPABASE_URL = \"https://xxx.supabase.co\"\n"
                 "SUPABASE_KEY = \"eyJ...\"")
        st.stop()
    url = _clean_url(st.secrets["SUPABASE_URL"])
    key = st.secrets["SUPABASE_KEY"].strip()
    if "supabase.co" not in url:
        st.error(f"SUPABASE_URL looks wrong: `{url}`\n"
                 "It should look like: `https://abcdefgh.supabase.co`")
        st.stop()
    try:
        client = create_client(url, key)
        st.session_state["sb_client"] = client
        return client
    except Exception as e:
        st.error(f"Cannot connect to Supabase: {e}")
        st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_user():
    return st.session_state.get("sb_user", None)

def _store_session(session):
    st.session_state["sb_user"]          = session.user
    st.session_state["sb_access_token"]  = session.access_token
    st.session_state["sb_refresh_token"] = session.refresh_token

def _clear_session():
    for k in ["sb_user","sb_access_token","sb_refresh_token",
              "sb_client","data_loaded","chat_history"]:
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

# ─────────────────────────────────────────────────────────────────────────────
# DATA SYNC
# ─────────────────────────────────────────────────────────────────────────────
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
                if "saved" not in g:
                    st.session_state.goals[i]["saved"] = 0.0
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

# ─────────────────────────────────────────────────────────────────────────────
# ERROR MESSAGES
# ─────────────────────────────────────────────────────────────────────────────
def _friendly_error(raw: str) -> str:
    r = raw.lower()
    if "invalid path" in r or "invalid url" in r:
        return "Config error: SUPABASE_URL is wrong. Must be: https://abcdef.supabase.co"
    if "email not confirmed" in r:
        return "Please confirm your email — check your inbox for a link from Supabase."
    if "invalid login" in r or "invalid_credentials" in r or "invalid email or password" in r:
        return "Incorrect email or password. Try again or use Forgot Password."
    if "already registered" in r or "user already registered" in r:
        return "This email is already registered. Switch to Sign in."
    if "password should be" in r or "password must be" in r:
        return "Password must be at least 6 characters."
    if "rate limit" in r or "too many" in r:
        return "Too many attempts. Please wait a minute and try again."
    return raw[:200]

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE  — Sign in · Create account · Forgot password
# ─────────────────────────────────────────────────────────────────────────────
def login_page(sb: Client, T: dict):
    A  = T.get("accent",  "#059669")
    SU = T.get("surface", "#FFFFFF")
    S2 = T.get("surface2","#F3F4F6")
    BO = T.get("border",  "#E5E7EB")
    TX = T.get("text",    "#111827")
    MU = T.get("muted",   "#6B7280")
    BG = T.get("bg",      "#F9FAFB")
    RD = "#DC2626"
    GR = "#16A34A"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,.stApp{{background:{BG}!important;font-family:Inter,sans-serif;}}
.lw{{
  max-width:400px;margin:3rem auto 0;
  background:{SU};border:1px solid {BO};
  border-radius:20px;padding:2.4rem 2rem 2rem;
  box-shadow:0 4px 32px rgba(0,0,0,0.07);
}}
.brand{{text-align:center;margin-bottom:1.6rem;}}
.brand-name{{font-size:1.65rem;font-weight:800;color:{TX};letter-spacing:-.02em;}}
.brand-sub{{font-size:.75rem;color:{MU};margin-top:2px;}}
.tab-row{{display:flex;border-bottom:2px solid {BO};margin-bottom:1.4rem;}}
.tab-btn{{flex:1;text-align:center;padding:.55rem;font-size:.82rem;font-weight:500;
  color:{MU};cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;
  transition:all .15s;}}
.tab-btn.active{{color:{A};border-bottom-color:{A};font-weight:600;}}
.msg-err{{background:#FEF2F2;border:1px solid #FECACA;border-radius:9px;
  padding:.65rem .9rem;color:{RD};font-size:.79rem;margin:.5rem 0;line-height:1.6;}}
.msg-ok {{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:9px;
  padding:.65rem .9rem;color:{GR};font-size:.79rem;margin:.5rem 0;line-height:1.6;}}
.msg-info{{background:#EFF6FF;border:1px solid #BFDBFE;border-radius:9px;
  padding:.65rem .9rem;color:#1D4ED8;font-size:.79rem;margin:.5rem 0;line-height:1.6;}}
.foot{{text-align:center;font-size:.65rem;color:{MU};margin-top:1.3rem;line-height:1.6;}}
.forgot-link{{text-align:right;font-size:.72rem;color:{A};cursor:pointer;margin:-.1rem 0 .6rem;}}
/* Input overrides */
label,[data-testid="stWidgetLabel"] *{{color:{TX}!important;font-size:.8rem!important;font-weight:500!important;}}
[data-testid="stTextInput"] input{{
  background:{S2}!important;border:1.5px solid {BO}!important;
  border-radius:9px!important;color:{TX}!important;font-size:.86rem!important;
  padding:.45rem .7rem!important;
}}
[data-testid="stTextInput"] input:focus{{border-color:{A}!important;outline:none!important;
  box-shadow:0 0 0 3px rgba(5,150,105,0.12)!important;}}
/* Button overrides */
.stButton>button{{
  background:{A}!important;border:none!important;border-radius:9px!important;
  color:#fff!important;font-weight:700!important;font-size:.86rem!important;
  padding:.5rem 1rem!important;width:100%;transition:filter .15s;
}}
.stButton>button:hover{{filter:brightness(1.07)!important;}}
.stRadio [role="radiogroup"]{{display:none!important;}}
</style>""", unsafe_allow_html=True)

    # ── Screen state ─────────────────────────────────────────────────────────
    if "auth_screen" not in st.session_state:
        st.session_state["auth_screen"] = "signin"   # signin | signup | forgot | reset_sent

    _, col, _ = st.columns([1, 2.2, 1])
    with col:
        st.markdown("<div class='lw'>", unsafe_allow_html=True)

        # Brand
        st.markdown(f"<div class='brand'>"
                    f"<div class='brand-name'>Seralung Finance</div>"
                    f"<div class='brand-sub'>Track. Spend. Build.</div>"
                    f"</div>", unsafe_allow_html=True)

        screen = st.session_state["auth_screen"]

        # ── Tab row (Sign in / Create account) ───────────────────────────────
        if screen in ("signin","signup"):
            si = "active" if screen=="signin" else ""
            su = "active" if screen=="signup" else ""
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Sign in",     use_container_width=True, key="tab_si",
                             type="primary" if screen=="signin" else "secondary"):
                    st.session_state["auth_screen"]="signin"; st.rerun()
            with c2:
                if st.button("Create account", use_container_width=True, key="tab_su",
                             type="primary" if screen=="signup" else "secondary"):
                    st.session_state["auth_screen"]="signup"; st.rerun()
            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

        # ── SIGN IN ───────────────────────────────────────────────────────────
        if screen == "signin":
            email    = st.text_input("Email address", placeholder="you@example.com", key="si_email")
            password = st.text_input("Password",      placeholder="Your password",    key="si_pass",  type="password")

            # Forgot password link
            if st.button("Forgot password?", key="goto_forgot",
                         help="Send a password reset link to your email",
                         use_container_width=False):
                st.session_state["auth_screen"] = "forgot"
                st.rerun()

            if st.button("Sign in", use_container_width=True, key="do_signin"):
                if not email or "@" not in email:
                    st.markdown("<div class='msg-err'>Enter a valid email address.</div>", unsafe_allow_html=True)
                elif not password:
                    st.markdown("<div class='msg-err'>Enter your password.</div>", unsafe_allow_html=True)
                else:
                    with st.spinner("Signing in..."):
                        try:
                            res = sb.auth.sign_in_with_password({
                                "email": email.strip(), "password": password
                            })
                            if res.session:
                                _store_session(res.session); st.rerun()
                            else:
                                st.markdown("<div class='msg-err'>Sign-in failed. Check your credentials.</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.markdown(f"<div class='msg-err'>{_friendly_error(str(e))}</div>", unsafe_allow_html=True)

        # ── CREATE ACCOUNT ────────────────────────────────────────────────────
        elif screen == "signup":
            email    = st.text_input("Email address",    placeholder="you@example.com",      key="su_email")
            password = st.text_input("Password",         placeholder="At least 6 characters", key="su_pass",   type="password")
            confirm  = st.text_input("Confirm password", placeholder="Repeat password",       key="su_confirm", type="password")

            if st.button("Create account", use_container_width=True, key="do_signup"):
                err = None
                if not email or "@" not in email: err = "Enter a valid email address."
                elif len(password) < 6:           err = "Password must be at least 6 characters."
                elif password != confirm:          err = "Passwords do not match."
                if err:
                    st.markdown(f"<div class='msg-err'>{err}</div>", unsafe_allow_html=True)
                else:
                    with st.spinner("Creating account..."):
                        try:
                            res = sb.auth.sign_up({
                                "email": email.strip(), "password": password
                            })
                            if res.user and res.session:
                                _store_session(res.session); st.rerun()
                            elif res.user:
                                st.markdown("<div class='msg-ok'>Account created! Check your email "
                                            "to confirm, then sign in.</div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div class='msg-err'>Sign-up failed. Try a different email.</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.markdown(f"<div class='msg-err'>{_friendly_error(str(e))}</div>", unsafe_allow_html=True)

        # ── FORGOT PASSWORD ───────────────────────────────────────────────────
        elif screen == "forgot":
            st.markdown(f"<div style='font-size:.9rem;font-weight:600;color:{TX};margin-bottom:.3rem;'>Reset your password</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:.78rem;color:{MU};margin-bottom:.9rem;line-height:1.5;'>"
                        "Enter the email you signed up with. We'll send you a link to reset your password.</div>",
                        unsafe_allow_html=True)
            reset_email = st.text_input("Your email address", placeholder="you@example.com", key="reset_email")

            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("Send reset link", use_container_width=True, key="do_reset"):
                    if not reset_email or "@" not in reset_email:
                        st.markdown("<div class='msg-err'>Enter a valid email address.</div>", unsafe_allow_html=True)
                    else:
                        with st.spinner("Sending..."):
                            try:
                                sb.auth.reset_password_email(reset_email.strip())
                                st.session_state["auth_screen"] = "reset_sent"
                                st.session_state["reset_email_sent"] = reset_email.strip()
                                st.rerun()
                            except Exception as e:
                                st.markdown(f"<div class='msg-err'>{_friendly_error(str(e))}</div>", unsafe_allow_html=True)
            with rc2:
                if st.button("Back to sign in", use_container_width=True, key="back_from_forgot"):
                    st.session_state["auth_screen"] = "signin"; st.rerun()

        # ── RESET EMAIL SENT ──────────────────────────────────────────────────
        elif screen == "reset_sent":
            sent_to = st.session_state.get("reset_email_sent","your email")
            st.markdown(f"<div class='msg-ok'>"
                        f"Password reset email sent to <b>{sent_to}</b>.<br><br>"
                        f"Check your inbox and click the link in the email. "
                        f"Once you've reset your password, come back here and sign in."
                        f"</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='msg-info'>"
                        f"Can't find the email? Check your Spam folder, or wait a minute and try again."
                        f"</div>", unsafe_allow_html=True)
            if st.button("Back to sign in", use_container_width=True, key="back_to_signin"):
                st.session_state["auth_screen"] = "signin"
                st.session_state.pop("reset_email_sent", None)
                st.rerun()

        # Footer
        st.markdown(f"<div class='foot'>Your data is encrypted and stored securely in Supabase.<br>"
                    f"We never share or sell your financial data.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
