"""Level configuration loaded from the assets state_config.yaml file."""

import re
from pathlib import Path
from typing import Optional, TypedDict

import yaml

from robot_navigation.config.settings import ASSETS_DIR, STATE_CONFIG_PATH


class LevelConfig(TypedDict):
    level: int
    file_name: str
    jff_path: str
    start: str
    goal: str
    rows: int
    cols: int
    obstacles: list[str]
    trap_state: str
    title: str
    description: str


_STATE_PATTERN = re.compile(r"^q(\d)(\d)$")


def load_levels(config_path: Path = STATE_CONFIG_PATH) -> dict[int, LevelConfig]:
    """Load and validate level metadata and its referenced JFLAP files."""
    with config_path.open(encoding="utf-8") as config_file:
        raw_config = yaml.safe_load(config_file)

    raw_levels = raw_config.get("levels") if isinstance(raw_config, dict) else None
    if not isinstance(raw_levels, dict) or not raw_levels:
        raise ValueError(f"'{config_path}' must define a non-empty levels mapping.")

    levels: dict[int, LevelConfig] = {}
    for level_id, raw_level in raw_levels.items():
        try:
            level_number = int(level_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Level identifier '{level_id}' must be an integer.") from exc
        if level_number < 1 or level_number in levels:
            raise ValueError(f"Level identifier '{level_id}' must be a unique positive integer.")
        if not isinstance(raw_level, dict):
            raise ValueError(f"Level {level_number} must be a mapping.")

        required = (
            "file_name", "start_state", "end_state", "num_grid_rows",
            "num_grid_cols", "num_obstacles", "obstacle_states",
            "trap_state", "title", "description",
        )
        missing = [field for field in required if field not in raw_level]
        if missing:
            raise ValueError(f"Level {level_number} is missing: {', '.join(missing)}.")

        file_name = raw_level["file_name"]
        if not isinstance(file_name, str) or not file_name:
            raise ValueError(f"Level {level_number} file_name must be a non-empty string.")
        if Path(file_name).name != file_name:
            raise ValueError(f"Level {level_number} file_name must be a filename, not a path.")
        jff_dir = (ASSETS_DIR / "dfa").resolve()
        jff_path = (jff_dir / file_name).resolve()
        if not jff_path.is_relative_to(jff_dir):
            raise ValueError(f"Level {level_number} file_name must point inside assets/dfa.")
        if not jff_path.is_file():
            raise FileNotFoundError(f"JFLAP file for level {level_number} not found: {jff_path}")

        obstacles = raw_level["obstacle_states"]
        if not isinstance(obstacles, list) or not all(isinstance(item, str) for item in obstacles):
            raise ValueError(f"Level {level_number} obstacle_states must be a list of state names.")
        if len(obstacles) != len(set(obstacles)):
            raise ValueError(f"Level {level_number} obstacle_states must be unique.")
        if raw_level["num_obstacles"] != len(obstacles):
            raise ValueError(f"Level {level_number} num_obstacles does not match obstacle_states.")
        if not isinstance(raw_level["num_obstacles"], int) or isinstance(raw_level["num_obstacles"], bool):
            raise ValueError(f"Level {level_number} num_obstacles must be an integer.")
        for field in ("title", "description"):
            if not isinstance(raw_level[field], str) or not raw_level[field].strip():
                raise ValueError(f"Level {level_number} {field} must be a non-empty string.")

        config: LevelConfig = {
            "level": level_number,
            "file_name": file_name,
            "jff_path": str(jff_path),
            "start": raw_level["start_state"],
            "goal": raw_level["end_state"],
            "rows": raw_level["num_grid_rows"],
            "cols": raw_level["num_grid_cols"],
            "obstacles": obstacles,
            "trap_state": raw_level["trap_state"],
            "title": raw_level["title"],
            "description": raw_level["description"],
        }
        validate_level(config)
        levels[level_number] = config
    return levels


def state_to_position(state: str) -> Optional[tuple[int, int]]:
    """Convert a grid state such as q12 to its row and column."""
    if not isinstance(state, str):
        return None
    match = _STATE_PATTERN.fullmatch(state)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def position_to_state(row: int, col: int) -> str:
    """Convert a row and column to its grid state name."""
    return f"q{row}{col}"


def validate_level(config: LevelConfig) -> None:
    """Sanity-check a level definition; raises ValueError if inconsistent."""
    rows, cols = config["rows"], config["cols"]
    if (
        not isinstance(rows, int) or isinstance(rows, bool)
        or not isinstance(cols, int) or isinstance(cols, bool)
        or not (1 <= rows <= 10 and 1 <= cols <= 10)
    ):
        raise ValueError("Grid dimensions must be integers between 1 and 10.")

    def in_grid(state: str) -> bool:
        pos = state_to_position(state)
        return pos is not None and 0 <= pos[0] < rows and 0 <= pos[1] < cols

    for key in ("start", "goal"):
        state = config[key]
        if not isinstance(state, str) or not in_grid(state):
            raise ValueError(f"{key} state '{state}' is outside the {rows}x{cols} grid.")
    for obstacle in config["obstacles"]:
        if not in_grid(obstacle):
            raise ValueError(f"Obstacle '{obstacle}' is outside the {rows}x{cols} grid.")
    if config["start"] in config["obstacles"] or config["goal"] in config["obstacles"]:
        raise ValueError("Start and goal cells cannot be obstacles.")
    if config["start"] == config["goal"]:
        raise ValueError("Start and goal must be different cells.")
    if not isinstance(config["trap_state"], str) or not config["trap_state"]:
        raise ValueError("trap_state must be a non-empty state name.")
    if config["trap_state"] in (config["start"], config["goal"], *config["obstacles"]):
        raise ValueError("The trap state cannot be a grid state.")


LEVELS = load_levels()
