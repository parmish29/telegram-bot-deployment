# Use Python image
FROM python:3.10-slim

WORKDIR /app

# Copy all application files
COPY . .

# Copy credentials.json explicitly (if not part of the above copy)
COPY credentials.json /app/credentials.json

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "bot.py"]
