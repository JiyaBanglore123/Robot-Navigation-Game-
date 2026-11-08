"""
JFLAP Parser integration module.
Preserves and re-exports the existing parser from src/misc/jff_parser.py.
"""

from typing import Any, Dict, List, Set
import networkx as nx
from src.misc.jff_parser import parse_jff, parse_dfa, parse_nfa


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
