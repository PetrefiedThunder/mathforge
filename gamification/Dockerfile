# Stage 1: Build stage to install dependencies
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage using a minimal image
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY main.py .
COPY sms_handler.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]