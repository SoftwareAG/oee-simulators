FROM postman/newman:alpine
LABEL maintainer="Alexander Eimer <alexander.eimer@adamos.com>"

# To have a global installed package available via require
ENV NODE_PATH=/usr/local/lib/node_modules

# Some config stuff
ENV DELAY_REQUEST 1000
ENV DELAY_ROUNDS 30000

COPY entrypoint.js .

ENTRYPOINT [ "node", "entrypoint.js" ]
CMD [ "" ]
