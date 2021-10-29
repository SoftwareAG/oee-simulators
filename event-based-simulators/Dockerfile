FROM python:3.8.11-alpine3.14

# event based simulator
ADD event_based_simulators.py /

# simulator definitions
ADD sumulators.json /

RUN pip install requests

CMD [ "python", "./event_based_simulators.py" ]
