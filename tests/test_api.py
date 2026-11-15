"""
Automated Test Suite for Person 2 (Ankur's Responsibilities).
Tests Flask routes, API request validation, error handling, static file serving,
and mock integration boundaries without implementing Jiya or Pavithra's logic.
"""

import unittest
from typing import Any, Dict, Optional
import networkx as nx

from robot_navigation.app import GameManager, create_app
from robot_navigation.automata.dfa_engine import DFAEngine, TransitionResult
from robot_navigation.game.game_state import GameState
from robot_navigation.game.grid_config import LEVELS, LevelConfig, state_to_position


# ==============================================================================
# MOCK CLASSES (For Decoupled Boundary Testing)
# ==============================================================================

class MockDFAEngine(DFAEngine):
    """Mock implementation of Jiya's DFAEngine for API testing."""
    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
        self.initial_state = "q00"
        self.accepting_states = {"q33"}

    def process_movement(self, current_state: str, movement: str) -> TransitionResult:
        if movement not in ("U", "D", "L", "R"):
            return {
                "next_state": None,
                "status": "INVALID",
                "message": f"Symbol '{movement}' not in alphabet."
            }
        # Generic mock transition
        return {
            "next_state": "q01",
            "status": "PLAYING",
            "message": "Move accepted."
        }


class MockGameState(GameState):
    """Mock implementation of Pavithra's GameState for API testing."""
    def __init__(self, level_config: LevelConfig, dfa_engine: DFAEngine):
        self.level_config = level_config
        self.dfa_engine = dfa_engine
        self.current_state = level_config["start"]
        self.move_counter = 0
        self.status = "READY"

    def move(self, direction: str) -> Dict[str, Any]:
        self.move_counter += 1
        self.status = "MOVING"
        self.current_state = "q01"
        return self.get_state()

    def reset(self) -> None:
        self.current_state = self.level_config["start"]
        self.move_counter = 0
        self.status = "READY"

    def get_state(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state,
            "robot_position": [0, 1] if self.move_counter > 0 else list(state_to_position(self.level_config["start"])),
            "status": self.status,
            "move_count": self.move_counter,
            "goal_position": list(state_to_position(self.level_config["goal"])),
            "obstacles": [list(state_to_position(state)) for state in self.level_config["obstacles"]],
            "rows": self.level_config["rows"],
            "cols": self.level_config["cols"],
            "start_position": list(state_to_position(self.level_config["start"]))
        }


class MockFailingMoveGameState(MockGameState):
    """GameState whose move method raises NotImplementedError."""
    def move(self, direction: str) -> Dict[str, Any]:
        raise NotImplementedError("Simulated unavailable game movement.")


# ==============================================================================
# TEST SUITE
# ==============================================================================

class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        """Set up test clients with mocked and unmocked game managers."""
        self.mock_levels: Dict[int, LevelConfig] = {1: LEVELS[1]}

        # Manager with mocked dependencies for successful flow tests
        self.mocked_manager = GameManager(
            dfa_engine_cls=MockDFAEngine,
            game_state_cls=MockGameState,
            levels=self.mock_levels
        )
        self.app = create_app(game_manager=self.mocked_manager, test_config={"TESTING": True})
        self.client = self.app.test_client()

    # 1. Homepage loads
    def test_homepage_loads(self):
        """Test that GET / renders index.html with HTTP 200."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DFA-9", response.data)
        self.assertIn(b"ROBOT NAVIGATION", response.data)
        self.assertNotIn(b"q00", response.data)
        self.assertNotIn(b"q33", response.data)

    # 2. Static assets served
    def test_static_assets(self):
        """Test that static CSS and JavaScript files are served properly."""
        css_res = self.client.get("/static/css/style.css")
        self.assertEqual(css_res.status_code, 200)
        self.assertIn(b"--bg-color", css_res.data)

        js_res = self.client.get("/static/js/game.js")
        self.assertEqual(js_res.status_code, 200)
        self.assertIn(b"api", js_res.data)

    # 3. DFA info endpoint
    def test_dfa_info_endpoint(self):
        """Test GET /api/dfa/info returns parsed JFLAP metadata without executing transitions."""
        response = self.client.get("/api/dfa/info")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("alphabet", data["data"])
        self.assertEqual(data["data"]["alphabet"], ["D", "L", "R", "U"])
        self.assertIn("q00", data["data"]["transition_table"])
        self.assertEqual(len(data["data"]["states"]), 14)
        self.assertEqual(data["data"]["trap_state"], LEVELS[1]["trap_state"])

    def test_levels_endpoint_returns_yaml_configuration(self):
        response = self.client.get("/api/levels")
        self.assertEqual(response.status_code, 200)
        level = response.get_json()["levels"][0]
        self.assertEqual(level["file_name"], LEVELS[1]["file_name"])
        self.assertEqual(level["start_state"], LEVELS[1]["start"])
        self.assertEqual(level["end_state"], LEVELS[1]["goal"])
        self.assertEqual(level["title"], LEVELS[1]["title"])

    def test_additional_configured_level_starts_without_code_changes(self):
        manager = GameManager(levels={1: LEVELS[1], 2: LEVELS[1]})
        client = create_app(game_manager=manager).test_client()

        levels_response = client.get("/api/levels")
        self.assertEqual(len(levels_response.get_json()["levels"]), 2)

        start_response = client.post("/api/game/start", json={"level": 2})
        self.assertEqual(start_response.status_code, 200)
        self.assertEqual(start_response.get_json()["state"]["level"], 2)

    # 4. Invalid JSON request handling
    def test_invalid_json_request_handling(self):
        """Test that endpoints reject non-JSON or malformed payloads with 400 Bad Request."""
        # Non-JSON content on /api/game/start
        res1 = self.client.post("/api/game/start", data="not json", content_type="text/plain")
        self.assertEqual(res1.status_code, 400)
        self.assertEqual(res1.get_json()["status"], "BAD_REQUEST")

        # Non-JSON content on /api/game/move
        res2 = self.client.post("/api/game/move", data="invalid body", content_type="text/plain")
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(res2.get_json()["status"], "BAD_REQUEST")

    # 5. Missing movement and start fields
    def test_missing_fields(self):
        """Test that missing required fields return 400 Bad Request."""
        # Missing 'level'
        res_start = self.client.post("/api/game/start", json={})
        self.assertEqual(res_start.status_code, 400)
        self.assertIn("Missing required field: 'level'", res_start.get_json()["error"])

        # Missing 'direction'
        res_move = self.client.post("/api/game/move", json={})
        self.assertEqual(res_move.status_code, 400)
        self.assertIn("Missing required field: 'direction'", res_move.get_json()["error"])

    # 6. Invalid direction
    def test_invalid_direction(self):
        """Test that unsupported directions return 400 Bad Request."""
        # Start game first
        self.client.post("/api/game/start", json={"level": 1})

        # Send invalid direction
        for bad_dir in ["JUMP", "NORTH", "TELEPORT", ""]:
            response = self.client.post("/api/game/move", json={"direction": bad_dir})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()["status"], "INVALID_DIRECTION")

        # Non-string direction
        response = self.client.post("/api/game/move", json={"direction": 42})
        self.assertEqual(response.status_code, 400)

    # 7. Invalid level handling
    def test_invalid_level(self):
        """Test non-existent or malformed levels."""
        # Non-integer level
        res_type = self.client.post("/api/game/start", json={"level": "level_one"})
        self.assertEqual(res_type.status_code, 400)

        # Unconfigured level
        res_missing = self.client.post("/api/game/start", json={"level": 999})
        self.assertEqual(res_missing.status_code, 404)
        self.assertEqual(res_missing.get_json()["status"], "LEVEL_NOT_FOUND")

    # 8. Operations without active session
    def test_no_active_session_handling(self):
        """Test that moving, getting state, or resetting without a session returns 400."""
        fresh_mgr = GameManager(
            dfa_engine_cls=MockDFAEngine,
            game_state_cls=MockGameState,
            levels=self.mock_levels
        )
        fresh_client = create_app(game_manager=fresh_mgr).test_client()

        res_state = fresh_client.get("/api/game/state")
        self.assertEqual(res_state.status_code, 400)
        self.assertEqual(res_state.get_json()["status"], "NO_ACTIVE_SESSION")

        res_move = fresh_client.post("/api/game/move", json={"direction": "UP"})
        self.assertEqual(res_move.status_code, 400)
        self.assertEqual(res_move.get_json()["status"], "NO_ACTIVE_SESSION")

        res_reset = fresh_client.post("/api/game/reset")
        self.assertEqual(res_reset.status_code, 400)
        self.assertEqual(res_reset.get_json()["status"], "NO_ACTIVE_SESSION")

    # 9. The implemented DFA engine starts a game successfully.
    def test_real_dfa_engine_starts_game(self):
        manager = GameManager(
            dfa_engine_cls=DFAEngine,
            game_state_cls=MockGameState,
            levels=self.mock_levels
        )
        client = create_app(game_manager=manager).test_client()
        response = client.post("/api/game/start", json={"level": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["state"]["current_state"], "q00")

        # Pavithra's GameState is now implemented, so starting a game succeeds
        impl_state_mgr = GameManager(
            dfa_engine_cls=MockDFAEngine,
            game_state_cls=GameState,
            levels=self.mock_levels
        )
        client2 = create_app(game_manager=impl_state_mgr).test_client()
        res2 = client2.post("/api/game/start", json={"level": 1})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.get_json()["state"]["status"], "READY")

        # Test move raising NotImplementedError
        failing_move_mgr = GameManager(
            dfa_engine_cls=MockDFAEngine,
            game_state_cls=MockFailingMoveGameState,
            levels=self.mock_levels
        )
        client3 = create_app(game_manager=failing_move_mgr).test_client()
        client3.post("/api/game/start", json={"level": 1})
        res3 = client3.post("/api/game/move", json={"direction": "UP"})
        self.assertEqual(res3.status_code, 501)
        self.assertEqual(res3.get_json()["status"], "NOT_IMPLEMENTED")

    # 10. Successful workflow with mock integration
    def test_successful_game_lifecycle_with_mocks(self):
        """Test full session flow: start -> move -> get_state -> reset."""
        # 1. Start game
        res_start = self.client.post("/api/game/start", json={"level": 1})
        self.assertEqual(res_start.status_code, 200)
        self.assertEqual(res_start.get_json()["state"]["status"], "READY")

        # 2. Process Move
        res_move = self.client.post("/api/game/move", json={"direction": "RIGHT"})
        self.assertEqual(res_move.status_code, 200)
        move_data = res_move.get_json()
        self.assertEqual(move_data["direction"], "RIGHT")
        self.assertEqual(move_data["symbol"], "R")
        self.assertEqual(move_data["state"]["move_count"], 1)

        # 3. Get State
        res_state = self.client.get("/api/game/state")
        self.assertEqual(res_state.status_code, 200)
        self.assertEqual(res_state.get_json()["state"]["move_count"], 1)

        # 4. Reset
        res_reset = self.client.post("/api/game/reset")
        self.assertEqual(res_reset.status_code, 200)
        self.assertEqual(res_reset.get_json()["state"]["move_count"], 0)
        self.assertEqual(res_reset.get_json()["state"]["status"], "READY")

    # 11. Missing JFF file handling
    def test_missing_jff_file(self):
        """A missing configured JFF file fails when that level starts."""
        missing_level = {**LEVELS[1], "jff_path": "non_existent_file.jff"}
        with self.assertRaises(FileNotFoundError):
            GameManager(levels={1: missing_level}).start_game(1)


if __name__ == "__main__":
    unittest.main()
