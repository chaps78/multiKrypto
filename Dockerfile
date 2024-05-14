FROM python:3.10



RUN   apt-get update \
  && apt-get install -y python3-pip python3-dev\
  && pip3 install pyTelegramBotAPI\
  && pip3 install python-binance\
  && pip3 install oauth2client\
  && pip3 install gspread



ADD . /app/





WORKDIR /app


CMD python3 trader.py > /app/pyout.txt
