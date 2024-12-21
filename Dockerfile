# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Tesseract OCR and other dependencies
RUN apt-get update && apt-get install -y tesseract-ocr

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 10000
EXPOSE 10000

# Set the Tesseract command and data directory environment variables
ENV TESSERACT_CMD /usr/bin/tesseract
ENV TESSDATA_DIR /usr/share/tesseract-ocr/4.00/tessdata

# Run the application using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
