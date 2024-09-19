FROM python:3.10-slim-bullseye

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        gcc \
        ffmpeg

RUN useradd -ms /bin/bash user
USER user
ENV HOME=/home/user
WORKDIR $HOME
RUN mkdir $HOME/.config && chmod -R 777 $HOME
ENV PATH="$HOME/.local/bin:$PATH"
        
WORKDIR $HOME/spotisub
ENV PATH="/home/uwsgi/.local/bin:${PATH}"

COPY requirements.txt .

RUN pip3 install -r requirements.txt

USER root
ENV HOME=/home/user
COPY main.py .
COPY init.py .
COPY spotisub spotisub/
COPY entrypoint.sh .
COPY first_run.sh .
COPY uwsgi.ini .
RUN chmod +x entrypoint.sh
RUN chmod +x first_run.sh

RUN chown -R user:user .


USER user
CMD ["./entrypoint.sh"]