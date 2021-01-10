FROM python:3.7

RUN mkdir /app
RUN mkdir /app/input
RUN mkdir /data
RUN mkdir /data/satd
VOLUME /data
WORKDIR /app

RUN apt-get update && \
apt-get install -y openjdk-11-jdk && \
apt-get clean;
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
ADD src /app/src
ADD conf /app/conf
ADD requirements.txt /app/
ADD run.sh /app/
RUN chmod +x run.sh

RUN ["pip", "install", "-r", "requirements.txt"]
