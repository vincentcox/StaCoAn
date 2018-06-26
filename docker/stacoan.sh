#!/bin/bash
pwd
ls -la
ls -la /
python3 /StaCoAn/src/stacoan.py --disable-browser --enable-server

# https://stackoverflow.com/questions/90418/exit-shell-script-based-on-process-exit-code
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

# Redirect to start.html
echo "<script>window.location = 'http://'+window.location.hostname+':8080'+'/start.html';</script>" > /StaCoAn/src/report/index.html
cd /StaCoAn/src/report/ && python -m http.server 8080
