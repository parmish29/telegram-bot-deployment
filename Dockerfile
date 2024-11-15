FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy everything from the local directory to the container's working directory
COPY . .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the default Cloud Run port
EXPOSE 8080

# Command to run the bot (ensure it's the entry point)
CMD ["python", "bot.py"]
