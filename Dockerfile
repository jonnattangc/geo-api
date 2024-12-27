FROM python:3.13-slim AS builder

WORKDIR /src

COPY requirements.txt /src/requirements.txt

RUN pip wheel --no-cache-dir --wheel-dir=/src/dist -r requirements.txt

FROM python:3.13.1-slim-bullseye

LABEL VERSION=1.0
LABEL DESCRIPCION="Python Geo HTTP 1.0"

ENV TZ 'UTC'
ENV HOST_BD ''
ENV USER_BD ''
ENV PASS_BD ''

ENV FLASK_APP app
ENV FLASK_DEBUG production

RUN addgroup --gid 10101 jonnattan && \
    adduser --home /home/jonnattan --uid 10100 --gid 10101 --disabled-password jonnattan

RUN cd /home/jonnattan && \
    mkdir -p /home/jonnattan/.local/bin && \
    export PATH=$PATH:/home/jonnattan/.local/bin && \
    chmod -R 755 /home/jonnattan && \
    chown -R jonnattan:jonnattan /home/jonnattan

WORKDIR /home/jonnattan

USER jonnattan

COPY . .

COPY --from=builder --chown=10100:10101 --chmod=755 /src/dist /home/jonnattan/dist

RUN pip install --no-cache-dir --no-index --find-links=file:///home/jonnattan/dist -r requirements.txt

WORKDIR /home/jonnattan/app

EXPOSE 8075

CMD [ "python", "http-server.py", "8075"]
# python3 http-server.py 8085
# CMD [ "tail", "-f", "/home/jonnattan/requirements.txt" ]
# pip freeze > requirements.txt
