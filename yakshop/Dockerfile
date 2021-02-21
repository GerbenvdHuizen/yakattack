FROM python:3
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000