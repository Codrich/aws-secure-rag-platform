FROM python:3.11-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /uvx /bin/

RUN groupadd -r app && useradd -r -g app app

WORKDIR /srv

COPY pyproject.toml uv.lock ./
COPY app/ ./app/

RUN uv sync --locked --no-dev --no-editable

ENV PATH="/srv/.venv/bin:$PATH"

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]