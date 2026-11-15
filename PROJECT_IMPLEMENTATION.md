# Robot Navigation Game — Implementation Guide

## Project summary

The Robot Navigation Game is a browser-based demonstration of deterministic finite
automata (DFA). Each movement command is an input symbol, and the robot's movement
is a state transition. The project includes a Flask API, a browser interface, a
JFLAP DFA parser and execution engine, a grid/game-state manager, and automated
tests.

The current Level 1 board is a 4 × 4 grid. The robot starts at `q00`, the goal is
the accepting state `q33`, and the obstacle cells are `q11`, `q22`, and `q31`.
Moving into an obstacle transitions to the `Crash` sink state.

## Architecture

```text
Browser UI (HTML, CSS, JavaScript)
                 │ JSON over HTTP
                 ▼
Flask app and GameManager
          ┌──────┴──────┐
          ▼             ▼
  JFLAP parser      GameState
          │             │
          ▼             │
      DFAEngine ◄───────┘
          │
          ▼
  NetworkX DFA graph
```

### Main components

- `src/robot_navigation/app.py` creates the Flask app and REST API. Its
  `GameManager` loads the JFLAP file, constructs the DFA engine, starts levels,
  and coordinates moves and resets.
- `src/robot_navigation/automata/jff_parser.py` parses JFLAP XML into a NetworkX
  `MultiDiGraph`. It extracts state names, initial/final-state metadata, and
  labeled transitions, and rejects malformed or nondeterministic DFA input.
- `src/robot_navigation/automata/dfa_engine.py` builds a state-and-symbol
  transition lookup from that graph and returns the next state and outcome for
  each movement.
- `src/robot_navigation/game/grid_config.py` defines Level 1 and converts
  between grid coordinates and names such as `q12`.
- `src/robot_navigation/game/game_state.py` applies DFA results to the game,
  synchronizes the robot position, tracks the input string and path, and handles
  reset and terminal game states.
- `src/robot_navigation/config/settings.py` defines direction mappings, server
  settings, and the DFA file path.
- `src/robot_navigation/web/templates/index.html`,
  `src/robot_navigation/web/static/css/style.css`, and
  `src/robot_navigation/web/static/js/game.js` provide the game interface, DFA
  viewer, string tester, keyboard controls, and API client.

## DFA and gameplay behavior

The input alphabet is `Σ = {U, D, L, R}`:

| API direction | DFA symbol | Grid change |
|---|---|---|
| `UP` | `U` | Row −1 |
| `DOWN` | `D` | Row +1 |
| `LEFT` | `L` | Column −1 |
| `RIGHT` | `R` | Column +1 |

The DFA engine accepts either JFLAP state IDs or state names. It validates
movement symbols, looks up the transition, and classifies its result:

- `PLAYING`: a valid transition to a non-final, non-crash state.
- `CRASHED`: the transition entered `Crash`.
- `WON`: the transition entered an accepting state.
- `INVALID`: the movement, state, or transition is not valid.

The game-state layer maps a valid self-loop at a boundary to `BLOCKED`, leaves
the robot at its last valid position after a crash, and rejects further moves
after `CRASHED` or `WON` until the game is reset. Invalid moves do not increment
the move counter. Game snapshots include the current state, robot and goal
positions, obstacles, move count, input string, path, crash position, and
terminal-state indicator.

The JFLAP file at the project root (`robot_navigation_dfa.jff`) is preferred when
present. `assets/robot_navigation_dfa.jff` is the fallback. `DFA_JFF_PATH` can
override both paths.

## Browser interface

The interface includes:

- A boot sequence and title/menu screens.
- A playable grid with keyboard and on-screen direction controls.
- Status feedback for ready, moving, blocked, crashed, and won states.
- A DFA viewer with the transition table and automaton tuple.
- An input-string tester that evaluates strings against the loaded DFA.
- A request-error notice that reports API or network errors without suggesting
  that project modules are still pending.

## REST API

All game endpoints use JSON except the page and static assets.

| Method and route | Purpose |
|---|---|
| `GET /` | Serve the browser interface. |
| `POST /api/game/start` | Start a level. Request: `{"level": 1}`. |
| `POST /api/game/move` | Move the robot. Request: `{"direction": "RIGHT"}`. |
| `GET /api/game/state` | Return the active game's state snapshot. |
| `POST /api/game/reset` | Reset the active game. |
| `GET /api/dfa/info` | Return DFA states, alphabet, transition table, initial state, and final states for the viewer. |

Successful game responses include `success: true` and a `state` object.
Invalid input and missing game sessions return structured JSON errors with
appropriate HTTP status codes.

## Run the application

### Windows

From the repository root, run:

```cmd
run.bat
```

The script creates `.venv` if necessary, installs `requirements.txt`, and starts
Flask. Open [http://127.0.0.1:5000](http://127.0.0.1:5000). To customize the
address, set `HOST` or `PORT` before running the script.

### Linux or Ubuntu

```bash
chmod +x run.sh
./run.sh
```

The script creates a virtual environment, installs dependencies, and starts the
server. For example, `HOST=0.0.0.0 PORT=8080 ./run.sh` changes the bind address
and port.

### Manual launch

After installing `requirements.txt`, run from the project root:

```bash
python -m flask --app app run --host 127.0.0.1 --port 5000
```

## Tests and verification

Run the full test suite from the project root:

```bash
python -m pytest tests/ -v
```

The tests cover API validation and mock boundaries, DFA state and transition
handling, crash and acceptance behavior, grid configuration, game-state updates,
and a real-engine game flow through the Flask test client. The completed suite
was verified with **33 passing tests and 2 passing subtests**.

## Current scope and operational notes

- Level 1 is the configured playable level; additional levels are not currently
  defined.
- Game state is held in the running Flask process rather than persisted to a
  database. The application is intended for local project/demo use.
- Flask's built-in development server is used by the launch scripts and is not
  intended as a production deployment server.
