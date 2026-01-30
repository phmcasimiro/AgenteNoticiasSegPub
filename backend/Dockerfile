# Build Stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies to a local directory
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime Stage
FROM python:3.10-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Copy backend code
# We copy the whole project structure because functionality depends on imports
COPY backend /app/backend

# Expose port
EXPOSE 8001

# Command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
