# Stage 1: Build stage - install dependencies.
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt .
# Install production dependencies without caching to keep the image lean.
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage - create the final runtime image.
FROM python:3.10-slim
WORKDIR /app
# Copy the installed Python packages from the builder stage.
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY main.py .
# Start the FastAPI server with uvicorn.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]