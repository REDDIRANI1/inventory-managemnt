FROM python:3.12-slim

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update \
    && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Set permissions
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
