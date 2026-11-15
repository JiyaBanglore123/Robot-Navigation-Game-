/**
 * DFA-9 Robot Navigation Game — Frontend Controller & API Client
 *
 * Implements:
 * - Centralized Fetch API communication layer
 * - Screen switching and state management
 * - Keyboard and D-pad movement coordination with request locking
 * - Dynamic grid rendering and visual feedback
 * - Retro sound effects via Web Audio API synthesis
 * - Boot sequence and interactive DFA viewer
 */

'use strict';

function escapeHtml(value) {
  const element = document.createElement('span');
  element.textContent = value;
  return element.innerHTML;
}

// ============================================================================
// 1. CENTRALIZED API LAYER
// ============================================================================

const api = {
  /**
   * Start a new game session.
   * @param {number} level
   * @returns {Promise<Object>}
   */
  async startGame(level) {
    const response = await fetch('/api/game/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level })
    });

    let data;
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }

    if (!response.ok || data?.success === false) {
      throw { status: response.status, data: data || { error: 'The server returned an empty response.' } };
    }

    if (!data || typeof data !== 'object') {
      throw { status: response.status, data: { error: 'The server returned an invalid game payload.' } };
    }

    return data;
  },

  /**
   * Send a movement command.
   * @param {string} direction - UP, DOWN, LEFT, or RIGHT
   * @returns {Promise<Object>}
   */
  async sendMovement(direction) {
    const response = await fetch('/api/game/move', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction })
    });
    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, data };
    }
    return data;
  },

  /**
   * Fetch current game state.
   * @returns {Promise<Object>}
   */
  async getGameState() {
    const response = await fetch('/api/game/state');
    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, data };
    }
    return data;
  },

  /**
   * Reset the active game session.
   * @returns {Promise<Object>}
   */
  async resetGame() {
    const response = await fetch('/api/game/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, data };
    }
    return data;
  },

  /**
   * Fetch static DFA definition and transition table.
   * @returns {Promise<Object>}
   */
  async getDfaInfo(level) {
    const query = level === undefined ? '' : `?level=${encodeURIComponent(level)}`;
    const response = await fetch(`/api/dfa/info${query}`);
    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, data };
    }
    return data;
  },

  async getLevels() {
    const response = await fetch('/api/levels');
    const data = await response.json();
    if (!response.ok) {
      throw { status: response.status, data };
    }
    return data;
  }
};

// ============================================================================
// 2. AUDIO SYNTHESIS SYSTEM (Web Audio API)
// ============================================================================

class SoundManager {
  constructor() {
    this.enabled = true;
    this.audioCtx = null;
  }

  _initCtx() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.audioCtx = new AudioContext();
      }
    }
    if (this.audioCtx && this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  toggle() {
    this.enabled = !this.enabled;
    return this.enabled;
  }

  playMove() {
    if (!this.enabled) return;
    this._initCtx();
    if (!this.audioCtx) return;

    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(440, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, this.audioCtx.currentTime + 0.08);

    gain.gain.setValueAtTime(0.15, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.08);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.09);
  }

  playWallBump() {
    if (!this.enabled) return;
    this._initCtx();
    if (!this.audioCtx) return;

    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(140, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(60, this.audioCtx.currentTime + 0.12);

    gain.gain.setValueAtTime(0.3, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.12);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.13);
  }

  playCrash() {
    if (!this.enabled) return;
    this._initCtx();
    if (!this.audioCtx) return;

    const osc = this.audioCtx.createOscillator();
    const gain = this.audioCtx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(320, this.audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(40, this.audioCtx.currentTime + 0.35);

    gain.gain.setValueAtTime(0.3, this.audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + 0.35);

    osc.connect(gain);
    gain.connect(this.audioCtx.destination);
    osc.start();
    osc.stop(this.audioCtx.currentTime + 0.36);
  }

  playGoal() {
    if (!this.enabled) return;
    this._initCtx();
    if (!this.audioCtx) return;

    const notes = [523.25, 659.25, 783.99, 1046.5]; // C5, E5, G5, C6
    notes.forEach((freq, idx) => {
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = 'square';
      osc.frequency.value = freq;

      const startTime = this.audioCtx.currentTime + idx * 0.12;
      gain.gain.setValueAtTime(0.12, startTime);
      gain.gain.exponentialRampToValueAtTime(0.01, startTime + 0.2);

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start(startTime);
      osc.stop(startTime + 0.22);
    });
  }
}

const soundManager = new SoundManager();

// ============================================================================
// 3. DIALOGUE DICTIONARY (Dee's personality)
// ============================================================================

const DEE_DIALOGUES = {
  ready: [
    "Ready for instructions. Where shall we transition?",
    "Deterministic Finite Automaton online. Feed me symbols!",
    "Standing by at the configured initial state."
  ],
  moving: [
    "Beep boop, moving!",
    "Nice move!",
    "Transition accepted by the DFA.",
    "State updated smoothly.",
    "Advancing through the state graph."
  ],
  blocked: [
    "Ouch. That was a wall.",
    "Self-loop activated. I stayed in the same state.",
    "Boundary collision! The automaton held its ground.",
    "Can't move through walls. Transition returned to current cell."
  ],
  crashed: [
    "Well, that went poorly.",
    "Entered the trap state. No exit!",
    "I regret everything.",
    "Automaton rejected the string. Trap state triggered."
  ],
  won: [
    "We did it! Accepting state reached!",
    "String accepted! 🎉",
    "Formal proof accomplished! Safe path navigated.",
    "Goal state satisfied! Determinism wins!"
  ]
};

function getRandomDeeLine(category) {
  const lines = DEE_DIALOGUES[category] || DEE_DIALOGUES.ready;
  return lines[Math.floor(Math.random() * lines.length)];
}

// ============================================================================
// 4. CLIENT GAME CONTROLLER
// ============================================================================

class GameController {
  constructor() {
    // Session state
    this.currentLevel = null;
    this.currentGridSize = { rows: 0, cols: 0 };
    this.robotPosition = null;
    this.visitedPositions = new Set();
    this.renderedLevel = null;
    this.inputString = [];
    this.moveCount = 0;
    this.isProcessingMove = false;
    this.isGameOver = false;
    this.timerInterval = null;
    this.timerSeconds = 0;

    // DFA cached metadata
    this.dfaData = null;

    // DOM Elements
    this.screens = {
      boot: document.getElementById('screen-boot'),
      title: document.getElementById('screen-title'),
      how: document.getElementById('screen-how'),
      level: document.getElementById('screen-level'),
      game: document.getElementById('screen-game')
    };

    this.modals = {
      result: document.getElementById('modal-result'),
      dfa: document.getElementById('modal-dfa-viewer'),
      notice: document.getElementById('modal-notice')
    };

    this.gridElement = document.getElementById('board-grid');
    this.inputStringDisplay = document.getElementById('input-string-display');
    this.dialogueText = document.getElementById('dialogue-speech');
    this.statusBadge = document.getElementById('status-badge');
    this.statState = document.getElementById('stat-state');
    this.statPos = document.getElementById('stat-position');
    this.statLastMove = document.getElementById('stat-last-move');
    this.statMoves = document.getElementById('stat-moves');
    this.gameTimer = document.getElementById('game-timer');

    this.init();
  }

  init() {
    this.bindEvents();
    this.loadLevels();
    this.runBootSequence();
  }

  // --------------------------------------------------------------------------
  // Navigation & Screen Management
  // --------------------------------------------------------------------------
  showScreen(screenName) {
    Object.keys(this.screens).forEach(name => {
      if (name === screenName) {
        this.screens[name].classList.remove('hidden');
        this.screens[name].classList.add('active');
      } else {
        this.screens[name].classList.add('hidden');
        this.screens[name].classList.remove('active');
      }
    });
  }

  showModal(modalName) {
    if (this.modals[modalName]) {
      this.modals[modalName].classList.remove('hidden');
    }
  }

  closeModal(modalName) {
    if (this.modals[modalName]) {
      this.modals[modalName].classList.add('hidden');
    }
  }

  // --------------------------------------------------------------------------
  // Boot Sequence (Screen 1)
  // --------------------------------------------------------------------------
  runBootSequence() {
    const lines = [
      "> BOOTING DFA-9 ENGINE ................... OK",
      "> LOADING ALPHABET {U, D, L, R} ........... OK",
      "> PARSING JFLAP SPECIFICATION ............ OK",
      "> INITIALIZING DETERMINISTIC TRANSITIONS .. OK",
      "> CHECKING BOUNDARIES & TRAP STATES ...... OK",
      "> CALIBRATING ROBOT 'DEE' ................ READY"
    ];

    const linesContainer = document.getElementById('boot-lines');
    const progressContainer = document.getElementById('boot-progress-container');
    const progressBar = document.getElementById('boot-progress-bar');
    const progressPercent = document.getElementById('boot-progress-percent');
    const robotGraphic = document.getElementById('boot-robot-graphic');
    const bootPrompt = document.getElementById('boot-prompt');

    let currentLine = 0;
    this.bootSkipped = false;

    const printNextLine = () => {
      if (this.bootSkipped) return;

      if (currentLine < lines.length) {
        const lineEl = document.createElement('div');
        lineEl.textContent = lines[currentLine];
        linesContainer.appendChild(lineEl);
        currentLine++;
        setTimeout(printNextLine, 220);
      } else {
        // Show progress bar
        progressContainer.classList.remove('hidden');
        let progress = 0;
        const interval = setInterval(() => {
          if (this.bootSkipped) {
            clearInterval(interval);
            return;
          }
          progress += 10;
          progressBar.style.width = `${progress}%`;
          progressPercent.textContent = `${progress}%`;
          if (progress >= 100) {
            clearInterval(interval);
            robotGraphic.classList.remove('hidden');
            bootPrompt.classList.remove('hidden');
          }
        }, 60);
      }
    };

    setTimeout(printNextLine, 300);
  }

  skipBootSequence() {
    this.bootSkipped = true;
    this.showScreen('title');
  }

  // --------------------------------------------------------------------------
  // Event Bindings
  // --------------------------------------------------------------------------
  bindEvents() {
    // Boot sequence skip
    document.getElementById('btn-boot-skip').addEventListener('click', () => this.skipBootSequence());
    this.screens.boot.addEventListener('click', () => {
      const bootPrompt = document.getElementById('boot-prompt');
      if (!bootPrompt.classList.contains('hidden')) {
        this.showScreen('title');
      }
    });

    // Title menu navigation
    document.getElementById('btn-menu-play').addEventListener('click', () => this.showScreen('level'));
    document.getElementById('btn-menu-how').addEventListener('click', () => this.showScreen('how'));
    document.getElementById('btn-menu-dfa').addEventListener('click', () => this.showModal('dfa'));

    // How It Works slides
    let currentSlide = 0;
    const slides = document.querySelectorAll('.how-slide');
    const dots = document.querySelectorAll('.slide-indicators .dot');
    const btnPrev = document.getElementById('btn-how-prev');
    const btnNext = document.getElementById('btn-how-next');

    const updateSlides = (index) => {
      slides.forEach((s, idx) => {
        s.classList.toggle('active', idx === index);
        s.classList.toggle('hidden', idx !== index);
      });
      dots.forEach((d, idx) => d.classList.toggle('active', idx === index));
      btnPrev.disabled = index === 0;
      btnNext.textContent = index === slides.length - 1 ? 'START PLAY ▶' : 'NEXT >';
    };

    btnPrev.addEventListener('click', () => {
      if (currentSlide > 0) {
        currentSlide--;
        updateSlides(currentSlide);
      }
    });

    btnNext.addEventListener('click', () => {
      if (currentSlide < slides.length - 1) {
        currentSlide++;
        updateSlides(currentSlide);
      } else {
        this.showScreen('level');
      }
    });

    document.getElementById('btn-how-close').addEventListener('click', () => this.showScreen('title'));

    // Level selection
    document.getElementById('btn-level-back').addEventListener('click', () => this.showScreen('title'));
    document.querySelector('.level-cards-grid').addEventListener('click', event => {
      const button = event.target.closest('.btn-play-level');
      if (button) this.startLevel(Number(button.closest('.level-card').dataset.level));
    });

    // In-game buttons
    document.getElementById('btn-game-reset').addEventListener('click', () => this.resetGame());
    document.getElementById('btn-game-menu').addEventListener('click', () => this.showScreen('title'));
    document.getElementById('btn-open-dfa-viewer').addEventListener('click', () => this.showModal('dfa'));

    // Sound toggle
    const btnSound = document.getElementById('btn-sound-toggle');
    const soundStatusLabel = document.getElementById('sound-status-label');
    const toggleSound = () => {
      const isEnabled = soundManager.toggle();
      btnSound.textContent = isEnabled ? '🔊' : '🔇';
      if (soundStatusLabel) {
        soundStatusLabel.textContent = `SOUND: ${isEnabled ? 'ON' : 'OFF'} [M]`;
      }
    };
    btnSound.addEventListener('click', toggleSound);

    // Modal close buttons
    document.getElementById('btn-dfa-close').addEventListener('click', () => this.closeModal('dfa'));
    document.getElementById('btn-notice-close').addEventListener('click', () => this.closeModal('notice'));
    document.getElementById('btn-notice-ok').addEventListener('click', () => this.closeModal('notice'));
    document.getElementById('btn-notice-view-dfa').addEventListener('click', () => {
      this.closeModal('notice');
      this.showModal('dfa');
    });

    // Result modal buttons
    document.getElementById('btn-result-retry').addEventListener('click', () => {
      this.closeModal('result');
      this.resetGame();
    });
    document.getElementById('btn-result-menu').addEventListener('click', () => {
      this.closeModal('result');
      this.showScreen('title');
    });

    // DFA Viewer tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const tabId = btn.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(c => {
          c.classList.toggle('hidden', c.id !== tabId);
        });
      });
    });

    // DFA String Tester
    document.getElementById('btn-run-tester').addEventListener('click', () => this.runStringTester());

    // D-Pad touch/mouse controls
    document.querySelectorAll('.dpad-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const direction = btn.dataset.dir;
        if (direction) {
          this.handleMoveInput(direction);
        }
      });
    });

    // Global Keyboard Handler
    window.addEventListener('keydown', (e) => this.handleKeyDown(e));
  }

  handleKeyDown(e) {
    // If on boot screen, any key skips to title
    if (!this.screens.boot.classList.contains('hidden')) {
      this.skipBootSequence();
      return;
    }

    // Toggle mute: 'M' or 'm'
    if (e.key === 'm' || e.key === 'M') {
      const btnSound = document.getElementById('btn-sound-toggle');
      if (btnSound) btnSound.click();
      return;
    }

    // Escape closes modals or goes back
    if (e.key === 'Escape') {
      this.closeModal('result');
      this.closeModal('dfa');
      this.closeModal('notice');
      return;
    }

    // Reset shortcut: 'R' or 'r' on game screen
    if ((e.key === 'r' || e.key === 'R') && !this.screens.game.classList.contains('hidden')) {
      if (!this.modals.result.classList.contains('hidden')) {
        document.getElementById('btn-result-retry').click();
      } else {
        this.resetGame();
      }
      return;
    }

    // Movement controls (Arrows or WASD)
    if (!this.screens.game.classList.contains('hidden')) {
      let direction = null;
      switch (e.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
          direction = 'UP';
          break;
        case 'ArrowDown':
        case 's':
        case 'S':
          direction = 'DOWN';
          break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
          direction = 'LEFT';
          break;
        case 'ArrowRight':
        case 'd':
        case 'D':
          direction = 'RIGHT';
          break;
      }

      if (direction) {
        e.preventDefault();
        this.handleMoveInput(direction);
      }
    }
  }

  // --------------------------------------------------------------------------
  // Game Lifecycle & Movement Logic
  // --------------------------------------------------------------------------
  async startLevel(level) {
    this.currentLevel = level;
    this.isGameOver = false;
    this.inputString = [];
    this.moveCount = 0;
    this.visitedPositions.clear();
    this.renderedLevel = null;
    this.renderInputString();
    this.showScreen('game');

    try {
      const result = await api.startGame(level);
      const levelInfo = result?.level_info || result?.level_info || { title: `Level ${level}` };
      const dfaInfo = result?.dfa_info || this.dfaData;

      if (!result || !result.state) {
        throw new Error('The server did not return a valid game state.');
      }

      document.getElementById('game-level-tag').textContent = levelInfo?.title || `Level ${level}`;

      if (dfaInfo) {
        this.dfaData = dfaInfo;
        this.populateDfaTable(dfaInfo);
        this.populateDfaTuple(dfaInfo);
      }

      this.applyGameState(result.state);
      this.startTimer();
    } catch (err) {
      this.handleApiError(err, 'Starting Game');
    }
  }

  async handleMoveInput(direction) {
    if (this.isProcessingMove || this.isGameOver) {
      return;
    }

    this.isProcessingMove = true;

    try {
      const response = await api.sendMovement(direction);
      soundManager.playMove();

      // Process response state updated by the backend
      const gameState = response.state || response;
      this.applyGameState(gameState, direction, response.symbol);
    } catch (err) {
      this.handleApiError(err, `Movement (${direction})`);
    } finally {
      // Cooldown matching animation transition
      setTimeout(() => {
        this.isProcessingMove = false;
      }, 190);
    }
  }

  async resetGame() {
    try {
      const response = await api.resetGame();
      const gameState = response.state || response;
      soundManager.playMove();
      this.isGameOver = false;
      this.inputString = [];
      this.renderInputString();
      this.visitedPositions.clear();
      this.visitedPositions.add(gameState.start_position.join(','));
      this.resetTimer();

      this.renderedLevel = null;
      this.applyGameState(gameState);
      this.updateStatusBadge('READY', 'status-ready');
      this.setDialogue(getRandomDeeLine('ready'));
    } catch (err) {
      this.handleApiError(err, 'Resetting Game');
    }
  }

  // --------------------------------------------------------------------------
  // Game State Rendering & Synchronization
  // --------------------------------------------------------------------------
  setupEmptyGrid(rows, cols) {
    this.currentGridSize = { rows, cols };
    this.gridElement.style.setProperty('--grid-cols', cols);
    this.gridElement.style.setProperty('--grid-rows', rows);
    this.gridElement.innerHTML = '';
    const colLabels = document.getElementById('coord-cols');
    const rowLabels = document.getElementById('coord-rows');
    colLabels.innerHTML = '';
    rowLabels.innerHTML = '';
    for (let c = 0; c < cols; c++) {
      const label = document.createElement('span');
      label.className = 'coord-label';
      label.textContent = `C${c}`;
      colLabels.appendChild(label);
    }
    for (let r = 0; r < rows; r++) {
      const label = document.createElement('span');
      label.className = 'coord-label';
      label.textContent = `R${r}`;
      rowLabels.appendChild(label);
    }

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = document.createElement('div');
        cell.className = 'grid-cell';
        cell.dataset.row = r;
        cell.dataset.col = c;
        cell.id = `cell-${r}-${c}`;

        const label = document.createElement('span');
        label.className = 'cell-label';
        label.textContent = this.gridState.grid_states[r][c];
        cell.appendChild(label);

        const stateName = label.textContent;
        if (stateName === this.gridState.start_state) cell.classList.add('start-cell');
        if (stateName === this.gridState.goal_state) cell.classList.add('goal-cell');
        if (this.gridState.obstacle_states.includes(stateName)) cell.classList.add('obstacle-cell');

        this.gridElement.appendChild(cell);
      }
    }

    this.renderRobotAt(...this.gridState.start_position);
  }

  applyGameState(state, lastDirection = null, symbol = null) {
    if (!state) return;

    // 1. Update Position & Dimensions
    if (state.rows && state.cols && (
      state.level !== this.renderedLevel ||
      state.rows !== this.currentGridSize.rows ||
      state.cols !== this.currentGridSize.cols
    )) {
      this.gridState = state;
      this.setupEmptyGrid(state.rows, state.cols);
      this.renderedLevel = state.level;
    }

    // 2. Extract Robot Position
    let r, c;
    if (Array.isArray(state.robot_position)) {
      [r, c] = state.robot_position;
    } else if (state.robot_position && typeof state.robot_position.row === 'number') {
      r = state.robot_position.row;
      c = state.robot_position.col;
    } else {
      [r, c] = state.start_position;
    }

    this.robotPosition = [r, c];
    this.visitedPositions.add(`${r},${c}`);
    this.renderRobotAt(r, c, lastDirection);
    this.updateVisitedCells();

    // 3. Update Input String
    if (symbol) {
      this.inputString.push(symbol);
      this.renderInputString();
    }

    // 4. Update Move Count
    this.moveCount = typeof state.move_count === 'number' ? state.move_count : (state.moves || this.inputString.length);
    this.statMoves.textContent = this.moveCount;

    // 5. Update Status and Telemetry
    const currentStateName = state.current_state;
    this.statState.textContent = currentStateName;
    this.statPos.textContent = `(${r}, ${c})`;
    this.statLastMove.textContent = symbol ? `${symbol} (${lastDirection})` : (lastDirection || 'None');

    // 6. Highlight active row in DFA Viewer
    this.highlightDfaRow(currentStateName, symbol);

    // 7. Visual Feedback based on backend status
    const status = (state.status || state.game_status || 'PLAYING').toUpperCase();
    this.handleStatusFeedback(status, currentStateName);
  }

  renderRobotAt(row, col, direction = null) {
    // Remove existing robot element
    const existing = document.getElementById('active-robot');
    if (existing) existing.remove();

    const targetCell = document.getElementById(`cell-${row}-${col}`);
    if (!targetCell) return;

    const robot = document.createElement('div');
    robot.className = 'robot-sprite';
    robot.id = 'active-robot';

    const eyeRow = document.createElement('div');
    eyeRow.className = 'sprite-eye-row';
    const eyeLeft = document.createElement('div');
    eyeLeft.className = 'sprite-eye';
    const eyeRight = document.createElement('div');
    eyeRight.className = 'sprite-eye';
    eyeRow.appendChild(eyeLeft);
    eyeRow.appendChild(eyeRight);

    const label = document.createElement('div');
    label.className = 'sprite-label';
    label.textContent = 'DFA-9';

    robot.appendChild(eyeRow);
    robot.appendChild(label);
    targetCell.appendChild(robot);
  }

  updateVisitedCells() {
    this.visitedPositions.forEach(coord => {
      const [r, c] = coord.split(',');
      const cell = document.getElementById(`cell-${r}-${c}`);
      if (cell && !cell.classList.contains('start-cell') && !cell.classList.contains('goal-cell')) {
        cell.classList.add('visited-cell');
      }
    });
  }

  renderInputString() {
    this.inputStringDisplay.innerHTML = '';
    if (this.inputString.length === 0) {
      this.inputStringDisplay.innerHTML = '<span class="placeholder-string">&epsilon; (empty)</span>';
      return;
    }

    this.inputString.forEach(s => {
      const tag = document.createElement('span');
      tag.className = 'input-symbol-tag';
      tag.textContent = s;
      this.inputStringDisplay.appendChild(tag);
    });

    this.inputStringDisplay.scrollTop = this.inputStringDisplay.scrollHeight;
  }

  handleStatusFeedback(status, currentStateName) {
    const robot = document.getElementById('active-robot');

    switch (status) {
      case 'MOVING':
      case 'PLAYING':
        this.updateStatusBadge('MOVING', 'status-moving');
        this.setDialogue(getRandomDeeLine('moving'));
        break;

      case 'BLOCKED':
        this.updateStatusBadge('BLOCKED', 'status-blocked');
        this.setDialogue(getRandomDeeLine('blocked'));
        soundManager.playWallBump();
        if (robot) {
          robot.classList.add('bump-anim');
          setTimeout(() => robot.classList.remove('bump-anim'), 220);
        }
        break;

      case 'CRASHED':
        this.isGameOver = true;
        this.stopTimer();
        this.updateStatusBadge('CRASHED', 'status-crashed');
        this.setDialogue(getRandomDeeLine('crashed'));
        soundManager.playCrash();
        if (robot) robot.classList.add('crash-anim');
        setTimeout(() => this.showResultPopup('crash', currentStateName), 700);
        break;

      case 'WON':
      case 'GOAL_REACHED':
      case 'ACCEPTING':
        this.isGameOver = true;
        this.stopTimer();
        this.updateStatusBadge('GOAL REACHED', 'status-won');
        this.setDialogue(getRandomDeeLine('won'));
        soundManager.playGoal();
        if (robot) robot.classList.add('win-anim');
        setTimeout(() => this.showResultPopup('win', currentStateName), 600);
        break;

      default:
        this.updateStatusBadge('READY', 'status-ready');
        break;
    }
  }

  updateStatusBadge(text, className) {
    this.statusBadge.className = `status-badge ${className}`;
    this.statusBadge.textContent = text;
  }

  setDialogue(text) {
    this.dialogueText.textContent = `"${text}"`;
  }

  showResultPopup(type, finalState) {
    const title = document.getElementById('result-title');
    const verdict = document.getElementById('result-verdict');
    const stars = document.getElementById('result-stars');
    const finalStateEl = document.getElementById('result-final-state');
    const inputStrEl = document.getElementById('result-input-string');
    const movesEl = document.getElementById('result-move-count');
    const dialog = document.getElementById('result-dialog');

    dialog.className = `modal-dialog result-dialog ${type}`;
    finalStateEl.textContent = finalState;
    inputStrEl.textContent = this.inputString.join(' ') || '(none)';
    movesEl.textContent = this.moveCount;

    if (type === 'win') {
      title.textContent = '🎉 GOAL REACHED! 🎉';
      verdict.textContent = 'STRING ACCEPTED';
      verdict.className = 'result-verdict accepted';

      // Star rating: 6 moves = ★★★, <= 8 = ★★, otherwise ★
      stars.textContent = this.moveCount <= 6 ? '★★★' : (this.moveCount <= 8 ? '★★☆' : '★☆☆');
    } else {
      title.textContent = '💥 ROBOT CRASHED 💥';
      verdict.textContent = 'STRING REJECTED';
      verdict.className = 'result-verdict rejected';
      stars.textContent = '☆☆☆';
    }

    this.showModal('result');
  }

  // --------------------------------------------------------------------------
  // Timer Implementation
  // --------------------------------------------------------------------------
  startTimer() {
    this.stopTimer();
    this.timerSeconds = 0;
    this.gameTimer.textContent = '⏱ 00:00';
    this.timerInterval = setInterval(() => {
      this.timerSeconds++;
      const mins = String(Math.floor(this.timerSeconds / 60)).padStart(2, '0');
      const secs = String(this.timerSeconds % 60).padStart(2, '0');
      this.gameTimer.textContent = `⏱ ${mins}:${secs}`;
    }, 1000);
  }

  stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  resetTimer() {
    this.startTimer();
  }

  // --------------------------------------------------------------------------
  // DFA Viewer & String Tester
  // --------------------------------------------------------------------------
  async loadLevels() {
    try {
      const response = await api.getLevels();
      const container = document.querySelector('.level-cards-grid');
      container.innerHTML = '';
      response.levels.forEach(level => {
        const card = document.createElement('article');
        card.className = 'level-card';
        card.dataset.level = level.level;

        const badge = document.createElement('div');
        badge.className = 'level-badge active-badge';
        badge.textContent = level.title;
        const heading = document.createElement('h3');
        heading.className = 'level-name';
        heading.textContent = `LEVEL ${level.level}: ${level.title}`;
        const metadata = document.createElement('div');
        metadata.className = 'level-meta';
        metadata.textContent =
          `GRID: ${level.num_grid_rows}×${level.num_grid_cols} · OBSTACLES: ${level.num_obstacles}`;
        const description = document.createElement('p');
        description.className = 'level-desc';
        description.textContent = level.description;
        const button = document.createElement('button');
        button.className = 'retro-btn btn-play-level';
        button.textContent = `START LEVEL ${level.level} ▶`;
        card.append(badge, heading, metadata, description, button);
        container.appendChild(card);
      });
      if (response.levels.length) await this.loadDfaInfo(response.levels[0].level);
    } catch (err) {
      console.error('Could not load configured levels:', err);
    }
  }

  async loadDfaInfo(level) {
    const response = await api.getDfaInfo(level);
    this.dfaData = response.data;
    this.populateDfaTable(response.data);
    this.populateDfaTuple(response.data);
  }

  populateDfaTable(data) {
    const tbody = document.getElementById('dfa-table-body');
    tbody.innerHTML = '';

    const states = data.states;
    const table = data.transition_table;
    const alphabet = data.alphabet;
    const header = document.getElementById('dfa-table-header');
    header.innerHTML = '';
    const stateHeader = document.createElement('th');
    stateHeader.textContent = 'State';
    header.appendChild(stateHeader);
    alphabet.forEach(symbol => {
      const th = document.createElement('th');
      th.textContent = symbol;
      header.appendChild(th);
    });

    states.forEach(s => {
      const tr = document.createElement('tr');
      tr.id = `dfa-row-${s.name}`;
      if (s.name === data.trap_state) tr.className = 'crash-row';

      let statePrefix = '';
      if (s.initial) statePrefix += '→ ';
      if (s.final) statePrefix += '* ';

      const tdState = document.createElement('td');
      tdState.textContent = `${statePrefix}${s.name}`;
      tr.appendChild(tdState);

      const stateTransitions = table[s.name];
      alphabet.forEach(sym => {
        const td = document.createElement('td');
        td.id = `cell-dfa-${s.name}-${sym}`;
        td.textContent = stateTransitions[sym] || '-';
        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });
  }

  populateDfaTuple(data) {
    const statesEl = document.getElementById('tuple-states');
    const startEl = document.getElementById('tuple-start');
    const finalEl = document.getElementById('tuple-final');
    const alphabetEl = document.getElementById('tuple-alphabet');

    if (statesEl) {
      const names = data.states.map(s => s.name);
      statesEl.textContent = `{ ${names.join(', ')} }`;
    }
    if (startEl) startEl.textContent = data.initial_state;
    if (finalEl) finalEl.textContent = `{ ${data.final_states.join(', ')} }`;
    if (alphabetEl) alphabetEl.textContent = `{ ${data.alphabet.join(', ')} }`;
    document.getElementById('tuple-trap').textContent = data.trap_state;
  }

  highlightDfaRow(stateName, lastSymbol = null) {
    document.querySelectorAll('.dfa-table tr').forEach(r => r.classList.remove('active-state-row'));
    document.querySelectorAll('.dfa-table td').forEach(c => c.classList.remove('flash-cell'));

    const row = document.getElementById(`dfa-row-${stateName}`);
    if (row) {
      row.classList.add('active-state-row');
      if (lastSymbol) {
        const cell = document.getElementById(`cell-dfa-${stateName}-${lastSymbol}`);
        if (cell) cell.classList.add('flash-cell');
      }
    }
  }

  runStringTester() {
    const input = document.getElementById('tester-string-input');
    const output = document.getElementById('tester-output');
    const rawStr = input.value.trim().toUpperCase();

    if (!rawStr) {
      output.innerHTML = '<span class="placeholder-string">Please enter an input string.</span>';
      return;
    }

    if (!this.dfaData) {
      output.innerHTML = '<span class="danger-text">DFA data not loaded.</span>';
      return;
    }

    const alphabet = new Set(this.dfaData.alphabet);
    const transitions = this.dfaData.transition_table;
    const finalStates = new Set(this.dfaData.final_states);
    let currentState = this.dfaData.initial_state;

    let log = [`<strong>Start State:</strong> ${escapeHtml(currentState)}`];
    let rejected = false;

    for (let i = 0; i < rawStr.length; i++) {
      const sym = rawStr[i];
      if (!alphabet.has(sym)) {
        log.push(`<span class="danger-text">Symbol '${escapeHtml(sym)}' not in alphabet &Sigma;!</span>`);
        rejected = true;
        break;
      }

      const nextState = transitions[currentState]?.[sym];
      if (nextState === undefined) {
        log.push(`&delta;(${escapeHtml(currentState)}, '${escapeHtml(sym)}') &rarr; undefined (REJECTED)`);
        rejected = true;
        break;
      }

      log.push(`&delta;(${escapeHtml(currentState)}, '${escapeHtml(sym)}') &rarr; <strong>${escapeHtml(nextState)}</strong>`);
      currentState = nextState;

      if (currentState === this.dfaData.trap_state) {
        log.push(`<span class="danger-text">Entered trap state '${escapeHtml(this.dfaData.trap_state)}'. String REJECTED.</span>`);
        rejected = true;
        break;
      }
    }

    const isAccepted = !rejected && finalStates.has(currentState);
    log.push('<hr style="border-color: var(--border-dim); margin: 6px 0;">');
    log.push(`<strong>Final State:</strong> ${escapeHtml(currentState)}`);
    log.push(isAccepted 
      ? '<strong style="color: var(--color-green);">VERDICT: STRING ACCEPTED &in; L(M) 🎉</strong>'
      : '<strong style="color: var(--color-red);">VERDICT: STRING REJECTED &notin; L(M) ✖</strong>');

    output.innerHTML = log.join('<br>');
  }

  // --------------------------------------------------------------------------
  // Error Handling (HTTP and network errors)
  // --------------------------------------------------------------------------
  handleApiError(err, actionContext) {
    console.error(`API Error during ${actionContext}:`, err);

    let message = 'An unexpected network error occurred.';
    if (err && err.data && err.data.error) {
      message = err.data.error;
    } else if (err && err.message) {
      message = err.message;
    }

    // Display a request-specific notice without implying team modules are pending.
    const noticeMsg = document.getElementById('notice-message');
    const noticeStatus = document.getElementById('notice-status');

    if (noticeMsg) {
      noticeMsg.textContent = `${actionContext} failed: ${message}`;
    }

    if (noticeStatus) {
      const status = err && err.status;
      noticeStatus.textContent = status
        ? `REQUEST FAILED (HTTP ${status})`
        : 'NETWORK ERROR';
    }

    this.showModal('notice');
    this.updateStatusBadge('REQUEST FAILED', 'status-blocked');
    this.setDialogue(`Notice: ${message}`);
  }
}

// Instantiate on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  window.gameApp = new GameController();
});
