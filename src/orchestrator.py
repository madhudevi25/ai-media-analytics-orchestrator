## routes user intent
import json
from src.llm_client import chat
from src.planner_agent import allowed_tools_schema, format_schema_for_prompt

def route_prompt(user_prompt: str, columns: list[str], numeric_columns: list[str], model: str) -> dict:
    """
    Input:
      - user_prompt: user's natural language request
      - columns/numeric_columns: real schema lists from Pandas
      - model: orchestrator model id

    Process:
      - asks LLM to choose a tool + parameters from a constrained schema

    Output:
      - dict like {"tool": "...", "args": {...}}
    """
    tool_schema = allowed_tools_schema(columns=columns, numeric_columns=numeric_columns)
    schema_text = format_schema_for_prompt(tool_schema)

    system = (
        "You are an orchestrator that routes the user's request to ONE allowed tool.\n"
        "Return ONLY valid JSON with keys: tool, args.\n"
        "Rules:\n"
        "- tool must be one of the allowed tools.\n"
        "- args must only contain allowed parameters.\n"
        "- do not include any extra keys.\n"
    )

    user = f"""User prompt:
{user_prompt}

Allowed tools schema (JSON):
{schema_text}

Return JSON only."""
    raw = chat(model=model, system=system, user=user)

    # Best-effort JSON parsing
    try:
        return json.loads(raw)
    except Exception:
        # Fallback: if model returns non-JSON, default safely
        return {"tool": "dataset_overview", "args": {}}
