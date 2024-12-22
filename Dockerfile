# Use an official Python image as the base
FROM python:3.10-slim

# Install system dependencies, Tesseract, and libGL
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    && apt-get clean

# Set the TESSDATA_PREFIX environment variable
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/

# Copy tessdata files to the correct location
COPY tessdata /usr/share/tesseract-ocr/4.00/tessdata/

# Set the working directory in the container
WORKDIR /app

# Copy application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5500

# Command to run the application
CMD ["python", "app.py"]
