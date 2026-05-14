FROM python:3.13-slim AS builder

WORKDIR /src

COPY requirements.txt /src/requirements.txt

RUN pip wheel --no-cache-dir --wheel-dir=/src/dist -r requirements.txt

FROM python:3.13-slim

LABEL MAINTAINER="Jonnattan Griffiths"
LABEL VERSION=1.0
LABEL DESCRIPCION="Python Geo HTTP 1.0"

ENV TZ 'UTC'
ENV HOST_BD ''
ENV USER_BD ''
ENV PASS_BD ''

ENV FLASK_APP app
ENV FLASK_DEBUG production
ENV PATH="/home/jonnattan/.local/bin:${PATH}"
ENV PYTHONPATH="/home/jonnattan/.local/lib/python3.13/site-packages"

RUN addgroup --gid 10101 jonnattan && \
    adduser --home /home/jonnattan --uid 10100 --gid 10101 --disabled-password jonnattan && \
    echo "jonnattan:jonnattan" | chpasswd

RUN cd /home/jonnattan && \
    mkdir -p /home/jonnattan/.local/bin && \
    export PATH=$PATH:/home/jonnattan/.local/bin && \
    chmod -R 755 /home/jonnattan && \
    chown -R jonnattan:jonnattan /home/jonnattan

WORKDIR /home/jonnattan

COPY --from=builder --chown=10100:10101 --chmod=755 /src/dist /home/jonnattan/dist

COPY --chown=10100:10101 requirements.txt .

USER jonnattan

RUN pip install --no-cache-dir --no-index --find-links=file:///home/jonnattan/dist -r requirements.txt

WORKDIR /home/jonnattan/app

COPY --chown=10100:10101 ./app . 

EXPOSE 8075

CMD [ "python", "main.py", "8075"]

# pip freeze > requirements.txt
