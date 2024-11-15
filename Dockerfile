FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the container should listen on
EXPOSE 8080

# Ensure your bot is running in the background and listening on 8080 if needed
CMD ["python", "bot.py"]
