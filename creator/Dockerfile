FROM python

ENV STATIC_URL /static
ENV STATIC_PATH /data/creator/static
COPY . /data/creator
RUN pip install -U pip
RUN pip install -r /data/creator/requirements.txt

WORKDIR /data/creator

CMD ["python", "./manage.py"]
