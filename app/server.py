from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from music21 import converter, note, chord
import fitz
import tempfile
import base64

app = FastAPI(title="STELLA MUSIC AI")
ROOT = Path(__file__).parent
MAX_SIZE = 10 * 1024 * 1024
MAX_PAGES = 12

@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")

@app.get("/api/status")
def status():
    return {"musicxml_ready": True, "pdf_import_ready": True, "pdf_omr_ready": False, "vocal_synthesis_ready": False}

def inspect_pdf(data):
    if not data.startswith(b"%PDF-"):
        raise HTTPException(422, "Ce fichier ne semble pas être un PDF valide.")
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise HTTPException(422, "Les PDF protégés par mot de passe ne sont pas pris en charge.")
            if not 1 <= len(doc) <= MAX_PAGES:
                raise HTTPException(422, f"Le PDF doit contenir entre 1 et {MAX_PAGES} pages.")
            pages = []
            for i, page in enumerate(doc):
                # 96 DPI pour un aperçu léger sur mobile. Aucun document conservé.
                pix = page.get_pixmap(matrix=fitz.Matrix(1.33, 1.33), alpha=False)
                preview = base64.b64encode(pix.tobytes("jpeg", jpg_quality=65)).decode("ascii")
                pages.append({"number": i + 1, "width": round(page.rect.width), "height": round(page.rect.height), "preview": "data:image/jpeg;base64," + preview})
            return {"format": "pdf", "page_count": len(pages), "pages": pages, "parts": [], "omr_completed": False, "warning": "PDF importé et pages préparées. La reconnaissance des notes et des voix n'est pas encore disponible."}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, "Impossible de lire ce PDF.")

@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".xml", ".musicxml", ".mxl", ".pdf"):
        raise HTTPException(422, "Choisissez un PDF ou un fichier MusicXML.")
    data = await file.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "Taille maximale : 10 Mo")
    if suffix == ".pdf":
        return inspect_pdf(data)
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
            return {"format": "musicxml", "parts": parts, "warning": "Vérifier les voix et les notes avant apprentissage. Synthèse chantée non disponible."}
        except Exception:
            raise HTTPException(422, "Fichier MusicXML illisible")
