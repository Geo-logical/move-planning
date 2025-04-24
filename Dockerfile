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

# Expose port
EXPOSE 8050

# Run the app with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8050", "item_planning:server"]

