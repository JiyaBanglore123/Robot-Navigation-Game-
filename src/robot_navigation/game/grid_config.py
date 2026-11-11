"""
Grid configuration for the DFA-based Robot Navigation Game.
Author: Pavithra S (Person 3)

Each level describes a rectangular grid whose cells correspond to states
of the JFLAP DFA (assets/robot_navigation_dfa.jff):

    cell (r, c)  <->  DFA state "q<r><c>"

Obstacle cells have no DFA state of their own; moving into one sends the
DFA to the trap state "Crash".
"""

import re
from typing import Optional, TypedDict


class LevelConfig(TypedDict):
    rows: int
    cols: int
    start: str
    goal: str
    obstacles: list[str]


# Name of the DFA trap state reached when the robot hits an obstacle.
CRASH_STATE = "Crash"

_STATE_PATTERN = re.compile(r"^q(\d)(\d)$")


LEVELS: dict[int, LevelConfig] = {
    # Level 1 — 4x4 grid matching the JFLAP DFA.
    #
    #        c0   c1   c2   c3
    #   r0 [ S ][   ][   ][   ]
    #   r1 [   ][ X ][   ][   ]
    #   r2 [   ][   ][ X ][   ]
    #   r3 [   ][ X ][   ][ G ]
    #
    # S = start (q00, initial state), G = goal (q33, accepting state),
    # X = obstacle (transition into Crash).
    # The 13 free cells are exactly the 13 non-Crash states in the .jff file.
    1: {
        "rows": 4,
        "cols": 4,
        "start": "q00",
        "goal": "q33",
        "obstacles": ["q11", "q22", "q31"],
    },
}


def state_to_position(state: str) -> Optional[tuple[int, int]]:
    """Convert a DFA state name like 'q12' to a grid position (1, 2).

    Returns None for states that are not grid cells (e.g. 'Crash').
    """
    if not isinstance(state, str):
        return None
    match = _STATE_PATTERN.match(state)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def position_to_state(row: int, col: int) -> str:
    """Convert a grid position (row, col) to its DFA state name 'q<row><col>'."""
    return f"q{row}{col}"


def validate_level(config: LevelConfig) -> None:
    """Sanity-check a level definition; raises ValueError if it is inconsistent."""
    rows, cols = config["rows"], config["cols"]
    if not (1 <= rows <= 10 and 1 <= cols <= 10):
        raise ValueError("Grid dimensions must be between 1 and 10 (single-digit state names).")

    def in_grid(state: str) -> bool:
        pos = state_to_position(state)
        return pos is not None and 0 <= pos[0] < rows and 0 <= pos[1] < cols

    for key in ("start", "goal"):
        if not in_grid(config[key]):
            raise ValueError(f"{key} state '{config[key]}' is outside the {rows}x{cols} grid.")
    for obstacle in config["obstacles"]:
        if not in_grid(obstacle):
            raise ValueError(f"Obstacle '{obstacle}' is outside the {rows}x{cols} grid.")
    if config["start"] in config["obstacles"] or config["goal"] in config["obstacles"]:
        raise ValueError("Start and goal cells cannot be obstacles.")
    if config["start"] == config["goal"]:
        raise ValueError("Start and goal must be different cells.")


for _level in LEVELS.values():
    validate_level(_level)
