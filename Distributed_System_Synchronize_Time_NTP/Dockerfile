FROM python:3.10-slim

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies (none needed for this project)
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true

# Make sure logs and results directories exist
RUN mkdir -p logs results

# Default command (will be overridden by docker-compose)
CMD ["python", "-m", "main"]
