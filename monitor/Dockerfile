FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1

WORKDIR /app

COPY shared/pyproject.toml /shared/pyproject.toml
COPY shared/nft_shared /shared/nft_shared
COPY monitor/pyproject.toml /app/pyproject.toml
RUN uv pip install /shared && uv pip install -e /app

COPY monitor/app /app/app

CMD ["python", "-m", "app.main"]
