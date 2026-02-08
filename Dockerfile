# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install rich cryptography
CMD ["python", "server.py"]