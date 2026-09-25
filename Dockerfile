FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if required for NLP libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
# For production MVP, install essential subset directly
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install fastapi uvicorn pydantic networkx requests spacy sentence-transformers

# Download Spacy model
RUN python -m spacy download en_core_web_sm || true

# Copy source code
COPY src/ /app/src/
COPY config/ /app/config/
COPY tests/ /app/tests/

# Expose FastAPI port
EXPOSE 8000

# Set environment to production
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Run API server
CMD ["python", "-m", "src.main", "api", "--port", "8000"]
