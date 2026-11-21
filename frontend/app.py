import streamlit as st
import requests
import json
import os
import importlib
import streamlit.components.v1 as components

# Try to import modules directly for local fallback if backend is offline
try:
    import modules.quality
    import modules.plagiarism
    import modules.ai_detection
    import modules.ast
    from modules.quality import compute_quality_metrics
    from modules.plagiarism import detect_plagiarism
    from modules.ai_detection import check_ai_generated
    from modules.ast import parse_code_to_ast
    LOCAL_FALLBACK = True
except ImportError:
    LOCAL_FALLBACK = False

# API Config
API_URL = "http://127.0.0.1:8000"

try:
    from backend.config import PLAGIARISM_FLAG_THRESHOLD
except ImportError:
    PLAGIARISM_FLAG_THRESHOLD = 0.75

st.set_page_config(
    page_title="CodeGuard - Multimodal Code Analysis & RBAC Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize Session State
if "token" not in st.session_state:
    st.session_state.token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "active_assignment_id" not in st.session_state:
    st.session_state.active_assignment_id = 1
if "nav_view" not in st.session_state:
    st.session_state.nav_view = "Dashboard Home"

def get_auth_headers():
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def login_user(username, password):
    try:
        res = requests.post(f"{API_URL}/login", data={"username": username, "password": password}, timeout=3)
        if res.status_code == 200:
            data = res.json()
            st.session_state.token = data.get("access_token")
            st.session_state.role = data.get("role")
            st.session_state.username = data.get("username")
            st.success(f"Successfully logged in as {username} ({data.get('role')})")
            st.rerun()
        else:
            st.error(f"Login failed: {res.json().get('detail', 'Invalid credentials')}")
    except requests.exceptions.RequestException as e:
        st.error(f"Cannot connect to backend API: {e}")

def logout_user():
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None
    st.rerun()

def fetch_available_assignments():
    try:
        res = requests.get(f"{API_URL}/assignments", headers=get_auth_headers(), timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return [{"assignment_id": 1, "title": "Factorial Checker", "course": "CS101"}]

def fetch_available_submissions():
    if not st.session_state.token:
        return []
    try:
        if st.session_state.role == "Student":
            res = requests.get(f"{API_URL}/my-submissions", headers=get_auth_headers(), timeout=3)
        else:
            res = requests.get(f"{API_URL}/faculty/submissions", headers=get_auth_headers(), timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []

def call_api(endpoint: str, payload: dict) -> dict:
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=payload, headers=get_auth_headers(), timeout=3)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    
    if LOCAL_FALLBACK:
        if endpoint == "/api/quality":
            m_res = compute_quality_metrics(payload["code"])
            if m_res.get("success") == False:
                return {"success": False, "error": m_res.get("error")}
            return {"success": True, "metrics": m_res}
        elif endpoint == "/api/plagiarism":
            return {"success": True, "report": detect_plagiarism(payload["code_a"], payload["code_b"])}
        elif endpoint == "/api/ai-detection":
            ai_res = check_ai_generated(payload["code"])
            if ai_res.get("success") == False:
                return {"success": False, "error": ai_res.get("error")}
            return {"success": True, "result": ai_res}
        elif endpoint == "/api/ast":
            ast_res = parse_code_to_ast(payload["code"])
            if ast_res.get("success") == False:
                return {"success": False, "error": ast_res.get("error")}
            return {"success": True, "ast": ast_res}
    
    return {"success": False, "error": "Backend API offline and local imports failed."}

def fetch_submission_raw_code(sub_id: int) -> str:
    """Fetch raw code of a submission via API or direct fallback."""
    if not sub_id:
        return ""
    try:
        res = requests.get(f"{API_URL}/submission/{sub_id}", headers=get_auth_headers(), timeout=3)
        if res.status_code == 200:
            return res.json().get("raw_code", "")
    except Exception:
        pass
    try:
        from backend.database.connection import SessionLocal
        from backend.database import crud
        db = SessionLocal()
        sub = crud.get_submission_by_id(db, sub_id)
        raw = sub.raw_code if sub else ""
        db.close()
        return raw
    except Exception:
        pass
    return ""

def get_normalized_code(code: str) -> str:
    """Return AST-normalized code with variable renaming placeholders."""
    if not code or not code.strip():
        return ""
    try:
        from modules.ast import normalize_code
        return normalize_code(code, language="python")
    except Exception:
        pass
    try:
        res = call_api("/api/ast", {"code": code})
        if res.get("success"):
            return res.get("ast", {}).get("normalized_code", "")
    except Exception:
        pass
    return ""


backend_online = False
try:
    res = requests.get(API_URL, timeout=1)
    if res.status_code == 200:
        backend_online = True
except requests.exceptions.RequestException:
    backend_online = False

# Styling Injection - Pure White & Light Theme with Dark Slate Text Contrast
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A !important;
        background-color: #FFFFFF !important;
    }

    /* Pure White / Light Slate App Background */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], header[data-testid="stHeader"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Sidebar styling - Light Slate background */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }

    /* Dialog / Modal Popup Background - Crisp Pure White Box */
    [data-testid="stDialog"], div[role="dialog"], div[data-baseweb="modal"], div[data-baseweb="modal-dialog"], div[data-baseweb="modal-content"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
    }

    /* Code Blocks - Crisp light slate background with dark text */
    code, pre, .stCodeBlock, div[data-testid="stCodeBlock"] {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    .stCodeBlock code span, code span {
        color: #0F172A !important;
    }

    /* Universal Dark Navy Text on White Backgrounds */
    h1, h2, h3, h4, h5, h6, .stHeading, [data-testid="stHeader"] {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    
    p, span, label, li, td, th, a {
        color: #0F172A !important;
    }

    /* Captions & Subtitles */
    div[data-testid="stCaptionContainer"], .stCaption, caption, small {
        color: #475569 !important;
    }

    /* Metric Cards - White background with Dark text */
    [data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        padding: 12px 16px !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }

    /* Input Labels, Selectboxes, Radio Buttons, Checkboxes & Toggles */
    [data-testid="stWidgetLabel"], label[data-testid="stWidgetLabel"] > div, label p {
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    
    /* Radio & Checkbox Text */
    div[role="radiogroup"] label span, div[data-testid="stCheckbox"] label span {
        color: #0F172A !important;
    }

    /* Selectbox dropdown container & menu items */
    div[data-baseweb="select"] > div, div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    li[role="option"] {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
    }
    li[role="option"]:hover {
        background-color: #F1F5F9 !important;
    }

    /* Tab Titles */
    button[data-baseweb="tab"] div {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    button[aria-selected="true"][data-baseweb="tab"] div {
        color: #2563EB !important;
        font-weight: 700 !important;
    }

    /* Expanders & Accordions - White Box with Dark Text */
    [data-testid="stExpander"] details summary p {
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }

    /* Form Inputs & Text Areas - White Input Boxes with Dark Text */
    .stTextInput input, .stTextArea textarea, select, div[data-baseweb="base-input"], div[data-baseweb="input"] {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
    }

    /* Dataframe & Table text contrast - White Box Table */
    [data-testid="stTable"], [data-testid="stDataFrame"], div[data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }

    /* Main Title */
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.6rem;
        font-weight: 700;
        color: #0F172A !important;
        letter-spacing: -0.5px;
        margin-bottom: 0.1rem;
    }
    
    .subtitle {
        font-size: 1.05rem;
        color: #475569 !important;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    
    /* White Container Cards with Dark Text */
    .card {
        background-color: #FFFFFF !important;
        border-radius: 10px;
        padding: 1.2rem;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        color: #0F172A !important;
    }
    
    .badge {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 50px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    
    .badge-clean {
        background-color: #ECFDF5 !important;
        color: #047857 !important;
        border: 1px solid #A7F3D0 !important;
    }
    .badge-review {
        background-color: #FFFBEB !important;
        color: #B45309 !important;
        border: 1px solid #FDE68A !important;
    }
    .badge-flagged {
        background-color: #FEF2F2 !important;
        color: #B91C1C !important;
        border: 1px solid #FECACA !important;
    }
    
    .user-pill {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px;
        padding: 0.7rem;
        margin-bottom: 1rem;
        color: #0F172A !important;
    }

    /* Light Secondary Buttons with Crisp Dark Text */
    div[data-testid="column"] button, .stButton button {
        width: 100% !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        margin: 0 !important;
        border: 1px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease-in-out !important;
    }
    div[data-testid="column"] button:hover, .stButton button:hover {
        background-color: #F1F5F9 !important;
        border-color: #2563EB !important;
        color: #1D4ED8 !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.15) !important;
    }
    /* Primary Action Buttons */
    button[kind="primary"], .stButton button[data-testid="stBaseButton-primary"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #1D4ED8 !important;
    }
    button[kind="primary"]:hover, .stButton button[data-testid="stBaseButton-primary"]:hover {
        background-color: #1D4ED8 !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🛡️ **CodeGuard**")
    st.caption("Multimodal Plagiarism & Code Quality Portal")
    
    if backend_online:
        st.markdown('<span style="color:#00C864; font-weight:600;">● Backend Online</span>', unsafe_allow_html=True)
    elif LOCAL_FALLBACK:
        st.markdown('<span style="color:#FFAA00; font-weight:600;">● Local Fallback Mode</span>', unsafe_allow_html=True)
    else:
        st.error("Backend offline")
        
    st.markdown("---")

    if st.session_state.token:
        st.markdown(f"""
        <div class="user-pill">
            <div style="font-size:0.75rem; color:#64748B; font-weight:600;">CURRENT USER</div>
            <div style="font-size:1rem; font-weight:700; color:#0F172A;">👤 {st.session_state.username}</div>
            <div style="font-size:0.8rem; color:#475569;">Role: <b>{st.session_state.role}</b></div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            logout_user()
    else:
        st.markdown("### 🔐 Login")
        with st.form("login_form"):
            uname = st.text_input("Username", value="")
            pwd = st.text_input("Password", type="password", value="")
            if st.form_submit_button("Sign In", use_container_width=True):
                login_user(uname, pwd)
                
        st.markdown("#### ⚡ Quick Logins")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👨‍🎓 Student", key="demo_stud", use_container_width=True):
                login_user("student", "stud123")
            if st.button("🏛️ HOD", key="demo_hod", use_container_width=True):
                login_user("hod", "hod123")
        with c2:
            if st.button("👨‍🏫 Professor", key="demo_prof", use_container_width=True):
                login_user("professor", "prof123")
            if st.button("⚡ Admin", key="demo_admin", use_container_width=True):
                login_user("admin", "admin123")

    st.markdown("---")
    
    # Navigation options
    if st.session_state.role == "Student":
        nav_options = ["Upload Submission", "My Submissions"]
    elif st.session_state.role == "Professor":
        nav_options = ["Review Queue", "Plagiarism Report", "AI Detection Report", "Bulk Upload", "Standalone Tools"]
    elif st.session_state.role == "HOD":
        nav_options = ["Department Analytics", "Plagiarism Report", "AI Detection Report", "Review Queue", "Standalone Tools"]
    elif st.session_state.role == "Admin":
        nav_options = ["User & Section Management", "Department Analytics", "Plagiarism Report", "AI Detection Report", "Bulk Upload", "Review Queue", "Standalone Tools"]
    else:
        nav_options = ["Dashboard Home", "Standalone Tools"]
    
    if "pending_nav_target" in st.session_state:
        target = st.session_state.pop("pending_nav_target")
        if target in nav_options:
            st.session_state["portal_nav"] = target

    if "portal_nav" in st.session_state and st.session_state["portal_nav"] not in nav_options:
        st.session_state["portal_nav"] = nav_options[0]

    navigation = st.radio("Portal Navigation", nav_options, key="portal_nav")
    st.caption("CodeGuard v1.0. RBAC Active.")

st.markdown('<div class="main-title">CodeGuard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multimodal Code Quality, Plagiarism, & AI Source Audit System</div>', unsafe_allow_html=True)

# ---------------- HELPER: UPDATE STANDALONE CODE KEYS ----------------
def update_standalone_code_keys(code_str):
    """
    Explicitly updates session state keys for all Standalone Tool text area widgets
    so Streamlit re-renders the new code in the text boxes immediately.
    """
    st.session_state["standalone_code"] = code_str
    st.session_state["q_tool_code"] = code_str
    st.session_state["plag_tool_a"] = code_str
    st.session_state["ai_tool_code"] = code_str
    st.session_state["ast_tool_code"] = code_str
    st.session_state["standalone_quality_res"] = None
    st.session_state["standalone_plag_res"] = None
    st.session_state["standalone_ai_res"] = None
    st.session_state["standalone_ast_res"] = None

# ---------------- HELPER: SEARCH & FETCH SUBMISSION ----------------
def search_and_fetch_submission(query):
    """
    Given a search string (submission ID e.g. '1' or '#1', or student username e.g. 'hod'):
    Returns a list of submission detail dicts matching the search query.
    """
    query = str(query).strip().lstrip("#")
    if not query:
        return []

    # 1. Check if query is numeric Submission ID
    if query.isdigit():
        sub_id = int(query)
        try:
            res = requests.get(f"{API_URL}/submission/{sub_id}", headers=get_auth_headers(), timeout=3)
            if res.status_code == 200:
                data = res.json()
                data["submission_id"] = sub_id
                return [data]
        except Exception:
            pass

    # 2. Query is a student username or keyword -> Search in faculty submissions list
    try:
        res = requests.get(f"{API_URL}/faculty/submissions", headers=get_auth_headers(), timeout=3)
        if res.status_code == 200:
            subs = res.json()
            matches = [s for s in subs if query.lower() in str(s.get("student_username", "")).lower() or query.lower() in str(s.get("file_name", "")).lower()]
            
            detailed_results = []
            for s in matches[:5]:
                try:
                    d_res = requests.get(f"{API_URL}/submission/{s['submission_id']}", headers=get_auth_headers(), timeout=3)
                    if d_res.status_code == 200:
                        d_data = d_res.json()
                        d_data["submission_id"] = s["submission_id"]
                        detailed_results.append(d_data)
                except Exception:
                    pass
            return detailed_results
    except Exception:
        pass

    return []

# ---------------- HELPER: RENDER ASSIGNMENT AI DETECTION SECTION ----------------
def render_ai_detection_section():
    """
    Renders a dedicated AI Detection Audit section:
    - Assessment/Assignment selector dropdown.
    - Metrics summary cards.
    - Interactive table with AI Detection Score column, clickable Submission IDs (opens popup dialog with code permission), and even Student buttons (filters student's submissions).
    """
    st.markdown("---")
    st.markdown("### 🤖 Assignment AI Detection Audit Report")
    st.caption("Audit AI generation probability for every student submission in the selected assignment.")
    
    # Trigger popup dialog if requested
    if st.session_state.get("trigger_popup_sub_id"):
        popup_id = st.session_state["trigger_popup_sub_id"]
        st.session_state["trigger_popup_sub_id"] = None
        show_submission_popup(popup_id)

    assignments = fetch_available_assignments()
    if not assignments:
        st.info("No assignments available.")
        return

    asgn_options = ["-- Select an Assignment --"] + [f"{a['title']} ({a['course']}) [ID: #{a['assignment_id']}]" for a in assignments]
    asgn_map = {f"{a['title']} ({a['course']}) [ID: #{a['assignment_id']}]": a["assignment_id"] for a in assignments}

    sel_ai_asgn_label = st.selectbox("Select Assessment for AI Detection Audit", asgn_options, key="ai_report_asgn_sel")

    if sel_ai_asgn_label == "-- Select an Assignment --":
        st.info("📌 Please select an assignment from the dropdown above to load its isolated AI detection report.")
    else:
        sel_ai_asgn_id = asgn_map[sel_ai_asgn_label]
        try:
            res = requests.get(f"{API_URL}/assignments/{sel_ai_asgn_id}/ai-report", headers=get_auth_headers(), timeout=5)
            if res.status_code == 200:
                ai_rep = res.json()
                
                st.info("ℹ️ **Faculty Decision-Support Notice:** AI Detection probability scores and review tiers prioritize submissions for manual faculty inspection. They do NOT constitute automated verdicts or definitive proof of academic dishonesty.")

                # Metrics Overview
                t_used = ai_rep.get("threshold_used", 0.54)
                h_pct = f"≥ {int(round(t_used * 100))}%"
                m_pct = f"{int(round(0.5 * t_used * 100))}-{int(round(t_used * 100))}%"
                l_pct = f"< {int(round(0.5 * t_used * 100))}%"

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Submissions", ai_rep.get("total_submissions", 0))
                m2.metric(f"Flagged for Review ({h_pct})", ai_rep.get("high_ai_count", 0))
                m3.metric(f"Optional Review ({m_pct})", ai_rep.get("moderate_ai_count", 0))
                m4.metric(f"Routine Structure ({l_pct})", ai_rep.get("low_ai_count", 0))

                h_col1, h_col2 = st.columns([3, 1])
                with h_col1:
                    st.markdown(f"#### 📊 Submissions AI Pattern Overlap Audit Table for `{ai_rep.get('assignment_title')}`")
                with h_col2:
                    if st.button("⚡ Bulk Approve Clean", key="bulk_approve_btn", type="primary", use_container_width=True, help="Preview clean submissions eligible for bulk approval"):
                        st.session_state["show_bulk_approve_modal"] = True

                if st.session_state.get("bulk_approve_success_msg"):
                    st.success(st.session_state.pop("bulk_approve_success_msg"))

                if st.session_state.get("show_bulk_approve_modal"):
                    show_bulk_approve_dialog(sel_ai_asgn_id, ai_rep.get('assignment_title', 'Assignment'))
                subs = ai_rep.get("submissions", [])
                
                if not subs:
                    st.info("No submissions found for this assignment.")
                else:
                    # Filter by Student Banner if active
                    active_student = st.session_state.get("filter_student_username")
                    if active_student:
                        f_col1, f_col2 = st.columns([4, 1])
                        with f_col1:
                            st.info(f"👤 **Filtered View: Showing All Submissions for Student** `{active_student}`")
                        with f_col2:
                            if st.button("✖ Clear Filter", key="ai_rep_clear_stud_filter", use_container_width=True):
                                st.session_state["filter_student_username"] = None
                                st.rerun()

                        display_subs = [s for s in subs if s.get("student_username") == active_student]
                        if not display_subs:
                            st.warning(f"No submissions found for student '{active_student}'.")
                            display_subs = subs
                    else:
                        display_subs = subs

                    # Custom Interactive Table with AI Detection Score Column
                    header_cols = st.columns([1.2, 1.8, 1.8, 1.8, 2.2, 1.4, 2.0])
                    with header_cols[0]: st.markdown("**ID** *(Click)*")
                    with header_cols[1]: st.markdown("**Student** *(Click)*")
                    with header_cols[2]: st.markdown("**Assignment**")
                    with header_cols[3]: st.markdown("**File Name**")
                    with header_cols[4]: st.markdown("🤖 **AI Pattern Score**")
                    with header_cols[5]: st.markdown("**Status**")
                    with header_cols[6]: st.markdown("**Submitted At**")

                    st.markdown("<hr style='margin:4px 0 10px 0; opacity:0.2;'>", unsafe_allow_html=True)

                    selected_id = st.session_state.get("selected_sub_id")

                    for idx, s in enumerate(display_subs):
                        sub_id = s["submission_id"]
                        stud_name = s.get("student_username", "Unknown")
                        asgn = s.get("assignment", "N/A")
                        fname = s.get("file_name", "file.py")
                        status = s.get("status", "Uploaded")
                        submitted_at = str(s.get("submitted_at", ""))[:19].replace("T", " ")
                        ai_score = s.get("ai_score", 0.0)
                        ai_pct = s.get("ai_percentage", "0.0%")

                        is_active = (selected_id == sub_id)

                        # AI Score Badge & Color
                        t_used = ai_rep.get("threshold_used", 0.54)
                        if ai_score >= t_used:
                            ai_badge = f"🔴 **Flagged Review** ({ai_pct})"
                        elif ai_score >= 0.5 * t_used:
                            ai_badge = f"🟡 **Optional Review** ({ai_pct})"
                        else:
                            ai_badge = f"🟢 **Routine Code** ({ai_pct})"

                        row_cols = st.columns([1.2, 1.8, 1.8, 1.8, 2.2, 1.4, 2.0])

                        # 1. Submission ID (Triggers popup preview with code permission toggle)
                        with row_cols[0]:
                            btn_text = f"👉 #{sub_id}" if is_active else f"#{sub_id}"
                            btn_type = "primary" if is_active else "secondary"
                            if st.button(btn_text, key=f"ai_rep_sub_{sub_id}_{idx}", type=btn_type, help=f"Click to open pop-up preview for Submission #{sub_id}"):
                                st.session_state["selected_sub_id"] = sub_id
                                st.session_state["trigger_popup_sub_id"] = sub_id
                                st.rerun()

                        # 2. Student Name (Even, uniform shape button - Click to filter student submissions)
                        with row_cols[1]:
                            if st.button(f"👤 {stud_name}", key=f"ai_rep_stud_{stud_name}_{sub_id}_{idx}", help=f"Click to filter ALL submissions for student '{stud_name}'"):
                                st.session_state["filter_student_username"] = stud_name
                                st.session_state["selected_sub_id"] = sub_id
                                st.rerun()

                        # 3. Assignment
                        with row_cols[2]:
                            st.write(f"`{asgn}`")

                        # 4. File Name (Clickable button to inspect code snippet)
                        with row_cols[3]:
                            is_ocr_file = fname.split(".")[-1].lower() in ["png", "jpg", "jpeg", "bmp", "tiff", "webp"]
                            icon = "🔍 OCR" if is_ocr_file else "📄"
                            btn_lbl = f"{icon} {fname}"
                            if st.button(btn_lbl, key=f"ai_rep_fname_{sub_id}_{idx}", help=f"Click to inspect code snippet for {fname}" + (" (OCR Extracted — Verification Recommended)" if is_ocr_file else "")):
                                st.session_state["selected_sub_id"] = sub_id
                                st.session_state["trigger_popup_sub_id"] = sub_id
                                st.rerun()
                            if is_ocr_file:
                                st.caption("⚠️ OCR — Verify Code")

                        # 5. AI Detection Score (Highlighted)
                        with row_cols[4]:
                            st.markdown(ai_badge)

                        # 6. Status
                        with row_cols[5]:
                            st.caption(status)

                        # 7. Submitted At
                        with row_cols[6]:
                            st.caption(submitted_at)

                    st.markdown("<hr style='margin:10px 0 16px 0; opacity:0.2;'>", unsafe_allow_html=True)

                    # Render audit view for selected submission if available
                    if selected_id:
                        detail_res = requests.get(f"{API_URL}/submission/{selected_id}", headers=get_auth_headers(), timeout=3)
                        if detail_res.status_code == 200:
                            render_full_submission_audit(detail_res.json(), can_approve=True, sub_id=selected_id)
            else:
                st.error(f"Could not load AI report ({res.status_code}): {res.json().get('detail')}")
        except Exception as e:
            st.error(f"Error fetching AI report: {e}")

# ---------------- HELPER: BULK APPROVE CONFIRMATION DIALOG ----------------
@st.dialog("⚡ Confirm Bulk Approval")
def show_bulk_approve_dialog(asgn_id, asgn_title):
    st.markdown(f"### Bulk Approval Preview for `{asgn_title}`")
    try:
        prev_res = requests.get(f"{API_URL}/assignments/{asgn_id}/bulk-approve-preview", headers=get_auth_headers(), timeout=5)
        if prev_res.status_code == 200:
            p_data = prev_res.json()
            st.info("ℹ️ **Safety Policy:** Bulk approval only approves clean submissions. Submissions flagged for similarity or AI review are held for manual faculty inspection.")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Eligible Clean", p_data.get("eligible_count", 0))
            c2.metric("🔴 Flagged (Held)", p_data.get("flagged_count", 0))
            c3.metric("⚠️ Excluded / Failed", p_data.get("incomplete_count", 0))
            
            if p_data.get("out_of_scope_count", 0) > 0:
                st.caption(f"🔒 {p_data['out_of_scope_count']} submissions belong to other sections and are excluded from your section scope.")
                
            st.markdown("---")
            col_conf, col_canc = st.columns(2)
            with col_conf:
                if st.button("🚀 Confirm & Release Eligible", type="primary", use_container_width=True, key="dialog_confirm_approve"):
                    b_res = requests.post(f"{API_URL}/assignments/{asgn_id}/bulk-approve", headers=get_auth_headers(), timeout=5)
                    if b_res.status_code == 200:
                        st.session_state["bulk_approve_success_msg"] = b_res.json().get("message", "Reports approved successfully.")
                        st.session_state["show_bulk_approve_modal"] = False
                        st.rerun()
                    else:
                        st.error(f"Bulk approval failed: {b_res.json().get('detail')}")
            with col_canc:
                if st.button("✖ Cancel", use_container_width=True, key="dialog_cancel_approve"):
                    st.session_state["show_bulk_approve_modal"] = False
                    st.rerun()
        else:
            st.error(f"Could not load preview ({prev_res.status_code}): {prev_res.json().get('detail')}")
    except Exception as e:
        st.error(f"Failed to load approval preview: {e}")

# ---------------- HELPER: BADGES ----------------
def render_status_badge(score, threshold=PLAGIARISM_FLAG_THRESHOLD):
    if score >= threshold:
        return f'<span class="badge badge-flagged">🔴 FLAGGED ({score:.2f})</span>'
    elif score >= 0.4:
        return f'<span class="badge badge-review">🟡 REVIEW ({score:.2f})</span>'
    else:
        return f'<span class="badge badge-clean">🟢 CLEAN ({score:.2f})</span>'

# ---------------- HELPER: SUBMISSION POPUP DIALOG ----------------
@st.dialog("📄 Submission Inspection & File Preview", width="large")
def show_submission_popup(sub_id):
    """
    Pop-up dialog triggered when clicking on a Submission ID:
    - Displays file preview (PDF, Image PNG/JPG, Word DOCX, or Code).
    - Asks for hover / permission toggle to view extracted raw source code.
    """
    st.markdown(f"### Submission ID: `#{sub_id}`")
    
    try:
        res = requests.get(f"{API_URL}/submission/{sub_id}", headers=get_auth_headers(), timeout=4)
        if res.status_code == 200:
            data = res.json()
            meta = data.get("metadata", {})
            raw_code = data.get("raw_code", "")
            file_name = meta.get("file_name", "file.py")

            # Meta summary
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"**Student:** `{meta.get('student_username', 'Unknown')}`")
            m2.markdown(f"**Assignment:** `{meta.get('assignment', 'N/A')}`")
            m3.markdown(f"**Section:** `{meta.get('section', 'N/A')}`")

            st.markdown("---")

            # File View / Preview Section
            ext = os.path.splitext(file_name)[1].lower() if file_name else ""
            if ext in [".pdf", ".png", ".jpg", ".jpeg", ".docx"]:
                st.markdown("#### 📎 File Document / Image View")
                if ext in [".png", ".jpg", ".jpeg"]:
                    st.info(f"🖼️ **Image File Detected:** `{file_name}`")
                    st.markdown(f"""
                    <div style="background-color: #F8FAFC; border: 1px dashed #94A3B8; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 12px; color: #0F172A;">
                        <span style="font-size: 2.5rem;">🖼️</span><br>
                        <strong style="color: #0F172A;">{file_name}</strong><br>
                        <span style="color: #64748B; font-size: 0.85rem;">Extracted & Processed via OCR Tesseract Engine</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif ext == ".pdf":
                    st.info(f"📄 **PDF Document Detected:** `{file_name}`")
                    st.markdown(f"""
                    <div style="background-color: #F8FAFC; border: 1px dashed #10B981; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 12px; color: #0F172A;">
                        <span style="font-size: 2.5rem;">📄</span><br>
                        <strong style="color: #0F172A;">{file_name}</strong><br>
                        <span style="color: #64748B; font-size: 0.85rem;">Parsed & Extracted via PDFPlumber Reader</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif ext == ".docx":
                    st.info(f"📝 **Word Document Detected:** `{file_name}`")
                    st.markdown(f"""
                    <div style="background-color: #F8FAFC; border: 1px dashed #3B82F6; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 12px; color: #0F172A;">
                        <span style="font-size: 2.5rem;">📝</span><br>
                        <strong style="color: #0F172A;">{file_name}</strong><br>
                        <span style="color: #64748B; font-size: 0.85rem;">Parsed & Extracted via Python-Docx Reader</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(f"💻 **Python Source Code File:** `{file_name}`")

            # Code Visibility Permission Switch / Hover Toggle
            st.markdown("#### 💻 Extracted Source Code Inspection")
            code_perm = st.toggle("🔒 Grant Permission to View Extracted Source Code", value=False, key=f"dialog_code_perm_{sub_id}")

            if code_perm:
                st.success("🔓 Permission Granted — Displaying Source Code:")
                st.code(raw_code, language=meta.get("language", "python").lower())
            else:
                st.warning("🔒 Code Preview Locked. Toggle permission switch above to reveal raw code.")

            st.markdown("---")
            act_c1, act_c2, act_c3 = st.columns([2, 2, 1])
            with act_c1:
                if st.button("🔍 Open Full Audit Below", use_container_width=True, type="primary"):
                    st.session_state["selected_sub_id"] = sub_id
                    st.session_state["scroll_to_audit"] = True
                    st.rerun()
            with act_c2:
                if st.button("🧪 Send Code to Standalone Tools", key=f"send_standalone_pop_{sub_id}", use_container_width=True):
                    update_standalone_code_keys(raw_code)
                    st.session_state["scroll_to_standalone_tools"] = True
                    st.session_state["pending_nav_target"] = "Standalone Tools"
                    st.rerun()
            with act_c3:
                if st.button("❌ Close", use_container_width=True):
                    st.rerun()
        else:
            st.error(f"Could not load details for submission #{sub_id} ({res.status_code})")
    except Exception as e:
        st.error(f"Error connecting to backend API: {e}")

# ---------------- HELPER: INTERACTIVE SUBMISSIONS TABLE ----------------
def render_interactive_submissions_table(subs, key_prefix="audit", show_approve_release_boxes=True):
    """
    Renders an interactive submissions table:
    - Hover & Click on Submission ID button -> Triggers pop-up modal dialog for file view & code permission.
    - Hover & Click on Student Username button -> Filters view to all submissions by that student.
    - Approve & Release boxes for every row with 1-click execution.
    """
    if not subs:
        st.info("No submissions found.")
        return None

    # Trigger popup dialog if requested
    if st.session_state.get("trigger_popup_sub_id"):
        popup_id = st.session_state["trigger_popup_sub_id"]
        st.session_state["trigger_popup_sub_id"] = None
        show_submission_popup(popup_id)

    # Session state initialization
    valid_ids = [s["submission_id"] for s in subs]
    if "selected_sub_id" not in st.session_state or st.session_state["selected_sub_id"] not in valid_ids:
        st.session_state["selected_sub_id"] = valid_ids[0]

    if "filter_student_username" not in st.session_state:
        st.session_state["filter_student_username"] = None

    # Filter by Student Banner if active
    active_student = st.session_state.get("filter_student_username")
    if active_student:
        f_col1, f_col2 = st.columns([4, 1])
        with f_col1:
            st.info(f"👤 **Filtered View: Showing All Submissions for Student** `{active_student}`")
        with f_col2:
            if st.button("✖ Clear Filter", key=f"{key_prefix}_clear_stud_filter", use_container_width=True):
                st.session_state["filter_student_username"] = None
                st.rerun()

        filtered_subs = [s for s in subs if s.get("student_username") == active_student]
        if not filtered_subs:
            st.warning(f"No submissions found for student '{active_student}'.")
            filtered_subs = subs
    else:
        filtered_subs = subs

    # Search bar & Batch controls
    s_col1, s_col2 = st.columns([3, 1])
    with s_col1:
        search_q = st.text_input(
            "🔎 Quick Filter (Student, Assignment, File Name, or ID)",
            placeholder="Type student name, assignment title, or file name...",
            key=f"{key_prefix}_search_input"
        ).strip().lower()
    with s_col2:
        st.write("") # spacing alignment
        st.caption(f"Showing **{len(filtered_subs)}** of {len(subs)} submissions")

    if search_q:
        filtered_subs = [
            s for s in filtered_subs
            if search_q in str(s.get("student_username", "")).lower()
            or search_q in str(s.get("assignment", "")).lower()
            or search_q in str(s.get("file_name", "")).lower()
            or search_q in str(s.get("submission_id", "")).lower()
        ]

    # Batch Action Buttons (Faculty)
    if show_approve_release_boxes and filtered_subs:
        b_col1, b_col2, b_col3 = st.columns([1.5, 1.5, 3])
        with b_col1:
            if st.button("✅ Approve All Filtered", key=f"{key_prefix}_approve_all_btn", use_container_width=True):
                cnt = 0
                for sub_item in filtered_subs:
                    sid = sub_item["submission_id"]
                    try:
                        requests.post(f"{API_URL}/approve-report/{sid}?approve=true", headers=get_auth_headers(), timeout=3)
                        cnt += 1
                    except Exception:
                        pass
                st.toast(f"Approved {cnt} submissions!")
                st.rerun()
        with b_col2:
            if st.button("🚀 Release All Filtered", key=f"{key_prefix}_release_all_btn", use_container_width=True):
                cnt = 0
                for sub_item in filtered_subs:
                    sid = sub_item["submission_id"]
                    try:
                        requests.post(f"{API_URL}/release-report/{sid}?release=true", headers=get_auth_headers(), timeout=3)
                        cnt += 1
                    except Exception:
                        pass
                st.toast(f"Released {cnt} reports to students!")
                st.rerun()

    # Render Table Headers
    if show_approve_release_boxes:
        header_cols = st.columns([1.0, 1.4, 1.6, 0.5, 1.4, 1.3, 1.6, 1.1, 1.1])
        with header_cols[0]: st.markdown("**ID** *(Click)*")
        with header_cols[1]: st.markdown("**Student** *(Click)*")
        with header_cols[2]: st.markdown("**Assignment**")
        with header_cols[3]: st.markdown("**Sec**")
        with header_cols[4]: st.markdown("**File Name**")
        with header_cols[5]: st.markdown("**Status**")
        with header_cols[6]: st.markdown("**Submitted At**")
        with header_cols[7]: st.markdown("**Approve Box**")
        with header_cols[8]: st.markdown("**Release Box**")
    else:
        header_cols = st.columns([1.2, 1.8, 2.0, 0.7, 1.8, 1.5, 2.2])
        with header_cols[0]: st.markdown("**ID** *(Click)*")
        with header_cols[1]: st.markdown("**Student** *(Click)*")
        with header_cols[2]: st.markdown("**Assignment**")
        with header_cols[3]: st.markdown("**Sec**")
        with header_cols[4]: st.markdown("**File Name**")
        with header_cols[5]: st.markdown("**Status**")
        with header_cols[6]: st.markdown("**Submitted At**")

    st.markdown("<hr style='margin:4px 0 10px 0; opacity:0.2;'>", unsafe_allow_html=True)

    # Render Table Rows
    selected_id = st.session_state.get("selected_sub_id")

    for idx, s in enumerate(filtered_subs):
        sub_id = s["submission_id"]
        stud_name = s.get("student_username", "Unknown")
        asgn = s.get("assignment", s.get("assignment_id", "N/A"))
        sec = s.get("section", s.get("section_id", "N/A"))
        fname = s.get("file_name", "file.py")
        status = s.get("status", "Uploaded")
        submitted_at = str(s.get("submitted_at", ""))[:19].replace("T", " ")

        is_active = (selected_id == sub_id)
        is_approved = s.get("is_approved") or (status in ["Approved", "Released", "Visible to Student"])
        is_released = s.get("report_visible") or (status in ["Released", "Visible to Student"])

        # Status badge
        if status in ["Released", "Visible to Student"]:
            status_badge = "🚀 Released"
        elif status in ["Completed", "Approved"]:
            status_badge = "🟢 Approved"
        elif status == "Faculty Review":
            status_badge = "🔵 Faculty Review"
        else:
            status_badge = "🟡 Uploaded"

        if show_approve_release_boxes:
            row_cols = st.columns([1.0, 1.4, 1.6, 0.5, 1.4, 1.3, 1.6, 1.1, 1.1])
        else:
            row_cols = st.columns([1.2, 1.8, 2.0, 0.7, 1.8, 1.5, 2.2])

        # 1. Submission ID (Click to trigger pop-up preview modal & select)
        with row_cols[0]:
            btn_text = f"👉 #{sub_id}" if is_active else f"#{sub_id}"
            btn_type = "primary" if is_active else "secondary"
            if st.button(btn_text, key=f"{key_prefix}_sub_btn_{sub_id}_{idx}", type=btn_type, help=f"Click to open pop-up preview for Submission #{sub_id}"):
                st.session_state["selected_sub_id"] = sub_id
                st.session_state["trigger_popup_sub_id"] = sub_id
                st.rerun()

        # 2. Student Name (Even, uniform shape button - Click to view all student's submissions)
        with row_cols[1]:
            if st.button(f"👤 {stud_name}", key=f"{key_prefix}_stud_btn_{stud_name}_{sub_id}_{idx}", help=f"Click to filter ALL submissions for student '{stud_name}'"):
                st.session_state["filter_student_username"] = stud_name
                st.session_state["selected_sub_id"] = sub_id
                st.rerun()

        # 3. Assignment
        with row_cols[2]:
            st.write(f"`{asgn}`")

        # 4. Section
        with row_cols[3]:
            st.write(f"{sec}")

        # 5. File Name (Clickable button to inspect code snippet)
        with row_cols[4]:
            if st.button(f"📄 {fname}", key=f"{key_prefix}_fname_btn_{sub_id}_{idx}", help=f"Click to inspect code snippet for {fname}"):
                st.session_state["selected_sub_id"] = sub_id
                st.session_state["trigger_popup_sub_id"] = sub_id
                st.rerun()

        # 6. Status
        with row_cols[5]:
            st.caption(status_badge)

        # 7. Submitted At
        with row_cols[6]:
            st.caption(submitted_at)

        # 8 & 9. Approve & Release Action Boxes
        if show_approve_release_boxes:
            with row_cols[7]:
                chk_app = st.checkbox("Approve", value=bool(is_approved), key=f"{key_prefix}_chk_app_{sub_id}_{idx}", help=f"1-Click to approve report for Submission #{sub_id}")
                if chk_app != bool(is_approved):
                    try:
                        res = requests.post(f"{API_URL}/approve-report/{sub_id}?approve={str(chk_app).lower()}", headers=get_auth_headers(), timeout=3)
                        if res.status_code == 200:
                            st.toast(f"Submission #{sub_id} approval updated!")
                            st.rerun()
                        else:
                            st.error(f"Approval update failed: {res.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

            with row_cols[8]:
                chk_rel = st.checkbox("Release", value=bool(is_released), key=f"{key_prefix}_chk_rel_{sub_id}_{idx}", help=f"1-Click to release report to student for Submission #{sub_id}")
                if chk_rel != bool(is_released):
                    try:
                        res = requests.post(f"{API_URL}/release-report/{sub_id}?release={str(chk_rel).lower()}", headers=get_auth_headers(), timeout=3)
                        if res.status_code == 200:
                            st.toast(f"Submission #{sub_id} release status updated!")
                            st.rerun()
                        else:
                            st.error(f"Release update failed: {res.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("<hr style='margin:10px 0 16px 0; opacity:0.2;'>", unsafe_allow_html=True)
    return st.session_state.get("selected_sub_id")

# ---------------- HELPER: RENDER SUBMISSION DETAILS ----------------
def render_full_submission_audit(submission_detail, can_approve=False, sub_id=None):
    st.markdown('<div id="full-audit-anchor"></div>', unsafe_allow_html=True)
    if st.session_state.get("scroll_to_audit"):
        components.html(
            """
            <script>
                setTimeout(function() {
                    var el = window.parent.document.getElementById('full-audit-anchor');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 150);
            </script>
            """,
            height=0
        )
        st.session_state["scroll_to_audit"] = False

    metadata = submission_detail.get("metadata", {})
    raw_code = submission_detail.get("raw_code", "")
    report = submission_detail.get("report")
    
    if report is None:
        user_role = st.session_state.get("user", {}).get("role", "")
        if user_role == "Student":
            st.markdown("#### Submission Overview")
            st.json(metadata)
            st.markdown("#### Submitted Code")
            st.code(raw_code, language=metadata.get("language", "python"))
            st.warning("🔒 Report is pending review by faculty.")
            return
        else:
            report = {
                "plagiarism": {"max_similarity_score": 0.0, "total_comparisons": len(submission_detail.get("comparisons", [])), "flagged": False},
                "ai_score": 0.0,
                "threshold_used": 0.54,
                "report_visible": False
            }

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview & Approval",
        "📊 Code Quality",
        "🔍 Plagiarism & Similarity",
        "🤖 AI Detector",
        "🌳 AST Structure"
    ])
    
    with tab1:
        st.json(metadata)
        st.code(raw_code, language=metadata.get("language", "python"))
        
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if can_approve and not report.get("report_visible"):
                if st.button(f"✅ Approve & Release Report #{sub_id}", key=f"app_{sub_id}", use_container_width=True):
                    app_res = requests.post(f"{API_URL}/approve-report/{sub_id}", headers=get_auth_headers(), timeout=3)
                    if app_res.status_code == 200:
                        st.success("Report approved and released to student!")
                        st.rerun()
        with c_act2:
            if st.button("🧪 Transfer Code to Standalone Tools", key=f"send_standalone_tab1_{sub_id}", use_container_width=True):
                update_standalone_code_keys(raw_code)
                st.session_state["scroll_to_standalone_tools"] = True
                st.session_state["pending_nav_target"] = "Standalone Tools"
                st.rerun()

    with tab2:
        if raw_code:
            q_res = call_api("/api/quality", {"code": raw_code})
            if q_res.get("success"):
                m = q_res["metrics"]
                sec_score = int(m.get("security_score", 100))
                if sec_score >= 80:
                    sec_color = "#16A34A"  # green
                    sec_bg = "#DCFCE7"
                    sec_border = "#86EFAC"
                elif sec_score >= 50:
                    sec_color = "#D97706"  # amber
                    sec_bg = "#FEF3C7"
                    sec_border = "#FCD34D"
                else:
                    sec_color = "#DC2626"  # red
                    sec_bg = "#FEE2E2"
                    sec_border = "#FCA5A5"

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Lines of Code", m.get("lines_of_code", m.get("loc", 0)))
                with c2:
                    c_level = m.get("complexity_level", "Low")
                    c_val = m.get("cyclomatic_complexity", 1)
                    st.metric("Cyclomatic Complexity", f"{c_val} ({c_level})")
                with c3:
                    st.metric("Maintainability Index", f"{m.get('maintainability_index', 100):.1f}")
                with c4:
                    st.markdown(f"""
                        <div style="background:{sec_bg}; border:1px solid {sec_border}; border-radius:8px; padding:6px 10px; text-align:center;">
                            <div style="font-size:0.8rem; color:#475569; font-weight:600;">Security Score</div>
                            <div style="font-size:1.6rem; color:{sec_color}; font-weight:800; line-height:1.2;">{sec_score} / 100</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")
                vulns = list(m.get("vulnerabilities", []))
                vuln_count = m.get("vulnerabilities_count", len(vulns))

                if vuln_count > 0 and vulns:
                    st.markdown(f"##### 🛡️ Detected Security Vulnerabilities ({vuln_count})")
                    # Sort by severity: HIGH first, then MEDIUM, then LOW
                    sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
                    vulns.sort(key=lambda v: (sev_order.get(str(v.get("severity", "")).upper(), 3), v.get("line") or 0))

                    rows_html = []
                    for v in vulns:
                        sev = str(v.get("severity", "LOW")).upper()
                        if sev == "HIGH":
                            s_badge = '<span style="background:#FEE2E2; color:#B91C1C; border:1px solid #FCA5A5; padding:2px 8px; border-radius:4px; font-weight:700;">HIGH</span>'
                        elif sev == "MEDIUM":
                            s_badge = '<span style="background:#FEF3C7; color:#B45309; border:1px solid #FCD34D; padding:2px 8px; border-radius:4px; font-weight:700;">MEDIUM</span>'
                        else:
                            s_badge = '<span style="background:#F1F5F9; color:#475569; border:1px solid #CBD5E1; padding:2px 8px; border-radius:4px; font-weight:600;">LOW</span>'

                        cwe_val = v.get("cwe") or "Unknown"
                        cwe_link = v.get("cwe_link") or f"https://cwe.mitre.org/data/definitions/{cwe_val}.html"
                        cwe_cell = f'<a href="{cwe_link}" target="_blank" style="color:#2563EB; font-weight:600; text-decoration:underline;">CWE-{cwe_val}</a>'
                        line_no = v.get("line", "-")
                        desc = v.get("issue_text", "")

                        rows_html.append(f"""
                            <tr style="border-bottom:1px solid #E2E8F0;">
                                <td style="padding:8px 12px; font-family:monospace; font-weight:600; text-align:center;">{line_no}</td>
                                <td style="padding:8px 12px; text-align:center;">{s_badge}</td>
                                <td style="padding:8px 12px; text-align:center;">{cwe_cell}</td>
                                <td style="padding:8px 12px; color:#1E293B;">{desc}</td>
                            </tr>
                        """)

                    table_html = f"""
                        <table style="width:100%; border-collapse:collapse; margin-top:8px; font-size:0.9rem; background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; overflow:hidden;">
                            <thead>
                                <tr style="background:#F8FAFC; border-bottom:2px solid #CBD5E1; text-align:left; color:#475569;">
                                    <th style="padding:10px 12px; width:70px; text-align:center;">Line</th>
                                    <th style="padding:10px 12px; width:100px; text-align:center;">Severity</th>
                                    <th style="padding:10px 12px; width:110px; text-align:center;">CWE</th>
                                    <th style="padding:10px 12px;">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(rows_html)}
                            </tbody>
                        </table>
                    """
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.success("✅ No security issues detected")

                with st.expander("🔍 View Raw Quality Metrics Detail"):
                    st.json(m)

    with tab3:
        if report and report.get("plagiarism"):
            plag = report["plagiarism"]
            score = plag.get("similarity_score") if plag.get("similarity_score") is not None else plag.get("max_similarity_score", 0.0)
            badge_html = render_status_badge(score)
            st.markdown(f"### Status: {badge_html}", unsafe_allow_html=True)
            with st.expander("🔍 Detailed Plagiarism Metrics", expanded=True):
                comparisons = plag.get("comparisons") or submission_detail.get("comparisons", [])
                top_match = plag.get("top_match") or submission_detail.get("top_match") or (comparisons[0] if comparisons else None)
                
                if score >= 0.75 and top_match:
                    target_sub = top_match.get("target_sub_id") or top_match.get("other_submission_id")
                    target_user = top_match.get("student_username") or top_match.get("other_student_username", "Unknown")
                    fused = top_match.get("fused_score", 0.0)
                    sem = top_match.get("semantic_score", 0.0)
                    struct = top_match.get("structural_score", 0.0)
                    
                    st.error(f"🚨 **High Similarity Alert — Flagged Match with Sub #{target_sub} ({target_user})**")
                    st.markdown(
                        f"**Diagnostic Breakdown:** Fused Similarity Score is **{fused:.2f}** "
                        f"(Semantic Embedding Similarity: **{sem:.2f}**, AST Structural Similarity: **{struct:.2f}**)."
                    )
                    st.markdown("---")

                st.markdown("#### Pairwise Comparison Audit")
                if not comparisons:
                    st.info("ℹ️ No other student submissions exist yet for this assignment.")
                else:
                    h_cols = st.columns([1.8, 1.8, 1.2, 1.2, 1.2, 1.2])
                    with h_cols[0]: st.markdown("**Compared Student** *(Click)*")
                    with h_cols[1]: st.markdown("**File Name** *(Click)*")
                    with h_cols[2]: st.markdown("**Fused**")
                    with h_cols[3]: st.markdown("**Semantic**")
                    with h_cols[4]: st.markdown("**Structural**")
                    with h_cols[5]: st.markdown("**Flagged?**")

                    st.markdown("<hr style='margin:4px 0 8px 0; opacity:0.2;'>", unsafe_allow_html=True)

                    for idx, c in enumerate(comparisons):
                        target_sub = c.get("target_sub_id") or c.get("other_submission_id")
                        target_user = c.get("student_username") or c.get("other_student_username", "Unknown")
                        fname = c.get("file_name") or c.get("other_file_name", "file.py")
                        fused = c.get("fused_score", 0.0)
                        sem = c.get("semantic_score", 0.0)
                        struct = c.get("structural_score", 0.0)
                        is_flagged = c.get("flagged") or fused >= PLAGIARISM_FLAG_THRESHOLD
                        flag_tag = "🔴 Yes" if is_flagged else "🟢 No"

                        r_cols = st.columns([1.8, 1.8, 1.2, 1.2, 1.2, 1.2])
                        with r_cols[0]:
                            if st.button(f"👤 Sub #{target_sub} ({target_user})", key=f"tab3_sub_{target_sub}_{idx}_{sub_id}", help=f"Click to inspect Submission #{target_sub}"):
                                st.session_state["selected_sub_id"] = target_sub
                                st.session_state["trigger_popup_sub_id"] = target_sub
                                st.rerun()

                        with r_cols[1]:
                            if st.button(f"📄 {fname}", key=f"tab3_fname_{target_sub}_{idx}_{sub_id}", help=f"Click to view code snippet for {fname}"):
                                st.session_state["selected_sub_id"] = target_sub
                                st.session_state["trigger_popup_sub_id"] = target_sub
                                st.rerun()

                        with r_cols[2]:
                            st.write(f"`{fused:.2f}`")
                        with r_cols[3]:
                            st.write(f"`{sem:.2f}`")
                        with r_cols[4]:
                            st.write(f"`{struct:.2f}`")
                        with r_cols[5]:
                            st.caption(flag_tag)

                    st.markdown("---")
                    st.markdown("#### 🔬 Side-by-Side Normalised Code Comparison")

                    # Prepare selector for compared submissions
                    comp_choices = []
                    for c_idx, c in enumerate(comparisons):
                        t_sub = c.get("target_sub_id") or c.get("other_submission_id")
                        t_user = c.get("student_username") or c.get("other_student_username", "Unknown")
                        t_fname = c.get("file_name") or c.get("other_file_name", "file.py")
                        t_fused = c.get("fused_score", 0.0)
                        t_struct = c.get("structural_score", 0.0)
                        comp_choices.append({
                            "index": c_idx,
                            "label": f"Sub #{t_sub} ({t_user} - {t_fname}) — Fused: {t_fused:.4f} | Jaccard: {t_struct:.4f}",
                            "target_sub_id": t_sub,
                            "target_user": t_user,
                            "target_file": t_fname,
                            "comparison": c
                        })

                    chosen_comp = st.selectbox(
                        "Select a comparison pair to view normalised AST evidence side-by-side:",
                        options=comp_choices,
                        format_func=lambda opt: opt["label"],
                        key=f"norm_code_pair_select_{sub_id}"
                    )

                    if chosen_comp:
                        sel_target_id = chosen_comp["target_sub_id"]
                        sel_target_user = chosen_comp["target_user"]
                        sel_target_file = chosen_comp["target_file"]
                        sel_c = chosen_comp["comparison"]

                        c_fused = sel_c.get("fused_score", 0.0)
                        c_sem = sel_c.get("semantic_score", 0.0)
                        c_struct = sel_c.get("structural_score", 0.0)

                        curr_user = metadata.get("student_username", "Unknown")
                        curr_file = metadata.get("file_name", "file.py")

                        # Both submissions identified
                        st.markdown(f"**Inspection Pair:** `Sub #{sub_id} ({curr_user} - {curr_file})` ⟷ `Sub #{sel_target_id} ({sel_target_user} - {sel_target_file})`")

                        # All three scores
                        sc1, sc2, sc3 = st.columns(3)
                        sc1.metric("Fused Score", f"{c_fused:.4f}")
                        sc2.metric("Semantic (Embedding)", f"{c_sem:.4f}")
                        sc3.metric("Structural (AST Jaccard)", f"{c_struct:.4f}")

                        # Plain explanation line
                        st.markdown(f"_Both files are shown with every identifier replaced by a placeholder. Renaming variables cannot change this form, which is why structural similarity is **{c_struct:.4f}**._")

                        # Fetch normalized code for both
                        norm_curr = get_normalized_code(raw_code)
                        target_raw = fetch_submission_raw_code(sel_target_id)
                        norm_target = get_normalized_code(target_raw)

                        # Edge case messages
                        if not norm_curr and not norm_target:
                            st.warning("⚠️ Normalised code could not be extracted for either submission (syntax error or empty source).")
                        elif not norm_curr:
                            st.warning(f"⚠️ Normalised code could not be extracted for Submission #{sub_id} ({curr_user}) due to syntax error or empty source.")
                        elif not norm_target:
                            st.warning(f"⚠️ Normalised code could not be extracted for Submission #{sel_target_id} ({sel_target_user}) due to syntax error or empty source.")

                        # CSS to guarantee long files scroll cleanly within their column without page stretching
                        st.markdown("""
                            <style>
                            div[data-testid="stCodeBlock"] pre {
                                max-height: 480px !important;
                                overflow-y: auto !important;
                            }
                            </style>
                        """, unsafe_allow_html=True)

                        # Two columns side by side
                        col_norm_a, col_norm_b = st.columns(2)
                        with col_norm_a:
                            st.caption(f"**Sub #{sub_id}**: {curr_user} ({curr_file})")
                            if norm_curr:
                                st.code(norm_curr, language="python")
                            else:
                                st.caption("_Normalised code unavailable_")

                        with col_norm_b:
                            st.caption(f"**Sub #{sel_target_id}**: {sel_target_user} ({sel_target_file})")
                            if norm_target:
                                st.code(norm_target, language="python")
                            else:
                                st.caption("_Normalised code unavailable_")
        else:
            st.info("No pairwise plagiarism data available.")

    with tab4:
        ai_val = report.get("ai_score") if (report and report.get("ai_score") is not None) else None
        ai_heuristics = (
            (report.get("ai_heuristics") or report.get("heuristics"))
            if isinstance(report, dict) else {}
        )
        t_used = report.get("threshold_used", 0.54) if report else 0.54

        if (ai_val is None or not ai_heuristics) and raw_code:
            ai_call = call_api("/api/ai-detection", {"code": raw_code})
            if ai_call.get("success"):
                res_data = ai_call.get("result", {})
                if ai_val is None:
                    ai_val = res_data.get("ai_probability", 0.0)
                if not ai_heuristics:
                    ai_heuristics = res_data.get("heuristics", {})
                t_used = res_data.get("threshold_used", t_used)

        if ai_val is not None:
            badge_html = render_status_badge(ai_val)
            st.markdown(f"### AI Score: {badge_html}", unsafe_allow_html=True)
            with st.expander("🔍 Code Characteristics", expanded=True):
                # Token Entropy — real computed value, show as bar
                entropy_val = float(ai_heuristics.get("token_entropy_score", 0.0))
                col1, col2 = st.columns([3, 7])
                with col1:
                    st.markdown(f"**Token Entropy (normalised):** `{entropy_val:.2f}`")
                with col2:
                    st.progress(min(max(entropy_val, 0.0), 1.0))

                st.markdown("")

                # Presence indicators — binary flags, no bars, no numeric scores
                has_docstring = ai_heuristics.get("has_docstring",
                    ai_heuristics.get("docstring_formatting_score", 0.0) > 0.5)
                has_type_hints = ai_heuristics.get("has_type_hints",
                    ai_heuristics.get("type_hint_density_score", 0.0) > 0.5)
                has_comments = ai_heuristics.get("has_comments",
                    ai_heuristics.get("comment_density_score", 0.0) > 0.5)

                st.markdown(f"Docstrings: **{'present' if has_docstring else 'absent'}**")
                st.markdown(f"Type hints: **{'present' if has_type_hints else 'absent'}**")
                st.markdown(f"Comments: **{'present' if has_comments else 'absent'}**")

                st.markdown("---")
                if ai_val >= t_used:
                    ai_status_str = "FLAGGED FOR REVIEW (🔴)"
                elif ai_val >= 0.5 * t_used:
                    ai_status_str = "OPTIONAL REVIEW (🟡)"
                else:
                    ai_status_str = "ROUTINE STRUCTURE (🟢)"
                st.markdown(f"**→ Classifier Output (logistic regression):** `{ai_val:.2f}` ({ai_status_str})")
                st.caption("Score is the trained classifier's probability output. The indicators above are shown for transparency and are not inputs to this score.")
        else:
            st.info("No AI detection analysis available for this submission.")

    with tab5:
        if raw_code:
            ast_res = call_api("/api/ast", {"code": raw_code})
            if ast_res.get("success"):
                ast_info = ast_res.get("ast", {})
                st.metric("Total Syntax Nodes", ast_info.get("num_nodes", 0))
                with st.expander("🔍 Detailed AST JSON"):
                    st.json(ast_info)


def render_unassigned_submissions_section():
    """
    Renders the dedicated section for pending submissions awaiting manual student identification.
    Displays:
    - Original filename
    - Assignment
    - Reason identification failed
    - Eligible student dropdown
    - Confirmation button to assign the file
    """
    try:
        res = requests.get(f"{API_URL}/faculty/unassigned-submissions", headers=get_auth_headers(), timeout=4)
        if res.status_code != 200:
            return
        pending_subs = res.json()
    except Exception:
        return

    if not pending_subs:
        st.success("🎉 No submissions awaiting student identification! All submitted files have been matched to registered students.")
        return

    st.markdown(f"### ⚠️ Submissions Awaiting Student Identification ({len(pending_subs)})")
    st.caption("These files could not be automatically matched to a registered student during upload. Select the correct student and confirm assignment to run analysis.")

    try:
        stud_res = requests.get(f"{API_URL}/faculty/eligible-students", headers=get_auth_headers(), timeout=4)
        eligible_students = stud_res.json() if stud_res.status_code == 200 else []
    except Exception:
        eligible_students = []

    stud_options = ["-- Select Eligible Student --"]
    stud_map = {}
    for s in eligible_students:
        reg = s.get("registration_number") or "No Reg #"
        label = f"🎓 {s.get('username')} [{reg}] - {s.get('email')}"
        stud_options.append(label)
        stud_map[label] = s.get("id")

    for idx, p in enumerate(pending_subs):
        sub_id = p["submission_id"]
        fname = p.get("file_name", "unknown")
        asgn_title = p.get("assignment_title", "Assignment")
        sec_name = p.get("section_name", "Section A")
        reason = p.get("unassigned_reason", "Awaiting student identification")

        with st.container():
            st.markdown(f"""
            <div style="background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 700; color: #92400E; font-size: 1.05rem;">📄 {fname} <span style="font-weight: 400; font-size: 0.85rem; color: #78350F;">(Submission #{sub_id})</span></div>
                    <span style="background-color: #FEF3C7; color: #B45309; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; border: 1px solid #FCD34D;">Awaiting Student Identification</span>
                </div>
                <div style="margin-top: 6px; font-size: 0.85rem; color: #451A03;">
                    <b>Assignment:</b> {asgn_title} &nbsp;|&nbsp; <b>Section:</b> {sec_name}
                </div>
                <div style="margin-top: 4px; font-size: 0.85rem; color: #B91C1C;">
                    <b>Reason:</b> {reason}
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_sel, c_btn = st.columns([3, 1])
            with c_sel:
                selected_label = st.selectbox(
                    f"Assign student for '{fname}':",
                    stud_options,
                    key=f"pending_stud_sel_{sub_id}_{idx}",
                    label_visibility="collapsed"
                )
            with c_btn:
                assign_btn = st.button(
                    f"✅ Confirm & Analyze",
                    key=f"confirm_assign_btn_{sub_id}_{idx}",
                    type="primary",
                    use_container_width=True
                )

            if assign_btn:
                if selected_label == "-- Select Eligible Student --":
                    st.error("⚠️ Please select a valid student from the dropdown before confirming.")
                else:
                    chosen_student_id = stud_map[selected_label]
                    with st.spinner(f"Associating '{fname}' and executing analysis pipeline..."):
                        try:
                            assign_res = requests.post(
                                f"{API_URL}/submissions/{sub_id}/assign-student",
                                json={"student_id": chosen_student_id},
                                headers=get_auth_headers(),
                                timeout=30
                            )
                            if assign_res.status_code == 200:
                                res_json = assign_res.json()
                                st.success(f"🎉 {res_json.get('message', 'Submission successfully assigned and analyzed!')}")
                                st.rerun()
                            else:
                                err_detail = assign_res.json().get("detail", "Assignment failed.")
                                st.error(f"❌ Could not assign: {err_detail}")
                        except Exception as e:
                            st.error(f"Error during assignment: {str(e)}")

        st.markdown("<hr style='margin: 8px 0 16px 0; opacity: 0.2;'>", unsafe_allow_html=True)

    st.markdown("---")


# =---------------- NAVIGATION VIEWS =----------------

if navigation == "Dashboard Home":
    st.markdown("### Welcome to CodeGuard")
    st.caption("Select a role or log in to access RBAC features.")
    
    if st.session_state.token:
        st.success(f"Logged in as **{st.session_state.username}** (`{st.session_state.role}`)")
    else:
        st.info("Log in using the sidebar to unlock student or faculty actions.")

elif navigation == "Upload Submission":
    st.markdown("### 📤 Upload Code Submission")
    st.caption("Upload your code file (.py, .pdf, .docx, image) or paste source text below. Only one submission is required.")
    
    assignments = fetch_available_assignments()
    asgn_dict = {f"{a['title']} ({a['course']})": a["assignment_id"] for a in assignments}
    
    sel_asgn_label = st.selectbox("Select Assignment", list(asgn_dict.keys()))
    sel_asgn_id = asgn_dict[sel_asgn_label]
    
    uploaded_file = st.file_uploader("Choose a code file (.py, .pdf, .docx, .png, .jpg)", type=["py", "pdf", "docx", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        if st.button("🚀 Upload File Submission", key="upload_file_btn", use_container_width=True):
            with st.spinner("Extracting text and validating Python syntax..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {"assignment_id": sel_asgn_id, "section_id": 1}
                try:
                    res = requests.post(f"{API_URL}/upload-file", data=data, files=files, headers=get_auth_headers(), timeout=10)
                    if res.status_code == 200:
                        ret = res.json()
                        st.success(f"✅ File Uploaded Successfully! Submission ID: #{ret.get('submission_id')}")
                        st.info("Your submission is now queued for faculty review.")
                    else:
                        st.error(f"❌ Upload Error ({res.status_code}): {res.json().get('detail')}")
                except Exception as e:
                    st.error(f"Upload failed: {str(e)}")
    else:
        st.markdown("---")
        st.markdown("#### Or Paste Raw Python Code:")
        with st.form("paste_upload_form"):
            file_name = st.text_input("File Name", value="solution.py")
            raw_code = st.text_area("Source Code", height=200, value=
r"""def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
""")
            submit_paste = st.form_submit_button("🚀 Upload Code Snippet", use_container_width=True)
            if submit_paste:
                payload = {
                    "assignment_id": sel_asgn_id,
                    "section_id": 1,
                    "file_name": file_name,
                    "language": "python",
                    "raw_code": raw_code
                }
                try:
                    res = requests.post(f"{API_URL}/upload", json=payload, headers=get_auth_headers(), timeout=5)
                    if res.status_code == 200:
                        ret = res.json()
                        st.success(f"✅ Code Uploaded! Submission ID: #{ret.get('submission_id')}")
                    else:
                        st.error(f"❌ Error ({res.status_code}): {res.json().get('detail')}")
                except Exception as e:
                    st.error(f"Submission failed: {str(e)}")

elif navigation == "My Submissions":
    st.markdown("### 📋 My Submissions")
    st.caption("View status and approved analysis reports for your submitted assignments.")
    
    try:
        res = requests.get(f"{API_URL}/my-submissions", headers=get_auth_headers(), timeout=3)
        if res.status_code == 200:
            subs = res.json()
            if not subs:
                st.info("No submissions found.")
            else:
                sel_id = render_interactive_submissions_table(subs, key_prefix="my_subs")
                if sel_id:
                    detail_res = requests.get(f"{API_URL}/submission/{sel_id}", headers=get_auth_headers(), timeout=3)
                    if detail_res.status_code == 200:
                        render_full_submission_audit(detail_res.json(), can_approve=False, sub_id=sel_id)
        else:
            st.error(f"Failed to fetch submissions ({res.status_code})")
    except Exception as e:
        st.error(f"Connection error: {e}")

elif navigation == "Review Queue" or navigation == "Approve & Release":
    # ---------------- DEDICATED PENDING IDENTIFICATION VIEW ----------------
    if st.session_state.get("review_subview") == "pending_identification":
        h_col1, h_col2 = st.columns([3, 1.2])
        with h_col1:
            st.markdown("### ⚠️ Submissions Awaiting Student Identification")
            st.caption("These files could not be automatically matched to a registered student during upload. Select the correct student and confirm assignment to run analysis.")
        with h_col2:
            if st.button("⬅️ Back to Review Queue", key="back_to_rq_btn", type="primary", use_container_width=True):
                st.session_state["review_subview"] = "main"
                st.rerun()
        st.markdown("---")
        render_unassigned_submissions_section()

    # ---------------- MAIN FACULTY REVIEW QUEUE VIEW ----------------
    else:
        # 1. Dynamic Pending Identification Count for Top-Right Button
        pending_count = 0
        try:
            c_res = requests.get(f"{API_URL}/faculty/unassigned-count", headers=get_auth_headers(), timeout=3)
            if c_res.status_code == 200:
                pending_count = c_res.json().get("count", 0)
        except Exception:
            pass

        # Top Header
        h_col1, h_col2 = st.columns([3, 1.3])
        with h_col1:
            st.markdown("### 👨‍🏫 Faculty Review Queue")
            st.caption("Audit student submissions, inspect AI and plagiarism patterns, and approve reports.")
        with h_col2:
            btn_badge = f"⚠️ Pending Identification ({pending_count})" if pending_count > 0 else "✅ Pending Identification (0)"
            btn_type = "primary" if pending_count > 0 else "secondary"
            if st.button(btn_badge, key="btn_open_pending_id", type=btn_type, use_container_width=True, help="Click to open dedicated page to map unassigned submissions"):
                st.session_state["review_subview"] = "pending_identification"
                st.rerun()

        # 2. Session State Initialization for Filters
        if "rq_asgn" not in st.session_state: st.session_state["rq_asgn"] = "All Assignments"
        if "rq_sec" not in st.session_state: st.session_state["rq_sec"] = "All Authorized Sections"
        if "rq_status" not in st.session_state: st.session_state["rq_status"] = "All Statuses"
        if "rq_search" not in st.session_state: st.session_state["rq_search"] = ""
        if "rq_sort" not in st.session_state: st.session_state["rq_sort"] = "Date (Newest First)"
        if "rq_page" not in st.session_state: st.session_state["rq_page"] = 1
        if "rq_page_size" not in st.session_state: st.session_state["rq_page_size"] = 20

        # Fetch filter options
        assignments = fetch_available_assignments()
        asgn_map = {f"{a['title']} ({a['course']})": a["assignment_id"] for a in assignments}
        asgn_options = ["All Assignments"] + list(asgn_map.keys())

        try:
            sec_res = requests.get(f"{API_URL}/faculty/sections", headers=get_auth_headers(), timeout=3)
            faculty_sections = sec_res.json() if sec_res.status_code == 200 else []
        except Exception:
            faculty_sections = []
        sec_map = {f"Section {s['section_name']}": s["id"] for s in faculty_sections}
        sec_options = ["All Authorized Sections"] + list(sec_map.keys())

        status_options = [
            "All Statuses",
            "Faculty Review",
            "Approved",
            "Released",
            "🔴 Flagged for Review"
        ]

        sort_options = [
            "Date (Newest First)",
            "Date (Oldest First)",
            "AI Pattern Score (High to Low)",
            "AI Pattern Score (Low to High)",
            "Similarity Score (High to Low)",
            "Similarity Score (Low to High)"
        ]

        # 3. Compact Filter Toolbar
        with st.container():
            t_col1, t_col2, t_col3, t_col4 = st.columns([1.6, 1.2, 1.2, 1.3])
            with t_col1:
                cur_asgn_idx = asgn_options.index(st.session_state["rq_asgn"]) if st.session_state["rq_asgn"] in asgn_options else 0
                sel_asgn = st.selectbox("📚 Assignment", asgn_options, index=cur_asgn_idx, key="rq_asgn_select")
            with t_col2:
                cur_sec_idx = sec_options.index(st.session_state["rq_sec"]) if st.session_state["rq_sec"] in sec_options else 0
                sel_sec = st.selectbox("🏫 Section / Class", sec_options, index=cur_sec_idx, key="rq_sec_select")
            with t_col3:
                cur_st_idx = status_options.index(st.session_state["rq_status"]) if st.session_state["rq_status"] in status_options else 0
                sel_status = st.selectbox("📋 Status", status_options, index=cur_st_idx, key="rq_status_select")
            with t_col4:
                cur_sort_idx = sort_options.index(st.session_state["rq_sort"]) if st.session_state["rq_sort"] in sort_options else 0
                sel_sort = st.selectbox("🔃 Sort By", sort_options, index=cur_sort_idx, key="rq_sort_select")

            s_col1, s_col2, s_col3 = st.columns([3, 1, 1])
            with s_col1:
                search_val = st.text_input("🔍 Search Submissions", value=st.session_state["rq_search"], placeholder="Type student username, registration number, filename, or ID...", key="rq_search_input").strip()
            with s_col2:
                cur_ps_idx = [20, 50, 100].index(st.session_state["rq_page_size"]) if st.session_state["rq_page_size"] in [20, 50, 100] else 0
                page_size_val = st.selectbox("📄 Page Size", [20, 50, 100], index=cur_ps_idx, key="rq_pagesize_select")
            with s_col3:
                st.write("") # vertical alignment
                if st.button("🔄 Reset Filters", key="rq_reset_btn", use_container_width=True, help="Clear all filters and search"):
                    st.session_state["rq_asgn"] = "All Assignments"
                    st.session_state["rq_sec"] = "All Authorized Sections"
                    st.session_state["rq_status"] = "All Statuses"
                    st.session_state["rq_search"] = ""
                    st.session_state["rq_sort"] = "Date (Newest First)"
                    st.session_state["rq_page"] = 1
                    st.session_state["rq_page_size"] = 20
                    st.rerun()

        # Check for filter changes -> reset page to 1
        if (sel_asgn != st.session_state["rq_asgn"] or 
            sel_sec != st.session_state["rq_sec"] or 
            sel_status != st.session_state["rq_status"] or 
            search_val != st.session_state["rq_search"] or 
            sel_sort != st.session_state["rq_sort"] or 
            page_size_val != st.session_state["rq_page_size"]):
            st.session_state["rq_asgn"] = sel_asgn
            st.session_state["rq_sec"] = sel_sec
            st.session_state["rq_status"] = sel_status
            st.session_state["rq_search"] = search_val
            st.session_state["rq_sort"] = sel_sort
            st.session_state["rq_page_size"] = page_size_val
            st.session_state["rq_page"] = 1
            st.rerun()

        # Build backend request parameters
        req_params = {
            "page": st.session_state["rq_page"],
            "page_size": st.session_state["rq_page_size"]
        }
        if st.session_state["rq_asgn"] != "All Assignments" and st.session_state["rq_asgn"] in asgn_map:
            req_params["assignment_id"] = asgn_map[st.session_state["rq_asgn"]]
        if st.session_state["rq_sec"] != "All Authorized Sections" and st.session_state["rq_sec"] in sec_map:
            req_params["section_id"] = sec_map[st.session_state["rq_sec"]]
        if st.session_state["rq_status"] != "All Statuses":
            req_params["status"] = st.session_state["rq_status"]
        if st.session_state["rq_search"]:
            req_params["search"] = st.session_state["rq_search"]

        sort_map = {
            "Date (Newest First)": ("date", "desc"),
            "Date (Oldest First)": ("date", "asc"),
            "AI Pattern Score (High to Low)": ("ai_score", "desc"),
            "AI Pattern Score (Low to High)": ("ai_score", "asc"),
            "Similarity Score (High to Low)": ("similarity", "desc"),
            "Similarity Score (Low to High)": ("similarity", "asc")
        }
        sb, so = sort_map.get(st.session_state["rq_sort"], ("date", "desc"))
        req_params["sort_by"] = sb
        req_params["sort_order"] = so

        # Query backend
        try:
            res = requests.get(f"{API_URL}/faculty/submissions", params=req_params, headers=get_auth_headers(), timeout=6)
            if res.status_code == 200:
                resp_data = res.json()
                subs = resp_data.get("items", []) if isinstance(resp_data, dict) else resp_data
                total_matching = resp_data.get("total", len(subs)) if isinstance(resp_data, dict) else len(subs)
                total_pages = resp_data.get("total_pages", 1) if isinstance(resp_data, dict) else 1
                metrics = resp_data.get("metrics", {}) if isinstance(resp_data, dict) else {}

                # 4. Summary Metrics Cards (Part C)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("📁 Total in Scope", metrics.get("total_in_scope", total_matching))
                m2.metric("⏳ Awaiting Review", metrics.get("awaiting_review", 0))
                m3.metric("🔴 Flagged for Review", metrics.get("flagged", 0))
                m4.metric("🚀 Approved & Released", metrics.get("approved_released", 0))

                # Active filter badges indicator
                active_filter_chips = []
                if st.session_state["rq_asgn"] != "All Assignments":
                    active_filter_chips.append(f"Assignment: **{st.session_state['rq_asgn']}**")
                if st.session_state["rq_sec"] != "All Authorized Sections":
                    active_filter_chips.append(f"Section: **{st.session_state['rq_sec']}**")
                if st.session_state["rq_status"] != "All Statuses":
                    active_filter_chips.append(f"Status: **{st.session_state['rq_status']}**")
                if st.session_state["rq_search"]:
                    active_filter_chips.append(f"Search: **\"{st.session_state['rq_search']}\"**")
                
                if active_filter_chips:
                    st.info(f"🏷️ **Active Filters:** {' &nbsp;|&nbsp; '.join(active_filter_chips)}")

                # 5. Empty State / Pagination Info
                if not subs:
                    st.warning("🔍 **No submissions match your current filters or search query.** Try broadening your search or click **Reset Filters** above.")
                else:
                    curr_p = st.session_state["rq_page"]
                    p_size = st.session_state["rq_page_size"]
                    start_idx = (curr_p - 1) * p_size + 1
                    end_idx = min(total_matching, curr_p * p_size)

                    # Top pagination / action bar
                    pg_col1, pg_col2, pg_col3 = st.columns([2.5, 1.5, 1.5])
                    with pg_col1:
                        st.markdown(f"Showing **{start_idx}–{end_idx}** of **{total_matching}** submissions *(Page {curr_p} of {total_pages})*")
                    with pg_col2:
                        if st.button("✅ Approve Page", key="rq_approve_page_btn", use_container_width=True, help="Approve all clean submissions currently displayed on this page"):
                            app_cnt = 0
                            for item in subs:
                                sid = item["submission_id"]
                                try:
                                    requests.post(f"{API_URL}/approve-report/{sid}?approve=true", headers=get_auth_headers(), timeout=3)
                                    app_cnt += 1
                                except Exception:
                                    pass
                            st.toast(f"Approved {app_cnt} submissions!")
                            st.rerun()
                    with pg_col3:
                        if st.button("🚀 Release Page", key="rq_release_page_btn", use_container_width=True, help="Release all reports currently displayed on this page"):
                            rel_cnt = 0
                            for item in subs:
                                sid = item["submission_id"]
                                try:
                                    requests.post(f"{API_URL}/release-report/{sid}?release=true", headers=get_auth_headers(), timeout=3)
                                    rel_cnt += 1
                                except Exception:
                                    pass
                            st.toast(f"Released {rel_cnt} reports to students!")
                            st.rerun()

                    # Trigger popup dialog if requested
                    if st.session_state.get("trigger_popup_sub_id"):
                        popup_id = st.session_state["trigger_popup_sub_id"]
                        st.session_state["trigger_popup_sub_id"] = None
                        show_submission_popup(popup_id)

                    # Table Header
                    header_cols = st.columns([1.0, 1.6, 1.6, 0.6, 1.4, 1.2, 1.2, 1.2, 1.2])
                    with header_cols[0]: st.markdown("**ID** *(Click)*")
                    with header_cols[1]: st.markdown("**Student**")
                    with header_cols[2]: st.markdown("**Assignment**")
                    with header_cols[3]: st.markdown("**Sec**")
                    with header_cols[4]: st.markdown("**File Name**")
                    with header_cols[5]: st.markdown("**AI Pattern**")
                    with header_cols[6]: st.markdown("**Similarity**")
                    with header_cols[7]: st.markdown("**Status**")
                    with header_cols[8]: st.markdown("**Actions**")

                    st.markdown("<hr style='margin:4px 0 10px 0; opacity:0.2;'>", unsafe_allow_html=True)

                    # Table Rows
                    selected_id = st.session_state.get("selected_sub_id", subs[0]["submission_id"] if subs else None)
                    if selected_id not in [s["submission_id"] for s in subs]:
                        selected_id = subs[0]["submission_id"] if subs else None
                        st.session_state["selected_sub_id"] = selected_id

                    for idx, s in enumerate(subs):
                        sub_id = s["submission_id"]
                        stud_name = s.get("student_username", "Unknown")
                        reg_no = s.get("registration_number")
                        asgn = s.get("assignment", "N/A")
                        sec = s.get("section", "N/A")
                        fname = s.get("file_name", "file.py")
                        status = s.get("status", "Uploaded")
                        ai_score = s.get("ai_score")
                        sim_score = s.get("similarity_score", 0.0)

                        is_active = (selected_id == sub_id)
                        is_approved = s.get("is_approved")
                        is_released = s.get("report_visible")

                        # AI badge
                        if ai_score is not None:
                            if ai_score >= 0.54:
                                ai_badge = f"🔴 {ai_score:.2f}"
                            elif ai_score >= 0.27:
                                ai_badge = f"🟡 {ai_score:.2f}"
                            else:
                                ai_badge = f"🟢 {ai_score:.2f}"
                        else:
                            ai_badge = "⚪ N/A"

                        # Similarity badge
                        if sim_score >= 0.75:
                            sim_badge = f"🔴 {sim_score:.2f}"
                        elif sim_score >= 0.50:
                            sim_badge = f"🟡 {sim_score:.2f}"
                        else:
                            sim_badge = f"🟢 {sim_score:.2f}"

                        # Status badge
                        if status in ["Released", "Visible to Student"] or is_released:
                            st_badge = "🚀 Released"
                        elif status in ["Completed", "Approved"] or is_approved:
                            st_badge = "🟢 Approved"
                        elif status == "Faculty Review":
                            st_badge = "🔵 In Review"
                        else:
                            st_badge = f"🟡 {status}"

                        row_cols = st.columns([1.0, 1.6, 1.6, 0.6, 1.4, 1.2, 1.2, 1.2, 1.2])

                        with row_cols[0]:
                            btn_text = f"👉 #{sub_id}" if is_active else f"#{sub_id}"
                            btn_type = "primary" if is_active else "secondary"
                            if st.button(btn_text, key=f"rq_sub_btn_{sub_id}_{idx}", type=btn_type, help="Click to open popup preview & inspect audit view below"):
                                st.session_state["selected_sub_id"] = sub_id
                                st.session_state["trigger_popup_sub_id"] = sub_id
                                st.rerun()

                        with row_cols[1]:
                            stud_label = f"👤 {stud_name}"
                            if reg_no:
                                stud_label += f"\n`{reg_no}`"
                            st.markdown(stud_label)

                        with row_cols[2]:
                            st.write(f"`{asgn}`")

                        with row_cols[3]:
                            st.caption(f"**{sec}**")

                        with row_cols[4]:
                            st.caption(f"`{fname}`")

                        with row_cols[5]:
                            st.markdown(f"**{ai_badge}**")

                        with row_cols[6]:
                            st.markdown(f"**{sim_badge}**")

                        with row_cols[7]:
                            st.caption(st_badge)

                        with row_cols[8]:
                            # 1-click Quick Toggle Approve
                            app_icon = "↩️" if is_approved else "✅"
                            app_tip = "Remove Approval" if is_approved else "Approve Report"
                            if st.button(app_icon, key=f"rq_app_{sub_id}_{idx}", help=app_tip):
                                try:
                                    requests.post(f"{API_URL}/approve-report/{sub_id}?approve={not is_approved}", headers=get_auth_headers(), timeout=3)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                    # Bottom Pagination Controls
                    if total_pages > 1:
                        st.markdown("<hr style='margin:10px 0 14px 0; opacity:0.2;'>", unsafe_allow_html=True)
                        b_pg1, b_pg2, b_pg3 = st.columns([1, 2, 1])
                        with b_pg1:
                            if st.button("⬅️ Previous Page", disabled=(curr_p <= 1), key="rq_prev_bottom", use_container_width=True):
                                st.session_state["rq_page"] = max(1, curr_p - 1)
                                st.rerun()
                        with b_pg2:
                            st.markdown(f"<div style='text-align:center; padding-top:6px; font-weight:600;'>Page {curr_p} of {total_pages}</div>", unsafe_allow_html=True)
                        with b_pg3:
                            if st.button("Next Page ➡️", disabled=(curr_p >= total_pages), key="rq_next_bottom", use_container_width=True):
                                st.session_state["rq_page"] = min(total_pages, curr_p + 1)
                                st.rerun()

                    # Render selected submission audit view below
                    if selected_id:
                        st.markdown("---")
                        detail_res = requests.get(f"{API_URL}/submission/{selected_id}", headers=get_auth_headers(), timeout=10)
                        if detail_res.status_code == 200:
                            render_full_submission_audit(detail_res.json(), can_approve=True, sub_id=selected_id)

            elif res.status_code == 403:
                st.error("Access Denied (403): You do not have permission to view this review queue.")
            else:
                st.error(f"Failed to fetch submissions ({res.status_code}): {res.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")

# PROMPT 1: All-vs-All Plagiarism Report View
elif navigation == "Plagiarism Report":
    st.markdown("### 🔍 All-vs-All Assignment Plagiarism Report")
    st.caption("Compare every student submission against all other submissions in the selected assignment.")
    
    assignments = fetch_available_assignments()
    asgn_options = ["-- Select an Assignment --"] + [f"{a['title']} ({a['course']}) [ID: #{a['assignment_id']}]" for a in assignments]
    asgn_map = {f"{a['title']} ({a['course']}) [ID: #{a['assignment_id']}]": a["assignment_id"] for a in assignments}
    
    col_a, col_b = st.columns([3, 1])
    with col_a:
        sel_asgn_label = st.selectbox("Select Assignment to Analyze", asgn_options, key="plag_asgn_sel")
    with col_b:
        threshold = st.slider("Similarity Warning Threshold", min_value=0.50, max_value=0.95, value=float(PLAGIARISM_FLAG_THRESHOLD), step=0.05)
        st.caption(f"Default: {PLAGIARISM_FLAG_THRESHOLD} fused score")

    if sel_asgn_label == "-- Select an Assignment --":
        st.info("📌 Please select an assignment from the dropdown above to load its isolated all-vs-all plagiarism report.")
    else:
        sel_asgn_id = asgn_map[sel_asgn_label]
        try:
            report_res = requests.get(f"{API_URL}/assignments/{sel_asgn_id}/plagiarism-report?threshold={threshold}", headers=get_auth_headers(), timeout=5)
            if report_res.status_code == 200:
                rep = report_res.json()
                
                # 1. Summary View ("at a glance")
                st.markdown("#### 📊 Assignment Overview Summary")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Submissions", rep.get("total_submissions", 0))
                m2.metric("Total Pairwise Comparisons", rep.get("total_pairs_analyzed", 0))
                m3.metric("Flagged Pairs (> Threshold)", rep.get("flagged_pairs_count", 0))
                m4.metric("Identified Clusters", rep.get("clusters_count", 0))

                clusters = rep.get("clusters", [])
                all_pairs = rep.get("all_pairs", [])
                
                view_mode = st.radio(
                    "Select Report View Format:",
                    ["🔴 Cluster Grouping View (Recommended)", "📋 Flat Pairwise Table View"],
                    horizontal=True,
                    key="plag_view_mode"
                )

                if view_mode == "🔴 Cluster Grouping View (Recommended)":
                    st.markdown("#### 🔴 Suspicious Submission Clusters")
                    st.caption("Submissions sharing high similarity grouped via NetworkX connected-components graph analysis.")
                    
                    if not clusters:
                        st.success("✅ No suspicious submission clusters detected above the specified threshold.")
                    else:
                        import pandas as pd
                        for clus in clusters:
                            clus_id = clus["cluster_id"]
                            sub_cnt = clus["submission_count"]
                            avg_sim = clus["avg_fused_score"]
                            max_sim = clus["max_fused_score"]
                            
                            header_title = f"🔴 Cluster #{clus_id} — {sub_cnt} Submissions (Avg Similarity: {avg_sim:.2f} | Max: {max_sim:.2f})"
                            with st.expander(header_title, expanded=True):
                                st.markdown("**Submissions in this cluster:**")
                                sub_chips = ", ".join([f"`Sub #{s['submission_id']} ({s['student_username']})`" for s in clus["submissions"]])
                                st.markdown(sub_chips)
                                
                                st.markdown("**Internal Pairwise Matrix:**")
                                c_table = []
                                for p in clus["internal_pairs"]:
                                    c_table.append({
                                        "Student A": f"{p['student1_username']} (Sub #{p['submission1_id']})",
                                        "Student B": f"{p['student2_username']} (Sub #{p['submission2_id']})",
                                        "Fused Score": f"{p['fused_score']:.4f}",
                                        "Semantic Score": f"{p['semantic_score']:.4f}",
                                        "Structural Score": f"{p['structural_score']:.4f}"
                                    })
                                st.dataframe(pd.DataFrame(c_table), use_container_width=True)

                else:
                    # Flat Pairwise Table View
                    if all_pairs:
                        st.markdown("#### 🚨 Flagged Pairwise Comparisons (Ranked by Highest Fused Similarity)")
                        st.caption("Sorted across all students in the assignment.")
                        
                        table_data = []
                        for p in all_pairs:
                            is_flagged = p["fused_score"] >= threshold
                            flag_tag = "🔴 FLAGGED" if is_flagged else "🟢 Clean"
                            table_data.append({
                                "Flag": flag_tag,
                                "Student A": f"{p['student1_username']} (Sub #{p['submission1_id']})",
                                "Student B": f"{p['student2_username']} (Sub #{p['submission2_id']})",
                                "Fused Score": f"{p['fused_score']:.4f}",
                                "Semantic (Embedding)": f"{p['semantic_score']:.4f}",
                                "Structural (Jaccard)": f"{p['structural_score']:.4f}"
                            })
                        
                        import pandas as pd
                        df_pairs = pd.DataFrame(table_data)
                        st.dataframe(df_pairs, use_container_width=True)

                st.markdown("---")

                # 2. Per-Student Comparison View
                st.markdown("#### 👤 Student-Level Comparison Inspector")
                st.caption("Select a student to see their similarity ranking against every other submission in this assignment.")
                
                students = rep.get("students", [])
                if not students:
                    st.info("No student submissions available for this assignment.")
                else:
                    stud_options = {f"{s['student_username']} ({s['file_name']})": s for s in students}
                    sel_stud_label = st.selectbox("Select Student Submission to Inspect:", list(stud_options.keys()))
                    sel_stud = stud_options[sel_stud_label]

                    # Top match breakdown explanation card
                    top_match = sel_stud.get("top_match")
                    if top_match:
                        st.markdown("##### 🎯 Top Match Diagnostic Breakdown")
                        fused = top_match["fused_score"]
                        sem = top_match["semantic_score"]
                        struct = top_match["structural_score"]
                        other_user = top_match["other_student_username"]

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Fused Score", f"{fused:.4f}")
                        c2.metric("Semantic Score", f"{sem:.4f}")
                        c3.metric("Structural Score", f"{struct:.4f}")

                        # Diagnostic reason statement
                        if struct >= 0.75 and sem < 0.75:
                            diag_msg = f"⚠️ **High Structural, Low Semantic Score** — Likely obfuscated copy or structural clone from student `{other_user}`."
                            st.warning(diag_msg)
                        elif sem >= 0.75 and struct < 0.75:
                            diag_msg = f"⚠️ **High Semantic, Low Structural Score** — Rewritten logic or semantic similarity with student `{other_user}`."
                            st.warning(diag_msg)
                        elif fused >= 0.75:
                            diag_msg = f"🚨 **High Fused Similarity** — Potential direct copy or duplicate submission with student `{other_user}`."
                            st.error(diag_msg)
                        else:
                            st.success(f"✅ **Low Similarity** — Top match with `{other_user}` is within acceptable parameters.")

                    # Interactive Table of all compared classmates
                    st.markdown(f"##### All Comparisons for `{sel_stud['student_username']}`")
                    comps = sel_stud.get("comparisons", [])
                    if not comps:
                        st.info("No comparisons recorded.")
                    else:
                        h_cols = st.columns([1.2, 2.0, 2.0, 1.2, 1.2, 1.2])
                        with h_cols[0]: st.markdown("**Status**")
                        with h_cols[1]: st.markdown("**Compared Student** *(Click)*")
                        with h_cols[2]: st.markdown("**File Name** *(Click)*")
                        with h_cols[3]: st.markdown("**Fused**")
                        with h_cols[4]: st.markdown("**Semantic**")
                        with h_cols[5]: st.markdown("**Structural**")

                        st.markdown("<hr style='margin:4px 0 8px 0; opacity:0.2;'>", unsafe_allow_html=True)

                        for idx, c in enumerate(comps):
                            other_sub_id = c.get("other_submission_id")
                            other_user = c.get("other_student_username", "Unknown")
                            other_fname = c.get("other_file_name", "file.py")
                            fused = c.get("fused_score", 0.0)
                            sem = c.get("semantic_score", 0.0)
                            struct = c.get("structural_score", 0.0)
                            is_warn = fused >= threshold
                            flag_tag = "🔴 FLAGGED" if is_warn else "🟢 OK"

                            r_cols = st.columns([1.2, 2.0, 2.0, 1.2, 1.2, 1.2])
                            with r_cols[0]:
                                st.caption(flag_tag)
                            with r_cols[1]:
                                if st.button(f"👤 {other_user}", key=f"plag_rep_stud_{other_sub_id}_{idx}", help=f"Click to inspect Submission #{other_sub_id}"):
                                    st.session_state["selected_sub_id"] = other_sub_id
                                    st.session_state["trigger_popup_sub_id"] = other_sub_id
                                    st.rerun()
                            with r_cols[2]:
                                if st.button(f"📄 {other_fname}", key=f"plag_rep_fname_{other_sub_id}_{idx}", help=f"Click to view code snippet for {other_fname}"):
                                    st.session_state["selected_sub_id"] = other_sub_id
                                    st.session_state["trigger_popup_sub_id"] = other_sub_id
                                    st.rerun()
                            with r_cols[3]:
                                st.write(f"`{fused:.4f}`")
                            with r_cols[4]:
                                st.write(f"`{sem:.4f}`")
                            with r_cols[5]:
                                st.write(f"`{struct:.4f}`")

            else:
                st.error(f"Could not load plagiarism report ({report_res.status_code}): {report_res.json().get('detail')}")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

        # Render AI Detection section directly below Plagiarism Report
        render_ai_detection_section()

elif navigation == "AI Detection Report":
    render_ai_detection_section()

# PROMPT 3: Teacher Bulk Upload View
elif navigation == "Bulk Upload":
    st.markdown("### 📦 Teacher Bulk Submission Upload")
    st.caption("Upload multiple student submissions (PDF, Word DOCX, Image, or .py) at once. The system will extract text, run validation, and compute all pairwise similarity scores.")
    
    assignments = fetch_available_assignments()
    asgn_dict = {f"{a['title']} ({a['course']})": a["assignment_id"] for a in assignments}
    asgn_options = list(asgn_dict.keys()) + ["➕ Create Custom Assessment / Assignment"]
    
    sel_asgn_label = st.selectbox("Target Assignment for Bulk Upload", asgn_options, key="bulk_asgn_sel")
    
    if sel_asgn_label == "➕ Create Custom Assessment / Assignment":
        c_col1, c_col2 = st.columns([3, 1])
        with c_col1:
            custom_title = st.text_input("📝 Custom Assessment Name (Whatever you want)", placeholder="Type any assessment name you want (e.g. Midterm Lab Exam)", key="bulk_custom_title").strip()
        with c_col2:
            custom_course = st.text_input("Course Code", value="CS101", key="bulk_custom_course").strip()
    else:
        custom_title = None
        custom_course = None

    # --- Section Selection ---
    try:
        sec_res = requests.get(f"{API_URL}/faculty/sections", headers=get_auth_headers(), timeout=3)
        if sec_res.status_code == 200:
            faculty_sections = sec_res.json()  # [{"id": ..., "section_name": ...}]
        else:
            faculty_sections = []
    except Exception:
        faculty_sections = []

    if not faculty_sections:
        st.error("⚠️ You have no sections assigned. Ask an Admin to assign you to a section before uploading.")
        st.stop()

    sec_dict = {f"Section {s['section_name']}": s["id"] for s in faculty_sections}
    sel_sec_label = st.selectbox(
        "📂 Target Section",
        options=list(sec_dict.keys()),
        key="bulk_sec_sel",
        help="Only sections you are authorized to manage are shown."
    )
    selected_section_id = sec_dict[sel_sec_label]

    bulk_files = st.file_uploader(
        "Select Multiple Code/Document Files (e.g. 30 PDFs/DOCXs/.py files)",
        type=["py", "pdf", "docx", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="bulk_uploader"
    )
    
    if bulk_files:
        st.info(f"📁 {len(bulk_files)} files selected for batch processing.")
        if st.button("🚀 Start Bulk Batch Processing", use_container_width=True):
            target_asgn_id = None
            if sel_asgn_label == "➕ Create Custom Assessment / Assignment":
                if not custom_title:
                    st.error("⚠️ Please type a custom assessment name before starting bulk upload.")
                    st.stop()
                try:
                    create_res = requests.post(f"{API_URL}/assignments", json={"title": custom_title, "course": custom_course or "CS101"}, headers=get_auth_headers(), timeout=5)
                    if create_res.status_code == 200:
                        target_asgn_id = create_res.json()["assignment_id"]
                        st.toast(f"Created custom assessment '{custom_title}'!")
                    else:
                        st.error(f"Failed to create custom assessment ({create_res.status_code}): {create_res.text}")
                        st.stop()
                except Exception as e:
                    st.error(f"Error creating custom assessment: {e}")
                    st.stop()
            else:
                target_asgn_id = asgn_dict[sel_asgn_label]

            progress_bar = st.progress(0.0)
            status_box = st.status("Processing bulk upload batch...")
            
            files_payload = []
            for f in bulk_files:
                files_payload.append(("files", (f.name, f.getvalue(), f.type)))
                
            try:
                status_box.update(label=f"Extracting & Analyzing {len(bulk_files)} files via pipeline...")
                res = requests.post(
                    f"{API_URL}/assignments/{target_asgn_id}/bulk-upload",
                    data={"section_id": selected_section_id},
                    files=files_payload,
                    headers=get_auth_headers(),
                    timeout=60
                )
                progress_bar.progress(1.0)
                
                if res.status_code == 200:
                    data = res.json()
                    status_box.update(label="Batch Processing Completed Successfully!", state="complete")
                    
                    st.success(f"🎉 Processed {data.get('processed_count')}/{data.get('total_files')} files under target assessment!")
                    
                    # Identification & unassigned breakdown
                    identified_cnt = data.get("identified_count", 0)
                    unassigned_cnt = data.get("unassigned_count", 0)
                    if identified_cnt > 0 or unassigned_cnt > 0:
                        st.info(f"👤 **Student Identification Summary:** {identified_cnt} file(s) automatically matched and analyzed.")
                    if unassigned_cnt > 0:
                        st.warning(f"⚠️ **{unassigned_cnt} file(s) could not be automatically identified** and are held safely under 'Awaiting Student Identification'. They will remain excluded from plagiarism comparisons until mapped.")

                    # Partial failure reporting (invalid extensions, size limits, etc.)
                    failed = data.get("failed_files", [])
                    if failed:
                        st.error(f"❌ {len(failed)} files failed validation:")
                        for ff in failed:
                            st.write(f"- `{ff['filename']}`: {ff['reason']}")
                    
                    st.markdown("---")
                    st.markdown("#### Next Actions:")
                    c_act1, c_act2 = st.columns(2)
                    with c_act1:
                        if unassigned_cnt > 0:
                            if st.button(f"⚠️ Map {unassigned_cnt} Pending File(s) in Review Queue", key="goto_pending_queue", type="primary", use_container_width=True):
                                st.session_state.portal_nav = "Review Queue"
                                st.rerun()
                    with c_act2:
                        if st.button("📊 View All-vs-All Plagiarism Report for this Assignment", key="goto_plag_report", use_container_width=True):
                            st.session_state.portal_nav = "Plagiarism Report"
                            st.rerun()
                else:
                    status_box.update(label="Bulk Upload Failed", state="error")
                    st.error(f"Bulk upload failed ({res.status_code}): {res.json().get('detail')}")
            except Exception as e:
                status_box.update(label="Error processing batch", state="error")
                st.error(f"Error during bulk upload execution: {str(e)}")

elif navigation == "Department Analytics":
    st.markdown("### 🏛️ Department Analytics")
    try:
        res = requests.get(f"{API_URL}/hod/analytics", headers=get_auth_headers(), timeout=3)
        if res.status_code == 200:
            analytics = res.json()
            st.metric("Total System Submissions", analytics.get("total_system_submissions", 0))
            st.json(analytics.get("section_breakdown"))
        else:
            st.error(f"Access Denied ({res.status_code})")
    except Exception as e:
        st.error(f"Error: {e}")

elif navigation == "User & Section Management":
    st.markdown("### ⚡ User & Section Management")
    with st.form("admin_create_user_form"):
        new_uname = st.text_input("New Username")
        new_email = st.text_input("New Email")
        new_pwd = st.text_input("New Password", type="password")
        new_role = st.selectbox("Role", ["Student", "Professor", "HOD", "Admin"])
        if st.form_submit_button("Register User", use_container_width=True):
            payload = {"username": new_uname, "email": new_email, "password": new_pwd, "role": new_role}
            res = requests.post(f"{API_URL}/admin/users", json=payload, headers=get_auth_headers(), timeout=3)
            if res.status_code == 200:
                st.success(f"Registered user `{new_uname}` (ID: {res.json().get('user_id')})")
            else:
                st.error(f"Error ({res.status_code}): {res.json().get('detail')}")

elif navigation == "Standalone Tools":
    st.markdown("### 🛠️ Standalone Code Analysis Tools")
    st.caption("Inspect, analyze, and run AI/AST/Quality audits on any custom code snippet or student submission.")
    
    # Initialize standalone code state if empty
    if "standalone_code" not in st.session_state or not st.session_state["standalone_code"]:
        default_snippet = r"""def add_numbers(a, b):
    # Returns sum of two numbers
    return a + b
"""
        update_standalone_code_keys(default_snippet)

    # ---------------- QUICK SEARCH & LOAD SUBMISSION CODE ----------------
    st.markdown("#### 🔎 Search & Auto-Load Submission Code")
    s_c1, s_c2 = st.columns([3, 1])
    with s_c1:
        search_input = st.text_input(
            "Enter Submission ID (e.g. 1) or Student Username (e.g. hod, demo_student_1):",
            placeholder="Type submission ID (e.g. 1) or student username and press Enter...",
            key="standalone_search_box"
        )
    with s_c2:
        st.write("") # spacing
        if st.button("⬇️ Scroll to Tools", key="scroll_to_tools_btn", use_container_width=True):
            st.session_state["scroll_to_standalone_tools"] = True
            st.rerun()

    if search_input:
        matched_subs = search_and_fetch_submission(search_input)
        if not matched_subs:
            st.warning(f"No submission found matching '{search_input}'. You can paste code manually below.")
        elif len(matched_subs) == 1:
            sub = matched_subs[0]
            meta = sub.get("metadata", {})
            new_code = sub.get("raw_code", "")
            update_standalone_code_keys(new_code)
            st.success(f"✅ Automatically loaded Submission **#{sub.get('submission_id')}** (`{meta.get('student_username')}` | File: `{meta.get('file_name')}`) into Standalone Tools!")
        else:
            st.info(f"Found {len(matched_subs)} submissions matching '{search_input}'. Select one to load:")
            sub_options = {f"Sub #{s.get('submission_id')} - {s.get('metadata', {}).get('file_name')} ({s.get('metadata', {}).get('assignment')})": s for s in matched_subs}
            selected_sub_label = st.selectbox("Choose Submission to Load:", list(sub_options.keys()), key="standalone_sub_picker")
            selected_sub = sub_options[selected_sub_label]
            new_code = selected_sub.get("raw_code", "")
            update_standalone_code_keys(new_code)
            st.success(f"✅ Loaded Submission **#{selected_sub.get('submission_id')}** into Standalone Tools!")

    st.markdown("---")
    
    # ---------------- MASTER SOURCE CODE EDITOR & AUTO-SYNC ----------------
    st.markdown("#### 💻 Master Source Snippet Editor")
    st.caption("Paste or edit your code snippet here. It automatically synchronizes across all 4 analysis tools below.")
    
    current_code = st.session_state.get("standalone_code", "")
    
    master_code = st.text_area("Master Source Code:", value=current_code, height=160, key="standalone_master_editor_box")
    if master_code != current_code:
        update_standalone_code_keys(master_code)
        st.rerun()

    m_c1, m_c2 = st.columns([2, 2])
    with m_c1:
        if st.button("⚡ Run All 4 Tools Simultaneously", key="run_all_standalone_tools", type="primary", use_container_width=True):
            st.session_state["standalone_quality_res"] = call_api("/api/quality", {"code": master_code})
            st.session_state["standalone_plag_res"] = call_api("/api/plagiarism", {"code_a": master_code, "code_b": master_code})
            st.session_state["standalone_ai_res"] = call_api("/api/ai-detection", {"code": master_code})
            st.session_state["standalone_ast_res"] = call_api("/api/ast", {"code": master_code})
            st.success("✅ Executed audits across all 4 tools! View results under each tab below.")
            st.rerun()
    with m_c2:
        if st.button("🧹 Reset / Clear Code", key="clear_standalone_code", use_container_width=True):
            update_standalone_code_keys("")
            st.rerun()

    st.markdown("---")
    st.markdown('<div id="standalone-tools-anchor"></div>', unsafe_allow_html=True)
    if st.session_state.get("scroll_to_standalone_tools"):
        components.html(
            """
            <script>
                setTimeout(function() {
                    var el = window.parent.document.getElementById('standalone-tools-anchor');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 150);
            </script>
            """,
            height=0
        )
        st.session_state["scroll_to_standalone_tools"] = False

    tool_tab1, tool_tab2, tool_tab3, tool_tab4 = st.tabs([
        "📊 Quality Analyzer",
        "🔍 Plagiarism A/B Checker",
        "🤖 AI Detector",
        "🌳 AST Inspector"
    ])

    # TAB 1: Quality Analyzer
    with tool_tab1:
        st.markdown("#### 📊 Code Quality & Security Metrics Analyzer")
        c_code = st.text_area("Source Snippet:", value=master_code, height=180, key="q_tool_code")
        if st.button("🚀 Run Quality Audit", key="q_tool_btn", type="primary", use_container_width=True):
            q_res = call_api("/api/quality", {"code": c_code})
            st.session_state["standalone_quality_res"] = q_res

        q_res = st.session_state.get("standalone_quality_res")
        if q_res:
            if q_res.get("success"):
                m = q_res.get("metrics", {})
                st.markdown("---")
                st.markdown("##### 📈 Quality Results")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Lines of Code", m.get("loc", 0))
                m2.metric("Comment Ratio", f"{m.get('comment_ratio', 0)*100:.1f}%")
                m3.metric("Maintainability Index", f"{m.get('maintainability_index', 0):.1f}")
                m4.metric("Security Score", f"{m.get('security_score', 100)}/100")

                st.markdown(f"**Cyclomatic Complexity:** `{m.get('cyclomatic_complexity', 1)}` ({m.get('complexity_level', 'Low')})")
                
                with st.expander("🔍 View Full JSON Quality Breakdown"):
                    st.json(m)
            else:
                st.error(f"Quality audit failed: {q_res.get('error', 'Unknown error')}")

    # TAB 2: Plagiarism A/B Checker
    with tool_tab2:
        st.markdown("#### 🔍 Pairwise Plagiarism & Structural A/B Comparison")
        col_code_a, col_code_b = st.columns(2)
        with col_code_a:
            cA = st.text_area("Code A (Source / Target):", value=master_code, height=160, key="plag_tool_a")
        with col_code_b:
            cB = st.text_area("Code B (To Compare Against):", value=master_code, height=160, key="plag_tool_b")
        
        if st.button("🚀 Check Similarity A vs B", key="plag_tool_btn", type="primary", use_container_width=True):
            p_res = call_api("/api/plagiarism", {"code_a": cA, "code_b": cB})
            st.session_state["standalone_plag_res"] = p_res

        p_res = st.session_state.get("standalone_plag_res")
        if p_res:
            if p_res.get("success"):
                rep = p_res.get("report", {})
                fused = rep.get("similarity_score", 0.0)
                badge_html = render_status_badge(fused)
                st.markdown("---")
                st.markdown(f"### Status: {badge_html}", unsafe_allow_html=True)
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Fused Score", f"{fused:.2f}")
                m2.metric("Semantic Cosine", f"{rep.get('semantic_embedding_cosine') or 0.0:.2f}")
                m3.metric("AST Structural Jaccard", f"{rep.get('ast_fingerprint_jaccard', 0.0):.2f}")

                if fused >= 0.75:
                    st.error("🚨 **High Similarity Alert** — Source code A and B exhibit strong structural and semantic alignment.")
                elif fused >= 0.40:
                    st.warning("🟡 **Moderate Similarity** — Source code A and B share notable logic patterns or tokens.")
                else:
                    st.success("🟢 **Low Similarity / Clean** — Code snippets show independent logic structures.")

                matches = rep.get("matches", [])
                if matches:
                    st.markdown(f"**Matching Shared Keywords/Tokens:** `{', '.join(matches)}`")

                with st.expander("🔍 View Full Pairwise Similarity JSON"):
                    st.json(rep)
            else:
                st.error(f"Plagiarism comparison failed: {p_res.get('error', 'Unknown error')}")

    # TAB 3: AI Detector
    with tool_tab3:
        st.markdown("#### 🤖 AI-Generated Code Detector & Signal Analyzer")
        ai_code = st.text_area("Source Snippet:", value=master_code, height=180, key="ai_tool_code")
        if st.button("🚀 Analyze AI Generation", key="ai_tool_btn", type="primary", use_container_width=True):
            ai_res = call_api("/api/ai-detection", {"code": ai_code})
            st.session_state["standalone_ai_res"] = ai_res

        ai_res = st.session_state.get("standalone_ai_res")
        if ai_res:
            if ai_res.get("success"):
                res = ai_res.get("result", {})
                ai_val = res.get("ai_probability", 0.0)
                badge_html = render_status_badge(ai_val)
                st.markdown("---")
                st.markdown(f"### AI Score: {badge_html}", unsafe_allow_html=True)
                
                with st.expander("🔍 Code Characteristics", expanded=True):
                    ai_heuristics = res.get("heuristics", {})
                    t_standalone = ai_res.get("threshold_used", 0.54)

                    # Token Entropy — real computed value, show as bar
                    entropy_val = float(ai_heuristics.get("token_entropy_score", 0.0))
                    col1, col2 = st.columns([3, 7])
                    with col1:
                        st.markdown(f"**Token Entropy (normalised):** `{entropy_val:.2f}`")
                    with col2:
                        st.progress(min(max(entropy_val, 0.0), 1.0))

                    st.markdown("")

                    # Presence indicators — binary flags, no bars, no numeric scores
                    has_docstring = ai_heuristics.get("has_docstring",
                        ai_heuristics.get("docstring_formatting_score", 0.0) > 0.5)
                    has_type_hints = ai_heuristics.get("has_type_hints",
                        ai_heuristics.get("type_hint_density_score", 0.0) > 0.5)
                    has_comments = ai_heuristics.get("has_comments",
                        ai_heuristics.get("comment_density_score", 0.0) > 0.5)

                    st.markdown(f"Docstrings: **{'present' if has_docstring else 'absent'}**")
                    st.markdown(f"Type hints: **{'present' if has_type_hints else 'absent'}**")
                    st.markdown(f"Comments: **{'present' if has_comments else 'absent'}**")

                    st.markdown("---")
                    sa_status = ('🔴 FLAGGED' if ai_val >= t_standalone
                                 else '🟡 OPTIONAL REVIEW' if ai_val >= 0.5 * t_standalone
                                 else '🟢 ROUTINE STRUCTURE')
                    st.markdown(f"**→ Classifier Output (logistic regression):** `{ai_val:.2f}` ({sa_status})")
                    st.caption("Score is the trained classifier's probability output. The indicators above are shown for transparency and are not inputs to this score.")

                with st.expander("🔍 View Raw AI Analysis JSON"):
                    st.json(res)
            else:
                st.error(f"AI Detection failed: {ai_res.get('error', 'Unknown error')}")

    # TAB 4: AST Inspector
    with tool_tab4:
        st.markdown("#### 🌳 Abstract Syntax Tree (AST) Structure Inspector")
        ast_code = st.text_area("Source Snippet:", value=master_code, height=180, key="ast_tool_code")
        if st.button("🚀 Inspect AST Tree", key="ast_tool_btn", type="primary", use_container_width=True):
            ast_res = call_api("/api/ast", {"code": ast_code})
            st.session_state["standalone_ast_res"] = ast_res

        ast_res = st.session_state.get("standalone_ast_res")
        if ast_res:
            if ast_res.get("success"):
                ast_info = ast_res.get("ast", {})
                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Syntax Nodes", ast_info.get("num_nodes", 0))
                m2.metric("Declared Functions", len(ast_info.get("functions", [])))
                m3.metric("Declared Classes", len(ast_info.get("classes", [])))

                if ast_info.get("normalized_code"):
                    st.markdown("**Normalized Code AST Representation:**")
                    st.code(ast_info["normalized_code"], language="python")

                if ast_info.get("fingerprint"):
                    st.markdown("**AST Sequence Fingerprint:**")
                    st.caption(f"`{ast_info['fingerprint']}`")

                with st.expander("🔍 Detailed AST JSON Hierarchy", expanded=True):
                    st.json(ast_info)
            else:
                st.error(f"AST Parsing failed: {ast_res.get('error', 'Unknown error')}")
