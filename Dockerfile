# Build stage
FROM python:3.9-slim as builder

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Final stage - for a lean production image
FROM python:3.9-slim

WORKDIR /app

# Copy installed python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy the application code itself
COPY --from=builder /app /app

EXPOSE 9876 8000 5001 8080

CMD ["python", "main.py"]