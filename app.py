# ============================================================
# AI MEDIA ANALYTICS ORCHESTRATOR
# Purpose: Evaluate where AI adds value in analytics workflows
# Mode: Option B (Kaggle auto-download at runtime)
# Secrets: Option 2 (Streamlit Secrets for Kaggle credentials)
# Repository: <your-github-username>/ai-media-analytics-orchestrator
# ============================================================

import os
import json
import glob
from pathlib import Path

import pandas as pd
import streamlit as st

DATASET_SLUG = "atharvasoundankar/impact-of-ai-on-digital-media-2020-2025"
CANONICAL_CSV_NAME = "impactanalysis.csv"

st.set_page_config(page_title="AI Media Analytics Orchestrator", layout="wide")


# ============================================================
# STEP 1: KAGGLE AUTH VIA STREAMLIT SECRETS
# Purpose:
# - Create ~/.kaggle/kaggle.json at runtime from Streamlit Secrets
# - Authenticate Kaggle downloads without committing secrets to GitHub
# ============================================================
def ensure_kaggle_auth():
    # Validate secrets exist (fail fast; prevents confusing errors later)
    if "kaggle" not in st.secrets:
        raise RuntimeError("Missing [kaggle] section in Streamlit secrets.")
    if "username" not in st.secrets["kaggle"] or "key" not in st.secrets["kaggle"]:
        raise RuntimeError("Missing kaggle.username or kaggle.key in Streamlit secrets.")

    kaggle_dir = Path.home() / ".kaggle"
    kaggle_dir.mkdir(parents=True, exist_ok=True)

    kaggle_json_path = kaggle_dir / "kaggle.json"
    kaggle_json = {
        "username": st.secrets["kaggle"]["username"],
        "key": st.secrets["kaggle"]["key"],
    }

    # Write runtime credentials file expected by Kaggle CLI/API
    kaggle_json_path.write_text(json.dumps(kaggle_json))

    # Kaggle expects restrictive permissions (600)
    try:
        os.chmod(kaggle_json_path, 0o600)
    except Exception:
        # Some environments restrict chmod; Streamlit Cloud typically allows it.
        pass


@st.cache_data(show_spinner=True)
def download_rename_load() -> pd.DataFrame:
    # ============================================================
    # STEP 2: DOWNLOAD + RENAME + LOAD (CANONICAL FILE)
    # Purpose:
    # - Download Kaggle dataset into temp folder
    # - Rename primary CSV to impactanalysis.csv
    # - Load CSV with column names unchanged (verbatim)
    # ============================================================

    ensure_kaggle_auth()

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()

    target_dir = Path("/tmp") / "kaggle_datasets" / DATASET_SLUG.replace("/", "__")
    target_dir.mkdir(parents=True, exist_ok=True)

    # Download and unzip dataset
    api.dataset_download_files(DATASET_SLUG, path=str(target_dir), unzip=True)

    # Find downloaded CSV(s)
    csv_files = sorted(target_dir.rglob("*.csv"))
    if not csv_files:
        raise RuntimeError(f"No CSV files found after download in: {target_dir}")

    # Rename the first CSV to canonical name for consistent downstream logic
    original_csv = csv_files[0]
    canonical_csv = target_dir / CANONICAL_CSV_NAME

    if original_csv.name != CANONICAL_CSV_NAME:
        # If canonical already exists from a previous run, remove it to avoid rename conflicts
        if canonical_csv.exists():
            canonical_csv.unlink()
        os.rename(original_csv, canonical_csv)

    # Load canonical CSV (no column renaming)
    df = pd.read_csv(canonical_csv)

    # Basic validation
    if df.shape[0] == 0 or df.shape[1] == 0:
        raise RuntimeError("Loaded dataset is empty (0 rows or 0 columns).")

    return df


def main():
    st.title("AI Media Analytics Orchestrator")

    with st.sidebar:
        st.subheader("Data Pipeline")
        st.caption("Option 2: Streamlit Secrets → Kaggle auth")
        st.caption("Option B: Download at runtime → rename to impactanalysis.csv")

        if st.button("Clear cache & re-download"):
            st.cache_data.clear()
            st.rerun()

    # Load data
    with st.spinner("Downloading dataset from Kaggle (cached after first run)..."):
        df = download_rename_load()

    # ============================================================
    # STEP 2.3: LOCK SCHEMA (DISPLAY AS-IS)
    # Purpose:
    # - Show schema exactly as it appears in the CSV
    # - Prevent hidden transformations and reduce hallucination risk
    # ============================================================
    st.subheader("Schema Lock (Columns used verbatim)")
    st.write(f"Rows: {df.shape[0]:,} | Columns: {df.shape[1]:,}")

    st.markdown("**Columns:**")
    st.code("\n".join(df.columns.tolist()))

    st.subheader("Data Preview")
    st.dataframe(df.head(50), use_container_width=True)


if __name__ == "__main__":
    main()

