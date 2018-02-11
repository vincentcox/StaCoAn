FROM python:3

RUN apt-get update && apt-get install upx -y

RUN git clone https://github.com/vincentcox/StaCoAn/
WORKDIR /StaCoAn/src
RUN pip3 install -r requirements.txt && chmod u+rwx /StaCoAn/src/jadx/bin/jadx

COPY stacoan.sh /stacoan.sh

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/stacoan.sh"]
