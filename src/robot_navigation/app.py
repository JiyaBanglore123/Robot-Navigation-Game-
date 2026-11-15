"""
Flask Backend Application for DFA-Based Robot Navigation Game.
Responsible for REST API endpoints, JFF parsing integration,
session coordination, and error handling.
Author: Ankur (Person 2)
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type

import networkx as nx
from flask import Flask, jsonify, render_template, request

# Ensure project root & src are in Python sys.path
PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent
for p in (str(PROJECT_ROOT), str(SRC_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from robot_navigation.automata.dfa_engine import DFAEngine
from robot_navigation.automata.jff_parser import extract_dfa_metadata, parse_dfa
from robot_navigation.config.settings import (
    DEBUG,
    DIRECTION_MAPPING,
    HOST,
    PORT,
    SECRET_KEY,
    VALID_DIRECTIONS,
)
from robot_navigation.game.game_state import GameState
from robot_navigation.game.grid_config import LEVELS, LevelConfig


class GameManager:
    """
    Manages DFA loading, level configuration, and runtime game session lifecycle.
    Implements dependency injection to cleanly decouple from Jiya's DFAEngine
    and Pavithra's GameState implementations.
    """

    def __init__(
        self,
        dfa_engine_cls: Type[DFAEngine] = DFAEngine,
        game_state_cls: Type[GameState] = GameState,
        levels: Optional[Dict[int, LevelConfig]] = None,
    ):
        self.dfa_engine_cls = dfa_engine_cls
        self.game_state_cls = game_state_cls
        self.levels = levels if levels is not None else LEVELS
        self.parsed_graphs: Dict[int, nx.MultiDiGraph] = {}
        self.parsed_graph: Optional[nx.MultiDiGraph] = None
        self.dfa_engine: Optional[DFAEngine] = None
        self.current_game_state: Optional[GameState] = None
        self.current_level: Optional[int] = None

    def load_automaton(self, level: int) -> nx.MultiDiGraph:
        """
        Loads the .jff file and parses it using the existing JFF parser.
        """
        if level in self.parsed_graphs:
            graph = self.parsed_graphs[level]
            self.parsed_graph = graph
            return graph
        level_config = self.levels[level]
        jff_path = level_config["jff_path"]
        if not os.path.exists(jff_path):
            raise FileNotFoundError(f"DFA specification file not found at: {jff_path}")

        try:
            with open(jff_path, "r", encoding="utf-8") as f:
                content = f.read()
            graph = parse_dfa(content)
            graph.graph["trap_state"] = level_config["trap_state"]
            state_names = {
                data.get("name", str(node_id))
                for node_id, data in graph.nodes(data=True)
            }
            if graph.nodes[graph.graph["initial_state"]].get("name") != level_config["start"]:
                raise ValueError(
                    f"Configured start state '{level_config['start']}' does not match the JFLAP initial state."
                )
            if level_config["start"] not in state_names:
                raise ValueError(f"Configured start state '{level_config['start']}' is absent from the DFA.")
            if level_config["goal"] not in state_names:
                raise ValueError(f"Configured end state '{level_config['goal']}' is absent from the DFA.")
            if level_config["trap_state"] not in state_names:
                raise ValueError(f"Configured trap state '{level_config['trap_state']}' is absent from the DFA.")
            final_names = {
                data.get("name", str(node_id))
                for node_id, data in graph.nodes(data=True)
                if data.get("final", False)
            }
            if level_config["goal"] not in final_names:
                raise ValueError(f"Configured end state '{level_config['goal']}' is not accepting.")
            expected_grid_states = {
                f"q{row}{col}"
                for row in range(level_config["rows"])
                for col in range(level_config["cols"])
            } - set(level_config["obstacles"])
            expected_states = expected_grid_states | {level_config["trap_state"]}
            if state_names != expected_states:
                raise ValueError(
                    "Configured grid states do not match states in the JFLAP file. "
                    f"Missing: {sorted(expected_states - state_names)}; "
                    f"unexpected: {sorted(state_names - expected_states)}."
                )
            self.parsed_graphs[level] = graph
            self.parsed_graph = graph
            return graph
        except Exception as e:
            raise ValueError(f"Failed to parse DFA file '{jff_path}': {str(e)}")

    def start_game(self, level: int) -> Dict[str, Any]:
        """
        Starts a new game session for the specified level.
        Injects the parsed DFA graph into DFAEngine, and the level configuration
        into GameState.
        """
        if level not in self.levels:
            raise KeyError(
                f"Level {level} is not configured in assets/state_config.yaml."
            )

        level_config = self.levels[level]
        graph = self.load_automaton(level)

        # Build the DFA transition engine from the parsed JFLAP graph.
        self.dfa_engine = self.dfa_engine_cls(graph)

        # Start the configured level with the shared DFA engine.
        game_level_config = {**level_config, "level": level}
        self.current_game_state = self.game_state_cls(game_level_config, self.dfa_engine)
        self.current_level = level

        # Retrieve initial game state representation
        return self.current_game_state.get_state()

    def process_move(self, symbol: str, direction: str) -> Dict[str, Any]:
        """
        Coordinates a movement operation on the active game session.
        """
        if self.current_game_state is None:
            raise RuntimeError("No active game session. Start a game first via /api/game/start.")

        # Coordinate movement through Pavithra's GameState manager
        # Pass the mapped DFA symbol as defined in the integration contract
        return self.current_game_state.move(symbol)

    def reset_game(self) -> Dict[str, Any]:
        """
        Resets the active game session to its initial state.
        """
        if self.current_game_state is None:
            raise RuntimeError("No active game session. Start a game first via /api/game/start.")

        self.current_game_state.reset()
        return self.current_game_state.get_state()

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the current game state dictionary.
        """
        if self.current_game_state is None:
            raise RuntimeError("No active game session. Start a game first via /api/game/start.")

        return self.current_game_state.get_state()

    def get_dfa_info(self, level: Optional[int] = None) -> Dict[str, Any]:
        """
        Returns metadata for the active level or the first configured level.
        """
        if level is None:
            level = self.current_level if self.current_level is not None else next(iter(self.levels))
        graph = self.load_automaton(level)
        info = extract_dfa_metadata(graph)
        info["trap_state"] = self.levels[level]["trap_state"]
        return info

    def get_levels(self) -> list[Dict[str, Any]]:
        """Return the public metadata used to render the level selector."""
        return [
            {
                "level": level,
                "file_name": config["file_name"],
                "start_state": config["start"],
                "end_state": config["goal"],
                "num_grid_rows": config["rows"],
                "num_grid_cols": config["cols"],
                "num_obstacles": len(config["obstacles"]),
                "obstacle_states": list(config["obstacles"]),
                "trap_state": config["trap_state"],
                "title": config["title"],
                "description": config["description"],
            }
            for level, config in self.levels.items()
        ]


def create_app(
    game_manager: Optional[GameManager] = None,
    test_config: Optional[dict] = None
) -> Flask:
    """
    Application factory for the Flask server.
    Supports dependency injection for automated testing.
    """
    app = Flask(
        __name__,
        template_folder=str(PACKAGE_DIR / "web" / "templates"),
        static_folder=str(PACKAGE_DIR / "web" / "static"),
    )

    app.config["SECRET_KEY"] = SECRET_KEY
    if test_config:
        app.config.update(test_config)

    # Initialize GameManager if not provided
    if game_manager is None:
        try:
            game_manager = GameManager()
        except Exception as e:
            app.logger.warning(f"GameManager initialization warning: {e}")
            # Keep None, will try loading when needed or handled in endpoints
            game_manager = None

    # Attach game manager to app context
    app.extensions["game_manager"] = game_manager

    # --------------------------------------------------------------------------
    # Error Handlers
    # --------------------------------------------------------------------------
    @app.errorhandler(NotImplementedError)
    def handle_not_implemented(e):
        """Return a structured response when a component is unavailable."""
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "NOT_IMPLEMENTED"
        }), 501

    @app.errorhandler(400)
    def handle_bad_request(e):
        description = getattr(e, "description", "Bad Request")
        return jsonify({
            "success": False,
            "error": description,
            "status": "BAD_REQUEST"
        }), 400

    @app.errorhandler(404)
    def handle_not_found(e):
        description = getattr(e, "description", "Resource Not Found")
        return jsonify({
            "success": False,
            "error": description,
            "status": "NOT_FOUND"
        }), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        """Safely returns JSON error without exposing internal stack trace."""
        app.logger.error(f"Internal server error: {e}")
        return jsonify({
            "success": False,
            "error": "An internal server error occurred.",
            "status": "INTERNAL_ERROR"
        }), 500

    # --------------------------------------------------------------------------
    # Frontend Page Route
    # --------------------------------------------------------------------------
    @app.route("/")
    def index():
        """Renders the single-page retro game interface."""
        return render_template("index.html")

    # --------------------------------------------------------------------------
    # REST API Endpoints
    # --------------------------------------------------------------------------
    @app.route("/api/game/start", methods=["POST"])
    def start_game():
        """
        Start a new game session.
        Payload: { "level": 1 }
        """
        mgr: Optional[GameManager] = app.extensions.get("game_manager")
        if mgr is None:
            return jsonify({
                "success": False,
                "error": "Game manager unavailable. DFA file missing or invalid.",
                "status": "UNAVAILABLE"
            }), 500

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Invalid or missing JSON payload in request body.",
                "status": "BAD_REQUEST"
            }), 400

        if "level" not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: 'level'",
                "status": "BAD_REQUEST"
            }), 400

        try:
            level = int(data["level"])
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "'level' must be an integer.",
                "status": "BAD_REQUEST"
            }), 400

        try:
            initial_state = mgr.start_game(level)
            return jsonify({
                "success": True,
                "level": level,
                "level_info": next(
                    item for item in mgr.get_levels() if item["level"] == level
                ),
                "dfa_info": mgr.get_dfa_info(level),
                "state": initial_state
            }), 200
        except KeyError as ke:
            return jsonify({
                "success": False,
                "error": str(ke).strip("'"),
                "status": "LEVEL_NOT_FOUND"
            }), 404
        except NotImplementedError as nie:
            return jsonify({
                "success": False,
                "error": str(nie),
                "status": "NOT_IMPLEMENTED"
            }), 501
        except Exception as ex:
            app.logger.error(f"Unexpected error starting game: {ex}")
            return jsonify({
                "success": False,
                "error": str(ex),
                "status": "ERROR"
            }), 500

    @app.route("/api/game/move", methods=["POST"])
    def move():
        """
        Process a movement command.
        Payload: { "direction": "UP" }
        Maps direction to DFA symbol and forwards to GameState.
        """
        mgr: Optional[GameManager] = app.extensions.get("game_manager")
        if mgr is None:
            return jsonify({
                "success": False,
                "error": "Game manager unavailable.",
                "status": "UNAVAILABLE"
            }), 500

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Invalid or missing JSON payload in request body.",
                "status": "BAD_REQUEST"
            }), 400

        if "direction" not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: 'direction'",
                "status": "BAD_REQUEST"
            }), 400

        raw_direction = data["direction"]
        if not isinstance(raw_direction, str):
            return jsonify({
                "success": False,
                "error": "'direction' must be a string.",
                "status": "BAD_REQUEST"
            }), 400

        direction = raw_direction.strip().upper()
        if direction not in VALID_DIRECTIONS:
            return jsonify({
                "success": False,
                "error": (
                    f"Invalid direction '{raw_direction}'. "
                    f"Supported directions are: {', '.join(sorted(VALID_DIRECTIONS))}"
                ),
                "status": "INVALID_DIRECTION"
            }), 400

        # Check if an active game session exists
        if mgr.current_game_state is None:
            return jsonify({
                "success": False,
                "error": "No active game session. Please start a game first via /api/game/start.",
                "status": "NO_ACTIVE_SESSION"
            }), 400

        # Map frontend direction to DFA symbol
        symbol = DIRECTION_MAPPING[direction]

        try:
            updated_state = mgr.process_move(symbol=symbol, direction=direction)
            return jsonify({
                "success": True,
                "direction": direction,
                "symbol": symbol,
                "state": updated_state
            }), 200
        except NotImplementedError as nie:
            return jsonify({
                "success": False,
                "error": str(nie),
                "status": "NOT_IMPLEMENTED"
            }), 501
        except Exception as ex:
            app.logger.error(f"Unexpected error processing move: {ex}")
            return jsonify({
                "success": False,
                "error": str(ex),
                "status": "ERROR"
            }), 500

    @app.route("/api/game/state", methods=["GET"])
    def get_state():
        """
        Retrieve current active game state.
        """
        mgr: Optional[GameManager] = app.extensions.get("game_manager")
        if mgr is None or mgr.current_game_state is None:
            return jsonify({
                "success": False,
                "error": "No active game session. Please start a game first via /api/game/start.",
                "status": "NO_ACTIVE_SESSION"
            }), 400

        try:
            current_state = mgr.get_state()
            return jsonify({
                "success": True,
                "state": current_state
            }), 200
        except NotImplementedError as nie:
            return jsonify({
                "success": False,
                "error": str(nie),
                "status": "NOT_IMPLEMENTED"
            }), 501
        except Exception as ex:
            app.logger.error(f"Unexpected error fetching state: {ex}")
            return jsonify({
                "success": False,
                "error": str(ex),
                "status": "ERROR"
            }), 500

    @app.route("/api/game/reset", methods=["POST"])
    def reset_game():
        """
        Reset the current game session to initial configuration.
        """
        mgr: Optional[GameManager] = app.extensions.get("game_manager")
        if mgr is None or mgr.current_game_state is None:
            return jsonify({
                "success": False,
                "error": "No active game session. Please start a game first via /api/game/start.",
                "status": "NO_ACTIVE_SESSION"
            }), 400

        try:
            reset_state = mgr.reset_game()
            return jsonify({
                "success": True,
                "message": "Game session successfully reset.",
                "state": reset_state
            }), 200
        except NotImplementedError as nie:
            return jsonify({
                "success": False,
                "error": str(nie),
                "status": "NOT_IMPLEMENTED"
            }), 501
        except Exception as ex:
            app.logger.error(f"Unexpected error resetting game: {ex}")
            return jsonify({
                "success": False,
                "error": str(ex),
                "status": "ERROR"
            }), 500

    @app.route("/api/dfa/info", methods=["GET"])
    def dfa_info():
        """
        Retrieve static DFA definition and transition table for the DFA Viewer.
        """
        mgr: Optional[GameManager] = app.extensions.get("game_manager")
        if mgr is None:
            return jsonify({
                "success": False,
                "error": "DFA information unavailable. Automaton file could not be parsed.",
                "status": "UNAVAILABLE"
            }), 500

        try:
            level_arg = request.args.get("level")
            try:
                level = int(level_arg) if level_arg is not None else None
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "'level' must be an integer.",
                    "status": "BAD_REQUEST"
                }), 400
            if level is not None and level not in mgr.levels:
                return jsonify({
                    "success": False,
                    "error": f"Level {level} is not configured.",
                    "status": "LEVEL_NOT_FOUND"
                }), 404
            info = mgr.get_dfa_info(level)
            return jsonify({
                "success": True,
                "data": info
            }), 200
        except Exception as ex:
            app.logger.error(f"Unexpected error extracting DFA metadata: {ex}")
            return jsonify({
                "success": False,
                "error": str(ex),
                "status": "ERROR"
            }), 500

    @app.route("/api/levels", methods=["GET"])
    def levels():
        """Return configured level metadata for the level selector."""
        mgr: Optional[GameManager] = app.extensions.get("game_manager")
        if mgr is None:
            return jsonify({
                "success": False,
                "error": "Level configuration unavailable.",
                "status": "UNAVAILABLE"
            }), 500
        return jsonify({"success": True, "levels": mgr.get_levels()}), 200

    return app


# Default application instance for `flask run` or `python app.py`
app = create_app()

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
