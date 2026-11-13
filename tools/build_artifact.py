"""Construieste varianta publicabila (Artifact) a viewer-ului intr-un folder dat.
Paginile publicate nu pot incarca fisiere locale de vendor, asa ca three.js vine de pe jsDelivr."""
import base64, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "viewer")
out = sys.argv[1]
os.makedirs(os.path.join(out, "echipamente", "glb"), exist_ok=True)

html = open(os.path.join(V, "index.html"), encoding="utf-8").read()
css = open(os.path.join(V, "style.css"), encoding="utf-8").read()
body = re.search(r"<!--APP-->(.*)<!--/APP-->", html, re.S).group(1)
three = "https://cdn.jsdelivr.net/npm/three@0.170.0/"
page = f"""<title>Manechin 3D</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
{css}
</style>
<script>window.MANECHIN = {{ assets: "./", clips: null, b64: true }};</script>
<script type="importmap">
{{ "imports": {{ "three": "{three}build/three.module.min.js", "three/addons/": "{three}examples/jsm/" }} }}
</script>
{body}"""
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
for f in ["app.js", "animations.js", "mocap.js", "exercises.json"]:
    shutil.copy(os.path.join(V, f), out)
# Artifact-ele nu servesc .glb: modelele merg ca text base64, decodate in browser.
for f in ["male-actual.glb", "female-actual.glb", "echipamente/glb/ez_bar_olympic.glb",
          "echipamente/glb/hyperextension_45.glb"]:
    data = base64.b64encode(open(os.path.join(ROOT, f), "rb").read())
    open(os.path.join(out, f + ".txt"), "wb").write(data)
print("ok", out)

# mișcările extrase automat: index + bucăți gzip, tot ca text base64
M = os.path.join(V, "mocap")
if os.path.isdir(M):
    os.makedirs(os.path.join(out, "mocap"), exist_ok=True)
    shutil.copy(os.path.join(M, "index.json"), os.path.join(out, "mocap"))
    for f in sorted(os.listdir(M)):
        if f.endswith(".dat"):
            data = base64.b64encode(open(os.path.join(M, f), "rb").read())
            open(os.path.join(out, "mocap", f + ".txt"), "wb").write(data)
