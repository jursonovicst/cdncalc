FROM python:3.7

COPY cdn /cdn
COPY requirements.txt requirements.txt
WORKDIR /

RUN pip install -r requirements.txt

ENTRYPOINT ["/usr/local/bin/python", "-m", "cdn"]
