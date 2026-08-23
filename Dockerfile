FROM python:3.11-slim
WORKDIR /app

# Install dependencies dulu (layer cache)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy kode backend + frontend + landing jadi 1 image
COPY backend/app ./app
COPY frontend ./frontend
COPY landing ./landing

EXPOSE 8000
# Render inject $PORT; fallback ke 8000 untuk lokal
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
