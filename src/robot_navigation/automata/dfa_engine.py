from typing import Optional, TypedDict

import networkx as nx


class TransitionResult(TypedDict):
    next_state: Optional[str]
    status: str
    message: str


class DFAEngine:
    ALPHABET = frozenset({"U", "D", "L", "R"})
    CRASH_STATE = "Crash"

    def __init__(self, graph: nx.MultiDiGraph):
        if not isinstance(graph, nx.MultiDiGraph):
            raise TypeError("DFAEngine requires a NetworkX MultiDiGraph.")

        self.graph = graph
        self.alphabet = self.ALPHABET
        self.state_names: dict[str, str] = {}
        aliases: dict[str, str] = {}
        initial_states: list[str] = []
        self.accepting_states: set[str] = set()

        for node_id, data in graph.nodes(data=True):
            node_id = str(node_id)
            name = str(data.get("name", node_id))
            for alias in (node_id, name):
                existing = aliases.get(alias)
                if existing is not None and existing != name:
                    raise ValueError(f"Ambiguous DFA state identifier '{alias}'.")
                aliases[alias] = name
            self.state_names[node_id] = name
            if data.get("initial", False):
                initial_states.append(name)
            if data.get("final", False):
                self.accepting_states.add(name)

        initial_state = graph.graph.get("initial_state")
        if initial_state is not None:
            initial_state = aliases.get(str(initial_state))
        if initial_state is None:
            if len(initial_states) != 1:
                raise ValueError("DFA must have exactly one initial state.")
            initial_state = initial_states[0]
        self.initial_state = initial_state

        final_state_ids = graph.graph.get("final_states", set())
        for state_id in final_state_ids:
            final_state = aliases.get(str(state_id))
            if final_state is None:
                raise ValueError(f"Unknown accepting DFA state '{state_id}'.")
            self.accepting_states.add(final_state)

        self.transition_table: dict[tuple[str, str], str] = {}
        for source_id, target_id, data in graph.edges(data=True):
            symbol = data.get("symbol")
            if symbol not in self.ALPHABET:
                raise ValueError(f"Unsupported DFA movement symbol '{symbol}'.")

            source = self.state_names[str(source_id)]
            target = self.state_names[str(target_id)]
            key = (source, symbol)
            if key in self.transition_table:
                raise ValueError(
                    f"Nondeterministic transition from {source} on {symbol}."
                )
            self.transition_table[key] = target

        self._state_aliases = aliases

    def process_movement(
        self,
        current_state: str,
        movement: str
    ) -> TransitionResult:
        if not isinstance(movement, str) or movement not in self.ALPHABET:
            return {
                "next_state": None,
                "status": "INVALID",
                "message": f"Invalid movement symbol '{movement}'. Expected U, D, L, or R.",
            }

        state = self._state_aliases.get(str(current_state))
        if state is None:
            return {
                "next_state": None,
                "status": "INVALID",
                "message": f"Unknown DFA state '{current_state}'.",
            }

        next_state = self.transition_table.get((state, movement))
        if next_state is None:
            return {
                "next_state": None,
                "status": "INVALID",
                "message": f"No transition from state '{state}' on '{movement}'.",
            }

        if next_state == self.CRASH_STATE:
            status = "CRASHED"
            message = "The robot hit an obstacle. The input string is rejected."
        elif next_state in self.accepting_states:
            status = "WON"
            message = "The robot reached the accepting state. The input string is accepted."
        else:
            status = "PLAYING"
            message = f"Transitioned to state '{next_state}'."

        return {
            "next_state": next_state,
            "status": status,
            "message": message,
        }
