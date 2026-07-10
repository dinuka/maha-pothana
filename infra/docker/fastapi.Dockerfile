FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-noto-core \
    fonts-noto-devanagari \
    fonts-noto-sinhala \
    && rm -rf /var/lib/apt/lists/*
RUN pip install uv
COPY apps/api/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt
COPY apps/api/ .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
