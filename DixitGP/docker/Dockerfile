FROM python:3.10
ENV PYTHONUNBUFFERED 1
RUN mkdir /usr/dixit_bot/
WORKDIR /usr/dixit_bot/
COPY ./requirements.txt .
RUN pip install -r requirements.txt
COPY . .
