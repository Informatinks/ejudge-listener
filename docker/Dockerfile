FROM python:3.6-alpine

ENV FLASK_APP=listener:app
ENV PIP_INDEX_URL=https://registry.tcsbank.ru/repository/pypi-all/simple/

COPY . /code
WORKDIR /code

RUN pip3 install -r requirements.txt -r dev-requirements.txt

CMD sleep 30 && flask test
