FROM python:3.12-slim

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

RUN useradd -m -u 1000 user

WORKDIR /home/user/app

COPY --chown=user apps/api/requirements.txt apps/api/requirements.txt

USER user

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r apps/api/requirements.txt

COPY --chown=user apps/api apps/api
COPY --chown=user data data

WORKDIR /home/user/app/apps/api

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
