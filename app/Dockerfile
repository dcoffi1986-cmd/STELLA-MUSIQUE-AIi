FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip ca-certificates curl fontconfig libfreetype6 libxext6 libxrender1 libxtst6 libxi6 libasound2t64 tesseract-ocr tesseract-ocr-fra && rm -rf /var/lib/apt/lists/*
# Audiveris official Linux installer includes its Java runtime.
ARG AUDIVERIS_VERSION=5.11.0
RUN set -eux; \
    curl -fL --retry 3 -o /tmp/audiveris.deb "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu24.04-x86_64.deb"; \
    apt-get update; \
    apt-get install -y --no-install-recommends /tmp/audiveris.deb; \
    rm -f /tmp/audiveris.deb; rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PATH="/opt/venv/bin:${PATH}" AUDIVERIS_BIN="/opt/audiveris/bin/Audiveris" PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
