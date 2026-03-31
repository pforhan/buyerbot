import os
import logging

# Define logging levels
NONE = 0
BASIC = 1
FULL = 2

_level_map = {
    "none": NONE,
    "basic": BASIC,
    "full": FULL
}

_current_level = _level_map.get(os.environ.get("DEBUG_LEVEL", "none").lower(), NONE)

def log_basic(msg: str):
    if _current_level >= BASIC:
        print(f"[BASIC] {msg}")

def log_full(msg: str):
    if _current_level >= FULL:
        print(f"[FULL] {msg}")
