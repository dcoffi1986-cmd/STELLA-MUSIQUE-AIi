from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, Response
from music21 import converter, note, chord
import fitz
import tempfile
import base64
from omr_experimental import detect_staves_and_candidates
from audiveris_adapter import available as audiveris_available, recognize_pdf

app = FastAPI(title="STELLA MUSIC AI")
ROOT = Path(__file__).parent
MAX_SIZE = 10 * 1024 * 1024
MAX_PAGES = 12

@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")

@app.get("/api/status")
def status():
    return {"musicxml_ready": True, "pdf_import_ready": True, "pdf_omr_ready": "audiveris" if audiveris_available() else "experimental", "audiveris_installed": audiveris_available(), "vocal_synthesis_ready": False}

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
            recognition = []
            for i, page in enumerate(doc):
                # 96 DPI pour un aperçu léger sur mobile. Aucun document conservé.
                pix = page.get_pixmap(matrix=fitz.Matrix(1.33, 1.33), alpha=False)
                if i < 4:
                    try:
                        result = detect_staves_and_candidates(pix)
                        recognition.append({'page': i+1, **result})
                    except Exception:
                        recognition.append({'page': i+1, 'staves': [], 'warning': 'Détection impossible sur cette page.'})
                preview = base64.b64encode(pix.tobytes("jpeg", jpg_quality=65)).decode("ascii")
                pages.append({"number": i + 1, "width": round(page.rect.width), "height": round(page.rect.height), "preview": "data:image/jpeg;base64," + preview})
            return {"format": "pdf", "page_count": len(pages), "pages": pages, "parts": [], "recognition": recognition, "omr_completed": False, "warning": "PDF importé. Détection expérimentale des positions de notes, à vérifier. Les voix chantées ne sont pas disponibles."}
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

@app.post("/api/recognize-musicxml")
async def recognize_musicxml(file: UploadFile = File(...)):
    if not audiveris_available():
        raise HTTPException(503, "Le moteur Audiveris nécessite un serveur OMR dédié ; il n'est pas encore installé.")
    if Path(file.filename or "").suffix.lower() != ".pdf":
        raise HTTPException(422, "Choisissez une partition PDF.")
    data = await file.read(MAX_SIZE + 1)
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "Taille maximale : 10 Mo")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(422, "PDF invalide.")
    try:
        output, ext = recognize_pdf(data)
        return Response(content=output, media_type="application/octet-stream",
            headers={"Content-Disposition": 'attachment; filename="partition-reconnue' + ext + '"'})
    except RuntimeError as err:
        raise HTTPException(422, str(err))
