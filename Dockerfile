# Dockerfile for Big Data Job Profile Analyzer
FROM python:3.9-slim

WORKDIR /app

# Copy project files
COPY analytics/ ./analytics/
COPY local_sim/ ./local_sim/
COPY config/ ./config/
COPY tests/ ./tests/
COPY analytics/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "analytics/visualize.py"]
