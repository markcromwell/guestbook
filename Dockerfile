FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Package lives under src/ (src-layout); put it on the import path so `main:app`
# (which does `from guestbook.app import app`) resolves in the container.
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8765"]
