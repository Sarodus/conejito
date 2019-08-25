FROM python

COPY . /data/workers
RUN pip install -U pip
RUN pip install -r /data/workers/requirements.txt

WORKDIR /data/workers
