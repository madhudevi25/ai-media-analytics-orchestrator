import streamlit as st
import pandas as pd

# Import your deterministic analytics modules (from Step 4)
from src.engine import load_data
from src.canned_reports import report_data_overview, report_top_groupby_summaries
from src.orchestrator import route_prompt
from src.llm_client import chat
from src.ruai_validator import ruai_check

# ----------------------------
# App config
# ----------------------------
st.set_page_config(page_title="AI Media Analytics Orchestrator", layout="wide")
st.title("AI Media Analytics Orchestrator")
st.caption("Canned reports + prompt-based analysis with RUAI validation (no hallucinated metrics).")


# ----------------------------
# Sidebar: Model transparency + settings
# ----------------------------
st.sidebar.header("Transparency")

# You will set these later when you wire the LLM agents.
# For now we show placeholders so the UI always communicates model intent.
ORCHESTRATOR_MODEL = st.sidebar.text_input("Orchestrator model", value="gpt-4.1-mini")
NARRATIVE_MODEL = st.sidebar.text_input("Narrative model", value="gpt-5")
VALIDATOR_MODEL = st.sidebar.text_input("RUAI validator model", value="gpt-4.1-nano")

st.sidebar.write("**Models used (planned):**")
st.sidebar.write(f"- Orchestrator: `{ORCHESTRATOR_MODEL}`")
st.sidebar.write(f"- Narrative: `{NARRATIVE_MODEL}`")
st.sidebar.write(f"- Validator: `{VALIDATOR_MODEL}`")

st.sidebar.divider()
st.sidebar.write("**Data rule:** All charts/tables are computed from the CSV. LLM (when enabled) only explains results.")


# ----------------------------
# Data loading (safe + beginner-friendly)
# ----------------------------
st.subheader("1) Load dataset")

uploaded = st.file_uploader("Upload impactanalysis.csv", type=["csv"])

df = None
if uploaded is not None:
    # Input: uploaded file object
    # Process: read into Pandas (no column renames)
    # Output: df
    df = pd.read_csv(uploaded)
    st.success("Loaded dataset from uploaded file.")
else:
    # Local fallback: useful if running locally and you have the file
    local_path = "app/data/impactanalysis.csv"
    try:
        df = load_data(local_path)
        st.info("Loaded dataset from local path: app/data/impactanalysis.csv")
    except Exception:
        st.warning("Upload impactanalysis.csv to begin (recommended for public GitHub repos).")


if df is None:
    st.stop()


# ----------------------------
# Basic dataset preview (transparency)
# ----------------------------
with st.expander("Preview data (first 10 rows)"):
    st.write("Rows, Columns:", df.shape)
    st.dataframe(df.head(10), use_container_width=True)

with st.expander("Show column names (kept as-is)"):
    st.write(list(df.columns))


# ----------------------------
# Canned Reports
# ----------------------------
st.subheader("2) Canned reports")

col1, col2 = st.columns(2)

with col1:
    if st.button("Run Report 1: Dataset Overview & Quality"):
        overview = report_data_overview(df)
        st.write("### Report 1: Overview")
        st.json(overview)

with col2:
    if st.button("Run Report 2: Auto Group-by Summaries"):
        pack = report_top_groupby_summaries(df)
        st.write("### Report 2: Group-by Summaries")
        st.write("Dimension candidates:", pack.get("dimension_candidates", []))
        st.write("Chosen dimensions:", pack.get("chosen_dimensions", []))

        summaries = pack.get("summaries", {})
        if summaries:
            for dim, table in summaries.items():
                st.write(f"#### Summary by: {dim}")
                st.dataframe(table, use_container_width=True)
        else:
            st.info(pack.get("message", "No summaries generated."))


# ----------------------------
# Prompt-based Ad-hoc (LLM will be wired in Step 6)
# ----------------------------
st.subheader("3) Ad-hoc prompt (coming next)")

user_prompt = st.text_area(
    "Ask a question about this dataset (example: 'Show the biggest year-over-year change and explain why')",
    height=90
)

if st.button("Run ad-hoc prompt"):
    if not user_prompt.strip():
        st.warning("Type a prompt first.")
    else:
        # Step 5: We do NOT call the LLM yet (no secrets configured).
        # We show what will happen next, and keep the app functional.
        st.info("LLM is not wired yet. Next step will: route prompt → compute results → explain → RUAI validate.")
        st.write("Your prompt:")
        st.code(user_prompt)

        st.write("Planned pipeline:")
        st.markdown(
            "- Orchestrator: classify request (canned vs ad-hoc)\n"
            "- Analytics Engine: compute tables/charts from CSV\n"
            "- Narrative: explain insights based on computed results\n"
            "- RUAI Validator: grounding + fairness + limitations\n"
            "- UI: show results + ask if it matches expectations"
        )



