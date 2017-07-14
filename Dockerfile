FROM gliderlabs/alpine:3.3
MAINTAINER Karim Boumedhel <karimboumedhel@gmail.com>

RUN apk add --no-cache python python-dev py-pip build-base \
  && pip install pyTelegramBotAPI

ADD nickyabbot.py /
VOLUME ["/root/database.sqlite"]

CMD ["python", "/nickyabbot.py"]
