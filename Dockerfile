# Use a Python base image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY jira_api.py .

# Set environment variables (if needed)
COPY .env.docker .

# Run the Python script when the container starts
CMD ["python", "jira_api.py"]