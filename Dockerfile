# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install rich cryptography
# Use -u for unbuffered logs so we can see server events in real-time on Fly.io
CMD ["python", "-u", "server.py"]