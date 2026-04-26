FROM python:3.11-slim

WORKDIR /app

# Устанавливаем shared пакет и зависимости сервиса
COPY shared/ /shared/
COPY api/ /app/

RUN pip install --no-cache-dir -e /shared && \
    pip install --no-cache-dir -r /app/requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]