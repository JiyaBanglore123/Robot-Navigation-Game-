from typing import Optional


class GameState:

    def __init__(self, level_config, dfa_engine):
        """
        TODO (PAVITHRA):

        Initialize a game session.

        Required logic:

        1. Store the selected level configuration.
        2. Store the DFA engine reference.
        3. Initialize the current state.
        4. Initialize the move counter.
        5. Initialize the game status.
        6. Maintain synchronization between the
           robot's DFA state and its grid position.
        """

        raise NotImplementedError(
            "Game-state initialization must be implemented by Pavithra."
        )

    def move(self, direction: str):
        """
        TODO (PAVITHRA):

        Coordinate one movement operation.

        Required logic:

        1. Reject movements if the game is already over.
        2. Call the DFA engine.
        3. Process its result.
        4. Update the current state when appropriate.
        5. Update the move counter.
        6. Synchronize the logical state with the grid.
        7. Update the game status.
        8. Return the updated game state.

        Do not independently implement DFA transitions.
        """

        raise NotImplementedError(
            "Game movement coordination must be implemented by Pavithra."
        )

    def reset(self):
        """
        TODO (PAVITHRA):

        Restore the game to its initial configuration.

        Reset:
        - Current state.
        - Game status.
        - Move counter.
        - Any session-specific navigation information.
        """

        raise NotImplementedError(
            "Game reset logic must be implemented by Pavithra."
        )

    def get_state(self) -> dict:
        """
        TODO (PAVITHRA):

        Return a serializable representation of the
        current game session.

        Include:
        - Current DFA state.
        - Robot position.
        - Game status.
        - Move counter.
        - Goal position.
        - Obstacle positions.
        """

        raise NotImplementedError(
            "Game-state serialization must be implemented by Pavithra."
        )
