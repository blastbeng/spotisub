FROM python:3.10-slim-bullseye

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        gcc \
        ffmpeg

ENV PATH="/home/uwsgi/.local/bin:${PATH}"

COPY requirements.txt .

RUN pip3 install -r requirements.txt

RUN mkdir -p /home/user 

WORKDIR /home/user

COPY main.py .
COPY init.py .
COPY spotisub spotisub/
COPY entrypoint.sh .
COPY first_run.sh .
COPY uwsgi.ini .
RUN chmod +x entrypoint.sh
RUN chmod +x first_run.sh

CMD ["./entrypoint.sh"]