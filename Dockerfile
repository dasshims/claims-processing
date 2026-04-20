FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

COPY backend/requirements.txt /app/backend-requirements.txt
COPY frontend/requirements.txt /app/frontend-requirements.txt
RUN pip install --no-cache-dir -r /app/backend-requirements.txt -r /app/frontend-requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend
COPY hf_start.sh /app/hf_start.sh
RUN chmod +x /app/hf_start.sh

EXPOSE 7860

CMD ["/app/hf_start.sh"]
