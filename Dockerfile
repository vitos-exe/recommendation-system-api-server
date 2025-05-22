# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv
RUN pip install uv

# Copy the dependency files
COPY pyproject.toml uv.lock* /app/

# Install dependencies using uv
# Using --system to install in the global site-packages
# If uv.lock exists, it will be used for faster, deterministic builds
RUN uv pip install --system --no-cache --requirement /app/pyproject.toml

# Copy the rest of the application code
COPY . /app/

# Copy SSL certificate and key
COPY localhost.pem /app/localhost.pem
COPY localhost-key.pem /app/localhost-key.pem

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/app/localhost-key.pem", "--ssl-certfile", "/app/localhost.pem"]
