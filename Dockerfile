# Use a lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=True
ENV PORT=8080

# Install system dependencies required for OpenCV & NumPy
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Expose Cloud Run port
EXPOSE 8080

# Run ADK Web Server
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8080"]
