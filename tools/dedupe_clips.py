"""Găsește clipurile dublate din 'clipuri de facut' și (cu --apply) le șterge, păstrând unul pe exercițiu.

Două clipuri sunt același exercițiu dacă numele lor coincide după ce scoatem:
(male)/(female), (VERSION-n), FIX, sufixul _small, zona corpului, cratimele și majusculele.

Din fiecare grup se păstrează, în ordine: clipul care are deja animație 3D, apoi cel fără sex în nume,
apoi varianta (male), apoi (female); la egalitate, cel fără VERSION / _small, apoi ID-ul cel mai mic.
"""
import collections, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIPS = os.path.join(ROOT, "clipuri de facut")
ANIMATED = {"0001", "0002", "0003", "0004", "0006", "0008", "6268"}
PAT = re.compile(r"^(\d+?)(1201|1101|12)[-_](.+)\.mp4$", re.I)

def parse(fn):
    m = PAT.match(fn)
    ident, rest = (m.group(1), m.group(3)) if m else ("", fn[:-4])
    name = [p for p in rest.split("_") if p][0]
    n = name.lower()
    n = re.sub(r"\((male|female)\)", "", n)
    n = re.sub(r"\(version-?\d+\)|-?version-?\d+", "", n)
    n = re.sub(r"-?fix\d*", "", n)
    key = re.sub(r"[^a-z0-9]+", " ", n).strip()
    low = fn.lower()
    rank = (
        0 if ident in ANIMATED else 1,
        0 if "(male)" not in low and "(female)" not in low else (1 if "(male)" in low else 2),
        ("version" in low) + ("_small" in low),
        int(ident) if ident else 10**9,
    )
    return key, rank

files = sorted(f for f in os.listdir(CLIPS) if f.lower().endswith(".mp4"))
groups = collections.defaultdict(list)
for f in files:
    key, rank = parse(f)
    groups[key].append((rank, f))

keep, drop, report = [], [], []
for key in sorted(groups):
    items = sorted(groups[key])
    keep.append(items[0][1])
    if len(items) > 1:
        drop += [f for _, f in items[1:]]
        report.append(f"{items[0][1]}\n" + "".join(f"    - {f}\n" for _, f in items[1:]))

print(f"{len(files)} clipuri, {len(keep)} exerciții unice, {len(drop)} dubluri", file=sys.stderr)
with open(os.path.join(ROOT, "DUBLURI_ELIMINATE.txt"), "w", encoding="utf-8") as out:
    out.write(f"Clipuri: {len(files)} | unice: {len(keep)} | dubluri eliminate: {len(drop)}\n")
    out.write("Format: clipul păstrat, apoi (-) dublurile lui eliminate.\n\n")
    out.write("\n".join(report))
if "--apply" in sys.argv:
    for i in range(0, len(drop), 200):
        subprocess.run(["git", "rm", "-q", "--"] + [os.path.join(CLIPS, f) for f in drop[i:i + 200]], cwd=ROOT, check=True)
