"""Genereaza viewer/exercises.json din numele clipurilor din 'clipuri de facut'."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIPS = os.path.join(ROOT, "clipuri de facut")
OUT = os.path.join(ROOT, "viewer", "exercises.json")

PAT = re.compile(r"^(\d+?)(1201|12)[-_](.+)\.mp4$", re.I)
BODY = {"waist": "Abdomen", "chest": "Piept", "back": "Spate", "thighs": "Coapse", "hips": "Fesieri",
        "shoulders": "Umeri", "upper-arms": "Brațe", "upper arms": "Brațe", "forearms": "Antebrațe",
        "calves": "Gambe", "neck": "Gât", "cardio": "Cardio", "plyometrics": "Pliometrie",
        "stretching": "Stretching", "weightlifting": "Haltere"}

def parse(fn):
    m = PAT.match(fn)
    if not m:
        stem = os.path.splitext(fn)[0]
        return [stem, stem.replace("-", " "), fn, "", ""]
    ident, _, rest = m.groups()
    parts = [p for p in rest.split("_") if p]
    name = parts[0]
    body = None
    for p in parts[1:]:
        key = re.sub(r"-?(FIX\d*|VERSION-\d+)$", "", p, flags=re.I).strip("-").lower()
        if key in BODY:
            body = BODY[key]
    gender = None
    g = re.search(r"\((male|female)\)", name, re.I)
    if g:
        gender = g.group(1).lower()
    # cratima devine spatiu, mai putin intre cifre ("3-4 Sit up")
    words = re.sub(r"(?<!\d)-|-(?!\d)", " ", name)
    words = re.sub(r"\s+", " ", words).strip()
    # format compact: [id, nume, fisier, zona, gen]
    return [ident, words, fn, body or "", (gender or "")[:1]]

files = sorted(f for f in os.listdir(CLIPS) if f.lower().endswith(".mp4"))
items = [parse(f) for f in files]
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
print(len(items), "exercitii ->", OUT, os.path.getsize(OUT) // 1024, "KB", file=sys.stderr)
