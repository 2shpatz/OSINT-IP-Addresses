FROM python:3.11
# FROM ubuntu:22.04
ARG APP_PORT=5000


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "${PYTHONPATH}:/service"

WORKDIR /service

COPY /utils/* /tmp

RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip install -r /tmp/requirements.txt
RUN rm -rf /tmp

COPY /src/ /service/

EXPOSE ${APP_PORT}
ENTRYPOINT [ "python3" ]
CMD [ "service.py" ]