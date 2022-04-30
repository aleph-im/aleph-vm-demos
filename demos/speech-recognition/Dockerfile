FROM debian:bullseye

RUN apt-get update && apt-get -y upgrade && apt-get install -y \
     libsecp256k1-dev \
     python3-pip \
     squashfs-tools \
     && rm -rf /var/lib/apt/lists/*

RUN pip install aleph-client==0.4.8

WORKDIR /usr/src/speech-recognition
COPY . .

RUN mkdir /opt/packages
RUN pip install -t /opt/packages -r requirements.txt
