"""Adaptateur Audiveris pour une installation OMR dédiée.

N'exécute Audiveris que si un binaire explicitement configuré existe.
Les fichiers temporaires sont supprimés après chaque conversion.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

MAX_OUTPUT = 15 * 1024 * 1024

def available():
    binary = os.environ.get("AUDIVERIS_BIN", "")
    return bool(binary and Path(binary).is_file() and os.access(binary, os.X_OK))

def recognize_pdf(data: bytes):
    if not available():
        raise RuntimeError("Audiveris n'est pas installé sur ce serveur.")
    with tempfile.TemporaryDirectory(prefix="stella_omr_") as temp:
        root = Path(temp)
        input_file = root / "partition.pdf"
        output = root / "output"
        output.mkdir()
        input_file.write_bytes(data)
        command = [os.environ["AUDIVERIS_BIN"], "-batch", "-export",
                   "-output", str(output), "--", str(input_file)]
        try:
            proc = subprocess.run(command, cwd=root, capture_output=True, text=True,
                                  timeout=150, check=False, env={**os.environ, "JAVA_TOOL_OPTIONS": "-Xmx512m -Djava.awt.headless=true"})
        except subprocess.TimeoutExpired:
            raise RuntimeError("La reconnaissance a dépassé la limite de temps.")
        if proc.returncode != 0:
            raise RuntimeError("Audiveris n'a pas pu transcrire cette partition.")
        files = sorted(output.rglob("*.mxl")) + sorted(output.rglob("*.musicxml"))
        if not files:
            raise RuntimeError("Audiveris n'a pas produit de partition MusicXML.")
        result = files[0]
        if result.stat().st_size > MAX_OUTPUT:
            raise RuntimeError("Le résultat MusicXML est trop volumineux.")
        if result.suffix == ".mxl" and not zipfile.is_zipfile(result):
            raise RuntimeError("Le résultat MXL est invalide.")
        return result.read_bytes(), result.suffix
