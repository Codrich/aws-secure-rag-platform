FROM python:3.11-slim AS base

# Non-root user
RUN groupadd -r app && useradd -r -g app app

WORKDIR /srv
COPY pyproject.toml ./
RUN pip install --no-cache-dir . && pip cache purge

COPY app/ ./app/

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
