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
    JFF_PATH,
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
        jff_path: str = JFF_PATH,
        dfa_engine_cls: Type[DFAEngine] = DFAEngine,
        game_state_cls: Type[GameState] = GameState,
        levels: Optional[Dict[int, LevelConfig]] = None,
    ):
        self.jff_path = jff_path
        self.dfa_engine_cls = dfa_engine_cls
        self.game_state_cls = game_state_cls
        self.levels = levels if levels is not None else LEVELS
        self.parsed_graph: Optional[nx.MultiDiGraph] = None
        self.dfa_engine: Optional[DFAEngine] = None
        self.current_game_state: Optional[GameState] = None
        self.current_level: Optional[int] = None

        # Load and parse DFA specification on initialization
        self.load_automaton()

    def load_automaton(self) -> nx.MultiDiGraph:
        """
        Loads the .jff file and parses it using the existing JFF parser.
        """
        if not os.path.exists(self.jff_path):
            raise FileNotFoundError(f"DFA specification file not found at: {self.jff_path}")

        try:
            with open(self.jff_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.parsed_graph = parse_dfa(content)
            return self.parsed_graph
        except Exception as e:
            raise ValueError(f"Failed to parse DFA file '{self.jff_path}': {str(e)}")

    def start_game(self, level: int) -> Dict[str, Any]:
        """
        Starts a new game session for the specified level.
        Injects the parsed DFA graph into DFAEngine, and the level configuration
        into GameState.
        """
        if level not in self.levels:
            raise KeyError(
                f"Level {level} is not configured in LEVELS. "
                "Grid configuration must be implemented by Pavithra."
            )

        level_config = self.levels[level]

        if self.parsed_graph is None:
            self.load_automaton()

        # Instantiate Jiya's DFAEngine (will raise NotImplementedError if not implemented)
        self.dfa_engine = self.dfa_engine_cls(self.parsed_graph)

        # Instantiate Pavithra's GameState (will raise NotImplementedError if not implemented)
        self.current_game_state = self.game_state_cls(level_config, self.dfa_engine)
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

    def get_dfa_info(self) -> Dict[str, Any]:
        """
        Returns static metadata of the parsed DFA for visualization.
        """
        if self.parsed_graph is None:
            self.load_automaton()
        return extract_dfa_metadata(self.parsed_graph)


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
        """Catches pending module implementations from Jiya or Pavithra."""
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
            info = mgr.get_dfa_info()
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

    return app


# Default application instance for `flask run` or `python app.py`
app = create_app()

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
