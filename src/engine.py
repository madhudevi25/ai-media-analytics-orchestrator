#--------------------------------------------------------------------------------------
#Step 4C — Create the Analytics Engine module (single source of truth)

#Input: none
#Process: writes engine.py
#Expected output: Wrote: /content/project/app/analytics/engine.py

#----------------------------------------------------------------------------------------

engine_code = r'''
import pandas as pd

def load_data(csv_path: str) -> pd.DataFrame:
    """
    Input:
      - csv_path: path to impactanalysis.csv

    Process:
      - reads CSV exactly as-is into a DataFrame
      - does NOT rename columns

    Output:
      - pandas DataFrame
    """
    df = pd.read_csv(csv_path)
    return df


def profile_data(df: pd.DataFrame) -> dict:
    """
    Input:
      - df: pandas DataFrame

    Process:
      - calculates a lightweight profile used for transparency and RUAI validation

    Output:
      - dict with row/col counts, column names, missing counts, duplicate rows
    """
    missing_by_col = df.isna().sum().sort_values(ascending=False).to_dict()
    dup_rows = int(df.duplicated().sum())

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "missing_by_column": missing_by_col,
        "duplicate_rows": dup_rows,
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
    }


def get_numeric_columns(df: pd.DataFrame) -> list:
    """
    Returns:
      - list of numeric columns (int/float) for safe aggregations
    """
    return list(df.select_dtypes(include=["number"]).columns)


def safe_groupby_summary(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """
    Input:
      - df: data
      - group_col: a column name chosen by the user or a canned report

    Process:
      - groups by group_col
      - summarizes numeric columns using mean, median, min, max, count
      - avoids making up any metric definitions; uses raw numeric columns only

    Output:
      - summary table DataFrame
    """
    if group_col not in df.columns:
        raise ValueError(f"Column not found: {group_col}")

    num_cols = get_numeric_columns(df)
    if len(num_cols) == 0:
        raise ValueError("No numeric columns found to summarize.")

    grouped = df.groupby(group_col)[num_cols].agg(["count", "mean", "median", "min", "max"])
    # Flatten multi-index columns for easier UI display
    grouped.columns = [f"{c0}__{c1}" for (c0, c1) in grouped.columns]
    grouped = grouped.reset_index()

    return grouped
'''
with open("/content/project/app/analytics/engine.py", "w") as f:
    f.write(engine_code)

print("Wrote: /content/project/app/analytics/engine.py")
