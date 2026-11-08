from typing import TypedDict


class LevelConfig(TypedDict):
    rows: int
    cols: int
    start: str
    goal: str
    obstacles: list[str]


LEVELS: dict[int, LevelConfig] = {

    # TODO (PAVITHRA):
    # Define actual levels.
    #
    # Required:
    # - Grid dimensions.
    # - Starting position.
    # - Destination position.
    # - Obstacle positions.
    #
    # IMPORTANT:
    # Every position must correspond to a valid
    # state in the JFLAP DFA.
}
