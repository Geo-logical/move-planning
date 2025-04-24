# Use a lightweight Python base
FROM python:3.11-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Make sure the /data directory exists and move DB there
RUN mkdir -p /data 
COPY move_data.db /data/move_data.db

# Expose port
EXPOSE 10000

# Run the app with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "item_planning:server"]

