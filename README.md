# Drone Range Trade Study

A range vs. cruise speed trade study for the ETH Zürich ASL long-range drone — 1 000 km range, 300 km/h max speed, 1 kg payload.

Drag sliders in real time to explore how airframe and propulsion choices shift the range envelope.

---

## Demo

![Simulation screenshot](screenshot.png)

*Dots mark the best-range speed for each propulsion type. The dashed gold line is the 1 000 km target; the dotted red line is the 300 km/h maximum speed requirement.*

---

## The Engineering Problem

Long range and high speed pull in opposite directions:

- Flying faster increases parasite drag quadratically — burning through energy reserves quickly
- Flying slower reduces parasite drag but increases induced drag and time aloft
- The optimal cruise speed (minimum drag) is set by the drag polar and wing geometry
- Propulsion type (electric vs. ICE vs. hybrid) changes how much useful energy fits in the weight budget

This tool models those trade-offs and lets you explore them interactively.

---

## Physics Model

Level, constant-altitude flight using a parabolic drag polar:

```
CD = CD₀ + CL² / (π · AR · e)
```

| Symbol | Meaning |
|--------|---------|
| `CD₀` | Zero-lift (parasite) drag coefficient |
| `AR` | Wing aspect ratio |
| `e` | Oswald efficiency factor |
| `CL` | Lift coefficient — set by W = L at each speed |

**Range model** — R = E_useful / D

At constant speed and altitude, power required is P = D·V, so:

```
R = V · (E / P) = E / D
```

Maximum range occurs at minimum drag — the speed where parasite drag equals induced drag.

**Atmosphere** — ISA (International Standard Atmosphere):

```
ρ(h) = p(h) / (287.05 · T(h))
```

---

## Propulsion systems

| System | Energy budget |
|--------|--------------|
| Electric | 80% of prop mass → battery @ slider Wh/kg × motor efficiency |
| Fuel (ICE) | 85% of prop mass → fuel @ 11 800 Wh/kg × engine efficiency |
| Hybrid | 40% battery + 60% fuel, both weighted by their own efficiencies |

---

## Sliders

### Airframe
| Slider | Range | Effect |
|--------|-------|--------|
| MTOW | 5 – 60 kg | Total takeoff mass |
| Wing area S | 0.2 – 4.0 m² | Shifts stall speed and lift-dependent drag |
| Aspect ratio AR | 5 – 25 | Higher AR → less induced drag → more range |
| CD₀ | 0.010 – 0.060 | Parasite drag — dominated by fuselage and interference |

### Propulsion
| Slider | Range | Effect |
|--------|-------|--------|
| Prop mass fraction | 0.10 – 0.65 | Share of MTOW devoted to energy + motors |
| Battery (Wh/kg) | 100 – 500 | Technology level — 250 Wh/kg is current state of art |
| ICE efficiency | 0.18 – 0.40 | Engine + prop combined efficiency |
| Altitude | 0 – 5 000 m | Lower air density → higher speed for same lift → more drag |

---

## Specifications (ETH ASL Focus Project)

| Parameter | Target |
|-----------|--------|
| Range | up to **1 000 km** |
| Max speed | up to **300 km/h** |
| Payload | ~**1 kg** (HD camera + sensors) |

---

## Installation

```bash
pip install matplotlib numpy
python main.py
```

---

## Related

- [CATCHY — Drone Interception Simulation](https://github.com/jamietrounce/CATCHY-sim) — same visual style, explores guidance and sensing trade-offs for intercepting a rogue drone.
