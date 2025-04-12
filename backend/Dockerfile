FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt update && apt install -y sqlite3

CMD ["python", "app.py"]
