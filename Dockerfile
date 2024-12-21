FROM python:3.11-slim

# Install OpenCV dependencies (libGL.so.1)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy your application code
COPY . /app

# Set the working directory
WORKDIR /app

# Start the app with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
