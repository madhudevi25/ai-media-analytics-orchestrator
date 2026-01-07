canned_code = r'''
import pandas as pd
from .engine import profile_data, get_numeric_columns, safe_groupby_summary

def report_data_overview(df: pd.DataFrame) -> dict:
    """
    Canned Report 1: Dataset Overview & Quality

    Output:
      - dict with profile, top missing columns, numeric column list
    """
    prof = profile_data(df)
    missing_sorted = sorted(prof["missing_by_column"].items(), key=lambda x: x[1], reverse=True)
    top_missing = missing_sorted[:10]

    return {
        "profile": {
            "rows": prof["rows"],
            "columns": prof["columns"],
            "duplicate_rows": prof["duplicate_rows"],
        },
        "top_missing_columns": top_missing,
        "numeric_columns": get_numeric_columns(df),
        "all_columns": prof["column_names"],
    }


def _candidate_dimension_columns(df: pd.DataFrame, max_unique: int = 25) -> list:
    """
    Heuristic:
      - picks object/category columns with <= max_unique unique values
      - these are good candidates for group-by summaries in dashboards
    """
    dim_cols = []
    for c in df.columns:
        if str(df[c].dtype) in ["object", "category"]:
            nunique = df[c].nunique(dropna=True)
            if nunique > 1 and nunique <= max_unique:
                dim_cols.append((c, int(nunique)))
    # Sort by uniqueness (lower first)
    dim_cols.sort(key=lambda x: x[1])
    return [c for c, _ in dim_cols]


def report_top_groupby_summaries(df: pd.DataFrame) -> dict:
    """
    Canned Report 2: Auto Group-by Summaries

    Output:
      - dict with chosen dimension columns and summary tables (first few)
    """
    dim_cols = _candidate_dimension_columns(df, max_unique=25)
    if len(dim_cols) == 0:
        return {
            "message": "No suitable categorical columns found for group-by summaries.",
            "dimension_candidates": [],
            "summaries": {}
        }

    # Generate summaries for up to 3 dimension columns to keep output manageable
    chosen = dim_cols[:3]
    summaries = {}
    for col in chosen:
        summaries[col] = safe_groupby_summary(df, col)

    return {
        "dimension_candidates": dim_cols,
        "chosen_dimensions": chosen,
        "summaries": summaries
    }
'''
with open("/content/project/app/analytics/canned_reports.py", "w") as f:
    f.write(canned_code)

print("Wrote: /content/project/app/analytics/canned_reports.py")

