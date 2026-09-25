#!/usr/bin/env python3
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingest

V = {"tipo": "Deumidificatore", "marca": "LG", "modello": "Drymaster", "codice": "DHB1260PL",
     "profilo": "Laundry Dry", "w": 205, "min": 120.0, "n": 1}
body = lambda voci: "Contributo\n```json\n%s\n```" % json.dumps({"wattson": 1, "voci": voci})

assert ingest.check(ingest.parse(body([V])))[0]["codice"] == "DHB1260PL"
for bad, why in ((dict(V, tipo=""), "tipo"), (dict(V, w=50), "scala"), (dict(V, marca="x@y.it"), "campo"),
                 (dict(V, modello="https://spam"), "campo"), (dict(V, n="tanti"), "numerici")):
    try:
        ingest.check(ingest.parse(body([bad])))
        raise AssertionError("accettata: %s" % bad)
    except ValueError as e:
        assert why in str(e), (why, e)
try:
    ingest.parse("niente json")
    raise AssertionError
except ValueError:
    pass

cat = ingest.merge([], [V], "a", "2026-09-25")
cat = ingest.merge(cat, [dict(V, w=210)], "a", "2026-09-26")          # stessa casa: sostituisce
assert len(cat) == 1 and cat[0]["case"] == 1 and cat[0]["w"] == 210, cat
cat = ingest.merge(cat, [dict(V, marca="lg", w=200, n=1000)], "b", "2026-09-27")   # altra casa, n gonfiato
assert cat[0]["case"] == 2 and cat[0]["w"] == round((210 * 1 + 200 * 20) / 21), cat
cat = ingest.merge(cat, [dict(V, w=2000)], "a", "2026-09-27")         # altra potenza: voce distinta
assert len(cat) == 2

d = tempfile.mkdtemp()
ev, cp = os.path.join(d, "ev.json"), os.path.join(d, "catalog.json")
json.dump({"issue": {"user": {"login": "Qualcuno"}, "body": body([V])}}, open(ev, "w"))
open(cp, "w").write("[]\n")
assert ingest.main(ev, cp) == 0 and json.load(open(cp))[0]["case"] == 1
assert "Qualcuno" not in open(cp).read()
json.dump({"issue": {"user": {"login": "Spam"}, "body": "compra qui"}}, open(ev, "w"))
assert ingest.main(ev, cp) == 1
print("ingest OK")
