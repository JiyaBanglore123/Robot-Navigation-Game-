
import xml.etree.ElementTree as ET
import networkx as nx
import matplotlib.pyplot as plt


def parse_jff(jff_content: str, automaton_type: str):
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


def parse_dfa(jff_content: str):
    return parse_jff(jff_content, "DFA")


def parse_nfa(jff_content: str):
    return parse_jff(jff_content, "NFA")
