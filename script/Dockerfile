FROM ubuntu:latest

ENV build_dep='curl'

RUN apt-get -y update && apt-get install -y --no-install-recommends \
         python3 python3-distutils ca-certificates \
         $build_dep \
    && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py \
    && pip install --no-cache-dir --compile boto3 numpy pandas fsspec s3fs \
    && apt-get purge -y --auto-remove $build_dep \
    && find /usr/local/lib/python3.*/ -name 'tests' -exec rm -r {} + \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /hls-lpdaac-orchestration-historical-v2
COPY . /hls-lpdaac-orchestration-historical-v2/

CMD ["python3", "make_report_athena.py"]
