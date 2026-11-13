"""Extrage scheletul 3D (MediaPipe Pose) din fiecare clip din 'clipuri de facut'.

Scrie câte un .npy pe clip în mocap_raw/ (int16, [cadre, 26, 3]):
  rândurile 0..24 = articulații în mm, centrate pe șold (x dreapta imaginii, y jos, z depărtare de cameră)
  rândul 25       = [deplasarea șoldului în imagine x, y (mm estimați), vizibilitatea medie ×1000]
Se procesează un cadru din patru (7,5 fps). Reluabil: sare peste clipurile deja făcute.
Necesită: pip install mediapipe opencv-python-headless numpy; apt install libegl1
"""
import os, sys, numpy as np
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIPS = os.path.join(ROOT, "clipuri de facut")
OUT = os.path.join(ROOT, "mocap_raw")
MODEL = os.path.join(ROOT, "tools", "models", "pose.task")
JOINTS = [0, 7, 8] + list(range(11, 33))
STEP = 4

def work(fn):
    dst = os.path.join(OUT, fn[:-4] + ".npy")
    if os.path.exists(dst):
        return 0
    import cv2, mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    lm = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=mpp.BaseOptions(model_asset_path=MODEL), running_mode=vision.RunningMode.VIDEO))
    cap = cv2.VideoCapture(os.path.join(CLIPS, fn))
    W, H = cap.get(3), cap.get(4)
    rows, n, last, root0 = [], 0, None, None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        n += 1
        if (n - 1) % STEP:
            continue
        res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), int(n * 1000 / 30))
        if res.pose_world_landmarks:
            w, im = res.pose_world_landmarks[0], res.pose_landmarks[0]
            pts = np.array([[w[j].x, w[j].y, w[j].z] for j in JOINTS]) * 1000
            # scara imagine → metri, din lungimea trunchiului (umeri–șolduri)
            wt = np.linalg.norm((pts[3] + pts[4]) / 2 - (pts[15] + pts[16]) / 2)
            px = lambda j: np.array([im[j].x * W, im[j].y * H])
            it = np.linalg.norm((px(11) + px(12)) / 2 - (px(23) + px(24)) / 2)
            hip = (px(23) + px(24)) / 2
            if root0 is None:
                root0 = hip
            k = wt / it if it > 1 else 0
            vis = np.mean([im[j].visibility for j in JOINTS])
            last = np.vstack([pts, [[(hip[0] - root0[0]) * k, (hip[1] - root0[1]) * k, vis * 1000]]])
        if last is not None:
            rows.append(last)
    lm.close()
    if rows:
        np.save(dst, np.clip(np.array(rows), -32000, 32000).astype(np.int16))
    return 1

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fd = os.open(os.devnull, os.O_WRONLY); os.dup2(fd, 2)
    files = sorted(f for f in os.listdir(CLIPS) if f.endswith(".mp4"))
    if len(sys.argv) > 1:
        files = files[: int(sys.argv[1])]
    with Pool(int(os.environ.get("JOBS", os.cpu_count()))) as p:
        for i, _ in enumerate(p.imap_unordered(work, files, chunksize=4)):
            if i % 100 == 0:
                print(i, "/", len(files), flush=True)
