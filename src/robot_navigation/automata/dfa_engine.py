from typing import Optional, TypedDict
import networkx as nx


class TransitionResult(TypedDict):
    next_state: Optional[str]
    status: str
    message: str


class DFAEngine:

    def __init__(self, graph: nx.MultiDiGraph):
        """
        TODO (JIYA):

        Initialize the DFA execution engine.

        Required logic:
        1. Store the parsed DFA graph.
        2. Extract the initial state.
        3. Extract accepting states.
        4. Construct an efficient transition lookup structure.
        5. Identify the movement alphabet.
        """

        raise NotImplementedError(
            "DFA execution engine must be implemented by Jiya."
        )

    def process_movement(
        self,
        current_state: str,
        movement: str
    ) -> TransitionResult:
        """
        TODO (JIYA):

        Process one movement using the DFA.

        Required logic:

        1. Validate the movement symbol.
        2. Look up the transition corresponding to
           (current_state, movement).
        3. Determine the destination state.
        4. Identify whether the destination is:
           - A normal state.
           - The Crash state.
           - An accepting state.
        5. Return a structured result.

        Expected statuses:
        PLAYING
        CRASHED
        WON
        INVALID

        Do not silently change the current state.
        Return the destination state and let the
        game-state manager handle synchronization.
        """

        raise NotImplementedError(
            "Movement processing must be implemented by Jiya."
        )
