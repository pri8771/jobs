# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --upgrade pip && pip install .

COPY config/ ./config/
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

ENTRYPOINT ["jobs-automation"]
CMD ["dashboard", "--host", "0.0.0.0", "--port", "8080"]
