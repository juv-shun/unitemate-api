FROM python:3.9-slim

RUN apt update && apt install -y nodejs npm awscli
RUN npm install -g serverless
RUN pip install -U pip && pip install poetry &&\
    poetry config virtualenvs.create false

WORKDIR /app
COPY ./ /app

RUN npm install
RUN poetry install
