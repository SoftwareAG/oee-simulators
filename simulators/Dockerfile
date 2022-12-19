FROM python:3.8.11-alpine3.14

RUN pip install requests \
    && addgroup -S appgroup \
    && adduser -S appuser -G appgroup

ADD --chown=appuser:appgroup main /home/appuser
WORKDIR /home/appuser

USER appuser

ARG ARG_CREATE_PROFILES
ENV CREATE_PROFILES ${ARG_CREATE_PROFILES:-false}

CMD [ "python", "./simulators.py" ]
