# Lightweight Python image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set workdir at service root so uvicorn can import main:app directly
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the source
COPY . /app

# Ensure bootstrap is executable
RUN chmod +x /app/bootstrap.sh

# Set default environment
ENV PORT=3001
ENV LOG_LEVEL=INFO

# Expose service port (PORT environment variable defaults to 3001)
EXPOSE 3001

# Use bootstrap entrypoint to guarantee deps/install and preflight check before start
ENTRYPOINT ["/app/bootstrap.sh"]
