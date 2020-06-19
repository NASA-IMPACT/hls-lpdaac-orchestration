FROM python:3.8-alpine

ARG AWS_ACCESS_KEY_ID 
ARG AWS_SECRET_ACCESS_KEY 
ARG AWS_SESSION_TOKEN 

RUN apk update
RUN apk add --no-cache aria2
RUN pip install -U pip
RUN pip install boto3

RUN apk add postgresql-dev gcc python3-dev musl-dev

WORKDIR /hls-lpdaac-orchestration

COPY . /hls-lpdaac-orchestration/
COPY . ~/.aws/

CMD ["python", "reconcile.py"]
