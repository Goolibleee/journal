# Use an official Python runtime as the base image
FROM python:3.11.4

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the port your application will run on
EXPOSE 8000

# Set the command to run your Flask application with Gunicorn
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000", "--log-level", "debug"]
