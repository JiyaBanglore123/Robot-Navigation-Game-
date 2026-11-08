"""
Game package.
Handles grid configurations, levels, and runtime game state management.
"""

from .grid_config import LevelConfig, LEVELS
from .game_state import GameState

__all__ = ["LevelConfig", "LEVELS", "GameState"]
