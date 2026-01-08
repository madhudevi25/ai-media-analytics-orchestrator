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
ORCHESTRATOR_MODEL = st.sidebar.text_input(
    "Orchestrator model",
    value=st.secrets.get("ORCHESTRATOR_MODEL", "gpt-4.1-mini")
)
NARRATIVE_MODEL = st.sidebar.text_input(
    "Narrative model",
    value=st.secrets.get("NARRATIVE_MODEL", "gpt-5")
)
VALIDATOR_MODEL = st.sidebar.text_input(
    "RUAI validator model",
    value=st.secrets.get("VALIDATOR_MODEL", "gpt-4.1-nano")
)

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
if st.button("Run ad-hoc prompt"):
    if not user_prompt.strip():
        st.warning("Type a prompt first.")
    else:
        # 1) Orchestrate: decide which tool to run (constrained to real columns)
        columns = list(df.columns)
        numeric_cols = get_numeric_columns(df)

        tool_choice = route_prompt(
            user_prompt=user_prompt,
            columns=columns,
            numeric_columns=numeric_cols,
            model=ORCHESTRATOR_MODEL
        )

        st.write("### Orchestrator decision (transparent)")
        st.json(tool_choice)

        # 2) Deterministic analytics (Pandas) - no hallucinated metrics
        tool = tool_choice.get("tool")
        args = tool_choice.get("args", {})

        computed_summary = ""
        result_table = None

        if tool == "dataset_overview":
            overview = report_data_overview(df)
            st.write("### Result: Dataset overview")
            st.json(overview)

            computed_summary = (
                f"Rows={overview['profile']['rows']}, Cols={overview['profile']['columns']}, "
                f"DuplicateRows={overview['profile']['duplicate_rows']}. "
                f"TopMissing={overview['top_missing_columns'][:3]}."
            )

        elif tool == "groupby_summary":
            group_col = args.get("group_col")
            if not group_col:
                st.warning("Orchestrator did not provide group_col; defaulting to dataset_overview.")
                overview = report_data_overview(df)
                st.json(overview)
                computed_summary = "Fallback to dataset overview due to missing group_col."
            else:
                result_table = safe_groupby_summary(df, group_col)
                st.write(f"### Result: Group-by summary for `{group_col}`")
                st.dataframe(result_table, use_container_width=True)

                computed_summary = (
                    f"Computed group-by summary for {group_col}. "
                    f"Returned {result_table.shape[0]} groups and {result_table.shape[1]} columns."
                )
        else:
            st.warning("Unsupported tool selected; defaulting to dataset_overview.")
            overview = report_data_overview(df)
            st.json(overview)
            computed_summary = "Fallback to dataset overview due to unsupported tool."

        # 3) Narrative: explain based on computed results only
        narrative_system = (
            "You are a data analyst. Explain insights only from the provided computed summary. "
            "Do NOT invent numbers. If the user asked for something not supported, explain limits."
        )
        narrative_user = f"""
User prompt:
{user_prompt}

Computed results summary:
{computed_summary}

Write:
1) What insight this provides
2) Why it matters
3) What limitations apply
4) Ask: 'Does this match what you expected?'
"""
        explanation = chat(model=NARRATIVE_MODEL, system=narrative_system, user=narrative_user)

        st.write("### Explanation")
        st.write(explanation)

        # 4) RUAI validation
        ruai = ruai_check(
            user_prompt=user_prompt,
            tool_choice=tool_choice,
            computed_summary=computed_summary,
            model=VALIDATOR_MODEL
        )

        st.write("### RUAI validation")
        st.json(ruai)

        # 5) User expectation confirmation (simple UI control)
        st.write("### Confirm")
        match = st.radio("Does this match your expectation?", ["Yes", "No"], horizontal=True)
        if match == "No":
            st.text_area("What did you expect instead? (This helps refine the prompt/router.)")




