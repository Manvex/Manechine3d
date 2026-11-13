"""Împachetează mocap_raw/*.npy în viewer/mocap/ (index.json + bucăți gzip de câte 100 de clipuri).

Per clip: 7,5 fps, 22 de rânduri (21 articulații + rădăcină), int16, codat ca diferențe între cadre.
"""
import gzip, json, os, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "mocap_raw")
OUT = os.path.join(ROOT, "viewer", "mocap")
KEEP = list(range(9)) + [11, 12] + list(range(15, 26))   # fără degetul mic și degetul mare
CHUNK = 100

os.makedirs(OUT, exist_ok=True)
ex = json.load(open(os.path.join(ROOT, "viewer", "exercises.json")))
clips, buf, off, chunk, total = {}, [], 0, 0, 0

def flush():
    global buf, off, chunk, total
    if buf:
        data = gzip.compress(np.concatenate(buf).astype("<i2").tobytes(), 9, mtime=0)
        total += len(data)
        open(os.path.join(OUT, f"c{chunk:03d}.dat"), "wb").write(data)
    buf, off, chunk = [], 0, chunk + 1

n = 0
for e in ex:
    src = os.path.join(RAW, e[2][:-4] + ".npy")
    if not os.path.exists(src):
        continue
    a = np.load(src)[:, KEEP, :]
    if len(a) < 4:
        continue
    d = a.copy()
    d[1:] = a[1:] - a[:-1]
    clips[e[0]] = [chunk, off, len(a)]
    buf.append(d.reshape(len(a), -1))
    off += len(a)
    n += 1
    if n % CHUNK == 0:
        flush()
flush()
json.dump({"fps": 7.5, "rows": len(KEEP), "clips": clips}, open(os.path.join(OUT, "index.json"), "w"), separators=(",", ":"))
print(len(clips), "clipuri,", chunk, "bucăți,", total // 1024, "KB")
