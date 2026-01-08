##converts prompt → analysis spec
import json

def allowed_tools_schema(columns: list[str], numeric_columns: list[str]) -> dict:
    """
    Input:
      - columns: all dataset column names (as-is)
      - numeric_columns: numeric columns inferred from Pandas

    Process:
      - defines a small set of allowed operations for the orchestrator
      - prevents the LLM from inventing operations or columns

    Output:
      - dict describing allowed tools and their parameters
    """
    return {
        "tools": [
            {
                "name": "dataset_overview",
                "description": "Return dataset quality + schema overview (rows/cols, missingness top columns, numeric columns).",
                "parameters": {}
            },
            {
                "name": "groupby_summary",
                "description": "Group by ONE categorical column and compute summary stats over numeric columns.",
                "parameters": {
                    "group_col": {
                        "type": "string",
                        "allowed_values": columns
                    }
                }
            },
        ],
        "notes": {
            "rules": [
                "Never invent columns; choose only from allowed_values.",
                "Never invent numbers; analytics must be computed via Pandas.",
                "If user asks for something not supported, choose dataset_overview and explain limitation."
            ],
            "numeric_columns_detected": numeric_columns
        }
    }

def format_schema_for_prompt(schema: dict) -> str:
    """
    Converts schema dict to a compact JSON string for LLM context.
    """
    return json.dumps(schema, indent=2)

