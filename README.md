# uu-mipy-workshop

A Pygame workshop project featuring a **D10 Dice Roller** — an interactive demo built with Python and Pygame. Used as a practical starting point for learning 2D game development concepts: the game loop, sprite sheets, animation state machines, and event-driven input.

Workshop slides (in Czech) are in [`docs/`](docs/).

---

## Demo: D10 Dice Roller

A 960×720 interactive dice table. You can place up to six D10 dice on the board, each with its own rainbow color variant, and roll them individually. Every completed roll adds to a running score.

**Controls**

| Input | Action |
|---|---|
| `A` | Add a die (max 6) |
| `Space` | Roll the selected die |
| Left click | Select and roll a die |

When a die rolls, a mini die animates across the floor tile grid — sliding from the right edge to the center with an ease-out curve and a damped spin — while the die face cycles through a 10-frame sequence before landing on the result.

---

## Project structure

```
main.py              # Game loop, rendering, event handling
d10_board.py         # Die data, grid layout, selection, drawing
d10_roll.py          # Roll state machine (idle / active / result)
d10_roll_effects.py  # Animated mini-die that travels across the floor
d10_sprites.py       # Sprite sheet loading and face extraction

sprites/
  d10-rainbow.png    # 10×10 sprite sheet: 10 color variants × 10 faces (0–9)
  floor-tile.png     # Repeating floor tile (20 columns × 10 rows)

docs/
  Pygame2026_workshop_final.pdf   # Workshop slides (Karel Šafr, Ph.D.)
```

### Key design details

- **Sprite sheet layout** — `d10-rainbow.png` is sliced into a 10×10 grid. Rows are color variants (0–9); columns are face values (0–9). `d10_sprites.py` extracts individual frames on load.
- **Roll animation** — `d10_roll.py` builds a 10-frame random sequence sampled from all 10 faces. Each frame shows for 80 ms (total ~800 ms). The final frame in the sequence is the result.
- **Roll effect** — `d10_roll_effects.py` spawns a 36×36 mini die that travels from the right edge of the floor to a randomised centre position. Motion uses a cubic ease-out over ~2.1 s; rotation uses exponential damping (`spin_velocity *= 0.98 ^ frame_scale`).
- **Die grid** — up to 6 dice arranged in a 3-column grid anchored to the bottom-left. Each new die is assigned the next unused color variant.
- **Score** — accumulates the face value returned when a roll completes. Mid-roll frames do not contribute.

---

## Setup

**Requirements:** Python 3.9+, Pygame

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

> Pygame cannot run inside Jupyter or any environment that hosts its own main loop. Run from a regular terminal.

To verify your Pygame installation:

```bash
python -m pygame.tests
```

---

## About the workshop

This project accompanies a Pygame workshop introducing 2D game development in Python. Topics covered in the slides include:

- What Pygame is and why to use it (built on SDL, modular, cross-platform, Android support via PGS4A)
- Core modules: `display`, `draw`, `event`, `key`, `time`, `mouse`, `transform`, `sprite`
- Key primitives: `Surface`, `Rect`, `Sound`, `Font`
- Free game-art resources: [OpenGameArt.org](https://opengameart.org)
- Alternative Python game/GUI libraries: Godot, Pyglet, Kivy, Ren'Py, PyQT6, Arcade, Cocos2d

---

## License

Copyright (c) 2026 Tomas Grusz. See [license.md](license.md) for terms.
