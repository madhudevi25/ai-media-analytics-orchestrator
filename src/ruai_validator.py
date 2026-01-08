from src.llm_client import chat

def ruai_check(
    user_prompt: str,
    tool_choice: dict,
    computed_summary: str,
    model: str
) -> dict:
    """
    Input:
      - user_prompt: what user asked
      - tool_choice: what orchestrator chose (tool + args)
      - computed_summary: short text summary of computed results (not raw data dump)
      - model: validator model id

    Process:
      - validator checks: grounding, clarity, limitations, fairness considerations
      - returns a structured RUAI report

    Output:
      - dict with status + notes to display in UI
    """
    system = (
        "You are a Responsible Use AI (RUAI) validator.\n"
        "You check that the output is grounded in computed data, does not invent facts, "
        "and clearly states limitations. Return concise JSON only."
    )

    user = f"""
User prompt:
{user_prompt}

Tool choice:
{tool_choice}

Computed results summary (from Pandas):
{computed_summary}

Return JSON with:
- grounded: true/false
- issues: list of strings
- limitations: list of strings
- fairness_notes: list of strings
"""
    raw = chat(model=model, system=system, user=user)

    # Best effort parse; if fail, return a conservative message
    import json
    try:
        return json.loads(raw)
    except Exception:
        return {
            "grounded": False,
            "issues": ["Validator returned non-JSON; treat output cautiously."],
            "limitations": ["Could not validate reliably due to validator formatting error."],
            "fairness_notes": ["No fairness validation performed."]
        }

