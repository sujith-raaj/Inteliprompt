import streamlit as st
from utils.api_client import optimize_prompt, get_history, delete_history_item, get_session_id

st.set_page_config(
    page_title="IntelliPrompt",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.user-bubble {
    background: #1e3a5f;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px 20%;
    font-size: 14px;
    line-height: 1.5;
}
.assistant-bubble {
    background: #f0f2f6;
    color: #1a1a1a;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 20% 8px 0;
    font-size: 14px;
    line-height: 1.5;
}
.chat-label {
    font-size: 11px;
    color: #888;
    margin-bottom: 4px;
}
.score-badge {
    display: inline-block;
    background: #4CAF50;
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ───────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

LLM_OPTIONS = {
    "Claude (Anthropic)": "claude",
    "ChatGPT (OpenAI)": "chatgpt",
    "Gemini (Google)": "gemini",
    "DeepSeek": "deepseek",
}

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ✨ IntelliPrompt")
    st.markdown("*Adaptive Prompt Optimizer*")
    st.divider()

    st.markdown("### 🎯 Target LLM")
    selected_label = st.radio(
        "Choose model:",
        list(LLM_OPTIONS.keys()),
        label_visibility="collapsed",
    )
    target_llm = LLM_OPTIONS[selected_label]

    st.divider()
    st.markdown("### 📜 Session History")

    try:
        history = get_history()
        if history:
            for item in history[:10]:
                col1, col2 = st.columns([5, 1])
                preview = item["original_prompt"][:40] + ("…" if len(item["original_prompt"]) > 40 else "")
                with col1:
                    st.markdown(f"<small>**{item['target_llm'].upper()}** · {item['quality_score']:.0f}/100<br>{preview}</small>", unsafe_allow_html=True)
                with col2:
                    if st.button("🗑", key=f"del_{item['id']}"):
                        delete_history_item(item["id"])
                        st.rerun()
                st.markdown("---")
        else:
            st.caption("No history yet.")
    except Exception:
        st.caption("Backend not connected.")

    st.divider()
    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.messages = []
        if "session_id" in st.session_state:
            del st.session_state.session_id
        st.rerun()

# ── Main chat area ───────────────────────────────────────────────────────────
st.markdown("## ✨ IntelliPrompt — Prompt Optimizer")
st.markdown(f"Targeting: **{selected_label}** &nbsp;|&nbsp; Session: `{get_session_id()[:8]}...`")
st.divider()

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding: 30px 10px 10px 10px;">
        <h1 style="font-size:2.4rem; margin-bottom:4px;">✨ IntelliPrompt</h1>
        <p style="font-size:1.1rem; color:#555; margin-top:0;">
            An Adaptive Prompt Optimization &amp; Model-Adaptive Translation Framework for Multi-LLM Systems
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .card {
        background: #f8f9fb;
        border: 1px solid #e0e4ea;
        border-radius: 12px;
        padding: 20px 22px;
        height: 100%;
    }
    .card h4 { margin-top: 0; margin-bottom: 8px; font-size: 1rem; }
    .card p, .card li { font-size: 0.88rem; color: #444; line-height: 1.6; }
    .card ul { padding-left: 18px; margin: 0; }
    .step-num {
        display: inline-block;
        background: #1e3a5f;
        color: white;
        border-radius: 50%;
        width: 26px; height: 26px;
        text-align: center;
        line-height: 26px;
        font-size: 13px;
        font-weight: bold;
        margin-right: 8px;
    }
    .llm-pill {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 4px;
    }
    .pipeline-step {
        background: #eef2ff;
        border-left: 3px solid #4f6ef7;
        padding: 6px 12px;
        border-radius: 0 8px 8px 0;
        margin: 4px 0;
        font-size: 0.83rem;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── What is IntelliPrompt ──
    st.markdown("---")
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown("""
        <div class="card">
        <h4>🧠 What is IntelliPrompt?</h4>
        <p>
        IntelliPrompt automatically transforms your raw, rough prompts into <b>high-quality, structured prompts</b>
        optimized for the specific LLM you're targeting — no prompt engineering expertise needed.
        </p>
        <p>
        It solves a core problem: the same prompt gives very different results across ChatGPT, Claude, Gemini, and DeepSeek
        because each model is trained differently. IntelliPrompt bridges that gap by adapting your prompt to each model's strengths.
        </p>
        <ul>
            <li>No login required — open and use instantly</li>
            <li>Works with 4 major LLMs</li>
            <li>Fully rule-based — no API cost for optimization</li>
            <li>Scores your prompt quality with detailed breakdown</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="card">
        <h4>🎯 Supported LLMs</h4>
        <p style="margin-bottom:10px;">Each LLM gets a prompt adapted to its unique style:</p>
        <div>
            <span class="llm-pill" style="background:#f0e6ff;color:#6b21a8;">🟣 Claude (Anthropic)</span><br>
            <small style="color:#666;font-size:11px;margin-left:4px;">XML tags · structured thinking · step-by-step</small>
        </div>
        <div style="margin-top:8px;">
            <span class="llm-pill" style="background:#e6ffe6;color:#166534;">🟢 ChatGPT (OpenAI)</span><br>
            <small style="color:#666;font-size:11px;margin-left:4px;">Role assignment · numbered steps · clear sections</small>
        </div>
        <div style="margin-top:8px;">
            <span class="llm-pill" style="background:#fff3e0;color:#92400e;">🟠 Gemini (Google)</span><br>
            <small style="color:#666;font-size:11px;margin-left:4px;">Bold headers · bullet points · concise framing</small>
        </div>
        <div style="margin-top:8px;">
            <span class="llm-pill" style="background:#e0f2fe;color:#075985;">🔵 DeepSeek</span><br>
            <small style="color:#666;font-size:11px;margin-left:4px;">Technical precision · markdown hints · code-friendly</small>
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Pipeline + Scoring ──
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("""
        <div class="card">
        <h4>⚙️ AMPOA — Adaptive Multi-stage Prompt Optimization Algorithm</h4>
        <p style="margin-bottom:8px;">Every prompt passes through these stages automatically:</p>
        <div class="pipeline-step">1. <b>Clean</b> — remove noise, fix punctuation, normalize text</div>
        <div class="pipeline-step">2. <b>Intent Detection</b> — explain / generate / analyze / debug / summarize…</div>
        <div class="pipeline-step">3. <b>Domain Detection</b> — technology / science / business / healthcare…</div>
        <div class="pipeline-step">4. <b>Entity Extraction</b> — key concepts and terms from your prompt</div>
        <div class="pipeline-step">5. <b>Context Enrichment</b> — add domain-specific framing</div>
        <div class="pipeline-step">6. <b>Prompt Expansion</b> — add clarity directives based on intent</div>
        <div class="pipeline-step">7. <b>Structuring</b> — Role · Task · Context · Constraints · Output Format</div>
        </div>
        """, unsafe_allow_html=True)
    with col_d:
        st.markdown("""
        <div class="card">
        <h4>📊 Quality Scoring — 5 Dimensions</h4>
        <p style="margin-bottom:8px;">Every optimized prompt is scored out of <b>100</b> across:</p>
        <div class="pipeline-step">🔵 <b>Clarity (25%)</b> — sentence structure, readability, action words</div>
        <div class="pipeline-step">🟢 <b>Specificity (25%)</b> — detail level, numbers, technical terms</div>
        <div class="pipeline-step">🟡 <b>Completeness (20%)</b> — role, context, task, output hints</div>
        <div class="pipeline-step">🟠 <b>Context (15%)</b> — domain vocabulary, background info</div>
        <div class="pipeline-step">🔴 <b>Actionability (15%)</b> — clear deliverable, action verb, outcome</div>
        <br>
        <p style="margin:0;">Grade scale: <b>A</b> ≥85 · <b>B</b> ≥70 · <b>C</b> ≥55 · <b>D</b> ≥40 · <b>F</b> &lt;40</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── How to use ──
    st.markdown("#### 🚀 How to Use")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.markdown("""
        <div class="card" style="text-align:center;">
        <span class="step-num">1</span><b>Pick a Target LLM</b>
        <p>Select Claude, ChatGPT, Gemini, or DeepSeek from the sidebar.</p>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown("""
        <div class="card" style="text-align:center;">
        <span class="step-num">2</span><b>Type Your Prompt</b>
        <p>Enter any rough prompt or question in the input box below.</p>
        </div>
        """, unsafe_allow_html=True)
    with h3:
        st.markdown("""
        <div class="card" style="text-align:center;">
        <span class="step-num">3</span><b>Click Optimize</b>
        <p>IntelliPrompt runs <b>AMPOA</b> (Adaptive Multi-stage Prompt Optimization Algorithm) + <b>MAPT</b> (Model-Adaptive Prompt Translation) and returns the optimized result.</p>
        </div>
        """, unsafe_allow_html=True)
    with h4:
        st.markdown("""
        <div class="card" style="text-align:center;">
        <span class="step-num">4</span><b>Copy &amp; Use</b>
        <p>Copy the adapted prompt and paste it directly into your chosen LLM.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Example prompts ──
    st.markdown("#### 💡 Try These Example Prompts")
    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        st.info("**Technology**\n\nexplain how neural networks work")
    with ex2:
        st.info("**Business**\n\nwrite a marketing strategy for a startup")
    with ex3:
        st.info("**Debug**\n\nmy python code gives index out of range error")

    st.markdown("---")
else:
    for msg in st.session_state.messages:
        st.markdown(f'<div class="chat-label" style="text-align:right">You</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="user-bubble">{msg["original_prompt"]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="chat-label">IntelliPrompt → {msg["target_llm"].upper()}</div>', unsafe_allow_html=True)

        with st.container():
            tab1, tab2, tab3 = st.tabs(["🌐 Universal Prompt", f"🎯 {msg['target_llm'].title()} Adapted", "📊 Quality Score"])

            with tab1:
                st.code(msg["universal_prompt"], language=None)
                with st.expander("🔍 AMPOA Pipeline Details"):
                    stages = msg.get("ampoa_stages", {})
                    cols = st.columns(3)
                    cols[0].metric("Intent", stages.get("intent", "—"))
                    cols[1].metric("Domain", stages.get("domain", "—"))
                    cols[2].metric("Entities", str(len(stages.get("entities", []))))
                    if stages.get("entities"):
                        st.caption("Extracted: " + ", ".join(stages["entities"][:10]))

            with tab2:
                st.code(msg["adapted_prompt"], language=None)

            with tab3:
                breakdown = msg.get("quality_breakdown", {})
                score = breakdown.get("score", 0)
                grade = breakdown.get("grade", "—")

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("Overall Score", f"{score:.1f}/100")
                    st.markdown(f'<span class="score-badge">Grade: {grade}</span>', unsafe_allow_html=True)
                with col2:
                    dims = ["clarity", "specificity", "completeness", "context", "actionability"]
                    for dim in dims:
                        val = breakdown.get(dim, 0)
                        st.caption(f"{dim.title()}: {val:.1f}/10")
                        st.progress(val / 10)

        st.divider()

# ── Input area ───────────────────────────────────────────────────────────────
st.markdown("### 💬 Enter your prompt")
with st.form("prompt_form", clear_on_submit=True):
    user_input = st.text_area(
        "Your prompt:",
        placeholder="e.g. explain how transformers work in simple terms",
        height=100,
        label_visibility="collapsed",
    )
    col1, col2 = st.columns([5, 1])
    with col2:
        submitted = st.form_submit_button("✨ Optimize", use_container_width=True, type="primary")

if submitted and user_input.strip():
    with st.spinner(f"Optimizing for {selected_label}..."):
        try:
            result = optimize_prompt(user_input.strip(), target_llm)
            st.session_state.messages.append({
                "original_prompt": result["original_prompt"],
                "universal_prompt": result["universal_prompt"],
                "adapted_prompt": result["adapted_prompt"],
                "target_llm": result["target_llm"],
                "quality_breakdown": result["quality_breakdown"],
                "ampoa_stages": result.get("ampoa_stages", {}),
            })
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}. Is the backend running? `uvicorn backend.main:app --reload`")
elif submitted:
    st.warning("Please enter a prompt.")
