# Wattson — appliance fingerprint catalog

The shared catalog of household appliances for [Wattson](https://github.com/tlabcustomaudio/wattson), the power-usage detective for Home Assistant.

Each entry says how much an appliance draws and for how long. It was measured in a real home with a "profiler" smart plug and cross-checked against the main meter. A freshly installed Wattson uses the catalog to recognise appliances that someone else has already measured.

## What it contains

`catalog.json` is a list of entries:

| Field | Example | Notes |
|---|---|---|
| `type` | Dehumidifier | |
| `brand` | LG | |
| `model` | Drymaster | |
| `code` | DHB1260PL | product code, the most precise identifier |
| `profile` | Laundry Dry | mode, state or program (e.g. *ABS print*, *Eco 50°*) |
| `w` | 205 | step seen on the main meter, watts (for a program: its peak). **0** = a measured-only state (standby, a lamp on) too small for the main meter: then `avg_w` is required |
| `min` | 120 | typical length of one block, minutes (for a program: the whole run) |
| `kwh` | 0.25 | optional: energy of one full run, measured by the plug |
| `avg_w` | 210 | optional: average power measured by the plug while on: what it **really** uses |
| `n` | 3 | times seen, in total |
| `homes` | 1 | how many different homes measured it (higher = more reliable) |
| `sources` | | one contribution per home, under an anonymous id |

**Why `w` and `avg_w` differ.** `w` is the jump Wattson sees on the main meter, which is how it recognises the appliance. It can be lower than the real draw: a dehumidifier starts its 35 W fan first (too small to show on the main meter), then the compressor adds +170 W. So `w` = 170, while the plug measures 210 W on average. Use `w` to recognise, `avg_w` and `kwh` to know the real consumption.

The five text fields are **all required**: an entry without a product code or a profile is rejected.

Two contributions are the same entry when type, brand, model, code and profile match (case-insensitive) and the power is within ±15 %. `w`, `min`, `kwh` and `avg_w` are the average of the contributions, weighted by how many times each home saw the appliance. Each home counts for at most 20, so nobody can dominate the average.

## Privacy

**Nothing about the home enters the catalog**: no room or device names, no timestamps, no addresses. A contributor is identified only by a hash of their GitHub login. The hash makes a re-sent contribution replace the previous one instead of adding to it. The issue that carries a contribution is public, like any GitHub issue.

## How to contribute

**With Wattson (automatic).** In Wattson's learning view, learn an appliance with the Profiler plug, filling in all the fields. If sharing is on, Wattson opens an issue here at the end of the session, using your GitHub account. You link the account once, the same way as for HACS. Sharing is **off by default**.

**By hand.** Open an issue with this block in the body:

````
```json
{"wattson": 1, "entries": [{"type": "Dehumidifier", "brand": "LG", "model": "Drymaster",
  "code": "DHB1260PL", "profile": "Laundry Dry", "w": 205, "min": 120, "n": 1}]}
```
````

A GitHub Action checks the format and the values: all fields present, w between 150 and 10000 W, min between 0.1 and 1440, no links or email addresses. It then merges the contribution into `catalog.json` and closes the issue. If something doesn't add up, the issue stays open with the `needs-review` label.

## Development

```bash
python3 tools/test_ingest.py
```
