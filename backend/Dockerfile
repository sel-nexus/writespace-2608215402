FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app
RUN addgroup --system writespace && adduser --system --ingroup writespace writespace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY entrypoint.sh /usr/local/bin/writespace-entrypoint
RUN chmod 755 /usr/local/bin/writespace-entrypoint && mkdir -p /app/data && chown -R writespace:writespace /app
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/writespace-entrypoint"]
