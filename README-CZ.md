# 🎲🪦 DIE SCREAMING!

DIE SCREAMING! je 2D stolní hra s desetistěnnými kostkami (D10) běžící v okně 960 × 720 px při 60 FPS. Hráč prochází 7 levely a v každém musí dosáhnout požadovaného skóre (5 / 10 / 25 / 50 / 100 / 250 / 500 bodů) v maximálně 10 hodech. Hráč nabíjí sílu hodu přidržením mezerníku a křikem do mikrofonu. Při game over lze získat jeden extra pokus dalším křikem nebo naskenováním QR kódu.

![Gameplay](/docs/gameplay2.png)

---

## 🕹 ️Jak se hraje

Na začátku každého levelu máš **10 pokusů** a sadu kostek rozmístěných na podlaze. Tvojím cílem je dosáhnout požadovaného skóre dříve, než pokusy dojdou.

- **Vyber** kostku kliknutím levým tlačítkem myši
- **Drž mezerník** a křič — čím hlasitěji křičíš, tím více se plní ukazatel síly hodu
- **Uvolni mezerník** — vybraná kostka se hodí
- **Enter** — přeskoč zbývající pokusy a přejdi rovnou na vyhodnocení skóre
- **R** — restart od levelu 1

Po každém hodu se kostky fyzicky odrážejí od stěn i od sebe. Hodnoty kostek se uzamknou po zastavení. Skóre se aktualizuje živě.

Pokud dosáhneš požadovaného skóre před vypotřebováním pokusů, postoupíš do dalšího levelu. Pokud ne, nastane **Game Over** — jeden extra pokus ale můžeš získat dalším křikem na obrazovce game over.

![Gameplay 2](/docs/gameplay.png)

### Levely

| Level | Požadované skóre | Kostek na ploše |
| ----- | ---------------- | --------------- |
| 1     | 5                | 1               |
| 2     | 10               | 2               |
| 3     | 25               | 3               |
| 4     | 50               | 4               |
| 5     | 100              | 6               |
| 6     | 250              | 8               |
| 7     | 500              | 10              |

---

## 🎮 Ovládání

| Vstup                               | Akce                     |
| ----------------------------------- | ------------------------ |
| Klik levým tlačítkem myši na kostku | Vyber ji                 |
| Drž `mezerník` + křič               | Nabíjej sílu hodu        |
| Uvolni `mezerník`                   | Hoď vybranou kostku      |
| `Enter`                             | Přeskoč zbývající pokusy |
| `R`                                 | Restart od levelu 1      |
| `Esc` / šipka zpět                  | Návrat do menu           |

---

## 📊 Výpočet skóre

Skóre je **aktuální součet všech kostek na ploše** — minulé hody se nesčítají; každá kostka přispívá jednou svojí aktuální hodnotou. Vzorec je zobrazován živě jako rozpad na skupiny.

### Pravidla (v pořadí priority)

**1. Postupky** — tři a více po sobě jdoucích unikátních hodnot tvoří postupku. Celý běh boduje `součet × 10`. Kostky zahrnuté v postupce nesčítají se jako osamělé.

```
Příklad: kostky 2, 3, 4, 5  →  (2 + 3 + 4 + 5) × 10 = 140
```

**2. Páry a více** — dvě a více kostek se stejnou hodnotou bodují `(hodnota × počet) × počet`.

```
Příklad: tři 7  →  7 × 3 × 3 = 63
Příklad: pár 5  →  5 × 2 × 2 = 20
```

**3. Osamělé kostky** — kostka, která není součástí postupky ani páru, přičítá svou číselnou hodnotu.

```
Příklad: osamělá 4  →  4
```

| Situace        | Vzorec        | Příklad             |
| -------------- | ------------- | ------------------- |
| Osamělá kostka | `hodnota`     | 7 → **7**           |
| Pár            | `(h × n) × n` | 2, 2 → **8**        |
| Trojice        | `(h × n) × n` | 3, 3, 3 → **27**    |
| Postupka (3+)  | `součet × 10` | 1, 2, 3 → **60**    |
| Kombinace      | součet obou   | 1, 2, 2, 3 → **68** |

Pravidla se kombinují. Plocha s kostkami `2, 3, 4, 7, 7, 9` boduje:

- Postupka `2, 3, 4`: `(2 + 3 + 4) × 10 = 90`
- Pár `7, 7`: `7 × 2 × 2 = 28`
- Osamělá `9`: `9`
- **Celkem: 127**

![Score breakdown](/docs/score-calculation.png)

---

## 🖼 ️Sprity

### D10 sprite sheet

`sprites/d10-rainbow.png` je **mřížka 10 × 10**. Každý řádek je barevná varianta (0–9); každý sloupec je hodnota kostky (0–9). Loader rozřeže sheet při startu hry a uloží snímky jako `faces[barva][hodnota]`.

![D10 sprite sheet](sprites/d10-rainbow.png)

### Dlaždice podlahy

`sprites/floor-tile.png` je dlaždice z dřevěných prken opakující se v mřížce 28 × 12 a tvoří herní plochu.

![Floor tile](sprites/floor-tile.png)

---

## 🏗 Struktura projektu

```
main.py               # Vstupní bod: inicializace, načtení assetů, stavový automat
settings.py           # Globální konstanty: barvy, cesty, herní pravidla, rozměry
game.py               # Třída GameSession, herní smyčka, pomocníci hodu
screens.py            # Obrazovky: intro, menu, ovládání, bodování
ui.py                 # Vše vizuální: podlaha, widgety, HUD, end screen, AnimatedGif
audio.py              # ShoutMeter — čtení mikrofonu a detekce křiku

d10_dice.py           # Kostky: data, fyzika, kolize, rozmístění, kreslení
d10_score.py          # Výpočet skóre a rozpad na skupiny
d10_score_formula.py  # Živá vizualizace vzorce skóre
d10_sprites.py        # Načítání sprite sheetu, extrakce snímků
d10_roll.py           # Stavový automat animace hodu (idle / active / result)
d10_roll_effects.py   # Animovaná mini-kostka (starší efekt)

sprites/
  d10-rainbow.png     # Sprite sheet 10×10: 10 barevných variant × hodnoty 0–9
  floor-tile.png      # Opakující se dlaždice podlahy
  qr.png              # QR kód zobrazovaný při game over
  rage_quit.gif       # Animovaný GIF na obrazovce game over

docs/
  Pygame2026_workshop_final.pdf   # Materiály workshopu (Karel Šafr, Ph.D.)
```

---

## 🧠 Klíčové moduly

### `d10_dice.py` — fyzika a kostky

Každá kostka je slovník s polohou (`x`, `y`), rychlostí (`vx`, `vy`), úhlem rotace a hodnotou. Pohyb je integrován každý snímek v `update_die_motion`. Tření se aplikuje exponenciálně (`FRICTION ^ frame_scale`; `FRICTION = 0.988`). Odrazy od stěn zachovávají `WALL_BOUNCE = 0.72` rychlosti. Kolize mezi kostkami řeší `resolve_die_collision` impulzovou metodou s koeficientem `DIE_BOUNCE = 0.86`. Kostka se zastaví, když `|v| < STOP_SPEED` (18 px/s).

Při hodu funkce `throw_die` namíří kostku k nejbližší jiné kostce s malým náhodným rozptylem a přidá spin (`spin_velocity`). Hodnota se během letu střídá každých 90 ms z náhodně promíchané sekvence; finální hodnota je ta, která zbyde při zastavení.

### `game.py` + `audio.py` — herní smyčka a mikrofon

`GameSession` drží kostky, zbývající pokusy, aktuální level a příznak `waiting_for_settle` — vyhodnocení skóre nastane až po zastavení všech kostek. Stavový automat obrazovek žije v `main.py`: `intro → menu → game / controls / scoring`.

**ShoutMeter** (`audio.py`) čte mikrofon přes `sounddevice` ve vedlejším vlákně a průběžně aktualizuje RMS hlasitost. Při nabíjení hodu se `throw_power` zvyšuje buď hlasitostí mikrofonu, nebo časem (dle `THROW_POWER_MODE` v `settings.py`). Při game over ShoutMeter detekuje dostatečný křik a zavolá `grant_shout_retry`.

### `d10_score.py` — bodování

```python
def calculate_score(dice_values): ...
def score_breakdown(dice_values): ...  # stejná logika, vrací označené skupiny pro UI
```

Funkce zpracuje seznam hodnot kostek ve třech krocích:

1. **Postupky** — najde všechny maximální běhy ≥ 3 po sobě jdoucích unikátních hodnot. Každý běh přidá `součet × 10` bodů a označí zahrnuté hodnoty.
2. **Páry a více** — pro každou hodnotu s počtem výskytů ≥ 2 přidá `(hodnota × počet) × počet` bodů.
3. **Osamělé kostky** — hodnoty s počtem 1, které nejsou součástí postupky, přidají svou číselnou hodnotu.

### `d10_score_formula.py` — živá vizualizace vzorce

Zavolá `score_breakdown()` a vykreslí ikonky kostek (se správnou barevnou variantou z aktuálních kostek) seskupené podle typu kombinace s barevnými odznaky. Skupiny jsou odděleny znaménkem `+` a doplněny celkovým součtem `=`. Panel je horizontálně centrován na polo-průhledném pozadí.

---

## 🛠 Spuštění

**Požadavky:** Python 3.9+, mikrofon (volitelný — bez mikrofonu se síla hodu nabíjí časem)

**Technologie:** Python 3.12, Pygame 2.6, sounddevice 0.5

```bash
# Vytvoř a aktivuj virtuální prostředí
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Nainstaluj závislosti
pip install -r requirements.txt

# Spusť hru
python main.py
```

> Pygame nelze spustit v prostředí Jupyter ani v headless prostředí. Spouštěj z normálního terminálu.

Ověření instalace Pygame:

```bash
python -m pygame.tests
```

## 💻 Kontributoři

Tuto hru vyvinul tým čtyř v rámci workshopu na Unicorn University. Členové týmu jsou:

- Bc. Tomáš Grusz ([@tomasgrusz](https://github.com/tomasgrusz))
- Bc. Kristian Kolumber ([@kolumber23](https://github.com/kolumber23))
- Bc. Apolena Kučerová ([@apikucerova-kickass](https://github.com/apikucerova-kickass))
- Bc. Tomáš Pour ([@pourik20](https://github.com/pourik20))
