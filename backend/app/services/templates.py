import re


def render_template(content: str, variables: dict[str, str]) -> str:
    def replace(match: re.Match) -> str:
        key = match.group(1).strip()
        if key not in variables:
            raise ValueError(f"Missing value for variable: {{{{{key}}}}}")
        return variables[key]

    return re.sub(r"\{\{(.*?)\}\}", replace, content)