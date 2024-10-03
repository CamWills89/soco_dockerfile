FROM python:3.12-slim

# Set a working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy your Flask application code
COPY . .

# Expose the port (can be overridden by environment variable)
EXPOSE 8080

# Set environment variable for port
ENV FLASK_PORT=8080

# Run the app using the environment variable for port
CMD flask --app app run --host 0.0.0.0 -p ${FLASK_PORT}
