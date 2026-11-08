"""
Automata package.
Handles DFA execution, transition validation, and JFLAP file parsing.
"""

from .dfa_engine import DFAEngine, TransitionResult
from .jff_parser import parse_dfa, parse_nfa, parse_jff

__all__ = ["DFAEngine", "TransitionResult", "parse_dfa", "parse_nfa", "parse_jff"]
