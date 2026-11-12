"""Évaluation sur vrai LLM : python -m eval.run_eval"""
import json
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
from graph import ask          # noqa: E402
from tools import refunds      # noqa: E402

cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
ok_count, rows = 0, []
for c in cases:
    refunds.reset()
    t0 = time.time()
    try:
        s = ask(c["message"], c["customer"])
        d = s["decision"]
        good = d["status"] == c["status"] and (c.get("amount") is None or d.get("amount") == c["amount"])
        info = f"{d['status']} {d.get('amount') or ''}".strip()
    except Exception as e:
        good, info, s = False, f"ERREUR {type(e).__name__}", {"steps": []}
    ok_count += good
    rows.append((c["id"], c["status"], info, "OK" if good else "KO",
                 len([x for x in s["steps"] if x == 'supervisor']), f"{time.time()-t0:.1f}s"))

print(f"{'cas':26}{'attendu':12}{'obtenu':18}{'':4}{'sup.':5}{'durée'}")
for r in rows:
    print(f"{r[0]:26}{r[1]:12}{r[2]:18}{r[3]:4}{r[4]:<5}{r[5]}")
print(f"\nScore : {ok_count}/{len(cases)} ({100*ok_count/len(cases):.0f} %)")
