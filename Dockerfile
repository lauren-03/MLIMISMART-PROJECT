# MlimiSmart: website and API in one container (Render, or any Docker host).

# 1. Build the React website
FROM node:22-slim AS website
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 2. Python API, which also serves the built website
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
WORKDIR /app

COPY backend/requirements.txt backend/requirements-english-voice.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
# The English voice needs about 1 GB of memory; leave it out on small servers.
ARG ENGLISH_VOICE=false
RUN if [ "$ENGLISH_VOICE" = "true" ]; then \
      pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
      && pip install --no-cache-dir -r backend/requirements-english-voice.txt; fi

COPY backend/ backend/
COPY --from=website /web/dist frontend/dist

# Chichewa voice (Kasanoma, Piper)
RUN mkdir -p backend/voices/kasanoma-chichewa \
    && curl -fsSL -o backend/voices/kasanoma-chichewa/model.onnx \
       https://huggingface.co/OpenVoiceOS/kasanoma-chichewa/resolve/main/model.onnx \
    && curl -fsSL -o backend/voices/kasanoma-chichewa/model.onnx.json \
       https://huggingface.co/OpenVoiceOS/kasanoma-chichewa/resolve/main/model.onnx.json

RUN chown -R user:user /app
USER user
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/home/user/.cache/huggingface \
    START_TUNNEL=false
WORKDIR /app/backend
EXPOSE 7860
CMD ["sh", "start.sh"]
