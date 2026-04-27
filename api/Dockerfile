FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1

WORKDIR /app

# Зависимости — отдельный слой, кэшируется
COPY shared/pyproject.toml /shared/pyproject.toml
COPY shared/nft_shared /shared/nft_shared
COPY api/pyproject.toml /app/pyproject.toml
RUN uv pip install /shared && uv pip install -e /app

# Исходный код
COPY api/app /app/app

# Порт и хост берём из env (API_HOST, API_PORT, API_WORKERS)
CMD ["sh", "-c", "uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --workers ${API_WORKERS:-1}"]
