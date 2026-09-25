#!/usr/bin/env python3
"""Unisce al catalogo un contributo arrivato come issue (lo apre Wattson, o una persona a mano).

Il corpo dell'issue contiene un blocco ```json con {"wattson": 1, "voci": [...]}. Ogni voce:
tipo, marca, modello, codice, profilo (testo), w (W), min (minuti), n (volte vista).
Chi contribuisce è l'autore dell'issue (hash del login): rimandare lo stesso apparecchio
sostituisce il proprio contributo, non lo somma. Nessun dato della casa entra nel catalogo.

Uso (dalla GitHub Action): ingest.py <evento.json> <catalog.json>  → stampa il commento, exit 0 = unito.
"""
import hashlib
import json
import re
import sys
from datetime import date

FIELDS = ("tipo", "marca", "modello", "codice", "profilo")
FP_TOL = 0.15          # stessa voce se potenza entro ±15 % (come in Wattson)
N_CAP = 20             # peso massimo di un contributo: nessuno domina la media dichiarando n enormi
TEXT = re.compile(r"^[\w .,'&()+/\-]*$", re.UNICODE)


def parse(body):
    m = re.search(r"```json\s*(\{.*?\})\s*```", body or "", re.S)
    if not m:
        raise ValueError("manca il blocco ```json con il contributo")
    return json.loads(m.group(1))


def check(data):
    """Voci pulite, o ValueError col motivo."""
    voci = data.get("voci") if isinstance(data, dict) else None
    if not isinstance(voci, list) or not 1 <= len(voci) <= 20:
        raise ValueError("servono da 1 a 20 voci")
    out = []
    for i, v in enumerate(voci, 1):
        e = {}
        for k in FIELDS:
            s = str(v.get(k) or "").strip()
            if len(s) > 60 or not TEXT.match(s) or re.search(r"@|https?:|www\.", s, re.I):
                raise ValueError("voce %d: campo %s non valido" % (i, k))
            e[k] = s
        if len(e["tipo"]) < 2:
            raise ValueError("voce %d: manca il tipo" % i)
        try:
            e["w"], e["min"], e["n"] = int(v["w"]), round(float(v["min"]), 1), int(v["n"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("voce %d: w/min/n mancanti o non numerici" % i)
        if not (150 <= e["w"] <= 10000 and 0.1 <= e["min"] <= 1440 and 1 <= e["n"] <= 1000):
            raise ValueError("voce %d: valori fuori scala (w 150–10000, min 0,1–1440, n 1–1000)" % i)
        out.append(e)
    return out


def key(d):
    return tuple(d.get(k, "").strip().lower() for k in FIELDS)


def merge(catalog, voci, src, day):
    for v in voci:
        e = next((e for e in catalog if key(e) == key(v) and abs(e["w"] - v["w"]) <= FP_TOL * e["w"]), None)
        if e is None:
            e = {k: v[k] for k in FIELDS}
            e["fonti"] = {}
            catalog.append(e)
        e["fonti"][src] = {"w": v["w"], "min": v["min"], "n": v["n"], "data": day}
        src_ = e["fonti"].values()
        wt = [min(x["n"], N_CAP) for x in src_]
        e.update(w=round(sum(x["w"] * k for x, k in zip(src_, wt)) / sum(wt)),
                 min=round(sum(x["min"] * k for x, k in zip(src_, wt)) / sum(wt), 1),
                 n=sum(x["n"] for x in src_), case=len(e["fonti"]))
    catalog.sort(key=key)
    return catalog


def main(event_path, catalog_path):
    ev = json.load(open(event_path))
    issue = ev["issue"]
    src = hashlib.sha256(issue["user"]["login"].lower().encode()).hexdigest()[:12]
    try:
        voci = check(parse(issue["body"]))
    except (ValueError, json.JSONDecodeError) as e:
        print("❌ Contributo non unito: %s. Resta aperto per una verifica a mano." % e)
        return 1
    catalog = json.load(open(catalog_path))
    merge(catalog, voci, src, date.today().isoformat())
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("✅ Grazie! Unit%s al catalogo: %s" % ("a" if len(voci) == 1 else "e", "; ".join(
        "%s · %s · %s%s — %d W, ~%s min" % (v["tipo"], v["marca"] or "?", v["modello"] or "?",
                                            " (%s)" % v["profilo"] if v["profilo"] else "", v["w"], v["min"])
        for v in voci)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
