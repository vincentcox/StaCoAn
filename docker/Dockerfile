# Start from Alpine OS with Oracle JDK8
FROM anapsix/alpine-java:latest

# Install Python3 and dos2unix
RUN apk add --update --no-cache python3 dos2unix && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache && \
    
# Install StaCoAn
  apk add --update --no-cache git && \
  cd /tmp && \
  git clone https://github.com/vincentcox/StaCoAn/ && \
  cd / && \
  mv /tmp/StaCoAn/src/ /StaCoAn && \
  rm -rf /tmp/* && \
  pip3 install -r /StaCoAn/requirements.txt && \
  chmod u+rwx /StaCoAn/jadx/bin/jadx && \
# Housekeeping
  apk del git && \
  apk del apk-tools && \
  find / -type d -name __pycache__ -exec rm -r {} + && \
  rm -rf /usr/lib/python*/lib2to3 && \
  rm -rf /usr/lib/python*/turtledemo && \
  rm -f /usr/lib/python*/turtle.py && \
  #rm -f /usr/lib/python*/webbrowser.py && \
  rm -f /usr/lib/python*/doctest.py && \
  rm -f /usr/lib/python*/pydoc.py && \
  rm -rf /root/.cache && \
  rm -rf /var/cache && \
  rm -rf /usr/share/terminfo && \
  rm -f /StaCoAn/test-apk.apk && \
  rm -f /StaCoAn/stacoan-windows.spec && \
  rm -f /StaCoAn/requirements.txt && \
  rm -f /StaCoAn/icon.ico && \
  rm -rf /var/cache/* && \
  rm -rf /var/log/*

# Set workdir
WORKDIR /StaCoAn

# Copy the script
COPY stacoan.sh /stacoan.sh
RUN dos2unix /stacoan.sh
# -----------------------------------------------------------------------------------------
# Expose us
EXPOSE 8000
EXPOSE 8080
ENTRYPOINT ["/bin/bash", "/stacoan.sh"]
