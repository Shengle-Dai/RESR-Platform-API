FROM python:3.9

RUN mkdir usr/app
WORKDIR usr/app

COPY . .

RUN mkdir data

RUN pip install -r requirements.txt

RUN flask db init

RUN flask db migrate

RUN flask db upgrade

CMD python run.py