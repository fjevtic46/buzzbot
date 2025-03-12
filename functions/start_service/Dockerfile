#Image Building: You'll need to build the Docker image for the start-service and push it to Google Container Registry (GCR).

FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]