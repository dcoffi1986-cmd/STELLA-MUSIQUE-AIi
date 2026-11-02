FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip curl ca-certificates fontconfig libfreetype6 libxext6 libxrender1 libxtst6 libxi6 libasound2t64 tesseract-ocr tesseract-ocr-fra && rm -rf /var/lib/apt/lists/*
ARG AUDIVERIS_VERSION=5.11.0
RUN set -eux; curl -fL --retry 3 -o /tmp/audiveris.deb "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu24.04-x86_64.deb"; dpkg-deb -x /tmp/audiveris.deb /; rm /tmp/audiveris.deb
WORKDIR /omr
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir fastapi uvicorn python-multipart
COPY omr/server.py /omr/server.py
ENV PATH="/opt/venv/bin:${PATH}" AUDIVERIS_BIN="/opt/audiveris/bin/Audiveris" PYTHONUNBUFFERED=1
EXPOSE 10000
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-10000}"]
