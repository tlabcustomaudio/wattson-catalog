#!/usr/bin/env python3
import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingest

V = {"type": "Dehumidifier", "brand": "LG", "model": "Drymaster", "code": "DHB1260PL",
     "profile": "Laundry Dry", "w": 205, "min": 120.0, "n": 1}
body = lambda entries: "Contribution\n```json\n%s\n```" % json.dumps({"wattson": 1, "entries": entries})

assert ingest.check(ingest.parse(body([V])))[0]["code"] == "DHB1260PL"
for bad, why in ((dict(V, type=""), "type"), (dict(V, code=""), "code"), (dict(V, profile=" "), "profile"),
                 (dict(V, w=50), "range"), (dict(V, brand="x@y.it"), "invalid"),
                 (dict(V, model="https://spam"), "invalid"), (dict(V, n="lots"), "numeric")):
    try:
        ingest.check(ingest.parse(body([bad])))
        raise AssertionError("accepted: %s" % bad)
    except ValueError as e:
        assert why in str(e), (why, e)
try:
    ingest.parse("no json here")
    raise AssertionError
except ValueError:
    pass

cat = ingest.merge([], [V], "a", "2026-09-25")
cat = ingest.merge(cat, [dict(V, w=210)], "a", "2026-09-26")          # same home: replaces
assert len(cat) == 1 and cat[0]["homes"] == 1 and cat[0]["w"] == 210, cat
cat = ingest.merge(cat, [dict(V, brand="lg", w=200, n=1000)], "b", "2026-09-27")   # another home, inflated n
assert cat[0]["homes"] == 2 and cat[0]["w"] == round((210 * 1 + 200 * 20) / 21), cat
cat = ingest.merge(cat, [dict(V, w=2000)], "a", "2026-09-27")         # different power: separate entry
assert len(cat) == 2

P = dict(V, profile="Eco 50", w=1900, min=125, kwh=0.95)                 # a program: kwh optional
cat = ingest.merge([], ingest.check({"entries": [P]}), "a", "2026-09-25")
cat = ingest.merge(cat, ingest.check({"entries": [dict(P, kwh=1.05)]}), "b", "2026-09-25")
assert cat[0]["kwh"] == 1.0 and "kwh" not in ingest.check({"entries": [V]})[0], cat
cat = ingest.merge(cat, ingest.check({"entries": [dict(P, kwh=1.05, avg_w=480)]}), "b", "2026-09-26")   # b re-sends
assert cat[0]["avg_w"] == 480 and cat[0]["homes"] == 2, cat
try:
    ingest.check({"entries": [dict(P, kwh="lots")]})
    raise AssertionError("text kwh accepted")
except ValueError:
    pass

d = tempfile.mkdtemp()
ev, cp = os.path.join(d, "ev.json"), os.path.join(d, "catalog.json")
json.dump({"issue": {"user": {"login": "Someone"}, "body": body([V])}}, open(ev, "w"))
open(cp, "w").write("[]\n")
assert ingest.main(ev, cp) == 0 and json.load(open(cp))[0]["homes"] == 1
assert "Someone" not in open(cp).read()
json.dump({"issue": {"user": {"login": "Spam"}, "body": "buy here"}}, open(ev, "w"))
assert ingest.main(ev, cp) == 1
print("ingest OK")
