FROM python:3.8-alpine

RUN apk update
RUN pip install -U pip
RUN pip install boto3

WORKDIR /hls-lpdaac-orchestration

COPY . /hls-lpdaac-orchestration/

CMD ["python", "reconcile.py"]
