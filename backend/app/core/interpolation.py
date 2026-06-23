import re


def extract_variables(content: str) -> list[str]:
    """Extract all {{variable}} names from a prompt template."""
    pattern = r"\{\{(\w+)\}\}"
    return list(set(re.findall(pattern, content)))


def interpolate(content: str, variables: dict[str, str]) -> dict:
    """
    Replace {{variable}} placeholders with actual values.
    Returns the result and lists of found/missing variables.
    """
    found = extract_variables(content)
    missing = [v for v in found if v not in variables]
    result = content

    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", value)

    return {
        "result": result,
        "variables_found": found,
        "variables_missing": missing,
    }
