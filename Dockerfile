FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# # Install system dependencies
# RUN apt-get update \
#     && apt-get -y install netcat-traditional gcc \
#     && apt-get clean

RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install
