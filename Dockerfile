# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script and credentials
COPY bot.py .
COPY credentials.json .

# Expose the port the bot listens on (if applicable)
# EXPOSE 8080 (only needed if the bot serves via a port)

# Run the bot
CMD ["python", "bot.py"]
