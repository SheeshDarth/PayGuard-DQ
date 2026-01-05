FROM python:3.11-slim

WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Create directories for data and artifacts
RUN mkdir -p /app/data /app/artifacts

# Default port
ENV PORT=8000
EXPOSE 8000

# Use shell form to properly expand $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT

