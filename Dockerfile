# Stage 1: Build frontend
FROM node:20-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run generate

# Stage 2: Python runtime
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    nmap \
    libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/

COPY --from=frontend-build /frontend/.output/public /usr/share/nginx/html

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /data

ENV BADPING_DB_PATH=/data/badping.db

EXPOSE 8765

LABEL org.opencontainers.image.title="BadPing"
LABEL org.opencontainers.image.description="Network monitoring tool - continuous ICMP/ARP ping with latency graphs and packet loss tracking"
LABEL org.opencontainers.image.url="https://github.com/badping/badping"
LABEL org.opencontainers.image.source="https://github.com/badping/badping"

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
