import streamlit as st
import requests
import json

# Try to import modules directly for local fallback if backend is offline
try:
    from modules.quality import compute_quality_metrics
    from modules.plagiarism import detect_plagiarism
    from modules.ai_detection import check_ai_generated
    from modules.ast import parse_code_to_ast
    LOCAL_FALLBACK = True
except ImportError:
    LOCAL_FALLBACK = False

# API Config
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="CodeGuard - Advanced Code Analysis Suite",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium CSS Styling Injection
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF3366 0%, #9933FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #B0B0D0;
        margin-bottom: 2rem;
    }
    
    .card {
        background-color: #1E1E2F;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #2F2F4F;
        margin-bottom: 1rem;
        transition: transform 0.2s, border-color 0.2s;
    }
    
    .card:hover {
        transform: translateY(-2px);
        border-color: #9933FF;
    }
    
    .metric-title {
        font-size: 0.9rem;
        color: #8C8CA8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-low { background-color: rgba(0, 200, 100, 0.2); color: #00C864; border: 1px solid #00C864; }
    .badge-medium { background-color: rgba(255, 170, 0, 0.2); color: #FFAA00; border: 1px solid #FFAA00; }
    .badge-high { background-color: rgba(255, 50, 50, 0.2); color: #FF3232; border: 1px solid #FF3232; }
    
    .api-status-online { color: #00C864; font-weight: 600; }
    .api-status-fallback { color: #FFAA00; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Helper function to query backend
def call_api(endpoint: str, payload: dict) -> dict:
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=3)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    
    # Fallback to local import if backend is offline
    if LOCAL_FALLBACK:
        if endpoint == "/api/quality":
            return {"success": True, "metrics": compute_quality_metrics(payload["code"])}
        elif endpoint == "/api/plagiarism":
            return {"success": True, "report": detect_plagiarism(payload["code_a"], payload["code_b"])}
        elif endpoint == "/api/ai-detection":
            return {"success": True, "result": check_ai_generated(payload["code"])}
        elif endpoint == "/api/ast":
            return {"success": True, "ast": parse_code_to_ast(payload["code"])}
    
    return {"success": False, "error": "Backend API offline and local imports failed."}

# Test connection to backend
backend_online = False
try:
    res = requests.get(API_URL, timeout=1)
    if res.status_code == 200:
        backend_online = True
except requests.exceptions.RequestException:
    backend_online = False

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/nolan/128/security-shield.png", width=80)
    st.markdown("### CodeGuard Control")
    
    if backend_online:
        st.markdown('Status: <span class="api-status-online">● Backend Online</span>', unsafe_allow_html=True)
    elif LOCAL_FALLBACK:
        st.markdown('Status: <span class="api-status-fallback">● Local Fallback Mode</span>', unsafe_allow_html=True)
        st.caption("Backend offline. Running computations directly in frontend context.")
    else:
        st.error("Backend offline. No fallbacks available.")
        
    st.markdown("---")
    
    navigation = st.radio(
        "Navigation",
        ["Dashboard Home", "Code Quality Analyzer", "Plagiarism Checker", "AI Code Detector", "AST Structural Inspector"]
    )
    
    st.markdown("---")
    st.caption("CodeGuard v1.0.0. Designed for elite repository monitoring.")

# Main app layout
st.markdown('<div class="main-title">CodeGuard</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Next-gen static analysis, plagiarism verification, and AI source auditing</div>', unsafe_allow_html=True)

if navigation == "Dashboard Home":
    st.markdown("### Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="metric-title">Quality Guard</div>
            <div class="metric-value">Active</div>
            <p style="color:#8C8CA8; margin-top:0.5rem;">Monitors lines of code, comments ratio, and general structural complexity.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="card">
            <div class="metric-title">Plagiarism Shield</div>
            <div class="metric-value">Active</div>
            <p style="color:#8C8CA8; margin-top:0.5rem;">Token-based and string similarity cross-checks on files.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="card">
            <div class="metric-title">AI Sentinel</div>
            <div class="metric-value">Active</div>
            <p style="color:#8C8CA8; margin-top:0.5rem;">Calculates likelihood of LLM generated signatures and syntax styles.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Sample Code Playground")
    sample_code = st.text_area("Paste code here for quick quality & structure analysis:", 
r"""def calculate_factorial(n):
    # This is a sample function to test CodeGuard quality analyzer
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    elif n == 0 or n == 1:
        return 1
    else:
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result
""")
    
    if st.button("Run Instant Audit", key="quick_audit"):
        with st.spinner("Analyzing..."):
            quality_res = call_api("/api/quality", {"code": sample_code})
            ast_res = call_api("/api/ast", {"code": sample_code})
            ai_res = call_api("/api/ai-detection", {"code": sample_code})
            
            if quality_res.get("success") and ast_res.get("success") and ai_res.get("success"):
                metrics = quality_res["metrics"]
                ast_info = ast_res["ast"]
                ai_info = ai_res["result"]
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Lines of Code (LOC)", metrics["loc"])
                c2.metric("Comments Ratio", f"{metrics['comment_ratio']*100:.1f}%")
                c3.metric("AST Nodes Count", ast_info["num_nodes"])
                c4.metric("AI Gen Probability", f"{ai_info['ai_probability']*100:.1f}%")
            else:
                st.error("Could not run instant audit. Please verify backend status.")

elif navigation == "Code Quality Analyzer":
    st.markdown("### Code Quality Analysis")
    code = st.text_area("Input Code Snippet:", height=250, value=
r"""# Simple helper class
class Calculator:
    def __init__(self):
        pass
        
    def add(self, a, b):
        return a + b
        
    def subtract(self, a, b):
        return a - b
""")
    
    if st.button("Compute Quality Metrics", key="run_quality"):
        with st.spinner("Calculating..."):
            res = call_api("/api/quality", {"code": code})
            if res.get("success"):
                m = res["metrics"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <div class="metric-title">Lines of Code</div>
                        <div class="metric-value">{m['loc']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="card">
                        <div class="metric-title">Comment Lines</div>
                        <div class="metric-value">{m['comment_lines']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    complexity = m['complexity_level']
                    badge_cls = "badge-low" if complexity == "Low" else "badge-medium" if complexity == "Medium" else "badge-high"
                    st.markdown(f"""
                    <div class="card">
                        <div class="metric-title">Complexity Level</div>
                        <div style="font-size: 2rem; font-weight:700; margin-top: 0.5rem;">
                            <span class="badge {badge_cls}">{complexity}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.error("Error analyzing quality.")

elif navigation == "Plagiarism Checker":
    st.markdown("### Plagiarism Checker")
    col1, col2 = st.columns(2)
    with col1:
        code_a = st.text_area("Document A (Original Source):", height=250, value=
r"""def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
""")
    with col2:
        code_b = st.text_area("Document B (Suspected Copy):", height=250, value=
r"""def sort_fast(items):
    if len(items) <= 1:
        return items
    middle_element = items[len(items) // 2]
    smaller = [val for val in items if val < middle_element]
    equal = [val for val in items if val == middle_element]
    larger = [val for val in items if val > middle_element]
    return sort_fast(smaller) + equal + sort_fast(larger)
""")
        
    if st.button("Check Similarity", key="run_plagiarism"):
        with st.spinner("Analyzing token overlap..."):
            res = call_api("/api/plagiarism", {"code_a": code_a, "code_b": code_b})
            if res.get("success"):
                report = res["report"]
                score = report["similarity_score"]
                
                st.markdown("#### Results")
                st.progress(score)
                st.markdown(f"**Similarity Index:** `{score * 100:.2f}%`")
                
                if score > 0.7:
                    st.error("⚠️ High similarity detected! Potential plagiarism or code duplication.")
                elif score > 0.4:
                    st.warning("⚠️ Moderate similarity detected. Review structure overlap.")
                else:
                    st.success("✅ Low similarity. Code appears original.")
                    
                st.markdown("**Shared unique keywords/tokens matching:**")
                st.write(", ".join([f"`{m}`" for m in report["matches"]]) if report["matches"] else "None")
            else:
                st.error("Error running plagiarism checker.")

elif navigation == "AI Code Detector":
    st.markdown("### AI Code Detection")
    code = st.text_area("Enter Code to Scan:", height=250, value=
r"""def compute_primes(limit):
    # Generates prime numbers up to limit using Sieve of Eratosthenes
    primes = []
    is_prime = [True] * (limit + 1)
    for p in range(2, limit + 1):
        if is_prime[p]:
            primes.append(p)
            for i in range(p * p, limit + 1, p):
                is_prime[i] = False
    return primes
""")
    
    if st.button("Analyze Code Origin", key="run_ai"):
        with st.spinner("Running AI source heuristic checks..."):
            res = call_api("/api/ai-detection", {"code": code})
            if res.get("success"):
                result = res["result"]
                prob = result["ai_probability"]
                st.markdown("#### Analysis Results")
                st.progress(prob)
                st.markdown(f"**AI Generated Probability:** `{prob * 100:.1f}%`")
                st.markdown(f"**Confidence:** `{result['confidence'] * 100:.1f}%`")
                
                st.json(result["heuristics"])
            else:
                st.error("Error analyzing AI signatures.")

elif navigation == "AST Structural Inspector":
    st.markdown("### AST Structural Inspection")
    code = st.text_area("Input Code to Parse:", height=250, value=
r"""import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def distance_from_origin(self):
        return math.sqrt(self.x**2 + self.y**2)
""")
    
    if st.button("Inspect AST Structure", key="run_ast"):
        with st.spinner("Parsing AST..."):
            res = call_api("/api/ast", {"code": code})
            if res.get("success"):
                ast_data = res["ast"]
                
                st.success("✅ Successfully Parsed Abstract Syntax Tree (AST)")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="card">
                        <div class="metric-title">Total Syntax Nodes</div>
                        <div class="metric-value">{ast_data['ast']['num_nodes']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="card">
                        <div class="metric-title">Classes Discovered</div>
                        <div class="metric-value">{len(ast_data['ast']['classes'])}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("**Discovered Functions:**")
                st.write(", ".join([f"`{f}()`" for f in ast_data['ast']['functions']]) if ast_data['ast']['functions'] else "None")
                
                st.markdown("**Discovered Classes:**")
                st.write(", ".join([f"`class {c}`" for c in ast_data['ast']['classes']]) if ast_data['ast']['classes'] else "None")
            else:
                st.error("Failed to parse code. Please ensure the code is valid Python syntax.")
