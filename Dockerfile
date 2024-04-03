FROM python:3.9

RUN mkdir usr/app
WORKDIR usr/app

COPY . .

RUN mkdir data

RUN pip install -r requirements.txt

CMD ["sh", "-c", "flask db upgrade && python run.py"]