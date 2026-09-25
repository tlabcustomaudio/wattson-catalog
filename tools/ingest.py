#!/usr/bin/env python3
"""Merge a contribution that arrived as an issue (opened by Wattson, or by hand) into the catalog.

The issue body holds a ```json block with {"wattson": 1, "entries": [...]}. Each entry:
type, brand, model, code, profile (text, all required), w (watts), min (minutes), n (times seen).
The contributor is the issue author (hashed login): re-sending the same appliance replaces
their own contribution instead of adding to it. No household data ever enters the catalog.

Usage (from the GitHub Action): ingest.py <event.json> <catalog.json>  → prints the comment, exit 0 = merged.
"""
import hashlib
import json
import re
import sys
from datetime import date

FIELDS = ("type", "brand", "model", "code", "profile")
FP_TOL = 0.15          # same entry if power within ±15 % (same as Wattson)
N_CAP = 20             # max weight of one contribution: nobody dominates the average by claiming a huge n
TEXT = re.compile(r"^[\w .,'&()+/\-]*$", re.UNICODE)


def parse(body):
    m = re.search(r"```json\s*(\{.*?\})\s*```", body or "", re.S)
    if not m:
        raise ValueError("the ```json block with the contribution is missing")
    return json.loads(m.group(1))


def check(data):
    """Clean entries, or ValueError with the reason."""
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not 1 <= len(entries) <= 20:
        raise ValueError("1 to 20 entries are required")
    out = []
    for i, v in enumerate(entries, 1):
        e = {}
        for k in FIELDS:
            s = str(v.get(k) or "").strip()
            if len(s) > 60 or not TEXT.match(s) or re.search(r"@|https?:|www\.", s, re.I):
                raise ValueError("entry %d: invalid %s" % (i, k))
            e[k] = s
        empty = [k for k in FIELDS if not e[k]]
        if empty:   # all required: the catalog is only as good as the data that goes in
            raise ValueError("entry %d: empty fields: %s" % (i, ", ".join(empty)))
        try:
            e["w"], e["min"], e["n"] = int(v["w"]), round(float(v["min"]), 1), int(v["n"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("entry %d: w/min/n missing or not numeric" % i)
        if not (150 <= e["w"] <= 10000 and 0.1 <= e["min"] <= 1440 and 1 <= e["n"] <= 1000):
            raise ValueError("entry %d: values out of range (w 150–10000, min 0.1–1440, n 1–1000)" % i)
        out.append(e)
    return out


def key(d):
    return tuple(d.get(k, "").strip().lower() for k in FIELDS)


def merge(catalog, entries, src, day):
    for v in entries:
        e = next((e for e in catalog if key(e) == key(v) and abs(e["w"] - v["w"]) <= FP_TOL * e["w"]), None)
        if e is None:
            e = {k: v[k] for k in FIELDS}
            e["sources"] = {}
            catalog.append(e)
        e["sources"][src] = {"w": v["w"], "min": v["min"], "n": v["n"], "date": day}
        s = e["sources"].values()
        wt = [min(x["n"], N_CAP) for x in s]
        e.update(w=round(sum(x["w"] * k for x, k in zip(s, wt)) / sum(wt)),
                 min=round(sum(x["min"] * k for x, k in zip(s, wt)) / sum(wt), 1),
                 n=sum(x["n"] for x in s), homes=len(e["sources"]))
    catalog.sort(key=key)
    return catalog


def main(event_path, catalog_path):
    ev = json.load(open(event_path))
    issue = ev["issue"]
    src = hashlib.sha256(issue["user"]["login"].lower().encode()).hexdigest()[:12]
    try:
        entries = check(parse(issue["body"]))
    except (ValueError, json.JSONDecodeError) as e:
        print("❌ Contribution not merged: %s. Left open for a manual review." % e)
        return 1
    catalog = json.load(open(catalog_path))
    merge(catalog, entries, src, date.today().isoformat())
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("✅ Thanks! Merged into the catalog: %s" % "; ".join(
        "%s · %s · %s · %s (%s) — %d W, ~%s min" % (v["type"], v["brand"], v["model"], v["code"], v["profile"],
                                                   v["w"], v["min"]) for v in entries))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
