# syntax=docker/dockerfile:1

# This image runs the Qt desktop pet app under Linux.
# Notes:
# - You need an X server on the host (Linux desktop) and pass DISPLAY + X11 socket.
# - On Windows/macOS you typically need an X server (VcXsrv/XQuartz) or run via VNC.
# - Ollama is NOT bundled; point BASE_URL to your Ollama endpoint.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- System deps for Qt/X11 ---
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgl1 \
      libegl1 \
      libxkbcommon0 \
      libx11-6 \
      libxext6 \
      libxrender1 \
      libxcb1 \
      libxfixes3 \
      libxi6 \
      libxrandr2 \
      libxcursor1 \
      libxinerama1 \
      libdbus-1-3 \
      libfontconfig1 \
      libfreetype6 \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Python deps (minimal) ---
COPY requirements.docker.txt ./requirements.docker.txt
RUN pip install --no-cache-dir -r requirements.docker.txt

# --- App code ---
COPY src ./src
COPY config.yaml config.example.yaml .
COPY AGENT.md .

# (Optional) copy your avatar asset if present
# COPY somebody.png ./somebody.png

# Default envs (override at runtime)
ENV BASE_URL=http://host.docker.internal:11434 \
    MODEL_NAME=qwen3.5:0.8b \
    LLM_ADAPTER=ollama_chat \
    OLLAMA_THINK=0 \
    HTTP_TIMEOUT_SECONDS=60

CMD ["python", "-m", "src.main"]
