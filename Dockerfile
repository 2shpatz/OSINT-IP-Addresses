FROM python:3.11
# FROM ubuntu:22.04

WORKDIR /service

COPY /utils/* /tmp

RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip install -r /tmp/requirements.txt
RUN rm -rf /tmp

COPY /src/ /service/

ENTRYPOINT [ "python3" ]
CMD [ "service.py" ]