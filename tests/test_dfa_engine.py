import unittest

from robot_navigation.automata.dfa_engine import DFAEngine
from robot_navigation.automata.jff_parser import parse_dfa
from robot_navigation.game.grid_config import LEVELS


def load_graph():
    with open(LEVELS[1]["jff_path"], encoding="utf-8") as jff_file:
        graph = parse_dfa(jff_file.read())
    graph.graph["trap_state"] = LEVELS[1]["trap_state"]
    return graph


class TestDFAEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DFAEngine(load_graph())

    def test_initial_and_accepting_states(self):
        self.assertEqual(self.engine.initial_state, "q00")
        self.assertEqual(self.engine.accepting_states, {"q33"})

    def test_transitions_accept_state_names_and_jflap_ids(self):
        self.assertEqual(
            self.engine.process_movement("q00", "R")["next_state"],
            "q01",
        )
        self.assertEqual(
            self.engine.process_movement("0", "R")["next_state"],
            "q01",
        )

    def test_boundary_self_loop_is_playing(self):
        result = self.engine.process_movement("q00", "U")
        self.assertEqual(result["next_state"], "q00")
        self.assertEqual(result["status"], "PLAYING")

    def test_obstacle_transition_is_crashed(self):
        result = self.engine.process_movement("q01", "D")
        self.assertEqual(result["next_state"], "Crash")
        self.assertEqual(result["status"], "CRASHED")

    def test_crash_state_is_a_trap(self):
        result = self.engine.process_movement("Crash", "L")
        self.assertEqual(result["next_state"], "Crash")
        self.assertEqual(result["status"], "CRASHED")

    def test_accepting_transition_is_won(self):
        result = self.engine.process_movement("q23", "D")
        self.assertEqual(result["next_state"], "q33")
        self.assertEqual(result["status"], "WON")

    def test_invalid_symbol_or_state_is_invalid(self):
        for state, symbol in (("q00", "X"), ("missing", "R")):
            with self.subTest(state=state, symbol=symbol):
                result = self.engine.process_movement(state, symbol)
                self.assertIsNone(result["next_state"])
                self.assertEqual(result["status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
