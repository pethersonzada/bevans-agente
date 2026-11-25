FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home suporte
COPY agente.py suporte.py api_bevans.py ./
COPY dados/suporte.json dados/suporte.json
USER suporte
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn api_bevans:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
