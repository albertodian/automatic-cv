import json

def load_profile(path: str) -> dict:
    """Load the candidate profile from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
