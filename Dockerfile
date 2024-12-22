# Use an official Python image as the base
FROM python:3.10-slim

# Install system dependencies and Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the application code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 5500

# Command to run the application
CMD ["python", "app.py"]
