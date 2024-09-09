FROM python:3.10-slim-bullseye
ARG UID=1000
ARG GID=1000
ARG TZ=Europe/Rome

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        gcc \
        locales


RUN sed -i '/it_IT.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG it_IT.UTF-8  
ENV LANGUAGE it_IT:it  
ENV LC_ALL it_IT.UTF-8

RUN groupadd --gid $GID user
RUN useradd --no-log-init --create-home --shell /bin/bash --uid $UID --gid $GID user
USER user
ENV HOME=/home/user
WORKDIR $HOME
RUN mkdir $HOME/.cache $HOME/.config && chmod -R 777 $HOME
ENV PATH="$HOME/.local/bin:$PATH"
        
WORKDIR $HOME/spotify-to-subsonic
ENV PATH="/home/uwsgi/.local/bin:${PATH}"

COPY requirements.txt .

RUN pip3 install -r requirements.txt

USER root
ENV HOME=/home/user
COPY main.py .
COPY generate_playlists.py .
COPY entrypoint.sh .
COPY uwsgi.ini .
RUN chmod +x entrypoint.sh

RUN chown -R user:user .
RUN chmod 777 -R .


USER user
CMD ["./entrypoint.sh"]