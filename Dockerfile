# All-in-one image (used by render.yaml): builds the web app, then runs
# API + Telegram webhook + reminders + Mini App/admin in a single service.

FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist ./static
RUN chmod +x scripts/start.sh && useradd --create-home --uid 10001 app && chown -R app /app
USER app
EXPOSE 8000
CMD ["./scripts/start.sh"]
