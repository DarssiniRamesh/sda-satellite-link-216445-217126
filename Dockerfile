# Lightweight Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install system deps if needed (none required now)
# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source
COPY . /app

# Default environment
ENV PORT=3001
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 3001

# Run using uvicorn without requiring venv activation
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
