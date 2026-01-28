# storage.py
import json
import os
from closet_model import Closet

DATA_DIR = "data"
CLOSET_FILE = os.path.join(DATA_DIR, "closet.json")

def load_closet() -> Closet:
    """Load closet from JSON, or return an empty closet if missing/corrupt."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(CLOSET_FILE):
        return Closet()

    try:
        with open(CLOSET_FILE, "r") as f:
            data = json.load(f)
        return Closet.from_dict(data)
    except (OSError, json.JSONDecodeError):
        # bad file -> start fresh
        return Closet()

def save_closet(closet: Closet) -> bool:
    """Save closet to JSON. Return True if success, False if error."""
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        with open(CLOSET_FILE, "w") as f:
            json.dump(closet.to_dict(), f, indent=4)
        return True
    except OSError:
        return False
