"""
Tests for the integrated DFA engine, grid configuration, and game state.
"""

import unittest

from robot_navigation.automata.dfa_engine import DFAEngine
from robot_navigation.automata.jff_parser import parse_dfa
from robot_navigation.game.game_state import GameState
from robot_navigation.game.grid_config import (
    LEVELS,
    position_to_state,
    state_to_position,
    validate_level,
)


def load_graph():
    with open(LEVELS[1]["jff_path"], encoding="utf-8") as f:
        graph = parse_dfa(f.read())
    graph.graph["trap_state"] = LEVELS[1]["trap_state"]
    return graph


class TestGridConfig(unittest.TestCase):

    def test_level1_matches_contract(self):
        self.assertEqual(LEVELS[1]["rows"], 4)
        self.assertEqual(LEVELS[1]["cols"], 4)
        self.assertEqual(LEVELS[1]["start"], "q00")
        self.assertEqual(LEVELS[1]["goal"], "q33")
        self.assertEqual(LEVELS[1]["obstacles"], ["q11", "q22", "q31"])
        self.assertEqual(LEVELS[1]["title"], "JFLAP DFA")

    def test_level_cells_match_dfa_states(self):
        graph = load_graph()
        dfa_states = {d["name"] for _, d in graph.nodes(data=True)} - {"Crash"}
        for cfg in LEVELS.values():
            cells = {position_to_state(r, c) for r in range(cfg["rows"]) for c in range(cfg["cols"])}
            free_cells = cells - set(cfg["obstacles"])
            self.assertEqual(free_cells, dfa_states)

    def test_start_and_goal_match_dfa(self):
        graph = load_graph()
        initial = next(d["name"] for _, d in graph.nodes(data=True) if d["initial"])
        finals = {d["name"] for _, d in graph.nodes(data=True) if d["final"]}
        self.assertEqual(LEVELS[1]["start"], initial)
        self.assertIn(LEVELS[1]["goal"], finals)

    def test_position_conversions(self):
        self.assertEqual(state_to_position("q12"), (1, 2))
        self.assertIsNone(state_to_position("Crash"))
        self.assertEqual(position_to_state(3, 0), "q30")

    def test_validate_rejects_bad_level(self):
        config = dict(LEVELS[1])
        with self.assertRaises(ValueError):
            validate_level({**config, "goal": "q00"})
        with self.assertRaises(ValueError):
            validate_level({**config, "obstacles": ["q44"]})


class TestGameState(unittest.TestCase):

    def setUp(self):
        self.game = GameState(LEVELS[1], DFAEngine(load_graph()))

    def play(self, symbols):
        state = None
        for s in symbols:
            state = self.game.move(s)
        return state

    def test_initial_state(self):
        s = self.game.get_state()
        self.assertEqual(s["current_state"], "q00")
        self.assertEqual(s["robot_position"], [0, 0])
        self.assertEqual(s["status"], "READY")
        self.assertEqual(s["move_count"], 0)
        self.assertEqual(s["goal_position"], [3, 3])
        self.assertEqual(s["obstacles"], [[1, 1], [2, 2], [3, 1]])
        self.assertEqual((s["rows"], s["cols"]), (4, 4))

    def test_normal_move(self):
        s = self.game.move("R")
        self.assertEqual(s["current_state"], "q01")
        self.assertEqual(s["robot_position"], [0, 1])
        self.assertEqual(s["status"], "MOVING")
        self.assertEqual(s["move_count"], 1)

    def test_wall_bump_is_blocked(self):
        s = self.game.move("U")
        self.assertEqual(s["current_state"], "q00")
        self.assertEqual(s["robot_position"], [0, 0])
        self.assertEqual(s["status"], "BLOCKED")
        self.assertEqual(s["move_count"], 1)

    def test_crash_into_obstacle(self):
        s = self.play(["R", "D"])  # q01 -> down into obstacle (1,1)
        self.assertEqual(s["current_state"], "Crash")
        self.assertEqual(s["status"], "CRASHED")
        self.assertEqual(s["robot_position"], [0, 1])
        self.assertEqual(s["crash_position"], [1, 1])
        self.assertTrue(s["is_game_over"])

    def test_winning_path(self):
        s = self.play(["R", "R", "R", "D", "D", "D"])
        self.assertEqual(s["current_state"], "q33")
        self.assertEqual(s["robot_position"], [3, 3])
        self.assertEqual(s["status"], "WON")
        self.assertEqual(s["move_count"], 6)
        self.assertEqual(s["input_string"], "RRRDDD")

    def test_moves_rejected_after_game_over(self):
        self.play(["R", "D"])
        s = self.game.move("L")
        self.assertEqual(s["status"], "CRASHED")
        self.assertEqual(s["move_count"], 2)

    def test_invalid_symbol_changes_nothing(self):
        s = self.game.move("X")
        self.assertEqual(s["current_state"], "q00")
        self.assertEqual(s["move_count"], 0)
        self.assertEqual(s["status"], "READY")

    def test_reset(self):
        self.play(["R", "D"])
        self.game.reset()
        s = self.game.get_state()
        self.assertEqual(s["current_state"], "q00")
        self.assertEqual(s["robot_position"], [0, 0])
        self.assertEqual(s["status"], "READY")
        self.assertEqual(s["move_count"], 0)
        self.assertEqual(s["path"], [[0, 0]])
        self.assertIsNone(s["crash_position"])

    def test_position_always_synced_with_state(self):
        for s in ["D", "D", "D", "U", "R", "R", "R", "D", "D"]:
            st = self.game.move(s)
            if st["current_state"] != "Crash":
                self.assertEqual(state_to_position(st["current_state"]), tuple(st["robot_position"]))

    def test_through_flask_api(self):
        from robot_navigation.app import GameManager, create_app
        mgr = GameManager()
        client = create_app(game_manager=mgr).test_client()
        r = client.post("/api/game/start", json={"level": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["state"]["status"], "READY")
        for d in ["RIGHT", "RIGHT", "RIGHT", "DOWN", "DOWN", "DOWN"]:
            r = client.post("/api/game/move", json={"direction": d})
        self.assertEqual(r.get_json()["state"]["status"], "WON")
        self.assertEqual(r.get_json()["state"]["current_state"], "q33")
        r = client.post("/api/game/reset")
        self.assertEqual(r.get_json()["state"]["move_count"], 0)


if __name__ == "__main__":
    unittest.main()
