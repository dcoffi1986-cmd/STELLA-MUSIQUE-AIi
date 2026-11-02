"""Dedicated Audiveris worker. Protect /recognize with OMR_TOKEN."""
import os
import logging
import time
import threading
import subprocess
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Header, HTTPException
from fastapi.responses import Response

app = FastAPI(title="STELLA OMR")
BIN = Path(os.getenv("AUDIVERIS_BIN", "/opt/audiveris/bin/Audiveris"))
MAX_PDF = 10 * 1024 * 1024

def run_startup_diagnostic():
    """Run a one-time CLI startup test in background, without uploading a PDF."""
    started = time.monotonic()
    try:
        p = subprocess.run([str(BIN), "-help"], capture_output=True, text=True,
                           timeout=20, env={**os.environ, "JAVA_TOOL_OPTIONS": "-Xmx384m -Djava.awt.headless=true"})
        logging.warning("OMR_CLI_DIAGNOSTIC exit=%s duration=%.2fs output=%s",
                        p.returncode, time.monotonic()-started, (p.stdout+p.stderr)[-1200:])
    except subprocess.TimeoutExpired:
        logging.error("OMR_CLI_DIAGNOSTIC timeout after 20s")
    except Exception as exc:
        logging.error("OMR_CLI_DIAGNOSTIC failed: %s", type(exc).__name__)

@app.on_event("startup")
def startup_diagnostic():
    threading.Thread(target=run_startup_diagnostic, daemon=True).start()

@app.get("/health")
def health():
    return {"audiveris_installed": BIN.is_file() and os.access(BIN, os.X_OK)}

@app.get("/diagnostic")
def diagnostic(x_omr_token: str = Header(default="")):
    token = os.environ.get("OMR_TOKEN")
    if not token or x_omr_token != token:
        raise HTTPException(401, "Accès non autorisé")
    if not BIN.is_file():
        return {"installed": False, "cli_starts": False}
    started = time.monotonic()
    try:
        p = subprocess.run([str(BIN), "-help"], capture_output=True, text=True,
                           timeout=20, env={**os.environ, "JAVA_TOOL_OPTIONS": "-Xmx384m -Djava.awt.headless=true"})
        return {"installed": True, "cli_starts": p.returncode == 0,
                "exit_code": p.returncode, "duration_seconds": round(time.monotonic()-started, 2),
                "output_tail": (p.stdout + p.stderr)[-1200:]}
    except subprocess.TimeoutExpired:
        return {"installed": True, "cli_starts": False, "timeout_seconds": 20}

@app.post("/recognize")
async def recognize(file: UploadFile = File(...), x_omr_token: str = Header(default="")):
    token = os.environ.get("OMR_TOKEN")
    if not token or x_omr_token != token:
        raise HTTPException(401, "Accès non autorisé")
    if not BIN.is_file():
        raise HTTPException(503, "Audiveris absent")
    data = await file.read(MAX_PDF + 1)
    if len(data) > MAX_PDF:
        raise HTTPException(413, "PDF trop volumineux")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(422, "PDF invalide")
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        pdf = root / "partition.pdf"
        pdf.write_bytes(data)
        out = root / "out"
        out.mkdir()
        started = time.monotonic()
        try:
            proc = subprocess.run([str(BIN), "-batch", "-export", "-output", str(out), "--", str(pdf)],
                                  cwd=root, capture_output=True, text=True, timeout=150,
                                  env={**os.environ, "JAVA_TOOL_OPTIONS": "-Xmx384m -Djava.awt.headless=true"})
        except subprocess.TimeoutExpired as exc:
            tail = (exc.stderr or b"")
            if isinstance(tail, bytes):
                tail = tail.decode("utf-8", errors="replace")
            logging.error("Audiveris timeout after %.1fs stderr_tail=%s", time.monotonic() - started, tail[-1800:])
            raise HTTPException(504, "Délai de reconnaissance dépassé")
        logging.info("Audiveris finished in %.1fs exit=%s", time.monotonic() - started, proc.returncode)
        if proc.returncode:
            logging.error("Audiveris failed exit=%s stderr=%s stdout=%s", proc.returncode, proc.stderr[-3000:], proc.stdout[-1000:])
            raise HTTPException(422, "La reconnaissance de la partition a échoué")
        matches = sorted(out.rglob("*.mxl")) + sorted(out.rglob("*.musicxml"))
        if not matches:
            logging.error("Audiveris produced no MusicXML: stderr=%s stdout=%s", proc.stderr[-3000:], proc.stdout[-1000:])
            raise HTTPException(422, "Aucune partition MusicXML produite")
        result = matches[0]
        if result.stat().st_size > 15 * 1024 * 1024:
            raise HTTPException(413, "Résultat trop volumineux")
        return Response(result.read_bytes(), media_type="application/octet-stream",
                        headers={"X-Music-Extension": result.suffix})
