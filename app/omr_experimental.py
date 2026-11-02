"""Détecteur OMR heuristique : portées et têtes de notes probables.
Aucune lecture de rythme, de clé, d'altération ou de voix SATB.
"""
import cv2
import numpy as np

NAMES = ("do", "ré", "mi", "fa", "sol", "la", "si")

def diatonic_name(step, clef):
    base = 30 if clef == "sol" else 18  # mi4 / sol2
    pos = base + step
    return f"{NAMES[pos % 7]}{pos // 7}"

def detect_staves_and_candidates(pix, max_staves=12):
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    elif pix.n == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    if gray.shape[1] > 1400:
        ratio = 1400 / gray.shape[1]
        gray = cv2.resize(gray, (1400, round(gray.shape[0] * ratio)))
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    h, w = binary.shape
    # Extract long horizontal strokes and group nearby rows into one staff line.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(35, w // 9), 1))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    ys = np.where(np.count_nonzero(horizontal, axis=1) > w * .35)[0]
    bands = []
    for y in ys:
        if bands and y <= bands[-1][-1] + 1:
            bands[-1].append(int(y))
        else:
            bands.append([int(y)])
    lines = [round(float(np.mean(b))) for b in bands]
    groups = []
    for i in range(len(lines) - 4):
        g = lines[i:i + 5]
        gaps = np.diff(g)
        if min(gaps) >= 5 and max(gaps) <= 35 and max(gaps) - min(gaps) <= 3:
            if not groups or g[0] > groups[-1][-1]:
                groups.append(g)
        if len(groups) >= max_staves:
            break
    results = []
    for idx, group in enumerate(groups):
        spacing = float(np.median(np.diff(group)))
        # Focus on the band around this staff; mask horizontal staff strokes.
        top = max(0, int(group[0] - 2.7 * spacing))
        bottom = min(h, int(group[-1] + 2.7 * spacing))
        crop = binary[top:bottom].copy()
        # Suppress long lines while retaining short oval noteheads.
        crop = cv2.subtract(crop, horizontal[top:bottom])
        # Oval opening suppresses narrow stems, isolated dots and text fragments.
        ew = max(3, int(round(spacing * .65)))
        eh = max(3, int(round(spacing * .42)))
        if ew % 2 == 0: ew += 1
        if eh % 2 == 0: eh += 1
        oval = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ew, eh))
        heads = cv2.morphologyEx(crop, cv2.MORPH_OPEN, oval)
        n, _, stats, centers = cv2.connectedComponentsWithStats(heads, 8)
        possible = []
        for k in range(1, n):
            x, y, cw, ch, area = [int(v) for v in stats[k]]
            cx, local_y = centers[k]
            cy = local_y + top
            if cx < w * .09 or cx > w * .98: continue
            if not (spacing * .5 <= cw <= spacing * 1.65): continue
            if not (spacing * .35 <= ch <= spacing * 1.4): continue
            if not (spacing * spacing * .19 <= area <= spacing * spacing * 1.7): continue
            # Reject uncertain vertical placements instead of forcing a pitch.
            raw_step = (group[-1] - cy) / (spacing / 2)
            step = round(raw_step)
            if abs(raw_step - step) > .32: continue
            possible.append((float(cx), float(cy), int(step), int(area)))
        # Suppress duplicate components around the same notehead.
        selected = []
        for cx, cy, step, area in sorted(possible, key=lambda p: -p[3]):
            if any(abs(cx - q[0]) < spacing * .75 and abs(cy - q[1]) < spacing * .55 for q in selected):
                continue
            selected.append((cx, cy, step, area))
        candidates = []
        for cx, cy, step, area in sorted(selected, key=lambda p: p[0])[:80]:
            candidates.append({"x": round(cx / w, 3), "y": round(cy / h, 3),
                "position": step, "note_if_treble": diatonic_name(step, "sol"),
                "note_if_bass": diatonic_name(step, "fa")})
        results.append({"staff": idx + 1, "lines": [round(v / h, 3) for v in group],
            "candidates": candidates})
    return {"staves": results, "warning": "Filtrage plus strict : faux positifs possibles et notes manquées. Les hauteurs supposent une clé non vérifiée."}
