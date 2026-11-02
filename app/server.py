from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from music21 import converter, note, chord
import tempfile

app = FastAPI(title="STELLA MUSIC AI")
ROOT = Path(__file__).parent

@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")

@app.get("/api/status")
def status():
    return {"musicxml_ready": True, "pdf_omr_ready": False, "vocal_synthesis_ready": False}

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".xml", ".musicxml", ".mxl"):
        raise HTTPException(422, "Cette première version analyse MusicXML. La reconnaissance PDF/image arrive ensuite.")
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "Taille maximale : 10 Mo")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ("score" + suffix)
        path.write_bytes(data)
        try:
            score = converter.parse(str(path))
            parts = []
            for i, part in enumerate(score.parts):
                events = []
                for el in part.recurse().notesAndRests:
                    pitches = [] if isinstance(el, note.Rest) else ([p.midi for p in el.pitches] if isinstance(el, chord.Chord) else [el.pitch.midi])
                    events.append({"offset": float(el.getOffsetInHierarchy(part)), "duration": float(el.quarterLength), "pitches": pitches, "lyric": getattr(el, "lyric", "") or ""})
                parts.append({"name": part.partName or f"Partie {i+1}", "events": events})
            return {"parts": parts, "warning": "Vérifier les voix et les notes avant apprentissage. Synthèse chantée non disponible."}
        except Exception:
            raise HTTPException(422, "Fichier MusicXML illisible")
