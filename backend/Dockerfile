FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.9.1+cpu torchvision==0.24.1+cpu
RUN pip install --no-cache-dir -r ./backend/requirements.txt

COPY backend/ ./backend/
COPY mars-wiut-cv-2026-1.0.0/mars-wiut-cv-2026-1.0/ ./mars-wiut-cv-2026-1.0/

ENV PYTHONPATH="/app/mars-wiut-cv-2026-1.0:/app/backend:${PYTHONPATH}"

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]