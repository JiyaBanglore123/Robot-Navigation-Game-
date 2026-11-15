# System Integration Contract & Specifications

> **Formal Language and Automata Theory (FLA) — University Project**  
> **Topic:** DFA-Based Robot Navigation Game  
> **Document Owner:** Ankur (Person 2 — Flask Backend & Frontend Lead)

---

## 1. Architectural Overview & Team Boundaries

The project architecture strictly decouples the three core modules so that each team member can implement, test, and maintain their assigned responsibilities independently:

```
                      ┌─────────────────────────────────────────┐
                      │          Browser Frontend (GUI)         │
                      │  HTML5 + CSS3 + Vanilla JavaScript      │
                      │  (Ankur - Person 2)                     │
                      └────────────────────┬────────────────────┘
                                           │ HTTP REST / JSON
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │          Flask Application Server       │
                      │  app.py, GameManager, Error Handling    │
                      │  (Ankur - Person 2)                     │
                      └─────────────┬───────────────────────────┘
                                    │
          ┌─────────────────────────┴─────────────────────────┐
          ▼                                                   ▼
┌───────────────────────────────┐           ┌───────────────────────────────┐
│     Automata DFA Engine       │           │      Game State Manager       │
│  automata/dfa_engine.py       │           │  game/game_state.py           │
│  (Jiya - Person 1)            │           │  game/grid_config.py          │
│  * Processes DFA transitions  │◄──────────┤  (Pavithra - Person 3)        │
│  * Checks accepting & crash   │           │  * Grid & Obstacle layout     │
└───────────────▲───────────────┘           │  * Position synchronization   │
                │                           └───────────────────────────────┘
┌───────────────┴───────────────┐
│       JFLAP DFA Parser        │
│  robot_navigation_dfa.jff     │
│  automata/jff_parser.py       │
│  (Shared / Ankur integrated)  │
└───────────────────────────────┘
```

---

## 2. Team Member Contracts & Signatures

### 2.1 Person 1 — Jiya (Automata Transition Engine)

Module file: `src/robot_navigation/automata/dfa_engine.py`

Status: implemented and covered by `tests/test_dfa_engine.py`.

#### Interface Contract:
```python
from typing import Optional, TypedDict
import networkx as nx

class TransitionResult(TypedDict):
    next_state: Optional[str]
    status: str       # One of: 'PLAYING', 'CRASHED', 'WON', 'INVALID'
    message: str

class DFAEngine:
    def __init__(self, graph: nx.MultiDiGraph):
        """
        Initialize the DFA execution engine.
        1. Store parsed NetworkX MultiDiGraph.
        2. Extract initial state (e.g. '0' or 'q00').
        3. Extract accepting states set (e.g. {'12'} or {'q33'}).
        4. Construct fast transition lookup table (state, symbol) -> next_state.
        5. Verify alphabet { 'U', 'D', 'L', 'R' }.
        """
        ...

    def process_movement(self, current_state: str, movement: str) -> TransitionResult:
        """
        Process one movement symbol using the DFA.
        :param current_state: Current state name or ID (e.g. 'q00', 'q12')
        :param movement: DFA input symbol from alphabet {'U', 'D', 'L', 'R'}
        :return: TransitionResult dictionary:
            - next_state: target state name (or None if invalid symbol)
            - status: 'PLAYING', 'CRASHED', 'WON', or 'INVALID'
            - message: human-readable status feedback
        """
        ...
```

#### Transition Result Status Codes:
- `PLAYING`: Transition was valid and robot moved to a non-accepting, non-crash state.
- `CRASHED`: Destination is the sink/trap state (`Crash`).
- `WON`: Destination is an accepting final state (`q33`).
- `INVALID`: Movement symbol is outside alphabet $\Sigma$ or not defined.

---

### 2.2 Person 3 — Pavithra (Grid & Game State Coordinator)

Module files: `src/robot_navigation/game/grid_config.py` and
`src/robot_navigation/game/game_state.py`

#### Grid Configuration Contract (`game/grid_config.py`):
```python
from typing import TypedDict

class LevelConfig(TypedDict):
    rows: int
    cols: int
    start: str          # Must match initial DFA state, e.g. 'q00'
    goal: str           # Must match final DFA state, e.g. 'q33'
    obstacles: list[str]# Obstacle states/positions, e.g. ['q11', 'q22', 'q31']

LEVELS: dict[int, LevelConfig] = {
    # Level 1 (4x4) and the configured obstacles are implemented.
}
```

#### Game State Contract (`game/game_state.py`):
```python
from typing import Optional
from automata.dfa_engine import DFAEngine
from game.grid_config import LevelConfig

class GameState:
    def __init__(self, level_config: LevelConfig, dfa_engine: DFAEngine):
        """
        Initialize a game session:
        1. Store level_config and dfa_engine instance.
        2. Set current_state to level_config['start'].
        3. Initialize move_counter to 0.
        4. Set game status to 'READY' or 'PLAYING'.
        5. Maintain bidirectional synchronization between grid position (r, c)
           and DFA state name 'q<r><c>'.
        """
        ...

    def move(self, direction: str) -> dict:
        """
        Coordinates one movement operation:
        1. Check if game is already over (CRASHED or WON); reject move if so.
        2. Invoke dfa_engine.process_movement(self.current_state, direction).
        3. Update self.current_state = result['next_state'].
        4. Increment move_counter.
        5. Synchronize robot position with grid cell.
        6. Return updated get_state() dictionary.
        """
        ...

    def reset(self) -> None:
        """
        Restore game to its initial configuration:
        - current_state = level_config['start']
        - move_counter = 0
        - status = 'READY'
        """
        ...

    def get_state(self) -> dict:
        """
        Return a JSON-serializable dictionary of the current state:
        {
            "current_state": str,      # e.g. "q12"
            "robot_position": [r, c],  # e.g. [1, 2]
            "status": str,              # "READY", "MOVING", "BLOCKED", "CRASHED", "WON"
            "move_count": int,          # e.g. 5
            "goal_position": [r, c],    # e.g. [3, 3]
            "obstacles": [[r, c], ...], # obstacle coordinates
            "rows": int,
            "cols": int
        }
        """
        ...
```

---

### 2.3 Person 2 — Ankur (Flask Backend, REST API, GUI & Integration)

Implemented files:
- `src/robot_navigation/app.py`: Flask application factory, REST endpoints, `GameManager` session lifecycle.
- `src/robot_navigation/automata/jff_parser.py`: JFLAP parser adapter and graph metadata extractor.
- `src/robot_navigation/config/settings.py`: Configurable directions, file paths, host, and port.
- `src/robot_navigation/web/templates/index.html`: Responsive single-page retro terminal UI.
- `src/robot_navigation/web/static/css/style.css`: Theme styling, animations (CRT glitch, slide, bump, crash).
- `src/robot_navigation/web/static/js/game.js`: Centralized API layer, Web Audio synthesizer, keyboard handler.
- `run.sh` / `run.bat`: Cross-platform startup scripts.
- `tests/test_api.py`: Automated Flask API test suite using dependency injection mocks.

---

## 3. Direction & Symbol Mapping Specification

The browser UI allows players to use Arrow keys or WASD (`UP`, `DOWN`, `LEFT`, `RIGHT`).  
The Flask backend maps these to the formal DFA alphabet $\Sigma$ via `config/settings.py`:

| Frontend Direction | Keyboard Keys | DFA Symbol ($\Sigma$) | Semantic Meaning |
|---|---|---|---|
| `UP` | `▲` / `W` | `U` | Move one row North ($r - 1$) |
| `DOWN` | `▼` / `S` | `D` | Move one row South ($r + 1$) |
| `LEFT` | `◀` / `A` | `L` | Move one column West ($c - 1$) |
| `RIGHT` | `▶` / `D` | `R` | Move one column East ($c + 1$) |

---

## 4. REST API Endpoint Specifications

All endpoints use standard JSON payloads and return structured responses.

### 4.1 Start Game
- **Endpoint:** `POST /api/game/start`
- **Request Body:**
  ```json
  {
    "level": 1
  }
  ```
- **Success Response (`200 OK`):**
  ```json
  {
    "success": true,
    "level": 1,
    "state": {
      "current_state": "q00",
      "robot_position": [0, 0],
      "status": "READY",
      "move_count": 0,
      "goal_position": [3, 3],
      "obstacles": [[1, 1], [2, 2], [3, 1]],
      "rows": 4,
      "cols": 4
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Missing `level` or invalid integer.
  - `404 Not Found`: Level not defined in `LEVELS`.
  - `501 Not Implemented`: an unavailable application component raised `NotImplementedError`.

---

### 4.2 Process Movement
- **Endpoint:** `POST /api/game/move`
- **Request Body:**
  ```json
  {
    "direction": "UP"
  }
  ```
- **Success Response (`200 OK`):**
  ```json
  {
    "success": true,
    "direction": "UP",
    "symbol": "U",
    "state": {
      "current_state": "q00",
      "robot_position": [0, 0],
      "status": "BLOCKED",
      "move_count": 1
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Missing `direction`, invalid direction string, or no active session.
  - `501 Not Implemented`: an unavailable movement component raised `NotImplementedError`.

---

### 4.3 Get Game State
- **Endpoint:** `GET /api/game/state`
- **Success Response (`200 OK`):**
  ```json
  {
    "success": true,
    "state": {
      "current_state": "q12",
      "robot_position": [1, 2],
      "status": "MOVING",
      "move_count": 3
    }
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: No active session started.
  - `501 Not Implemented`: an unavailable state component raised `NotImplementedError`.

---

### 4.4 Reset Game
- **Endpoint:** `POST /api/game/reset`
- **Success Response (`200 OK`):**
  ```json
  {
    "success": true,
    "message": "Game session successfully reset.",
    "state": {
      "current_state": "q00",
      "robot_position": [0, 0],
      "status": "READY",
      "move_count": 0
    }
  }
  ```

---

### 4.5 DFA Automaton Info (For DFA Viewer)
- **Endpoint:** `GET /api/dfa/info`
- **Success Response (`200 OK`):**
  ```json
  {
    "success": true,
    "data": {
      "alphabet": ["D", "L", "R", "U"],
      "initial_state": "q00",
      "final_states": ["q33"],
      "states": [
        { "id": "0", "name": "q00", "initial": true, "final": false },
        { "id": "13", "name": "Crash", "initial": false, "final": false }
      ],
      "transition_table": {
        "q00": { "U": "q00", "D": "q10", "L": "q00", "R": "q01" }
      }
    }
  }
  ```

---

## 5. State & Position Mapping Conventions

1. **Grid Coordinates:** 0-indexed `[row, col]`. Row 0 is the top row; Column 0 is the leftmost column.
2. **State Naming in JFLAP DFA:**
   - Free cell at `(r, c)` has DFA state name `q<r><c>`.
   - Start cell: `(0, 0)` $\rightarrow$ State `q00` (ID `0`, `initial=True`).
   - Goal cell: `(3, 3)` $\rightarrow$ State `q33` (ID `12`, `final=True`).
   - Obstacles: Missing from grid coordinates and mapped to the trap state `Crash` (ID `13`).
3. **Wall Bumps (Self-Loops):**
   - When the robot moves into an exterior boundary wall, the DFA transitions from state `qrc` back to `qrc`.
   - The frontend detects this as `BLOCKED` (amber highlight and bounce animation).
4. **Crash (Trap State):**
   - When moving into an obstacle, the DFA transitions to state `Crash`.
   - All subsequent movements from `Crash` self-loop to `Crash` on all input symbols $\{U, D, L, R\}$.
   - The game ends with `STRING REJECTED`.

---

## 6. Integration Status and Verification

Jiya's DFA engine and Pavithra's grid/game-state modules are implemented. The Flask
`GameManager` loads the JFLAP file, injects its parsed graph into `DFAEngine`, and
routes movements through `GameState`. The root-level `robot_navigation_dfa.jff` is
preferred when present; `assets/dfa/robot_navigation_dfa.jff` is the fallback.

Run `python -m pytest -q` to validate unit and integration behavior, then launch the
application with `run.bat` on Windows or `./run.sh` on Linux.
