FROM python:3.10-slim-bullseye

# Install dependencies and gosu
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        gcc \
        ffmpeg \
        curl && \
        curl -LO https://github.com/tianon/gosu/releases/latest/download/gosu-$(dpkg --print-architecture | awk -F- '{ print $NF }') \
        && chmod 0755 gosu-$(dpkg --print-architecture | awk -F- '{ print $NF }') \
        && mv gosu-$(dpkg --print-architecture | awk -F- '{ print $NF }') /usr/local/bin/gosu && \
        rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash user

USER user
ENV HOME=/home/user
ENV PATH="$HOME/.local/bin:$PATH"

WORKDIR $HOME/spotisub
ENV PATH="/home/uwsgi/.local/bin:${PATH}"

COPY main.py init.py entrypoint.sh first_run.sh uwsgi.ini requirements.txt ./
COPY spotisub spotisub/
RUN pip3 install --no-cache-dir -r requirements.txt

USER root
RUN chmod +x entrypoint.sh && \
    chmod +x first_run.sh && \
    chown -R user:user .

# CMD runs as root initially but switches to the user inside entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]