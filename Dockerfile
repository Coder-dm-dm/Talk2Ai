# --- Stage 1: Builder for Dependencies ---
FROM python:3.12.3-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final Runtime Image ---
FROM python:3.12.3-slim
WORKDIR /app

# Create non-root user
RUN useradd --no-create-home appuser

# ✅ Create /data folder with proper permissions
RUN mkdir -p /data && chown -R appuser:appuser /data

# Switch to non-root user
USER appuser

# Copy installed dependencies
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Run app
CMD ["python", "answer_phone.py"]
