FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    g++ \
    make \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY app.py .
COPY requirements.txt .
COPY apt.txt .
COPY README.md .
COPY students/ students/

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port (Gradio uses 7860 by default)
EXPOSE 7860

# Run the app
CMD ["python", "app.py"]

