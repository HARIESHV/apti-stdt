# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create directories for persistent data
RUN mkdir -p uploads static/question_images

# Expose the port from the environment or default to 5000
EXPOSE 5000

# Run app.py
CMD ["python", "app.py"]
