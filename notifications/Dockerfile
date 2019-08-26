FROM python

COPY . /data/notifications
RUN pip install -U pip
RUN pip install -r /data/notifications/requirements.txt

WORKDIR /data/notifications

CMD ["python", "./manage.py"]
