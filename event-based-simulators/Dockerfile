FROM python:3.8.11-alpine3.14

RUN pip install requests \
    && addgroup -S appgroup \
    && adduser -S appuser -G appgroup

ADD --chown=appuser:appgroup main /home/appuser
WORKDIR /home/appuser

USER appuser
CMD [ "python", "./event_based_simulators.py" ]
