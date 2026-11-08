"""
JFLAP Parser integration module.
Parses JFLAP .jff files into NetworkX directed multigraphs and extracts
automata metadata for GUI visualization.
"""

from typing import Any, Dict, List, Set
import xml.etree.ElementTree as ET
import networkx as nx


def parse_jff(jff_content: str, automaton_type: str = "DFA") -> nx.MultiDiGraph:
    """
    Parse a JFLAP .jff string and return a NetworkX graph.

    Parameters:
        jff_content: Complete JFF XML content as a string.
        automaton_type: 'DFA' or 'NFA'

    Returns:
        NetworkX directed graph containing:
            - States
            - Transitions
            - Initial state
            - Final states
    """
    automaton_type = automaton_type.upper()

    if automaton_type not in ("DFA", "NFA"):
        raise ValueError("automaton_type must be DFA or NFA")

    root = ET.fromstring(jff_content)

    if root.tag != "structure":
        raise ValueError("Invalid JFLAP file: Expected <structure>")

    automaton = root.find("automaton")

    if automaton is None:
        raise ValueError("No automaton found in JFF file")

    graph = nx.MultiDiGraph()

    initial_state = None
    final_states = set()

    # Extract states
    for state in automaton.findall("state"):
        state_id = state.get("id")
        state_name = state.get("name", state_id)

        x = float(state.findtext("x", "0"))
        y = float(state.findtext("y", "0"))

        is_initial = state.find("initial") is not None
        is_final = state.find("final") is not None

        graph.add_node(
            state_id,
            name=state_name,
            x=x,
            y=y,
            initial=is_initial,
            final=is_final
        )

        if is_initial:
            if initial_state is not None:
                raise ValueError("Multiple initial states found")

            initial_state = state_id

        if is_final:
            final_states.add(state_id)

    if initial_state is None:
        raise ValueError("No initial state found")

    # Extract transitions
    for transition in automaton.findall("transition"):
        source = transition.findtext("from")
        target = transition.findtext("to")
        read_symbol = transition.findtext("read")

        if source not in graph or target not in graph:
            raise ValueError(
                f"Invalid transition: {source} -> {target}"
            )

        # JFLAP represents epsilon using an empty read element
        symbol = (
            read_symbol.strip()
            if read_symbol is not None
            else "ε"
        )

        if symbol == "":
            symbol = "ε"

        graph.add_edge(
            source,
            target,
            symbol=symbol
        )

    # DFA validation
    if automaton_type == "DFA":
        transitions = {}

        for source, target, data in graph.edges(data=True):
            symbol = data["symbol"]

            if symbol == "ε":
                raise ValueError(
                    "DFA cannot contain epsilon transitions"
                )

            key = (source, symbol)

            if key in transitions:
                raise ValueError(
                    f"Nondeterministic transition from "
                    f"{source} on {symbol}"
                )

            transitions[key] = target

    # Attach automaton metadata
    graph.graph["type"] = automaton_type
    graph.graph["initial_state"] = initial_state
    graph.graph["final_states"] = final_states

    return graph


def parse_dfa(jff_content: str) -> nx.MultiDiGraph:
    """Convenience helper to parse a DFA from .jff content string."""
    return parse_jff(jff_content, "DFA")


def parse_nfa(jff_content: str) -> nx.MultiDiGraph:
    """Convenience helper to parse an NFA from .jff content string."""
    return parse_jff(jff_content, "NFA")


def extract_dfa_metadata(graph: nx.MultiDiGraph) -> Dict[str, Any]:
    """
    Helper function to extract DFA metadata for GUI visualization.
    Reads static graph properties without performing state execution.

    Parameters:
        graph: NetworkX MultiDiGraph returned by parse_dfa()

    Returns:
        Dict containing states, alphabet, transition_table, initial_state, and final_states.
    """
    initial_state_id = graph.graph.get("initial_state")
    final_state_ids: Set[str] = graph.graph.get("final_states", set())

    # Map state ID to state details
    states: List[Dict[str, Any]] = []
    id_to_name: Dict[str, str] = {}
    alphabet: Set[str] = set()

    for node_id, data in graph.nodes(data=True):
        name = data.get("name", str(node_id))
        id_to_name[str(node_id)] = name
        states.append({
            "id": str(node_id),
            "name": name,
            "initial": bool(data.get("initial", False)),
            "final": bool(data.get("final", False)),
            "x": data.get("x", 0.0),
            "y": data.get("y", 0.0)
        })

    # Sort states by name/id for consistent display
    states.sort(key=lambda s: s["name"])

    # Build transition table: {state_name: {symbol: next_state_name}}
    transition_table: Dict[str, Dict[str, str]] = {}
    for node_id in graph.nodes:
        state_name = id_to_name[str(node_id)]
        transition_table[state_name] = {}

    for source_id, target_id, data in graph.edges(data=True):
        symbol = data.get("symbol", "")
        if symbol:
            alphabet.add(symbol)
            src_name = id_to_name.get(str(source_id), str(source_id))
            tgt_name = id_to_name.get(str(target_id), str(target_id))
            transition_table[src_name][symbol] = tgt_name

    initial_state_name = id_to_name.get(str(initial_state_id), str(initial_state_id))
    final_state_names = [id_to_name.get(str(fid), str(fid)) for fid in final_state_ids]

    return {
        "states": states,
        "alphabet": sorted(list(alphabet)),
        "initial_state": initial_state_name,
        "initial_state_id": str(initial_state_id),
        "final_states": sorted(final_state_names),
        "final_state_ids": sorted(list(final_state_ids)),
        "transition_table": transition_table
    }


__all__ = ["parse_jff", "parse_dfa", "parse_nfa", "extract_dfa_metadata"]
