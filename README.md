# 🤖 DFA-Based Robot Navigation Game

> **Formal Language and Automata Theory (FLA) — University Project**  
> An interactive web application where every key press represents an input symbol from alphabet $\Sigma = \{U, D, L, R\}$, and every robot move across the grid represents a formal state transition $\delta(q, \sigma) \to q'$ in a Deterministic Finite Automaton (DFA).

---

## 1. Project Overview

The **DFA-Based Robot Navigation Game** illustrates core theoretical concepts of automata theory through gamification:
- **Alphabet ($\Sigma$):** The set of valid input symbols $\{U, D, L, R\}$ corresponding to Up, Down, Left, and Right movements.
- **States ($Q$):** Grid cells corresponding to states (e.g. $q_{00}$ to $q_{33}$) plus a designated trap/sink state `Crash`.
- **Start State ($q_0$):** Starting cell $q_{00}$.
- **Accepting States ($F$):** Destination goal cell $q_{33}$. Strings reaching this state are **accepted**.
- **Trap State:** Obstacle collision leads to `Crash`, where all transitions self-loop, resulting in string **rejection**.
- **Self-Loops:** Boundary walls keep the robot in its current cell with a `BLOCKED` status.

The visual theme follows a **retro terminal aesthetic** featuring the mascot **DFA-9 ("Dee")**.

---

## 2. Architecture

The system uses a modular 3-tier architecture with clear separation of concerns:

```
┌────────────────────────────────────────────────────────┐
│                   Browser Client (GUI)                 │
│         HTML5 · Retro Terminal CSS3 · Vanilla JS       │
│                Implemented by Ankur                    │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP REST API (JSON)
                            ▼
┌────────────────────────────────────────────────────────┐
│                 Flask Application Server               │
│         app.py · GameManager · config/settings.py      │
│                Implemented by Ankur                    │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
              ▼                            ▼
┌───────────────────────────┐┌───────────────────────────┐
│     Automata DFA Engine   ││     Game State Manager    │
│   automata/dfa_engine.py  ││     game/game_state.py    │
│   automata/jff_parser.py  ││     game/grid_config.py   │
│   Assigned to Jiya        ││   Assigned to Pavithra    │
└───────────────────────────┘└───────────────────────────┘
```

---

## 3. Directory Structure

```text
Robot-Navigation-Game/
│
├── app.py                      # Root convenience runner
├── requirements.txt            # Project dependencies (Flask, NetworkX, Matplotlib, pytest)
├── pytest.ini                  # Pytest configuration
├── run.sh                      # One-click execution script for Linux / Ubuntu
├── run.bat                     # One-click execution script for Windows
├── README.md                   # Project documentation
├── INTEGRATION.md              # Team contracts, JSON specs, and module boundaries
│
├── assets/
│   └── robot_navigation_dfa.jff # Checked-in JFLAP DFA fallback
├── robot_navigation_dfa.jff    # Project DFA used when present (Jiya)
│
├── docs/
│   └── robot_navigation_gui_design.md # GUI design guidelines
│
├── src/
│   └── robot_navigation/       # Primary application package
│       ├── __init__.py
│       ├── app.py              # Flask backend, GameManager, and REST routes
│       ├── automata/
│       │   ├── __init__.py
│       │   ├── jff_parser.py   # Consolidated NetworkX JFLAP parser & metadata extractor
│       │   └── dfa_engine.py   # DFA Engine (Jiya)
│       ├── game/
│       │   ├── __init__.py
│       │   ├── grid_config.py  # Grid config & levels (Pavithra)
│       │   └── game_state.py   # GameState manager (Pavithra)
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py     # Configuration, mappings, paths, host/port
│       └── web/
│           ├── templates/
│           │   └── index.html  # Retro terminal single-page interface
│           └── static/
│               ├── css/
│               │   └── style.css # Retro UI styling, animations, responsiveness
│               └── js/
│                   └── game.js   # Centralized API layer, Web Audio synthesizer
│
└── tests/
    ├── __init__.py
    ├── test_api.py             # API validation and mock-boundary tests
    ├── test_dfa_engine.py      # DFA transition and outcome tests
    └── test_game_state.py      # Grid, game state, and real API integration tests
```

---

## 4. Installation Instructions

### Prerequisites
- Python 3.10 or higher
- `git`
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Setup
Clone the repository:
```bash
git clone https://github.com/JiyaBanglore123/Robot-Navigation-Game-.git
cd Robot-Navigation-Game-
```

---

## 5. Running on Ubuntu / Linux

Use the provided executable bash script:
```bash
chmod +x run.sh
./run.sh
```

The script automatically:
1. Detects the project root.
2. Verifies Python 3 installation.
3. Creates `.venv` if not already present.
4. Installs/updates dependencies from `requirements.txt`.
5. Starts the Flask server at `http://127.0.0.1:5000`.

To run with custom host or port:
```bash
HOST=0.0.0.0 PORT=8080 ./run.sh
```

---

## 6. Running on Windows

Double-click `run.bat` or run from Command Prompt / PowerShell:
```cmd
run.bat
```

The batch script automatically:
1. Changes to the repository root directory.
2. Checks for `python` on `PATH`.
3. Creates `.venv` if needed.
4. Installs requirements.
5. Launches Flask on `http://127.0.0.1:5000`.

---

## 7. Flask REST API Documentation

### `GET /`
Renders the retro terminal frontend application.

### `POST /api/game/start`
Starts a new game session.
- **Request:**
  ```json
  { "level": 1 }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "success": true,
    "level": 1,
    "state": {
      "current_state": "q00",
      "robot_position": [0, 0],
      "status": "READY",
      "move_count": 0
    }
  }
  ```

### `POST /api/game/move`
Processes a movement direction.
- **Supported Directions:** `UP`, `DOWN`, `LEFT`, `RIGHT`
- **Request:**
  ```json
  { "direction": "UP" }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "success": true,
    "direction": "UP",
    "symbol": "U",
    "state": {
      "current_state": "q00",
      "status": "BLOCKED",
      "move_count": 1
    }
  }
  ```

### `GET /api/game/state`
Returns current session state.
- **Response (`200 OK`):**
  ```json
  {
    "success": true,
    "state": { "current_state": "q00", "move_count": 0, "status": "READY" }
  }
  ```

### `POST /api/game/reset`
Resets the active game session to initial conditions.

### `GET /api/dfa/info`
Returns static transition table, alphabet, initial state, and accepting states parsed from `robot_navigation_dfa.jff` (or the checked-in assets fallback) for visualization in the DFA Viewer.

---

## 8. Module Responsibilities (Strict Boundaries)

| Team Member | Role | Assigned Files | Status |
|---|---|---|---|
| **Jiya (Person 1)** | DFA Design & Transition Logic | `robot_navigation_dfa.jff`, `src/robot_navigation/automata/dfa_engine.py` | **Completed** |
| **Ankur (Person 2)** | Backend, API, Frontend, Integration | `src/robot_navigation/app.py`, `src/robot_navigation/web/`, `src/robot_navigation/config/`, `run.sh`, `run.bat`, `tests/` | **Completed** |
| **Pavithra (Person 3)** | Grid Config & Game State Coordination | `src/robot_navigation/game/grid_config.py`, `src/robot_navigation/game/game_state.py` | **Completed** |

---

## 9. Integration Instructions

The DFA engine, configured level, and game-state manager are integrated with the Flask
API. Start the server using `run.bat` on Windows or `./run.sh` on Linux, open
`http://127.0.0.1:5000`, and start Level 1 to play.

For full contract specifications, consult [INTEGRATION.md](INTEGRATION.md).

---

## 10. Implementation Status

The assigned DFA, game-state, and API work is implemented. The following checklist
records Jiya's completed deliverables:
- [x] Construct the transition lookup dictionary from the parsed NetworkX MultiDiGraph in `DFAEngine.__init__`.
- [x] Implement `DFAEngine.process_movement(current_state, movement)` and classify `PLAYING`, `CRASHED`, `WON`, and `INVALID` outcomes.
- [x] Add automata-specific test cases for transition correctness, accepting states, and crash detection.

---

## 11. Running Automated Tests

Run the unit, automata, game-state, and API test suites:
```bash
python -m pytest tests/ -v
```
