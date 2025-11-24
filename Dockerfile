# Lightweight Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set workdir at service root so uvicorn can import main:app directly
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY . /app

# Set default environment
ENV PORT=3001
ENV LOG_LEVEL=INFO

# Expose service port
EXPOSE 3001

# Ensure we run from the service root so 'uvicorn main:app' finds /app/main.py
# No need to modify PYTHONPATH because /app is the working directory
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
