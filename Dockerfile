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

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV PORT=5000
ENV MONGO_URI=mongodb://mongodb:27017/aptipro

# Run app.py when the container launches
# Waitress is used inside app.py so this is production-ready
CMD ["python", "app.py"]
