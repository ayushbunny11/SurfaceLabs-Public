import re

def check_only_script_tag(v):
    pattern = re.compile(r'(?i)<\s*/?\s*script\b[^>]*>')

    if isinstance(v, list):
        return [check_only_script_tag(item) for item in v]

    if isinstance(v, dict):
        return {k: check_only_script_tag(val) for k, val in v.items()}

    if isinstance(v, str):
        if pattern.search(v):
            raise ValueError("Invalid syntax -> script")
        return v

    return v
