# 🤖 Robot Navigation Game — GUI Design Document

> A grid game where every key press is an input symbol and every robot move is a DFA transition.
> This document covers the **frontend**: screens, flow, animations, and how the GUI talks to the DFA.

---

## 1. Design Concept

**Theme:** *Retro terminal meets friendly robot.*
Think old-school green-on-black boot screens, but with a cute robot named **DFA-9** ("Dee") as the mascot.

**Why this theme works for an automata project**
- A terminal look makes the "state machine" feel natural.
- The robot's *state* is always visible, so the audience literally sees the DFA running.
- Humour (Dee's dialogue) keeps a technical demo fun.

**Design pillars**
1. **Show the automaton.** Current state, input string and transition are always on screen.
2. **Instant feedback.** Every input gets an animation within 100 ms.
3. **Playful, not cluttered.** Few colours, big shapes, short text.

---

## 2. Tech Stack (pick one)

| Option | Best for | Notes |
|---|---|---|
| **Pygame (Python)** | Easiest to connect to the Python DFA | Animations done manually with timers |
| **Tkinter (Python)** | Simplest, lowest risk | Fewer animation options, still fine |
| **HTML + CSS + JS** | Best-looking transitions | DFA table copied to JSON, or served via Flask |

**Recommendation:** Pygame, since the DFA is already Python and it handles every animation below.
All timings in this document are in milliseconds so they work in any stack.

---

## 3. Colour Palette & Fonts

| Role | Colour | Hex |
|---|---|---|
| Background | Deep navy-black | `#0B0F1A` |
| Grid lines | Dim slate | `#1F2A44` |
| Robot / primary | Cyan | `#00E5FF` |
| Goal / success | Neon green | `#39FF14` |
| Obstacle / crash | Red | `#FF3B3B` |
| Wall bump / warning | Amber | `#FFB300` |
| Text | Off-white | `#E6F1FF` |

**Fonts:** `Press Start 2P` (titles, retro feel) and `JetBrains Mono` or `Courier New` (body, terminal text).

---

## 4. Screen Map & Flow

```
 BOOT SEQUENCE ──► TITLE SCREEN ──► LEVEL SELECT ──► GAME SCREEN ──► RESULT POPUP
                        │                                  ▲              │
                        ├──► HOW IT WORKS                  └── Retry/Next ┘
                        └──► DFA VIEWER (table + diagram)
```

| # | Screen | Purpose |
|---|---|---|
| 1 | Boot Sequence | Fun intro, loads the DFA (5–6 s, skippable) |
| 2 | Title Screen | Main menu |
| 3 | How It Works | Explains DFA ↔ game in 3 slides |
| 4 | Level Select | Choose a grid |
| 5 | Game Screen | The main play area |
| 6 | Result Popup | Win / Crash summary |
| 7 | DFA Viewer | Transition table + JFLAP diagram, live-highlighted |

---

## 5. 🎬 Screen 1 — The Boot Sequence (the fun intro)

This is the first thing the audience sees, so it gets the most polish.
**Press any key at any time to skip.**

### Timeline

| Time | What happens | Transition / effect |
|---|---|---|
| 0.0 s | Black screen, a blinking cursor `█` | Cursor blinks every 500 ms |
| 0.5 s | Text **types out** line by line, ~35 ms per character | Typewriter effect + soft key-click sound |
| 3.0 s | Progress bar fills: `[██████████] 100%` | Bar fills in steps, each step flashes brighter |
| 3.8 s | Screen **glitches** (2 quick horizontal slices shift, colours split) | Glitch lasts 250 ms |
| 4.1 s | Robot face appears, **eyes boot up**: dot → line → open eyes | Eyes blink once |
| 4.8 s | Dee says a line (typed): *"Hi! I'm Dee. Please don't walk me into a wall."* | Typewriter, speech bubble pops with a small bounce |
| 5.8 s | `PRESS ANY KEY TO START` pulses | Fade in/out loop, 1 s cycle |
| On key | Screen **CRT-shuts off** (squashes to a horizontal line, then a dot) | 400 ms, then Title fades in |

### Boot text (typed line by line)

```
> BOOTING DFA-9 ...................... OK
> LOADING ALPHABET {U, D, L, R} ...... OK
> BUILDING STATE MAP (14 states) ..... OK
> CHECKING WALLS ..................... OK
> CHECKING OBSTACLES ................. OK  (3 found. rude.)
> DETERMINISM VERIFIED ............... YES  (no confusion allowed)
> LOCATING GOAL ...................... FOUND
> WAKING UP ROBOT .................... ☺
```

### Fun details
- Random "tip" under the progress bar each run, e.g. *"Fun fact: a DFA has exactly one next state for every input."*
- Typos that **self-correct** (types `BOOTNG`, backspaces, fixes to `BOOTING`) once in the sequence.
- **Easter egg:** typing `UUDDLRLR` on the boot screen (Konami-style) makes Dee do a little dance and shows *"You found a secret path! It is still a valid string."*

---

## 6. Screen 2 — Title Screen

```
┌──────────────────────────────────────────┐
│                                          │
│        R O B O T   N A V I G A T I O N   │
│                  G A M E                 │
│                                          │
│                  ( 🤖 )                  │
│                                          │
│              ▶  PLAY                     │
│                 HOW IT WORKS             │
│                 DFA VIEWER               │
│                 QUIT                     │
│                                          │
│   Built with finite automata  ·  Team X  │
└──────────────────────────────────────────┘
```

**Transitions & behaviour**
- Title letters **drop in one by one** (40 ms stagger) with a tiny bounce.
- Background: a slow-moving faint grid with a few tiny "states" (circles) drifting and connecting with arrows, like a DFA diagram in the background.
- Dee idles: blinks every 3 s, looks left/right.
- Menu items: hovered item gets a `▶` marker and a cyan glow. Up/Down arrows and Enter also work.
- Clicking an item: the screen **slides left** (250 ms) to the next screen.

---

## 7. Screen 3 — How It Works

Three slides, navigated with Next / Back (slide transition: **slide + fade**, 300 ms).

1. **Inputs are moves.** Show the four arrow keys labelled U / D / L / R. *"Each key press is a symbol from the alphabet."*
2. **Cells are states.** A mini 3×3 grid where each cell is labelled `q00 … q22`. *"Where the robot stands is its state."*
3. **Rules are transitions.** Three examples animated in a loop:
   - Free cell → robot moves, state changes
   - Wall → robot stays (self-loop)
   - Obstacle → `Crash` (trap state)

---

## 8. Screen 4 — Level Select

Three cards side by side, each with a small map preview.

| Level | Grid | Obstacles | Description |
|---|---|---|---|
| 1 — Warm-up | 4×4 | 3 | The JFLAP-designed map |
| 2 — Maze Runner | 6×6 | 8 | Needs planning |
| 3 — Nightmare | 8×8 | 16 | For show-offs |

**Behaviour**
- Cards **fan in** from the bottom (80 ms stagger).
- Hover: card lifts 8 px and glows.
- Locked levels show a 🔒 and unlock after beating the previous one.
- Each card shows the best (fewest) move count.

> Only Level 1 needs a matching JFLAP file. Other levels can be generated by the same code that builds the transition table.

---

## 9. Screen 5 — Game Screen (main)

### Layout

```
┌────────────────────────────────────────────────────────────┐
│  LEVEL 1                         ⏱ 00:23      [⟲ Reset] [≡] │
├───────────────────────────────────┬────────────────────────┤
│                                   │  DFA STATUS            │
│   S  ·  ·  ·                      │  ─────────────────     │
│   ·  ▓  ·  ·        GRID         │  State     : q12       │
│   ·  ·  ▓  ·                      │  Position  : (1, 2)    │
│   ·  ▓  ·  ⚑                      │  Last move : R         │
│                                   │  Status    : MOVING    │
│                                   │  Moves     : 7         │
│                                   │                        │
│                                   │  INPUT STRING          │
│                                   │  R R D L R R           │
│                                   │                        │
│                                   │  💬 "Nice move!"       │
├───────────────────────────────────┴────────────────────────┤
│              [ ▲ ]                                          │
│        [ ◀ ] [ ▼ ] [ ▶ ]        [↶ Undo]  [📋 Table]        │
└────────────────────────────────────────────────────────────┘
```

### Grid visuals

| Element | Look |
|---|---|
| Start cell | Dim cyan ring with `S` |
| Free cell | Dark tile with faint border |
| Obstacle | Red tile with a ✖ or cracked look |
| Goal | Green flag, soft pulsing glow |
| Robot | Cyan rounded square with eyes, facing the last move direction |
| Visited cells | Faint cyan trail that fades slowly |

### Controls
- **Keyboard:** Arrow keys or WASD
- **On-screen D-pad:** buttons for mouse and touch
- **Reset:** back to `q00`, clears the input string
- **Undo:** removes the last symbol and replays the string from `q00` (valid because a DFA is deterministic)

### Status panel

| Status | Shown when | Colour |
|---|---|---|
| MOVING | State changed to a free cell | Cyan |
| BLOCKED | State did not change (wall bump) | Amber |
| CRASHED | State is `Crash` | Red |
| GOAL REACHED | State is the accepting state | Green |

> **Tip for the DFA link:** the GUI can detect "blocked" with `new_state == old_state`, so no extra logic is needed.

### Move animations

| Event | Animation | Duration |
|---|---|---|
| Valid move | Robot **slides** to the next cell with ease-out; trail tile lights up | 180 ms |
| Wall bump | Robot nudges toward the wall and **bounces back**; panel flashes amber | 200 ms |
| Obstacle hit | Robot moves in, **screen shakes**, tile flashes red, robot **spins and fades** | 600 ms |
| Goal reached | Robot jumps twice, green **confetti** bursts, grid dims behind the popup | 1000 ms |
| New input symbol | Symbol **pops into** the input string with a small scale-up | 120 ms |

Inputs are ignored while an animation is running (or queued, max 2) so key spam cannot break the state.

### Dee's dialogue (random line per event)

| Event | Lines |
|---|---|
| Valid move | "Beep boop, moving!" · "Nice move!" · "Transition accepted." |
| Wall bump | "Ouch. That was a wall." · "Self-loop activated." · "I stayed in the same state. Again." |
| Obstacle | "Well, that went poorly." · "Entered trap state. No exit." · "I regret everything." |
| Goal | "We did it! Accepting state reached!" · "String accepted! 🎉" |
| Idle 10 s | "Are you still there?" · "Take your time. I'm a finite machine, not impatient." |

---

## 10. Screen 6 — Result Popup

Appears over the dimmed game screen (**scale-up from centre, 250 ms**).

**Win**
```
        🎉  GOAL REACHED!  🎉
   Final state : q33  (accepting)
   Input string: R R R D D D
   Moves       : 6      ★ ★ ★
   Verdict     : STRING ACCEPTED
      [ Next Level ]   [ Retry ]   [ Menu ]
```

**Crash**
```
        💥  ROBOT CRASHED  💥
   Final state : Crash  (trap state)
   Input string: D D R R R D
   Verdict     : STRING REJECTED
      [ Retry ]   [ Undo last move ]   [ Menu ]
```

- Star rating: ★★★ = optimal moves, ★★ = within +2, ★ = anything else.
- Showing **ACCEPTED / REJECTED** ties the game back to automata theory for the evaluators.

---

## 11. Screen 7 — DFA Viewer

Two tabs: **Transition Table** and **Diagram**.

**Transition Table tab**
- Rows = states, columns = `U D L R`.
- The **current state's row is highlighted live** while the game runs, and the cell for the last input flashes.
- Start state marked `→`, goal marked `*`, trap state in red.

**Diagram tab**
- JFLAP screenshot or exported image of the DFA.
- Optional upgrade: draw the diagram in the GUI and glow the active state circle.

**String Tester (bonus)**
- Text box: type `RRRDDD`, press Run.
- The robot replays the string step by step (400 ms per step) and ends with ACCEPTED or REJECTED.

---

## 12. Transition Cheat Sheet

| From → To | Effect | Duration |
|---|---|---|
| Boot → Title | CRT shut-off, then fade in | 400 ms |
| Title → any menu page | Slide left | 250 ms |
| Any page → back | Slide right | 250 ms |
| Level card → Game | Card **expands** to fill the screen, grid fades in | 400 ms |
| Game → Result | Dim + popup scale-up | 250 ms |
| Result → Next Level | Wipe left to right | 350 ms |

**Rule:** all transitions use **ease-in-out** and stay under 500 ms so the game never feels slow.

---

## 13. Sound (optional but fun)

| Event | Sound |
|---|---|
| Typing in boot | Soft key click |
| Move | Short blip |
| Wall bump | Low thud |
| Crash | Descending "wah-wah" |
| Goal | Rising 3-note chime |

Add a 🔊 / 🔇 toggle in the top bar. Free sound effects: freesound.org or generate with `jsfxr` / `sfxr`.

---

## 14. How the GUI Talks to the DFA

The GUI never decides what a move means. It only sends an input symbol and reads the new state.

```python
# Interface the GUI expects from Member 1's DFA module
dfa = RobotDFA()          # starts at q00
dfa.reset()               # back to start
dfa.step("R")             # returns new state, e.g. "q01"
dfa.state                 # current state name
dfa.is_goal()             # True if in the accepting state
dfa.is_crashed()          # True if in the trap state
dfa.position()            # (row, col) for the current state, None if Crash
```

**Game loop in plain words**
1. Player presses a key → map it to `U/D/L/R`.
2. Call `dfa.step(symbol)`.
3. Compare old and new state → choose animation (move, bump, crash, goal).
4. Update the status panel, input string, and DFA Viewer highlight.
5. If `is_goal()` or `is_crashed()` → show the result popup.

---

## 15. Suggested Folder Structure

```
robot_navigation_game/
├── dfa/
│   ├── robot_dfa.py          # transition table + RobotDFA class (Member 1)
│   └── robot_navigation_dfa.jff
├── gui/
│   ├── main.py               # screen manager, game loop
│   ├── screens/
│   │   ├── boot.py
│   │   ├── title.py
│   │   ├── how_it_works.py
│   │   ├── level_select.py
│   │   ├── game.py
│   │   ├── result.py
│   │   └── dfa_viewer.py
│   └── effects.py            # typewriter, glitch, shake, confetti
├── assets/
│   ├── fonts/
│   ├── sounds/
│   └── sprites/
├── tests/
│   └── test_dfa.py
└── README.md
```

---

## 16. Build Order (for the team)

1. **Grid + robot moving** with arrow keys, wired to the DFA (get this working first).
2. Status panel and input string.
3. Result popup (win / crash).
4. Title screen and screen-to-screen transitions.
5. **Boot sequence** (typewriter, progress bar, glitch).
6. DFA Viewer with live highlight.
7. Level select and extra levels.
8. Sound, Easter eggs and polish.

---

## 17. Demo Script (for the presentation)

1. Let the **boot sequence** play. It gets the audience's attention.
2. Say: *"Every key press is an input symbol; every cell is a state."*
3. Walk the robot: `R R R D D D` and show the state changing in the panel.
4. Bump a wall deliberately: *"Same state, a self-loop."*
5. Hit an obstacle: *"Trap state. The DFA rejects the string."*
6. Open the **DFA Viewer** to show the table matches the JFLAP diagram.
7. Use the **String Tester** to run `RRRDDD` and show **ACCEPTED**.

---

## 18. Checklist

- [ ] Every input produces a visible animation
- [ ] GUI state always matches `dfa.state`
- [ ] Wall bumps show **BLOCKED**, not a crash
- [ ] Crash state cannot be left (all keys ignored until Reset)
- [ ] Boot sequence is skippable
- [ ] Transition table in the viewer matches the JFLAP file
- [ ] Works at 1280×720 and fullscreen
