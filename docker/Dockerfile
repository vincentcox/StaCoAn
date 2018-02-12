FROM python:3

RUN apt-get update && apt-get install upx software-properties-common -y

# https://github.com/re6exp/debian-jessie-oracle-jdk-8
RUN echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" | tee /etc/apt/sources.list.d/webupd8team-java.list  && \
    echo "deb-src http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main" | tee -a /etc/apt/sources.list.d/webupd8team-java.list  && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886  && \
    apt-get update

RUN echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections  && \
    echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections  && \
    DEBIAN_FRONTEND=noninteractive  apt-get install -y --force-yes oracle-java8-installer oracle-java8-set-default

RUN rm -rf /var/cache/oracle-jdk8-installer  && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/vincentcox/StaCoAn/
WORKDIR /StaCoAn/src
RUN pip3 install -r requirements.txt && chmod u+rwx /StaCoAn/src/jadx/bin/jadx

COPY stacoan.sh /stacoan.sh

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/stacoan.sh"]
