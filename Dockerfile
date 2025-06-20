# syntax=docker/dockerfile:1

FROM python:3

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "subitize_app.py" ]
