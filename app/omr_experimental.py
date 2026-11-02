"""Reconnaissance expérimentale de hauteurs sur une portée imprimée.

Ne reconnaît ni durées, ni altérations, ni clés automatiquement.
Résultats indicatifs à vérifier ; ne pas utiliser pour la synthèse SATB.
"""
import cv2
import numpy as np

NAMES = ["do", "ré", "mi", "fa", "sol", "la", "si"]
# Ligne inférieure de la clé de sol : mi4 ; clé de fa : sol2.
def diatonic_name(step, clef):
    base = 4 * 7 + 2 if clef == "sol" else 2 * 7 + 4
    pos = base + step
    return f"{NAMES[pos % 7]}{pos // 7}"

def detect_staves_and_candidates(pix, max_staves=12):
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if pix.n == 3 else cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY) if pix.n == 4 else img
    # Reduce oversized pages to avoid excess memory on free hosting.
    if gray.shape[1] > 1400:
        ratio = 1400 / gray.shape[1]
        gray = cv2.resize(gray, (1400, round(gray.shape[0] * ratio)))
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    h, w = binary.shape
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(35, w // 9), 1))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    strengths = np.count_nonzero(horizontal, axis=1)
    ys = np.where(strengths > w * .35)[0]
    bands = []
    for y in ys:
        if bands and y <= bands[-1][-1] + 1:
            bands[-1].append(int(y))
        else:
            bands.append([int(y)])
    lines = [round(sum(b)/len(b)) for b in bands]
    groups = []
    for i in range(len(lines)-4):
        group = lines[i:i+5]
        gaps = np.diff(group)
        if np.min(gaps) >= 5 and np.max(gaps) <= 35 and np.max(gaps)-np.min(gaps) <= 3:
            if not groups or group[0] > groups[-1][-1]:
                groups.append(group)
        if len(groups) >= max_staves: break
    results = []
    # Remove long staff lines, then locate oval-like connected components.
    stripped = cv2.subtract(binary, horizontal)
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(stripped, 8)
    for idx, group in enumerate(groups):
        spacing = float(np.median(np.diff(group)))
        candidates = []
        for k in range(1, n):
            x,y,cw,ch,area = map(int, stats[k])
            cx,cy = centroids[k]
            if not (group[0]-2.5*spacing <= cy <= group[-1]+2.5*spacing): continue
            if not (spacing*.55 <= cw <= spacing*2.2 and spacing*.40 <= ch <= spacing*1.8): continue
            if not (spacing*spacing*.16 <= area <= spacing*spacing*2.3): continue
            # Position from bottom line in half-spaces. Stems and dots can be mistaken.
            step = int(round((group[-1]-cy)/(spacing/2)))
            candidates.append({"x": round(float(cx)/w, 3), "y": round(float(cy)/h, 3),
                "position": step, "note_if_treble": diatonic_name(step,"sol"),
                "note_if_bass": diatonic_name(step,"fa")})
        results.append({"staff":idx+1, "lines": [round(v/h,3) for v in group],
            "candidates":sorted(candidates,key=lambda p:p["x"])[:80]})
    return {"staves":results, "warning":"Détection expérimentale : les symboles peuvent être confondus avec des notes. Clés, altérations, rythmes et voix non vérifiés."}
