FROM python:3.8.11-alpine3.14

ADD main /

RUN pip install requests

CMD [ "python", "./event_based_simulators.py" ]
