FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY services/api/requirements.cloudrun.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r /tmp/requirements.txt

COPY agents/__init__.py ./agents/__init__.py
COPY agents/google_adk/__init__.py agents/google_adk/runtime.py ./agents/google_adk/
COPY demo ./demo
COPY services ./services

RUN addgroup --system studiogrid && \
    adduser --system --ingroup studiogrid --home /nonexistent studiogrid
USER studiogrid

CMD ["sh", "-c", "exec uvicorn services.api.main:app --host 0.0.0.0 --port ${PORT}"]
