import json

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Forge — AI Software Engineering Team",
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _api_get(path: str, timeout: int = 15) -> dict | list:
    response = requests.get(f"{API_URL}{path}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def _api_post(path: str, timeout: int = 30) -> requests.Response:
    response = requests.post(f"{API_URL}{path}", timeout=timeout)
    response.raise_for_status()
    return response


try:
    backend_health = _api_get("/health", timeout=3)
    backend_online = True
except requests.RequestException:
    backend_health = {}
    backend_online = False

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { background:#080B12; color:#F5F7FA; font-family:'Inter',sans-serif; }
    [data-testid="stHeader"] { background:rgba(8,11,18,0.82); }
    [data-testid="stToolbar"] { display:none; }
    .block-container { max-width:1420px; padding-top:2rem; padding-bottom:3rem; }
    [data-testid="stSidebar"] { background:#101522; border-right:1px solid #283148; }
    [data-testid="stSidebar"] * { color:#C7CEDB !important; }
    .forge-hero { padding:36px 32px; border:1px solid #283148; border-radius:18px;
        background: radial-gradient(circle at top right, rgba(53,208,186,0.15), transparent 60%),
        linear-gradient(120deg,#141C30 0%,#101522 100%); margin-bottom:24px; }
    .forge-brand-row { display:flex; align-items:center; gap:14px; margin-bottom:8px; }
    .forge-logo { font-size:44px; line-height:1; }
    .forge-title { font-size:38px; font-weight:800; letter-spacing:-0.5px;
        background:linear-gradient(90deg,#F5F7FA 0%,#35D0BA 100%);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .forge-tagline { font-size:16px; color:#9FB0C8; font-weight:500; margin-top:4px; }
    .forge-tagline strong { color:#35D0BA; font-weight:700; }
    .forge-pipeline { display:flex; flex-wrap:wrap; gap:10px; margin-top:22px; padding-top:22px;
        border-top:1px solid #283148; }
    .forge-step { flex:1 1 auto; min-width:120px; padding:12px 14px; border:1px solid #283148;
        border-radius:10px; background:rgba(20,28,48,0.6); }
    .forge-step .num { font-size:11px; color:#35D0BA; font-weight:700; letter-spacing:1px; }
    .forge-step .name { font-size:14px; font-weight:600; color:#F5F7FA; margin-top:2px; }
    .forge-step .role { font-size:11px; color:#7C8AA0; margin-top:2px; }
    .forge-arrow { color:#35D0BA; font-size:18px; align-self:center; }
    div.stButton > button { background:#35D0BA !important; color:#080B12 !important;
        font-weight:700; border:0 !important; border-radius:9px; min-height:44px; }
    div.stButton > button:hover { background:#58E2CF !important; color:#080B12 !important;
        border:0 !important; }
    .forge-card { padding:18px; border:1px solid #283148; border-radius:12px;
        background:rgba(16,21,34,0.6); margin-bottom:12px; }
    .forge-metric { font-size:42px; font-weight:800; color:#35D0BA; }
    .forge-telbar { display:flex; gap:24px; padding:14px 18px; border:1px solid #283148;
        border-radius:12px; background:rgba(16,21,34,0.6); margin-bottom:16px; }
    .forge-telbar .label { font-size:11px; color:#7C8AA0; letter-spacing:1px; }
    .forge-telbar .value { font-size:22px; font-weight:700; color:#F5F7FA; }
    .forge-telbar .value.cost { color:#35D0BA; }
    .forge-log { padding:14px; border:1px solid #283148; border-radius:10px;
        background:#05080E; color:#9FE8DA; font-family:monospace; font-size:13px;
        max-height:300px; overflow:auto; white-space:pre-wrap; }
    .forge-foot { margin-top:28px; padding-top:16px; border-top:1px solid #283148;
        color:#7C8AA0; font-size:12px; text-align:center; }
    .forge-status { display:flex; align-items:center; gap:10px; margin-bottom:18px;
        color:#9FB0C8; font-size:12px; }
    .forge-status .dot { width:8px; height:8px; border-radius:50%;
        background:#FF5C5C; box-shadow:0 0 12px rgba(255,92,92,.7); }
    .forge-status .dot.online { background:#35D0BA; box-shadow:0 0 12px rgba(53,208,186,.7); }
    .forge-status strong { color:#F5F7FA; }
    .forge-kicker { color:#35D0BA; font-size:11px; font-weight:700;
        letter-spacing:1.6px; text-transform:uppercase; margin-bottom:8px; }
    div[data-testid="stForm"] { border:1px solid #283148; border-radius:16px;
        background:linear-gradient(145deg,rgba(20,28,48,.85),rgba(16,21,34,.72));
        padding:22px; }
    div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input {
        background:#0B101B; border-color:#33415C; color:#F5F7FA; }
    div[data-testid="stTextArea"] textarea:focus, div[data-testid="stTextInput"] input:focus {
        border-color:#35D0BA; box-shadow:0 0 0 1px #35D0BA; }
    </style>
    """,
    unsafe_allow_html=True,
)

status_class = "online" if backend_online else ""
status_text = "Backend connected" if backend_online else "Backend unavailable"
feature_count = len(backend_health.get("features", {})) if backend_online else 0
st.markdown(
    f"<div class='forge-status'><span class='dot {status_class}'></span>"
    f"<strong>{status_text}</strong>"
    f"<span>· API {API_URL} · {feature_count} services enabled</span></div>",
    unsafe_allow_html=True,
)

# ---- HERO ----
st.markdown(
    """
    <div class='forge-hero'>
      <div class='forge-brand-row'>
        <div class='forge-logo'>🔨</div>
        <div>
          <div class='forge-kicker'>AI engineering command center</div>
          <div class='forge-title'>Forge</div>
          <div class='forge-tagline'>A multi-agent AI software engineering team that
            <strong>plans, builds, tests, and reviews</strong> your code.</div>
        </div>
      </div>
      <div class='forge-pipeline'>
        <div class='forge-step'><div class='num'>01</div><div class='name'>Product Manager</div>
          <div class='role'>Plans</div></div>
        <div class='forge-arrow'>→</div>
        <div class='forge-step'><div class='num'>02</div><div class='name'>Architect</div>
          <div class='role'>Designs</div></div>
        <div class='forge-arrow'>→</div>
        <div class='forge-step'><div class='num'>03</div><div class='name'>Developer</div>
          <div class='role'>Builds</div></div>
        <div class='forge-arrow'>→</div>
        <div class='forge-step'><div class='num'>04</div><div class='name'>QA Engineer</div>
          <div class='role'>Tests</div></div>
        <div class='forge-arrow'>→</div>
        <div class='forge-step'><div class='num'>05</div><div class='name'>Reviewer</div>
          <div class='role'>Audits</div></div>
        <div class='forge-arrow'>⟳</div>
        <div class='forge-step'><div class='num'>+</div><div class='name'>Repair Loop</div>
          <div class='role'>Fixes</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def _telemetry_bar(tel: dict) -> str:
    return (
        "<div class='forge-telbar'>"
        f"<div><div class='label'>INPUT TOKENS</div>"
        f"<div class='value'>{tel.get('total_input_tokens', 0):,}</div></div>"
        f"<div><div class='label'>OUTPUT TOKENS</div>"
        f"<div class='value'>{tel.get('total_output_tokens', 0):,}</div></div>"
        f"<div><div class='label'>TOTAL</div>"
        f"<div class='value'>{tel.get('total_tokens', 0):,}</div></div>"
        f"<div><div class='label'>EST. COST</div>"
        f"<div class='value cost'>${tel.get('total_cost_usd', 0):.4f}</div></div>"
        "</div>"
    )


# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("### 📜 Project history")
    try:
        projects = _api_get("/projects", timeout=5)
        if projects:
            for p in projects:
                label = f"{p['project_name']} · {p['status']}"
                if st.button(label, key=p["id"], use_container_width=True):
                    st.session_state["selected_id"] = p["id"]
        else:
            st.info("No projects yet.")
    except Exception:
        st.warning("Backend not reachable. Start the API first.")
    st.markdown("---")
    st.markdown("### 🔎 RAG corpus")
    try:
        stats = _api_get("/rag/stats", timeout=5)
        st.caption(f"{stats.get('documents',0)} approved projects indexed")
        if st.button("Rebuild corpus", use_container_width=True):
            r = _api_post("/rag/rebuild", timeout=30)
            st.success(f"Indexed {r.json().get('documents',0)} documents")
    except Exception:
        st.warning("RAG endpoint unreachable")
    st.markdown("---")
    st.caption("Forge v2.0.0 · 7 features · powered by Groq")

# ---- REQUIREMENT FORM ----
st.markdown("### 📝 Submit a software requirement")

with st.form("requirement_form"):
    requirement = st.text_area(
        "Software requirement", height=150,
        value=("Build a Python document management application with PDF upload, "
               "text extraction, search, history, and unit tests."),
    )
    c1, c2 = st.columns(2)
    with c1:
        project_name = st.text_input("Project name", "Document Manager")
    with c2:
        preferred_language = st.text_input("Preferred language", "Python")
    additional = st.text_area("Additional context (optional)", height=50)
    fc1, fc2 = st.columns(2)
    with fc1:
        use_rag = st.checkbox("Use RAG over past projects", value=True)
    with fc2:
        use_repair = st.checkbox("Auto-repair loop (Dev→QA→fix)", value=True)
    submitted = st.form_submit_button("🔥 Run the five agents (live)", use_container_width=True)

# ---- LIVE STREAMING RUN ----
if submitted:
    payload = {
        "requirement": requirement,
        "project_name": project_name,
        "preferred_language": preferred_language,
        "additional_context": additional,
        "enable_rag": use_rag,
        "enable_repair_loop": use_repair,
    }
    st.markdown("#### 🔴 Live agent stream")
    log_box = st.empty()
    tel_box = st.empty()
    log_lines: list[str] = []
    telemetry = None
    final_event = None
    try:
        with requests.post(
            f"{API_URL}/generate/stream", json=payload, stream=True, timeout=600
        ) as resp:
            resp.raise_for_status()
            for raw in resp.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data: "):
                    continue
                ev = json.loads(raw[6:])
                t = ev.get("type")
                if t == "stage_start":
                    log_lines.append(f"▶ [{ev['stage']}] {ev['agent']} running…")
                elif t == "stage_end":
                    u = ev.get("usage", {})
                    tok = u.get("input_tokens", 0) + u.get("output_tokens", 0)
                    log_lines.append(f"✓ [{ev['stage']}] done · {tok} tokens")
                elif t == "repair_start":
                    log_lines.append(
                        f"🔧 repair iter {ev['iteration']} "
                        f"(score {ev['score_before']} → target)"
                    )
                elif t == "repair_end":
                    arrow = "↑" if ev.get("improved") else "→"
                    log_lines.append(
                        f"🔧 repair iter {ev['iteration']} done: "
                        f"{ev['score_before']}→{arrow}{ev['score_after']}"
                    )
                elif t == "telemetry":
                    telemetry = ev["telemetry"]
                elif t == "done":
                    final_event = ev
                    log_lines.append(
                        f"✅ done · project {ev['project_id']} · "
                        f"{ev.get('iterations',0)} repairs · final score {ev.get('final_score')}"
                    )
                elif t == "error":
                    log_lines.append(f"❌ ERROR: {ev.get('detail')}")
                log_box.markdown(
                    "<div class='forge-log'>" + "\n".join(log_lines[-20:]) + "</div>",
                    unsafe_allow_html=True,
                )
                if telemetry:
                    tel_box.markdown(_telemetry_bar(telemetry), unsafe_allow_html=True)
        if final_event:
            detail = _api_get(f"/projects/{final_event['project_id']}", timeout=15)
            st.session_state["current"] = detail
            st.success("Agents finished. Full results below.")
    except Exception as e:
        st.error(f"Stream failed: {e}")

# ---- LOAD SELECTED FROM HISTORY ----
if "selected_id" in st.session_state:
    try:
        detail = _api_get(f"/projects/{st.session_state['selected_id']}", timeout=10)
        st.session_state["current"] = detail
    except Exception as e:
        st.warning(f"Could not load project: {e}")

# ---- RESULTS ----
if "current" in st.session_state:
    data = st.session_state["current"]
    pid = data["project_id"]
    result = data["result"]
    telemetry = result.get("telemetry")
    iterations = result.get("iterations", [])
    rag_ctx = result.get("rag_context", [])

    st.markdown(
        f"<div class='forge-card'>Project ID <code>{pid}</code> · status "
        f"<strong style='color:#35D0BA'>{data.get('status','')}</strong>"
        f"{f' · {len(iterations)} repair iteration(s)' if iterations else ''}</div>",
        unsafe_allow_html=True,
    )

    if telemetry:
        st.markdown(_telemetry_bar(telemetry), unsafe_allow_html=True)

    tabs = st.tabs([
        "📋 Plan", "🏗️ Architecture", "💻 Code", "🧪 QA", "🔒 Review",
        "🔧 Repair", "📊 Telemetry", "🔁 Diff", "🔎 RAG",
    ])

    with tabs[0]:
        plan = result.get("plan", {})
        st.markdown(f"#### {plan.get('project_title','Untitled')}")
        st.markdown(plan.get("problem_statement", ""))
        for label, key in [("Objectives", "objectives"), ("Features", "features"),
                           ("Assumptions", "assumptions"),
                           ("Development phases", "development_phases")]:
            items = plan.get(key, [])
            if items:
                st.markdown(f"**{label}**")
                for it in items:
                    st.markdown(f"- {it}")

    with tabs[1]:
        arch = result.get("architecture", {})
        st.markdown(f"#### {arch.get('overview','')}")
        st.markdown("**Technology stack:** " + ", ".join(arch.get("technology_stack", [])))
        st.markdown("**Components:**")
        for c in arch.get("components", []):
            st.markdown(f"- {c}")
        st.markdown("**Folder structure:**")
        for f in arch.get("folder_structure", []):
            st.code(f)
        st.markdown("**Security considerations:**")
        for s in arch.get("security_considerations", []):
            st.markdown(f"- {s}")

    with tabs[2]:
        code = result.get("code", {})
        st.markdown(f"#### {code.get('summary','')}")
        for f in code.get("files", []):
            with st.expander(f"📄 {f['path']}"):
                lang = "python" if f["path"].endswith(".py") else "text"
                st.code(f["content"], language=lang)
        st.markdown("**Setup instructions:**")
        st.code(code.get("setup_instructions", ""))

    with tabs[3]:
        qa = result.get("qa", {})
        st.markdown("#### Test strategy")
        st.markdown(qa.get("test_strategy", ""))
        for tc in qa.get("test_cases", []):
            with st.expander(f"✓ {tc.get('name','')}"):
                st.markdown(f"**Description:** {tc.get('description','')}")
                st.markdown(f"**Inputs:** `{tc.get('inputs','')}`")
                st.markdown(f"**Expected:** {tc.get('expected','')}")
        st.markdown("**Edge cases:**")
        for ec in qa.get("edge_cases", []):
            st.markdown(f"- {ec}")

    with tabs[4]:
        rv = result.get("review", {})
        st.markdown(
            "<div class='forge-card' style='text-align:center'>"
            "<div style='color:#9FB0C8;font-size:12px;letter-spacing:1px'>FINAL OVERALL SCORE</div>"
            f"<div class='forge-metric'>{rv.get('overall_score','—')}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(rv.get("summary", ""))
        for category, title in [("bugs", "🐞 Bugs"), ("security", "🛡️ Security"),
                                ("maintainability", "🔧 Maintainability")]:
            st.markdown(f"#### {title}")
            findings = rv.get(category, [])
            if not findings:
                st.info("No findings.")
            for f in findings:
                sev = f.get("severity", "?")
                color = {"critical": "#FF5C5C", "high": "#FFA94D",
                         "medium": "#FFD43B", "low": "#35D0BA"}.get(sev, "#9FB0C8")
                st.markdown(
                    f"<div class='forge-card'>"
                    f"<span style='color:{color};font-weight:700'>[{sev.upper()}]</span> "
                    f"<code>{f.get('file','?')}</code> · line {f.get('line','?')}<br>"
                    f"<strong>Issue:</strong> {f.get('issue','')}<br>"
                    f"<strong>Fix:</strong> <em>{f.get('recommendation','')}</em></div>",
                    unsafe_allow_html=True,
                )

    with tabs[5]:
        if not iterations:
            st.info(
                "No repair iterations were needed (score already met threshold, "
                "or loop disabled)."
            )
        else:
            st.markdown("**Score progression**")
            chart_data = {"iteration": [it["iteration"] for it in iterations],
                          "score": [it["score_after"] for it in iterations]}
            st.line_chart(chart_data, x="iteration", y="score")
            for it in iterations:
                with st.expander(
                    f"Iteration {it['iteration']}: {it['score_before']} → {it['score_after']} "
                    f"({'improved' if it['improved'] else 'no gain'})"
                ):
                    st.markdown(f"**Findings addressed:** {it.get('findings_addressed',0)}")
                    st.markdown(f"**QA summary:** {it.get('qa_summary','')}")
                    st.markdown(f"**Review summary:** {it.get('review_summary','')}")

    with tabs[6]:
        if not telemetry:
            st.info("No telemetry recorded.")
        else:
            st.markdown(_telemetry_bar(telemetry), unsafe_allow_html=True)
            st.markdown("#### Per-agent usage")
            rows = []
            for a in telemetry.get("agents", []):
                rows.append({
                    "Agent": a.get("agent"),
                    "Stage": a.get("stage"),
                    "Input": a.get("input_tokens", 0),
                    "Output": a.get("output_tokens", 0),
                    "Cost $": round(a.get("cost_usd", 0), 6),
                })
            st.dataframe(rows, use_container_width=True)

    with tabs[7]:
        st.markdown("#### Diff vs last approved snapshot")
        try:
            diff = _api_get(f"/projects/{pid}/diff", timeout=15)
            added = sum(1 for f in diff["files"] if f["status"] == "added")
            removed = sum(1 for f in diff["files"] if f["status"] == "removed")
            modified = sum(1 for f in diff["files"] if f["status"] == "modified")
            unchanged = sum(1 for f in diff["files"] if f["status"] == "unchanged")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Added", added)
            c2.metric("Removed", removed)
            c3.metric("Modified", modified)
            c4.metric("Unchanged", unchanged)
            st.caption(f"+{diff['total_additions']} / −{diff['total_deletions']} lines · "
                       f"base: {diff['base']} vs {diff['comparison']}")
            for f in diff["files"]:
                if f["status"] == "unchanged":
                    continue
                with st.expander(
                    f"{f['status'].upper()} · {f['path']} "
                    f"(+{f['additions']}/−{f['deletions']})"
                ):
                    st.code(f["patch"], language="diff")
        except Exception as e:
            st.warning(f"Could not load diff: {e}")

    with tabs[8]:
        if not rag_ctx:
            st.info("No RAG matches (RAG disabled, or no approved projects indexed yet).")
        else:
            st.markdown(f"#### {len(rag_ctx)} similar approved project(s) retrieved")
            for m in rag_ctx:
                with st.expander(f"{m['meta'].get('project_name','')} · score {m['score']}"):
                    st.caption(f"id: {m['doc_id']}")
                    st.write(m["snippet"])

    # ---- ACTION BUTTONS ----
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Approve & write files", use_container_width=True):
            try:
                out = _api_post(f"/projects/{pid}/approve", timeout=60).json()
                st.success("Approved! Files written to `generated_projects/`:")
                for w in out.get("written_files", []):
                    st.code(w)
            except Exception as e:
                st.error(f"Approve failed: {e}")
    with col2:
        if st.button("🐳 Run tests (Docker sandbox)", use_container_width=True):
            try:
                out = _api_post(
                    f"/projects/{pid}/test/sandbox", timeout=180
                ).json()
                st.code(out.get("stdout", "") or "(no stdout)")
                if out.get("stderr"):
                    st.code(out["stderr"])
                st.caption(f"returncode: {out.get('returncode')} · mode: {out.get('mode')}")
            except Exception as e:
                st.error(f"Sandbox test failed: {e}")
    with col3:
        if st.button("📤 Export to GitHub", use_container_width=True):
            try:
                out = _api_post(
                    f"/projects/{pid}/export/github", timeout=60
                ).json()
                if out.get("pushed"):
                    st.success(f"Pushed to {out['remote_url']}")
                elif out.get("remote_url"):
                    st.info(f"Repo created: {out['remote_url']} (push may have failed)")
                else:
                    st.success(
                        f"Local repo ready: {out['local_repo']} "
                        f"(commit {out['commit_sha'][:7]})"
                    )
                    st.caption("Set ENABLE_GITHUB_EXPORT=true and GITHUB_TOKEN to push remote.")
            except Exception as e:
                st.error(f"Export failed: {e}")

st.markdown(
    "<div class='forge-foot'>Forge v2.0.0 — plans, builds, tests, reviews, "
    "and repairs your code. 7 features: repair loop · telemetry · streaming · "
    "diff · GitHub export · Docker sandbox · RAG.</div>",
    unsafe_allow_html=True,
)
