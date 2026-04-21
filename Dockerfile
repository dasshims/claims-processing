FROM node:20-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend-requirements.txt
RUN pip3 install --no-cache-dir -r /app/backend-requirements.txt

COPY web/package.json /app/web/package.json
WORKDIR /app/web
RUN npm install

WORKDIR /app
COPY backend /app/backend
COPY web /app/web
COPY hf_start.sh /app/hf_start.sh
RUN chmod +x /app/hf_start.sh

WORKDIR /app/web
RUN npm run build

WORKDIR /app
EXPOSE 7860

CMD ["/app/hf_start.sh"]
