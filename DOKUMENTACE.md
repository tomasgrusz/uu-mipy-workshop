# DIE SCREAMING!

**Autor:** Tým 6  (Bc. Apolena Kučerová, Bc. Tomáš Pour, Bc. Kristian Kolumber, Bc. Tomáš Grusz)
**Datum:** 13. 6. 2026  
**Technologie:** Python 3.12, Pygame 2.6, sounddevice 0.5

---

# Technická dokumentace

## Popis hry

DIE SCREAMING! je 2D stolní hra s desetistěnnými kostkami (D10) běžící v okně 960 × 720 px při 60 FPS. Hráč prochází 7 levely a v každém musí dosáhnout požadovaného skóre (5 / 10 / 25 / 50 / 100 / 250 / 500 bodů) v maximálně 10 hodech. Hráč nabíjí sílu hodu přidržením mezerníku a křikem do mikrofonu. Při game over lze získat jeden extra pokus dalším křikem nebo naskenováním QR kódu.

---

## Struktura projektu

```
main.py               # Vstupní bod: inicializace Pygame, stavový automat obrazovek
settings.py           # Globální konstanty (rozlišení, levely, barvy, cesty k assetům)
game.py               # GameSession, herní smyčka
screens.py            # Obrazovky: intro, menu, controls, scoring
ui.py                 # Vykreslovací pomocníci: HUD, tlačítka, power bar, GIF loader
audio.py              # ShoutMeter — čtení mikrofonu přes sounddevice
d10_dice.py           # Data kostek, fyzika, kolize, kreslení (přejmenováno z d10_board)
d10_roll.py           # Stavový automat animace hodu (idle / active / result)
d10_score.py          # Výpočet skóre (páry, postupky, kombinace)
d10_score_formula.py  # Vizualizace skóre přímo ve hře
d10_sprites.py        # Načítání sprite sheetu, extrakce snímků

sprites/
  d10-rainbow.png     # Sprite sheet 10 × 10: 10 barevných variant × hodnoty 0–9
  floor-tile.png      # Dlaždice podlahy (opakující se)
  qr.png              # QR kód zobrazovaný při game over
  rage_quit.gif       # Animovaný GIF na obrazovce game over
```

---

## Klíčové moduly

### `d10_dice.py` — fyzika a kostky

Každá kostka je slovník s polohou (`x`, `y`), rychlostí (`vx`, `vy`), úhlem rotace a hodnotou. Pohyb je integrován každý snímek v `update_die_motion`. Tření se aplikuje exponenciálně (`FRICTION ^ frame_scale`), odrazy od stěn zachovávají `WALL_BOUNCE = 0.72` rychlosti. Kolize mezi kostkami řeší `resolve_die_collision` pomocí impulzové metody (koeficient `DIE_BOUNCE = 0.86`). Kostka se zastaví, když `|v| < STOP_SPEED (18 px/s)`.

Při hodu funkce `throw_die` namíří kostku směrem k nejbližší jiné kostce s malým náhodným rozptylem a přidá spin (`spin_velocity`). Hodnota se během pohybu střídá každých 90 ms z náhodně promíchané sekvence; finální hodnota je ta, která zbyde při zastavení.

### `game.py` + `audio.py` — herní smyčka a mikrofon

`GameSession` drží kostky, zbývající pokusy, aktuální level a příznak `waiting_for_settle` — vyhodnocení skóre nastane až po zastavení všech kostek. Stavový automat obrazovek žije v `main.py`: `intro → menu → game / controls / scoring`.

**ShoutMeter** (`audio.py`) čte mikrofon přes `sounddevice` ve vedlejším vlákně a průběžně aktualizuje úroveň hlasitosti. Při nabíjení hodu se síla hodu (`throw_power`) zvyšuje buď časem (hold Space), nebo aktuální hlasitostí mikrofonu — záleží na konstantě `THROW_POWER_MODE` v `settings.py`. Při game over ShoutMeter detekuje dostatečný křik a zavolá `grant_shout_retry`.

### `d10_score.py` — bodování

```python
def calculate_score(dice_values): ...
```

Funkce zpracuje seznam hodnot kostek ve třech krocích:

1. **Postupka** — nalezne všechny maximalní běhy ≥ 3 po sobě jdoucích unikátních hodnot. Každý takový běh přidá `součet × 10` bodů a označí zahrnuté hodnoty.
2. **Páry a více** — pro každou hodnotu s počtem výskytů ≥ 2 přidá `(hodnota × počet) × počet` bodů.
3. **Osamělé kostky** — hodnoty s počtem 1, které nejsou součástí postupky, přidají svou číselnou hodnotu.

Pravidla se kombinují: kostka, jejíž hodnota splňuje obě podmínky, přispívá do obou výpočtů.

| Situace | Vzorec | Příklad |
|---|---|---|
| Osamělá kostka | `hodnota` | 7 → **7** |
| Pár | `(h × n) × n` | 2, 2 → **8** |
| Trojice | `(h × n) × n` | 3, 3, 3 → **27** |
| Postupka (3+) | `součet × 10` | 1, 2, 3 → **60** |
| Kombinace | součet obou bonusů | 1, 2, 2, 3 → **68** |

---

## Sprite sheet

`d10-rainbow.png` je mřížka 10 × 10. Řádky odpovídají barevným variantám (0–9), sloupce hodnotám kostek (0–9). Modul `d10_sprites.py` rozřeže sheet při startu hry a uloží snímky jako `faces[barva][hodnota]`.

---

## Spuštění

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Hra vyžaduje fyzické okno (nefunguje v Jupyter nebo headless prostředí). Mikrofon je volitelný — pokud není dostupný, síla hodu se nabíjí pouze časem.
