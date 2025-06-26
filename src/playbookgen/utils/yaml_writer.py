import os
import re
from typing import Optional


def extract_yaml_from_messages(message) -> Optional[str]:
    """Return YAML code block in assistant message."""
    pattern = re.compile(r"```yaml\n(.*?)```", re.DOTALL)
    match = pattern.search(message)
    if match:
        return match.group(1).strip()
    return None

def write_playbook_to_file(yaml_text: str, path: str) -> None:
    """Write provided YAML text to the given file path, creating directories."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w") as f:
        f.write(yaml_text)
