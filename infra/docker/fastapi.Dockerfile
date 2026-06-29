FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY apps/api/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt
COPY apps/api/ .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
